"""`Bitcrusher`'s own invariant and planted-fault tests.

The dossier is `workspace docs/effects-internal/dossiers/Bitcrusher.md`.
Exhaustive rate coverage lives in the evidence pack, not here.
"""

import math
import os
import sys
import unittest
from array import array

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audiocore                                                # noqa: E402
import kit_faults                                               # noqa: E402
import kit_probes as probes                                     # noqa: E402
from audioeffects import bitcrusher as rebuilt                  # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

VENDOR = "PyDevices"

RATE = 48000
Bitcrusher = rebuilt.Bitcrusher


def source(frames=2048, channels=2, rate=RATE, peak=12000, hz=1000.0):
    t = np.arange(frames)
    tone = np.round(peak * np.sin(2.0 * np.pi * hz * t / rate)).astype(np.int16)
    pcm = np.empty(frames * channels, dtype=np.int16)
    for channel in range(channels):
        pcm[channel::channels] = tone
    return audiocore.RawSample(
        array("h", pcm.tobytes()), sample_rate=rate, channel_count=channels)


def silence_source(frames=2048, channels=2, rate=RATE):
    return audiocore.RawSample(
        array("h", bytes(frames * channels * 2)),
        sample_rate=rate, channel_count=channels)


def left(render):
    return render.data[:, 0].astype(np.float64)


class FloorQuantize(Bitcrusher):
    """T1's fault: the staircase floors instead of rounding."""

    NAME = 'Bitcrusher'
    FLOOR = True


class WrongStep(Bitcrusher):
    """T2's fault: two bits stolen, so Δ is four times too big."""

    NAME = 'Bitcrusher'
    BITS_OFFSET = -2


class ForcedBandLimit(Bitcrusher):
    """T5's fault: the anti-alias filter is locked on."""

    NAME = 'Bitcrusher'
    FORCE_BAND_LIMIT = True


class SnapRate(Bitcrusher):
    """T6's fault: hold ratio snapped to an integer."""

    NAME = 'Bitcrusher'
    SNAP_RATE = True


class LateClick(Bitcrusher):
    """CLICK: report 256 samples of latency the DSP does not have."""

    NAME = 'Bitcrusher'
    LATENCY_SAMPLES = 256


class SkewedHold(Bitcrusher):
    """T4's and T5's fault: the hold runs at two fifths of the rate it
    reports.

    Same kind -- it is still one `audioshaper.SampleHold` doing a
    zero-order hold on an exact integer ratio, so this is not a filter
    wearing a disguise. What it breaks is the one thing both rows are
    about: the hold rate the class says it has. T4's sinc tilt is computed
    from the REPORTED rate and the wet is held at 0.4 of it, so the tilt is
    the wrong curve -- 3.06 dB out at the shipped hold's own 5 kHz point,
    not only on the integer-4 leg the last fault needed. T5's images move
    from |f - k*f_hold| to |f - 0.4k*f_hold| and the bin the trait names
    goes empty; two fifths and not a half on purpose, because halving the
    hold rate leaves k = 2 sitting on the same 1 kHz image.

    It fires wherever the wet branch is live, including at 22.05 kHz where
    the shipped Rate clamps to the running rate and the clean class is an
    identity: halving an identity is still a hold. Unreachable -- no macro
    sets the reported rate apart from the running one, and the clamp is the
    only place the two meet, which is exactly where this fault differs
    most.
    """

    NAME = 'Bitcrusher'
    HOLD_SKEW = (2, 5)


def staircase(frames=2048, dwell=8, bits=12, channels=2):
    """A slow amplitude staircase: `dwell` frames on each code.

    This is T2's material AT THE SHIPPED DEFAULT. A sine's residual through
    patch 0 is the hold's, not the quantizer's -- the hold's error is a
    thousand times the quantizer's, so `WrongStep` cannot be told from the
    clean class there (audiocomponents#71). Material that is already
    piecewise constant for longer than one hold period passes the hold
    almost untouched, so what is left is the staircase the Bits knob sets.

    **The step scales with the depth**, which is the fix the second-pass
    refutation asked for. It used to climb one code per stair whatever Bits
    said, so at 12 bits it crossed the row's stated sixteen quantizer steps
    and at 8 bits it crossed one -- and `WrongStep` read exactly 1.0000 at
    Bits MIDI 72 and 80 and at shipped patches 1 and 3, where a guard that
    cannot move is not a guard. Delta/16 per stair crosses sixteen steps at
    every depth the material can hold (4 bits and up: at 3 the staircase
    would need 131072 codes and there are 65536).
    """
    step = max(1, (1 << (16 - int(bits))) // 16)
    codes = (np.arange(frames) // dwell) * step
    one = np.clip(codes - (frames // (2 * dwell)) * step,
                  -32768, 32767).astype(np.int16)
    pcm = np.empty(frames * channels, dtype=np.int16)
    for channel in range(channels):
        pcm[channel::channels] = one
    return pcm


def wide_click(frames=8192, offset=256, width=4, channels=2):
    """`kit_probes.click_stereo` is ONE nonzero sample, and a decimating
    hold keeps `den` of every `num` frames, so at patch 0's Rate 45 % of
    offsets vanish at 48 kHz and 40 % at 44.1. That is a sample-and-hold
    working, not the class failing. A latency probe needs an event at
    least ceil(N) samples wide."""
    pcm = np.zeros(frames * channels, dtype=np.int16)
    for channel in range(channels):
        start = offset * channels + channel
        pcm[start:(offset + width) * channels:channels] = 16384
    return pcm


def full_ramp(frames=65536, channels=2):
    """A full-scale ramp, one code per frame -- T1's and T2's wide material
    at Rate = the running rate. It visits every code of the table, which a
    sine at any one amplitude does not."""
    one = np.clip(np.round(-32768.0 + 65535.0 * np.arange(frames)
                           / (frames - 1)), -32768, 32767).astype(np.int16)
    pcm = np.empty(frames * channels, dtype=np.int16)
    for channel in range(channels):
        pcm[channel::channels] = one
    return pcm


#: One table point stands for this many int16 codes, and every riser in the
#: staircase is that wide. `bitcrusher.CURVE_STEP`, repeated here so the
#: test states the law rather than importing it from the thing under test.
CURVE_STEP = 8


def law_mean(bits):
    """T1's mean error on ONE-SIDED material, in LSB: `s / 2Delta`."""
    return CURVE_STEP / (2.0 * (1 << (16 - int(bits))))


def law_ratio(bits):
    """T2's DC-removed rms over Delta/sqrt(12): `1 - s/Delta`."""
    return 1.0 - CURVE_STEP / float(1 << (16 - int(bits)))


def residual(cls, material, rate=RATE, wet=True, **kw):
    """(mean, max, rms) of wet - dry, each divided by its own unit.

    Read on the WET BRANCH by default (audiocomponents#78's `wet_render`),
    so Mix scales nothing: T1 and T2 are statements about the converter,
    and reading them through the blend made `WrongStep` unreadable at Mix
    MIDI 32 because the CLEAN class was red there too.
    """
    frames = len(material) // 2
    wet_src = probes.ArraySource(material, rate=rate, channels=2, block=256)
    dry_src = probes.ArraySource(material, rate=rate, channels=2, block=256)
    effect = cls.create(wet_src, rate, **kw)
    bits = int(round(effect.macro(0)))
    if wet and effect.macro(4) > 0.0:
        try:
            rendered = probes.wet_render(effect, frames, rate=rate)
        except kit.MeasurementRefused:
            # A null build IS a wire: its output is the borrowed source and
            # there is no dry voice to mute, so its whole output is its wet
            # branch. Every other build goes through `wet_render`.
            rendered = probes.render(effect.output, frames, rate=rate,
                                     allow_starved_taps=True)
    else:
        rendered = probes.render(effect.output, frames, rate=rate)
    dry = probes.render(dry_src, frames, rate=rate)
    effect.deinit()
    err = left(rendered) - left(dry)
    delta = float(1 << (16 - bits))
    centred = err - err.mean()
    rms = math.sqrt(float(np.mean(centred * centred)))
    return (err.mean() / delta, float(np.max(np.abs(err))) / delta,
            rms / (delta / math.sqrt(12.0)))


class TheSurface(unittest.TestCase):

    def test_six_macros_and_seven_patches(self):
        effect = Bitcrusher.create(source(), RATE)
        self.assertEqual(len(Bitcrusher.MACRO_LABELS), 6)
        self.assertEqual(len(Bitcrusher.PATCHES), 7)
        self.assertEqual(effect.macro(0), 12.0)
        self.assertAlmostEqual(effect.macro(1), 26040.0, delta=1.0)
        self.assertEqual(effect.macro(2), 0.0)
        self.assertEqual(effect.macro(3), 0.0)
        self.assertEqual(effect.macro(4), 1.0)
        self.assertEqual(effect.macro(5), 0.0)
        # The hold displaces an event by up to ceil(N) - 1 samples and the
        # kit reads exactly that; declaring 0 was red at 44.1 kHz.
        self.assertEqual(effect.latency_samples, 1)
        self.assertEqual(effect.tail_samples, 0)
        self.assertEqual(effect.capabilities, ())
        effect.deinit()

    def test_band_limit_reports_a_tail(self):
        effect = Bitcrusher.create(source(), RATE)
        effect.set_macro(3, 127)
        self.assertEqual(effect.tail_samples, 640)
        effect.deinit()

    def test_the_reported_tail_bounds_the_worst_corner(self):
        """Every Rate stop at every rate, not the one the default sets.
        The worst is Rate MIDI 0 at 44.1 kHz -- a 420 Hz corner -- and it
        rings 530 frames, which 640 bounds and 256 did not."""
        worst = 0
        for rate in (48000, 44100, 22050):
            for midi in range(0, 128, 16):
                frames = 8192
                pcm = np.zeros(frames * 2, dtype=np.int16)
                burst = (20000 * np.sin(2.0 * np.pi * 200.0
                                        * np.arange(256) / rate)
                         ).astype(np.int16)
                pcm[0:512:2] = burst
                pcm[1:512:2] = burst
                effect = Bitcrusher.create(
                    probes.ArraySource(pcm, rate=rate, channels=2,
                                       block=256), rate, band_limit=1.0)
                effect.set_macro(1, midi)
                reported = effect.tail_samples
                wet = probes.render(effect.output, frames, rate=rate)
                effect.deinit()
                live = np.nonzero(np.abs(np.asarray(wet.data)[:, 0]))[0]
                tail = int(live[-1]) - 255 if len(live) else 0
                worst = max(worst, tail)
                self.assertLessEqual(tail, reported,
                                     "%d Hz Rate %d" % (rate, midi))
        self.assertGreater(worst, 256)


class TheInvariants(unittest.TestCase):

    def test_mix_zero_is_a_wire(self):
        wet_src = source()
        dry_src = source()
        effect = Bitcrusher.create(wet_src, RATE, mix=0.0)
        wet = probes.render(effect.output, 2048, class_name="Bitcrusher")
        dry = probes.render(dry_src, 2048, class_name="dry")
        result = kit.wire(wet, dry, latency_samples=0)
        self.assertTrue(result["passed"], result["red"])
        effect.deinit()

    def test_mix_zero_is_level_honest(self):
        wet_src = source()
        dry_src = source()
        effect = Bitcrusher.create(wet_src, RATE, mix=0.0)
        wet = probes.render(effect.output, 2048, class_name="Bitcrusher")
        dry = probes.render(dry_src, 2048, class_name="dry")
        result = kit.level(wet, dry)
        self.assertTrue(result["passed"], result["red"])
        effect.deinit()

    def test_silence_in_is_silence_out(self):
        src = silence_source()
        effect = Bitcrusher.create(src, RATE)
        wet = probes.render(effect.output, 2048)
        self.assertFalse(wet.data.any())
        effect.deinit()

    def test_click_matches_reported_zero(self):
        """A FOUR-sample event: `click_stereo`'s single sample is one the
        hold may drop -- 45 % of offsets vanish at 48 kHz -- and a probe the
        effect is allowed to swallow measures nothing."""
        probe = wide_click()
        wet_src = probes.ArraySource(probe, rate=RATE, channels=2, block=256)
        dry_src = probes.ArraySource(probe, rate=RATE, channels=2, block=256)
        effect = Bitcrusher.create(wet_src, RATE)
        reported = effect.latency_samples
        wet = probes.render(effect.output, 8192, rate=RATE)
        dry = probes.render(dry_src, 8192, rate=RATE)
        result = kit.click(wet, dry, reported, subsample=False)
        self.assertTrue(result["passed"], result["red"])
        effect.deinit()

    def test_reporting_256_is_red(self):
        probe = wide_click()
        wet_src = probes.ArraySource(probe, rate=RATE, channels=2, block=256)
        dry_src = probes.ArraySource(probe, rate=RATE, channels=2, block=256)
        effect = LateClick.create(wet_src, RATE)
        wet = probes.render(effect.output, 8192, rate=RATE)
        dry = probes.render(dry_src, 8192, rate=RATE)
        result = kit.click(wet, dry, 256, subsample=False)
        self.assertFalse(result["passed"], result)
        effect.deinit()

    def test_rate_clamps_to_the_running_rate(self):
        """And says so: `hold_rate_hz` is what runs, `macro(1)` what was
        asked. At 22.05 kHz the top four of the knob's seventeen MIDI stops
        -- and patch 0's own hold -- land here."""
        effect = Bitcrusher.create(source(rate=22050), 22050, rate_hz=26040.0)
        self.assertEqual((effect._hold_num, effect._hold_den), (1, 1))
        self.assertEqual(effect.hold_rate_hz, 22050.0)
        self.assertAlmostEqual(effect.macro(1), 26040.0, delta=1.0)
        self.assertEqual(effect.latency_samples, 0)
        effect.deinit()

    def test_reset_and_deinit(self):
        probe = probes.sine(1000.0, 0.05, -12.0)
        holder = probes.SwitchableSource(
            probes.ArraySource(probe, rate=RATE, channels=2, block=256))
        silent = probes.ArraySource(
            probes.silence(2048, 2), rate=RATE, channels=2, block=256)
        effect = Bitcrusher.create(holder, RATE)

        def pull(blocks):
            return probes.render(effect.output, blocks * 256, rate=RATE,
                                 channels=2, block=256, class_name="Bitcrusher")

        result = kit.state(
            effect, pull=pull, swap=holder.swap, probe_source=holder.inner,
            silent_source=silent, blocks=8, alloc_pulls=20)
        self.assertTrue(result["passed"], result["red"])


class TheQuantizerRounds(unittest.TestCase):
    """T1, revised 2026-09-17 under vision 7.2 -- see the dossier.

    The old clause was "mean(output - input) within +-0.05 LSB of zero".
    It was met by CANCELLATION: the table used to be built on a grid
    7.99988 codes apart against the node's 8, so the staircase's treads
    wandered and the two halves of a sine happened to sum to nothing, while
    a one-sided ramp read -0.25 LSB and DC on a half-step +-0.5 (second-pass
    refutation). On the node's own grid the law is uniform and exact:

        riser width s = 65536 / (CURVE_POINTS - 1) = 8 codes
        mean error   = s / 2Delta   LSB      (`law_mean`)
        max |error|  = 0.5          LSB, at every depth
        DC-removed rms = (1 - s/Delta) * Delta/sqrt(12)  (`law_ratio`)

    The mean is a rounding asymmetry, not an offset the class adds: the
    riser sits on the low side of every transition, so a code is reached
    s/2 codes early. f(0) is exactly 0, so silence in is still silence out.
    """

    def test_the_default_rounds(self):
        """At the constructor default -- 12 bits, the standout's 26.04 kHz
        hold, Mix 1, Output 0 dB -- on material the hold passes."""
        mean, peak, ratio = residual(Bitcrusher, staircase())
        self.assertAlmostEqual(mean, law_mean(12), delta=0.02)
        self.assertLessEqual(peak, 0.5)

    def test_every_depth_in_the_span_rounds(self):
        """Rate = the running rate, a full-scale ramp, EVERY integer depth.
        The even-bit sweep is what hid 13 and 15 (audiocomponents#71)."""
        material = full_ramp(16384)
        for bits in range(2, 13):
            mean, peak, ratio = residual(
                Bitcrusher, material, bits=float(bits), rate_hz=float(RATE),
                dither=0.0, mix=1.0)
            self.assertAlmostEqual(mean, law_mean(bits), delta=0.02,
                                   msg="bits %d" % bits)
            self.assertLessEqual(peak, 0.5, "bits %d" % bits)

    def test_no_depth_in_the_span_is_a_wire(self):
        material = full_ramp(16384)
        for bits in range(2, 13):
            mean, peak, ratio = residual(
                Bitcrusher, material, bits=float(bits), rate_hz=float(RATE),
                mix=1.0)
            self.assertGreater(peak, 0.0, "bits %d is a wire" % bits)

    def test_a_floor_quantizer_is_red_at_the_default(self):
        clean = residual(Bitcrusher, staircase())
        floored = residual(FloorQuantize, staircase())
        self.assertAlmostEqual(clean[0], law_mean(12), delta=0.02)
        self.assertGreater(abs(floored[0] - law_mean(12)), 0.02)
        self.assertAlmostEqual(floored[0] - clean[0], -0.5, delta=0.1)

    def test_null_build_is_red(self):
        def measure_with(subject):
            mean, peak, ratio = residual(subject, staircase())
            return {"passed": bool(
                abs(float(mean) - law_mean(12)) <= 0.02
                and float(peak) <= 0.5)}
        kit_faults.null_build_red(Bitcrusher, measure_with)


class ErrorPower(unittest.TestCase):
    """T2, revised twice under vision 7.2 -- see the dossier.

    The bar is no longer Delta/sqrt(12). A table read by linear
    interpolation cannot be a hard staircase: every riser is one table
    point wide, so the error is a triangle of amplitude Delta/2 with a
    corner taken off it and the DC-removed rms is `(1 - s/Delta)` of the
    ideal -- exactly, at every depth, derived from the node's own indexing
    and not fitted. At 12 bits that is HALF. Reaching 0.9375 would need a
    65537-point table, 128 KB against this one's 16, and it still would not
    reach Delta/sqrt(12).

    The per-bit step follows from the same law and is NOT 6.0 dB across the
    span: `20*log10((Delta_b - s)/(Delta_b+1 - s))` is 6.02 dB while
    Delta >> s and opens to 9.54 dB at 11 -> 12. The old clause's "6.0 +-
    1.0 dB per bit" was never measured, and 11 -> 12 reads +4.771 dB on the
    class as it was and +9.54 on the class as it is.
    """

    def test_the_default_follows_the_law(self):
        mean, peak, ratio = residual(Bitcrusher, staircase())
        self.assertLessEqual(abs(ratio / law_ratio(12) - 1.0), 0.10)

    def test_a_wrong_step_is_red_at_the_default(self):
        """The guard the audit asked for: the CLEAN class is green here and
        the fault is not, so absence cannot read as agreement."""
        clean = residual(Bitcrusher, staircase())[2]
        wrong = residual(WrongStep, staircase())[2]
        self.assertLessEqual(abs(clean / law_ratio(12) - 1.0), 0.10)
        self.assertGreater(abs(wrong / law_ratio(12) - 1.0), 0.10)
        self.assertGreater(wrong / clean, 2.0)

    def test_the_span_follows_the_law(self):
        """Rate = the running rate, full-scale ramp, every depth 2-12.

        One law, no holes. The old row's holes at 10 and 11 (0.900 and
        0.863 against a 1.0 bar) were the law being read against the wrong
        target -- `law_ratio` says 0.875 and 0.750 there.
        """
        material = full_ramp(16384)
        for bits in range(2, 13):
            ratio = residual(Bitcrusher, material, bits=float(bits),
                             rate_hz=float(RATE), mix=1.0)[2]
            self.assertLessEqual(abs(ratio / law_ratio(bits) - 1.0), 0.10,
                                 "bits %d: %.4f vs %.4f"
                                 % (bits, ratio, law_ratio(bits)))

    def test_every_per_bit_step_is_the_law(self):
        """The clause the pack never measured. Each step is read, and each
        is held to the law rather than to a flat 6 dB."""
        material = full_ramp(16384)
        rms = {}
        for bits in range(2, 13):
            ratio = residual(Bitcrusher, material, bits=float(bits),
                             rate_hz=float(RATE), mix=1.0)[2]
            rms[bits] = ratio * (1 << (16 - bits)) / math.sqrt(12.0)
        for bits in range(2, 12):
            got = 20.0 * math.log10(rms[bits] / rms[bits + 1])
            want = 20.0 * math.log10(
                float((1 << (16 - bits)) - CURVE_STEP)
                / float((1 << (15 - bits)) - CURVE_STEP))
            self.assertAlmostEqual(got, want, delta=0.5,
                                   msg="%d -> %d" % (bits, bits + 1))

    def test_null_build_is_red(self):
        def measure_with(subject):
            ratio = residual(subject, staircase())[2]
            return {"passed": bool(
                abs(float(ratio) / law_ratio(12) - 1.0) <= 0.10)}
        kit_faults.null_build_red(Bitcrusher, measure_with)


class TheHold(unittest.TestCase):
    """T4 and T6 at 48 kHz."""

    def tilt_db(self, cls, hz, rate_hz, frames=8192):
        material = source(frames=frames, peak=16384, hz=hz)
        dry_src = source(frames=frames, peak=16384, hz=hz)
        effect = cls.create(material, RATE, bits=12.0, rate_hz=rate_hz,
                            mix=1.0)
        wet = probes.render(effect.output, frames, rate=RATE)
        dry = probes.render(dry_src, frames, rate=RATE)
        effect.deinit()

        def line(render):
            x = render.data[frames // 2:, 0].astype(np.float64)
            spectrum = np.abs(np.fft.rfft(x * np.hanning(len(x))))
            index = int(round(hz * len(x) / RATE))
            peak = float(np.max(spectrum[max(0, index - 2):index + 3]))
            return 20.0 * math.log10(max(peak, 1e-12))
        return line(wet) - line(dry)

    def sinc_db(self, hz, rate_hz):
        x = math.pi * hz / rate_hz
        return 20.0 * math.log10(abs(math.sin(x) / x))

    #: T4 is quantified over BOTH holds the Rate knob reaches: the
    #: standout's 1.8433 (the shipped default) and an integer 4. The
    #: integer leg is not decoration -- at 1.8433 the sinc curve is so
    #: shallow below 5 kHz that a WIRE sits inside the 1 dB bar, and a
    #: measurement a wire passes has demonstrated nothing.
    T4_POINTS = ((26040.0, 1000.0), (26040.0, 3000.0), (26040.0, 5000.0),
                 (12000.0, 1000.0), (12000.0, 3000.0), (12000.0, 5000.0))

    def worst_tilt_error(self, cls):
        worst = 0.0
        for rate_hz, hz in self.T4_POINTS:
            got = self.tilt_db(cls, hz, rate_hz)
            worst = max(worst, abs(got - self.sinc_db(hz, rate_hz)))
        return worst

    def test_the_hold_is_a_sinc(self):
        self.assertLessEqual(self.worst_tilt_error(Bitcrusher), 1.0)

    def test_inverting_the_legs_is_red_at_the_default(self):
        """Read on the same six points the trait is, and the default is one
        of them. At audioif `977ef26` a hold-then-decimate pair is close to
        an identity, so this is red by the size of the sinc curve itself --
        which is also why the integer-4 leg has to be in the measurement."""
        self.assertGreater(self.worst_tilt_error(SkewedHold), 1.0)

    def test_null_build_is_red(self):
        def measure_with(subject):
            return {"passed": bool(self.worst_tilt_error(subject) <= 1.0)}
        kit_faults.null_build_red(Bitcrusher, measure_with)

    def runs(self, cls, rate_hz, frames=30000):
        src = source(frames=frames, peak=20000, hz=100.0)
        effect = cls.create(src, RATE, bits=12.0, rate_hz=rate_hz, mix=1.0)
        wet = probes.render(effect.output, frames)
        effect.deinit()
        pcm = np.asarray(wet.data)[:, 0]
        lengths = []
        run = 1
        for i in range(1, len(pcm)):
            if pcm[i] == pcm[i - 1]:
                run += 1
            else:
                lengths.append(run)
                run = 1
        lengths.append(run)
        return lengths

    def test_integer_ratio_is_all_n(self):
        lengths = self.runs(Bitcrusher, 12000.0)
        self.assertEqual(set(lengths), {4})

    def test_the_standout_ratio_is_ones_and_twos(self):
        """T6 as redefined: at least 99 % of runs are 1 or 2, and the
        length-2 share of those is 0.843 +/- 0.02.

        The residue is the QUANTIZER, not the hold: two adjacent held
        samples that land in the same code read as one longer run. It
        tracks Bits exactly -- 99.69 % at 12 bits, 98.61 at 10, 88.76 at 8,
        3.57 at 6 -- which is why the trait cannot be 100 % now that Bits
        stops at 12 and the quantizer is always in the path. The frozen row
        held Bits at 16, which the surface no longer reaches."""
        lengths = self.runs(Bitcrusher, 26040.0)
        pair = [item for item in lengths if item in (1, 2)]
        self.assertGreaterEqual(len(pair) / float(len(lengths)), 0.99)
        twos = sum(1 for item in pair if item == 2)
        self.assertAlmostEqual(twos / float(len(pair)), 0.843, delta=0.02)

    def test_snapping_the_ratio_collapses_the_alphabet(self):
        lengths = self.runs(SnapRate, 26040.0)
        pair = [item for item in lengths if item in (1, 2)]
        twos = sum(1 for item in pair if item == 2)
        self.assertGreater(abs(twos / float(len(pair)) - 0.843), 0.02)

    def test_null_build_is_red_on_the_alphabet(self):
        def measure_with(subject):
            lengths = self.runs(subject, 26040.0)
            pair = [item for item in lengths if item in (1, 2)]
            if not pair:
                return {"passed": False}
            twos = sum(1 for item in pair if item == 2)
            return {"passed": bool(
                len(pair) / float(len(lengths)) >= 0.99
                and abs(twos / float(len(pair)) - 0.843) <= 0.02)}
        kit_faults.null_build_red(Bitcrusher, measure_with)


class TheRateKnob(unittest.TestCase):
    """The two things the refuter found on the Rate knob."""

    def test_asking_for_the_running_rate_is_identity(self):
        for rate in (48000, 44100, 22050):
            effect = Bitcrusher.create(
                source(rate=rate), rate, rate_hz=float(rate))
            self.assertEqual((effect._hold_num, effect._hold_den), (1, 1),
                             "%d Hz" % rate)
            self.assertEqual(effect.latency_samples, 0, "%d Hz" % rate)
            effect.deinit()

    def test_the_hold_lands_on_the_whole_hertz(self):
        """`num`/`den` is the running rate over the asked rate rounded to
        the hertz, so the hold rate is exact -- not near. There is no grid
        to lose an LSB on any more: the pair of `SpeedChanger`s this
        replaced could not be made reciprocal at Q16 and slipped a sample
        per ~190k frames (audioif#97)."""
        for asked in (26040.0, 12000.0, 8000.0, 7947.0, 6040.0):
            for rate in (48000, 44100, 22050):
                effect = Bitcrusher.create(
                    source(rate=rate), rate, rate_hz=asked)
                want = min(float(rate), float(int(asked + 0.5)))
                self.assertAlmostEqual(effect.hold_rate_hz, want, places=9,
                                       msg="%.0f Hz at %d" % (asked, rate))
                effect.deinit()

    def test_asking_for_a_rate_it_cannot_reach_is_disclosed(self):
        """Four of the seventeen MIDI stops are above 22.05 kHz, so at that
        rate they are all the same hold: the running rate, an identity."""
        dead = []
        for midi in range(0, 128, 8):
            effect = Bitcrusher.create(source(rate=22050), 22050)
            effect.set_macro(1, midi)
            if effect.hold_rate_hz >= 22050.0:
                dead.append(midi)
            self.assertLessEqual(effect.hold_rate_hz, 22050.0)
            effect.deinit()
        self.assertEqual(dead, [104, 112, 120])


class TheOutputTrim(unittest.TestCase):
    """Output is an output level, not a wet-only trim."""

    def measure(self, output_db, mix=1.0):
        frames = 4096
        hz = 341.0 * RATE / 16384.0
        flat = Bitcrusher.create(source(frames=frames, peak=8192, hz=hz),
                                 RATE, rate_hz=float(RATE), mix=mix,
                                 output_db=0.0)
        trim = Bitcrusher.create(source(frames=frames, peak=8192, hz=hz),
                                 RATE, rate_hz=float(RATE), mix=mix,
                                 output_db=output_db)
        one = probes.render(flat.output, frames)
        two = probes.render(trim.output, frames)
        flat.deinit()
        trim.deinit()
        return kit.rms_db(left(two)) - kit.rms_db(left(one))

    def test_output_moves_the_level_at_mix_one(self):
        self.assertAlmostEqual(self.measure(-6.0), -6.0, delta=0.1)

    def test_output_moves_the_level_at_a_blend(self):
        self.assertAlmostEqual(self.measure(-6.0, mix=0.35), -6.0, delta=0.1)


class TheAliasFilter(unittest.TestCase):
    """T5: Band Limit is off by default and the fault turns it on."""

    def test_default_band_limit_is_not_in_the_path(self):
        """Off means unplugged, not mixed out. Two biquads nobody asked
        for cost 0.200 ms on the P4 and 0.338 on the S3."""
        effect = Bitcrusher.create(source(), RATE)
        self.assertEqual(effect.macro(3), 0.0)
        self.assertFalse(effect._band)
        self.assertIs(effect._hold_source, effect._wet_in)
        effect.deinit()

    def test_band_limit_on_uses_the_filtered_hold(self):
        effect = Bitcrusher.create(source(), RATE, band_limit=1.0)
        self.assertTrue(effect._band)
        self.assertIs(effect._hold_source, effect._sections[-1])
        effect.deinit()

    def test_forced_band_limit_is_on_at_defaults(self):
        effect = ForcedBandLimit.create(source(), RATE)
        self.assertTrue(effect._band)
        self.assertIs(effect._hold_source, effect._sections[-1])
        effect.deinit()

    def test_the_knob_re_sources_the_hold_mid_stream(self):
        """`SampleHold` has `play()`, which is why there is one hold node
        and not two pairs. Toggling Band Limit while the graph is running
        must move the branch, not raise and not leave the class silent."""
        for rate in (48000, 44100, 22050):
            # 6 kHz against a 3360 Hz corner: above it, so the branch the
            # knob picks is audible in the peak. A 1 kHz tone at the
            # default Rate sits a decade below the corner and both
            # branches read the same.
            src = source(frames=8192, rate=rate, peak=16384, hz=6000.0)
            effect = Bitcrusher.create(src, rate, rate_hz=8000.0)
            probes.render(effect.output, 1024, rate=rate)
            effect.set_macro(3, 127)
            self.assertIs(effect._hold_source, effect._sections[-1])
            on = probes.render(effect.output, 2048, rate=rate)
            effect.set_macro(3, 0)
            self.assertIs(effect._hold_source, effect._wet_in)
            off = probes.render(effect.output, 2048, rate=rate)
            effect.deinit()
            self.assertTrue(np.any(np.asarray(on.data)), "%d Hz on" % rate)
            self.assertTrue(np.any(np.asarray(off.data)), "%d Hz off" % rate)
            self.assertGreater(int(np.abs(np.asarray(off.data)).max()),
                               int(np.abs(np.asarray(on.data)).max()),
                               "%d Hz: the filtered branch is not quieter"
                               % rate)

    def image_db(self, band, hz=7000.0, f_hold=8000.0, frames=8192,
                 rate=RATE, cls=None):
        """The hold's image at |f_hold - hz|, against the INPUT tone."""
        cls = cls or Bitcrusher
        wet_src = source(frames=frames, peak=16384, hz=hz, rate=rate)
        dry_src = source(frames=frames, peak=16384, hz=hz, rate=rate)
        effect = cls.create(wet_src, rate, bits=12.0, rate_hz=f_hold,
                            mix=1.0, band_limit=band)
        wet = probes.render(effect.output, frames, rate=rate)
        dry = probes.render(dry_src, frames, rate=rate)
        effect.deinit()

        def line(render, freq):
            x = render.data[frames // 2:, 0].astype(np.float64)
            spectrum = np.abs(np.fft.rfft(x * np.hanning(len(x))))
            index = int(round(freq * len(x) / rate))
            peak = float(np.max(spectrum[max(0, index - 2):index + 3]))
            return 20.0 * math.log10(max(peak, 1e-12))
        return line(wet, abs(f_hold - hz)) - line(dry, hz)

    def test_the_image_stands_at_its_own_level(self):
        """T5, demonstrated 2026-09-17 at audioif `977ef26`.

        It was disconfirmed at `cebb7ca` with audioif#91 named as the cause:
        `SpeedChanger` reset its phase at every source buffer, the line
        smeared, and the 1 kHz image read -31.7 dB. With the phase carried
        it reads what a zero-order hold puts there.
        """
        for rate in (48000, 44100, 22050):
            loud = self.image_db(0.0, rate=rate)
            self.assertLessEqual(abs(loud), 3.0, "%d Hz" % rate)

    def test_band_limit_removes_the_image(self):
        """It FILTERS it now, and the number is a filter's.

        Until 2026-09-17 the band limit was four identical 2nd-order
        sections -- 48 dB/octave with its real -3 dB point at 0.66x the
        nominal corner -- and about an octave above that the wet was below
        one 12-bit code: digital silence, which read as "-384 dB of
        rejection" and could not tell a filter from an empty converter
        (second-pass refutation). Two sections at the 4th-order
        Butterworth pole Qs put 27.5 / 27.7 / 37.9 dB under the image and
        leave the tone that made it audible.
        """
        for rate in (48000, 44100, 22050):
            loud = self.image_db(0.0, rate=rate)
            quiet = self.image_db(1.0, rate=rate)
            self.assertLess(quiet - loud, -20.0, "%d Hz" % rate)

    def test_band_limit_is_a_filter_and_not_a_mute(self):
        """An octave above the corner the wet is attenuated, not empty."""
        for rate in (48000, 44100, 22050):
            hz = 9000.0 if rate > 22050 else 7000.0
            wet_src = source(frames=8192, peak=16384, hz=hz, rate=rate)
            effect = Bitcrusher.create(wet_src, rate, bits=12.0,
                                       rate_hz=8000.0, mix=1.0,
                                       band_limit=1.0)
            wet = probes.wet_render(effect, 8192, rate=rate)
            effect.deinit()
            data = np.abs(np.asarray(wet.data)[:, 0])
            self.assertGreater(int(data[-1024:].max()), 64, "%d Hz" % rate)

    def test_above_the_default_nyquist_the_image_is_down(self):
        """The frozen row's SECOND quantification point, and it is
        DISCONFIRMED: a 17 kHz tone through patch 0's 26.04 kHz hold puts
        its image at 9.04 kHz, which reads -4.91 dB at 48 kHz and -5.16 at
        44.1 against a +/-3 dB bar. 1.79 dB of that is the hold's own sinc
        at the image frequency; the rest is a non-integer ratio spreading a
        tone this close to fs/2.8. Recorded, not redefined away."""
        got = self.image_db(0.0, hz=17000.0, f_hold=26040.0)
        self.assertLess(got, -3.0)
        self.assertGreater(got, -8.0)

    def test_inverting_the_legs_is_red_at_the_default(self):
        """T5's guard is T4's, and on purpose: both traits are statements
        about the same `SpeedChanger` pair, so a fault in that pair is
        same-kind for both. A fault that forced Band Limit on would be
        REACHABLE -- Band Limit at 127 gives the same reading."""
        self.assertLess(self.image_db(0.0, cls=SkewedHold), -3.0)

    def test_null_build_is_red(self):
        def measure_with(subject):
            return {"passed": bool(
                abs(self.image_db(0.0, cls=subject)) <= 3.0)}
        kit_faults.null_build_red(Bitcrusher, measure_with)


class TheFaultsAreNotTheSurface(unittest.TestCase):

    def _build(self, cls):
        return cls.create(source(), RATE)

    def test_floor_is_not_a_macro(self):
        out = kit_faults.fault_reachability(
            Bitcrusher, FloorQuantize,
            lambda effect: bool(getattr(type(effect), "FLOOR", False)),
            self._build, label="Bitcrusher FloorQuantize")
        self.assertEqual(out["target"], True)
        self.assertEqual(out["clean"], False)
        self.assertEqual(out["checked"], 109)

    def test_wrong_step_is_not_a_macro(self):
        out = kit_faults.fault_reachability(
            Bitcrusher, WrongStep,
            lambda effect: int(getattr(type(effect), "BITS_OFFSET", 0)),
            self._build, label="Bitcrusher WrongStep")
        self.assertEqual(out["target"], -2)
        self.assertEqual(out["clean"], 0)
        self.assertEqual(out["checked"], 109)

    def test_snap_rate_is_not_a_macro(self):
        out = kit_faults.fault_reachability(
            Bitcrusher, SnapRate,
            lambda effect: bool(getattr(type(effect), "SNAP_RATE", False)),
            self._build, label="Bitcrusher SnapRate")
        self.assertEqual(out["target"], True)
        self.assertEqual(out["clean"], False)
        self.assertEqual(out["checked"], 109)

    def test_inverted_legs_are_not_a_macro(self):
        out = kit_faults.fault_reachability(
            Bitcrusher, SkewedHold,
            lambda effect: getattr(type(effect), "HOLD_SKEW", None),
            self._build, label="Bitcrusher SkewedHold")
        self.assertEqual(out["target"], (2, 5))
        self.assertEqual(out["clean"], None)
        self.assertEqual(out["checked"], 109)


class TheClickAtEveryRate(unittest.TestCase):
    """`latency_samples` against a probe the hold cannot swallow."""

    def test_a_single_sample_event_can_be_dropped(self):
        """The disclosure, measured over its whole span, so it is not
        mistaken for a defect.

        A decimating hold keeps `den` of every `num` frames, so a
        one-sample event survives exactly `den/num` of the time and the
        fraction that vanishes is `(N-1)/N`. Swept over forty consecutive
        offsets: 18/40 at 48 kHz against 45.8 %, 16/40 at 44.1 against
        41.0 %, 0/40 at 22.05 where Rate clamps and nothing is dropped.
        """
        for rate, want in ((48000, 0.458), (44100, 0.410), (22050, 0.0)):
            dropped = 0
            for offset in range(256, 296):
                probe = probes.click_stereo(8192, offset=offset)
                effect = Bitcrusher.create(
                    probes.ArraySource(probe, rate=rate, channels=2,
                                       block=256), rate)
                wet = probes.render(effect.output, 8192, rate=rate)
                effect.deinit()
                if not np.any(np.asarray(wet.data)):
                    dropped += 1
            self.assertAlmostEqual(dropped / 40.0, want, delta=0.06,
                                   msg="%d Hz" % rate)

    def test_the_click_matches_at_every_rate(self):
        for rate in (48000, 44100, 22050):
            probe = wide_click()
            wet_src = probes.ArraySource(probe, rate=rate, channels=2,
                                         block=256)
            dry_src = probes.ArraySource(probe, rate=rate, channels=2,
                                         block=256)
            effect = Bitcrusher.create(wet_src, rate)
            reported = effect.latency_samples
            wet = probes.render(effect.output, 8192, rate=rate)
            dry = probes.render(dry_src, 8192, rate=rate)
            effect.deinit()
            for subsample in (False, True):
                result = kit.click(wet, dry, reported, subsample=subsample)
                self.assertTrue(result["passed"],
                                "%d Hz subsample=%s: %s"
                                % (rate, subsample, result["red"]))


class TheStepSpanPrecondition(unittest.TestCase):
    """T1, T2 and T6 hold where the probe spans the staircase, and the row
    says how much of it (audit 3 (p)2 and (p)3, ruling (m)).

    The old T2 row said "where the probe spans >= 16 steps" and the rebuild
    dropped it. It is the precondition all three rows need, because below
    it the material stops exercising the converter: the mean error law is a
    statement about a probe that visits many treads, and at 7.3 steps the
    same ramp reads **+0.25703 LSB against a +0.25000 law**. The audit
    found T1's mean out at -55 dBFS, T2's rms clause reading -8.14 % on a
    full-scale ramp and T6 at 97.26 % at -50 dBFS; one precondition covers
    all three, and it is a **statement about steps, not about dBFS**, so it
    scales with the depth in force.

    At 12 bits a step is 16 codes, so 16 steps is 256 codes peak to peak -
    **-48 dBFS** - and every shipped patch is read far above it. At 8 bits
    the same 16 steps is -24 dBFS.

    **And the material has to sweep the codes.** The law is the average of
    a staircase's treads, so it is read on a ramp or a staircase; a sine
    dwells at its extremes and samples the same staircase unevenly, so its
    mean wanders with the phase at every level - +0.23960 at -6 dBFS,
    +0.27602 at -40, **+0.28648 at -55**, which is the reading audit 3
    (p)2 found. That is the probe, not the converter, and the row says so
    rather than claiming a law a sine was never going to show.
    """

    SPAN_STEPS = 16

    def ramp(self, dbfs, frames=16384, channels=2):
        peak = 10.0 ** (dbfs / 20.0)
        values = np.linspace(-peak, peak, frames)
        quantised = np.clip(np.round(values * 32767.0),
                            -32768, 32767).astype(np.int16)
        pcm = np.empty(frames * channels, dtype=np.int16)
        for channel in range(channels):
            pcm[channel::channels] = quantised
        return array("h", pcm.tobytes())

    def steps_at(self, dbfs, bits=12):
        step = 65536.0 / float(1 << bits)
        return 2.0 * (10.0 ** (dbfs / 20.0)) * 32767.0 / step

    def test_the_law_holds_wherever_the_probe_spans_the_steps(self):
        for dbfs in (0.0, -20.0, -40.0):
            self.assertGreater(self.steps_at(dbfs), self.SPAN_STEPS, dbfs)
            mean, peak, ratio = residual(
                Bitcrusher, self.ramp(dbfs), bits=12.0,
                rate_hz=float(RATE), dither=0.0, mix=1.0)
            self.assertAlmostEqual(mean, law_mean(12), delta=0.02,
                                   msg="%s dBFS" % dbfs)
            self.assertLessEqual(peak, 0.5, "%s dBFS" % dbfs)

    def sine(self, dbfs, frames=16384, hz=1000.0, channels=2):
        index = np.arange(frames)
        values = (10.0 ** (dbfs / 20.0)) * np.sin(
            2.0 * math.pi * hz * index / RATE)
        quantised = np.clip(np.round(values * 32767.0),
                            -32768, 32767).astype(np.int16)
        pcm = np.empty(frames * channels, dtype=np.int16)
        for channel in range(channels):
            pcm[channel::channels] = quantised
        return array("h", pcm.tobytes())

    def test_a_sine_is_not_the_probe_this_law_is_read_on(self):
        """The other half of the precondition. A sine's mean is out at
        every level, which is why the row's probe is a staircase - and why
        a row that claimed the law on a sine would be false."""
        out = []
        for dbfs in (-6.0, -40.0, -55.0):
            mean, _peak, _ratio = residual(
                Bitcrusher, self.sine(dbfs), bits=12.0,
                rate_hz=float(RATE), dither=0.0, mix=1.0)
            out.append((dbfs, mean))
        self.assertTrue(
            any(abs(mean - law_mean(12)) > 0.02 for _dbfs, mean in out),
            out)

    def test_below_it_the_row_is_not_claimed_and_the_law_drifts(self):
        """The other half of a precondition: if the law held everywhere the
        clause would be charity, and if it failed inside the span the row
        would be false."""
        self.assertLess(self.steps_at(-55.0), self.SPAN_STEPS)
        mean, _peak, _ratio = residual(
            Bitcrusher, self.ramp(-55.0), bits=12.0, rate_hz=float(RATE),
            dither=0.0, mix=1.0)
        self.assertGreater(abs(mean - law_mean(12)), 0.005, mean)

    def test_the_precondition_scales_with_the_depth(self):
        """16 steps at 8 bits is a different level, and the law holds
        there too - which is what makes it a step clause and not a dBFS
        one."""
        for bits in (8, 10, 12):
            step = 65536.0 / float(1 << bits)
            peak = self.SPAN_STEPS * step / 2.0 / 32767.0
            dbfs = 20.0 * math.log10(peak * 4.0)
            mean, _peak, _ratio = residual(
                Bitcrusher, self.ramp(dbfs), bits=float(bits),
                rate_hz=float(RATE), dither=0.0, mix=1.0)
            self.assertAlmostEqual(mean, law_mean(bits), delta=0.02,
                                   msg="bits %d at %.1f dBFS" % (bits, dbfs))


class TheTierOneRowsAtEveryShippedPatch(unittest.TestCase):
    """audiocomponents#87.

    `Bitcrusher` declares no BIPOLAR macro, so the centre detent moved
    none of its bytes and none of these readings. They are taken anyway:
    #87's guard is that Tier 1's silence and tail rows are read at every
    shipped patch and not at the constructor default alone, and that is
    what this class needs most - one of its patches is not silent in,
    silent out, and the default is.
    """

    #: Empty since the third fix round. Patch 5 turns the dither on, and
    #: dither is noise a converter adds whether or not there is a signal:
    #: the class put about -66 dBFS of it out on digital silence, **8 345
    #: of 16 384 frames nonzero, to the last frame, at every rate** (audit
    #: 3 (p)1, ruling (n)). `DITHER_GATE_DB` is the gate on the sum that
    #: reaches the quantiser - 6 dB above the dither's own level, so the
    #: only thing that closes it is the input going away - and a bar wide
    #: enough for dither is exactly what this row does not have.
    RED = {}

    RED_TAIL = {}

    def peaks(self):
        """`{patch: (silence_peak, tail_samples, residual, declared)}`."""
        rows = {}
        for patch in sorted(Bitcrusher.PATCHES):
            effect = Bitcrusher.create(silence_source(RATE), RATE,
                                       patch=patch)
            quiet = probes.render(effect.output, RATE, rate=RATE,
                                  channels=2, block=256)
            effect.deinit()
            probe, burst_end = probes.burst_silence(
                hz=1000.0, on_ms=200.0, total_s=1.0, dbfs=-6.0, rate=RATE,
                channels=2)
            effect = Bitcrusher.create(
                probes.ArraySource(probe, rate=RATE, channels=2, block=256),
                RATE, patch=patch)
            declared = effect.tail_samples
            wet = probes.render(effect.output, len(probe) // 2, rate=RATE,
                                channels=2, block=256)
            effect.deinit()
            result = kit.tail(wet, burst_end_frame=burst_end,
                              declared_tail_samples=declared)
            rows[patch] = (int(np.abs(quiet.data).max()),
                           result["values"]["tail_samples"],
                           result["values"]["residual_lsb"], declared)
        return rows

    def test_silence_in_is_silence_out_at_every_shipped_patch(self):
        for patch, row in sorted(self.peaks().items()):
            with self.subTest(patch=patch, why=self.RED.get(patch)):
                if patch in self.RED:
                    self.assertGreater(row[0], 0, self.RED[patch])
                    continue
                self.assertEqual(row[0], 0,
                                 "patch %d emits %d LSB into digital "
                                 "silence" % (patch, row[0]))

    def test_the_declared_tail_holds_at_every_shipped_patch(self):
        for patch, row in sorted(self.peaks().items()):
            _quiet, tail_samples, residual, declared = row
            with self.subTest(patch=patch, why=self.RED_TAIL.get(patch)):
                if patch in self.RED_TAIL:
                    self.assertGreater(residual, 0, self.RED_TAIL[patch])
                    continue
                self.assertEqual(residual, 0,
                                 "patch %d never returns to zero (%d LSB "
                                 "left)" % (patch, residual))
                self.assertLessEqual(tail_samples or 0, declared,
                                     "patch %d rings %s samples against a "
                                     "declared %s"
                                     % (patch, tail_samples, declared))

    def test_program_change_onto_digital_silence_stays_silent(self):
        """A patch change is a wire message and can arrive between notes."""
        for patch in sorted(Bitcrusher.PATCHES):
            effect = Bitcrusher.create(silence_source(RATE), RATE, patch=0)
            before = probes.render(effect.output, RATE // 2, rate=RATE,
                                   channels=2, block=256)
            effect.program_change(patch)
            after = probes.render(effect.output, RATE // 2, rate=RATE,
                                  channels=2, block=256)
            effect.deinit()
            with self.subTest(patch=patch, why=self.RED.get(patch)):
                self.assertEqual(int(np.abs(before.data).max()), 0)
                peak = int(np.abs(after.data).max())
                if patch in self.RED:
                    self.assertGreater(peak, 0, self.RED[patch])
                    continue
                self.assertEqual(peak, 0,
                                 "program_change(%d) on silence emitted %d "
                                 "LSB" % (patch, peak))
