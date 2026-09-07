"""`DynamicEQ`'s own invariant, trait and planted-fault battery.

The class gate (`docs/effects-roadmap.md`, "The class gate") asks for two
things this file carries: every Tier 1 invariant green, and every demonstrated
Tier 2 trait shown **red on a planted fault of the same kind**. Numbers are
printed as they are measured so the evidence pack quotes a run and not a
recollection; the dossier is `docs/effects/DynamicEQ.md` and the pack is
`docs/effects/DynamicEQ-evidence.md`.

Every fault below is planted in a **live instance**, by reaching into the
graph the class built, so the control and the faulted run are the same code
path with one thing changed. A fault planted in the module would prove that a
different class fails.
"""

import array
import math
import unittest

import audiocore

import audioeffects
from audioeffects import _component
from audioeffects.rebuilt import dynamiceq as module

RATE = 48000
CHANNELS = 2
FULL_SCALE = 32767.0


# --------------------------------------------------------------------------
# The rig


def amp(level_db):
    return int(round(FULL_SCALE * (10.0 ** (level_db / 20.0))))


def sine(hz, amplitude, frames, rate=RATE, channels=CHANNELS):
    data = array.array('h', bytes(2 * channels * frames))
    step = 2.0 * math.pi * hz / rate
    for index in range(frames):
        value = int(round(amplitude * math.sin(step * index)))
        for channel in range(channels):
            data[index * channels + channel] = value
    return data


def burst(hz, amplitude, on_frames, total_frames, lead, rate=RATE,
          channels=CHANNELS):
    """Silence, tone, silence. The lead matters: `audiocore.RawSample` hands
    its buffer back from the beginning, so a burst at frame 0 replays after a
    `reset()` and reads exactly like a node that was never cleared."""
    data = array.array('h', bytes(2 * channels * total_frames))
    step = 2.0 * math.pi * hz / rate
    for index in range(on_frames):
        value = int(round(amplitude * math.sin(step * index)))
        for channel in range(channels):
            data[(lead + index) * channels + channel] = value
    return data


def impulse(amplitude, at, total_frames, channels=CHANNELS):
    data = array.array('h', bytes(2 * channels * total_frames))
    for channel in range(channels):
        data[at * channels + channel] = amplitude
    return data


#: T1's sweep. The two skirt frequencies are not decoration: at f0 itself
#: the notch is exactly zero and the band-pass is exactly unity whatever Q
#: is, so a mistuned branch is invisible there and visible on the skirt -
#: which is where the planted faults below read 0.22 and 0.40 dB.
T1_SWEEP = (100.0, 500.0, 1500.0, 2500.0, 3000.0, 3600.0, 6000.0, 12000.0)


def build(data, rate=RATE, channels=CHANNELS, **options):
    source = audiocore.RawSample(data, sample_rate=rate,
                                 channel_count=channels)
    return audioeffects.create('DynamicEQ', source, rate, **options), source


def render(node, frames, channels=CHANNELS):
    out = array.array('h')
    while len(out) // channels < frames:
        result, buffer = audiocore.get_buffer(node)
        raw = bytes(buffer)
        if not raw:
            break
        chunk = array.array('h')
        chunk.frombytes(raw)
        out.extend(chunk)
    return out[:frames * channels]


def rms(data, skip=0, channels=CHANNELS, channel=0):
    total = 0.0
    count = 0
    for index in range(skip * channels + channel, len(data), channels):
        value = float(data[index])
        total += value * value
        count += 1
    return math.sqrt(total / count) if count else 0.0


def gain_db(wet, dry):
    if wet <= 0.0 or dry <= 0.0:
        return float('-inf')
    return 20.0 * math.log10(wet / dry)


def tone_gain(hz, level_db, frames=48000, rate=RATE, channels=CHANNELS,
              **options):
    """Composite gain on a steady tone, read after the detector settles."""
    data = sine(hz, amp(level_db), frames, rate, channels)
    effect, _ = build(data, rate=rate, channels=channels, **options)
    out = render(effect.output, frames, channels)
    skip = frames // 2
    return gain_db(rms(out, skip, channels), rms(data, skip, channels))


def law(over_db, ratio, knee_db=6.0):
    """`audioif/src/shared/audioif_dynamics.c:392-403`, in Python."""
    half = knee_db * 0.5
    slope = 1.0 - 1.0 / ratio
    if over_db <= -half:
        return 0.0
    if over_db < half and knee_db > 0.0:
        x = over_db + half
        return -slope * x * x / (2.0 * knee_db)
    return -slope * over_db


def h_bp_db(hz, centre, q, rate=RATE):
    """|H_bandpass(f)| in dB from S1's own coefficients."""
    w0 = 2.0 * math.pi * centre / rate
    alpha = math.sin(w0) / (2.0 * q)
    cos0 = math.cos(w0)
    w = 2.0 * math.pi * hz / rate
    br = alpha - alpha * math.cos(-2 * w)
    bi = -alpha * math.sin(-2 * w)
    ar = (1.0 + alpha) - 2.0 * cos0 * math.cos(-w) + (1.0 - alpha) \
        * math.cos(-2 * w)
    ai = -2.0 * cos0 * math.sin(-w) + (1.0 - alpha) * math.sin(-2 * w)
    num = math.sqrt(br * br + bi * bi)
    den = math.sqrt(ar * ar + ai * ai)
    return 20.0 * math.log10(num / den) if num > 0 else float('-inf')


def composite_db(hz, centre, q, level_db, threshold_db, ratio, rate=RATE):
    """The closed form T5 is measured against: both sections share a
    denominator, so the sum is one numerator over it."""
    w0 = 2.0 * math.pi * centre / rate
    alpha = math.sin(w0) / (2.0 * q)
    cos0 = math.cos(w0)
    scale = 10.0 ** (law(level_db + h_bp_db(hz, centre, q, rate)
                         - threshold_db, ratio) / 20.0)
    w = 2.0 * math.pi * hz / rate
    br = (1.0 + scale * alpha) - 2.0 * cos0 * math.cos(-w) \
        + (1.0 - scale * alpha) * math.cos(-2 * w)
    bi = -2.0 * cos0 * math.sin(-w) + (1.0 - scale * alpha) \
        * math.sin(-2 * w)
    ar = (1.0 + alpha) - 2.0 * cos0 * math.cos(-w) + (1.0 - alpha) \
        * math.cos(-2 * w)
    ai = -2.0 * cos0 * math.sin(-w) + (1.0 - alpha) * math.sin(-2 * w)
    return 20.0 * math.log10(math.sqrt(br * br + bi * bi)
                             / math.sqrt(ar * ar + ai * ai))


def _tone_level_db(data, hz=750.0, rate=RATE, channels=CHANNELS,
                   skip=24000):
    """One tone's level out of a two-tone probe, by a single-bin DFT over a
    whole number of cycles."""
    frames = len(data) // channels - skip
    cycles = int(frames * hz / rate)
    span = int(round(cycles * rate / hz))
    real = imag = 0.0
    step = 2.0 * math.pi * hz / rate
    for index in range(span):
        value = float(data[(skip + index) * channels])
        real += value * math.cos(step * index)
        imag -= value * math.sin(step * index)
    return 20.0 * math.log10(2.0 * math.sqrt(real * real + imag * imag)
                             / span)


def _reset_residual(clear):
    """Reset the class 32 frames after a 300 Hz burst at Q 12 - inside the
    ring-down - and report the loudest sample it leaves behind."""
    data = burst(300.0, amp(-3.0), 4800, 96000, 4800)
    effect, _ = build(data, frequency=300.0, q=12.0, threshold_db=-60.0,
                      ratio=8.0)
    render(effect.output, 4800 + 4800 + 32)
    clear(effect)
    after = render(effect.output, 2400)
    return max(abs(v) for v in after)


# --------------------------------------------------------------------------
# Tier 1 - the invariants


class Tier1(unittest.TestCase):
    def test_wire_at_mix_zero_is_byte_identical(self):
        """WIRE. Mix 0 is the dry tap at unity and both branches at zero, so
        it is a byte compare and not a claim about the split being flat."""
        data = sine(1000.0, amp(-4.4), 48000)
        effect, _ = build(data, mix=0.0)
        out = render(effect.output, 48000)
        self.assertEqual(effect.latency_samples, 0)
        self.assertEqual(bytes(out), bytes(data))

    def test_level_is_honest_below_threshold(self):
        """LEVEL. Nothing is added anywhere: a tone 10 dB under the threshold
        comes out at unity through the whole processor."""
        moved = tone_gain(3000.0, -41.0)
        print("\n  LEVEL: -41 dBFS at f0 -> %+0.4f dB" % moved)
        self.assertLess(abs(moved), 0.05)

    def test_tail_reaches_exact_zero_at_every_band(self):
        """TAIL. Burst then silence; the last non-zero frame and the residual
        after it. `audiobiquad`'s float state is flushed below 1e-20, which is
        the whole reason this class is not on the ported biquad."""
        for centre in (60.0, 400.0, 3000.0):
            data = burst(centre, amp(-3.0), 9600, 158400, 4800)
            effect, _ = build(data, frequency=centre, q=2.0,
                              threshold_db=-60.0, ratio=8.0)
            out = render(effect.output, 158400)
            last = 0
            for index in range(len(out) // CHANNELS):
                if out[index * CHANNELS] or out[index * CHANNELS + 1]:
                    last = index
            residual = max(abs(v) for v in out[-4800 * CHANNELS:])
            print("  TAIL %7.1f Hz: last non-zero frame %6d, residual %d LSB"
                  % (centre, last, residual))
            self.assertEqual(residual, 0)
            self.assertLessEqual(last - 14400, effect.tail_samples)

    def test_latency_is_zero_at_48k_and_44k1(self):
        """CLICK. An impulse comes out where it went in, at full height."""
        for rate in (48000, 44100):
            data = impulse(20000, 50, 24000)
            effect, _ = build(data, rate=rate)
            out = render(effect.output, 24000)
            peak = max(abs(v) for v in out)
            at = 0
            for index in range(len(out) // CHANNELS):
                if abs(out[index * CHANNELS]) == peak:
                    at = index
                    break
            print("  CLICK %d Hz: peak %d at frame %d, reported %d"
                  % (rate, peak, at, effect.latency_samples))
            self.assertEqual(peak, 20000)
            self.assertEqual(at - 50, effect.latency_samples)

    def test_reset_clears_every_node_and_leaves_the_source_rendering(self):
        """STATE. The reset lands 32 frames after the burst ends, inside the
        ring-down, so there is really something to clear; and the burst leads
        with silence, because `RawSample` replays a burst at frame 0 whatever
        the class did."""
        residual = _reset_residual(lambda effect: effect.reset())
        print("  STATE: residual after reset %d LSB" % residual)
        self.assertLess(residual, 100)

        data = burst(3000.0, amp(-3.0), 4800, 96000, 4800)
        effect, source = build(data, frequency=3000.0, q=8.0,
                               threshold_db=-60.0, ratio=8.0)
        render(effect.output, 12000)
        effect.reset()
        self.assertEqual(effect.patch_index, 0)
        # The borrowed source is never reset and never deinitialised.
        self.assertIsNotNone(audiocore.get_buffer(source)[1])
        effect.deinit()
        effect.deinit()
        self.assertIsNotNone(audiocore.get_buffer(source)[1])
        with self.assertRaises(RuntimeError):
            effect.output

    def test_deinit_releases_every_node_the_class_built(self):
        effect, source = build(sine(1000.0, amp(-6.0), 4800))
        nodes = [effect._guard, effect._notch, effect._band, effect._cell,
                 effect._mixer] + list(effect._taps)
        render(effect.output, 2400)
        effect.deinit()
        for node in nodes:
            with self.assertRaises(Exception):
                audiocore.get_buffer(node)

    def test_capabilities_is_empty_and_the_transport_is_never_read(self):
        """`capabilities` names `"tempo_sync"` if and only if the transport
        is read, so the honest test is to hand the class a transport that
        records being called and render through it."""
        calls = []

        def transport():
            calls.append(1)
            return _component.static_transport()

        data = sine(1000.0, amp(-6.0), 24000)
        source = audiocore.RawSample(data, sample_rate=RATE, channel_count=2)
        effect = audioeffects.create('DynamicEQ', source, RATE,
                                     transport=transport)
        render(effect.output, 24000)
        for index in range(len(effect.MACRO_LABELS)):
            effect.set_macro(index, 64)
        effect.program_change(2)
        render(effect.output, 2400)
        print("\n  CAPS: transport read %d times, capabilities %r"
              % (len(calls), effect.capabilities))
        self.assertEqual(effect.capabilities, ())
        self.assertEqual(calls, [])

    def test_mono_is_the_same_processing(self):
        """Every invariant holds at `channel_count` 1."""
        for channels in (1, 2):
            moved = tone_gain(3000.0, -10.0, channels=channels)
            print("  MONO: %d channel -> %+0.3f dB at f0" % (channels, moved))
            self.assertLess(abs(moved + 14.577), 0.05)

    def test_rate_honesty_at_44k1_and_22k05(self):
        """Tier 1's rate row: the law holds at every rate, and a band above
        the running rate's usable span clamps rather than refusing."""
        for rate in (48000, 44100, 22050):
            moved = tone_gain(3000.0, -10.0, frames=rate, rate=rate)
            print("  RATE %5d: %+0.3f dB at f0" % (rate, moved))
            self.assertLess(abs(moved + 14.577), 0.35)
        effect, _ = build(sine(1000.0, amp(-6.0), 2400), rate=22050)
        effect.set_macro(0, 127)
        print("  RATE clamp at 22050: asked %0.1f Hz, applied %0.1f Hz"
              % (effect.macro(0), effect.frequency_hz))
        self.assertAlmostEqual(effect.frequency_hz, 22050 * 0.4, places=3)
        self.assertGreater(effect.macro(0), effect.frequency_hz)

    def test_pulling_output_allocates_nothing(self):
        import gc
        effect, _ = build(sine(1000.0, amp(-6.0), 96000))
        render(effect.output, 4800)
        gc.collect()
        before = len(gc.get_objects())
        for _ in range(20):
            audiocore.get_buffer(effect.output)
        gc.collect()
        print("  ALLOC: live objects %d -> %d" % (before,
                                                  len(gc.get_objects())))
        self.assertLessEqual(len(gc.get_objects()) - before, 8)


# --------------------------------------------------------------------------
# Tier 2 - the traits


class Tier2(unittest.TestCase):
    def test_t1_the_split_is_exact(self):
        """T1. Detector idle: reconstruction within 0.05 dB, and an impulse
        out at its input peak."""
        worst = 0.0
        for hz in T1_SWEEP:
            moved = tone_gain(hz, -20.0, threshold_db=0.0, ratio=1.0)
            print("\n  T1 %8.1f Hz -> %+0.4f dB" % (hz, moved))
            worst = max(worst, abs(moved))
        print("  T1 worst deviation from unity: %0.4f dB" % worst)
        self.assertLess(worst, 0.05)
        for centre, q in ((100.0, 0.5), (3000.0, 2.0), (10000.0, 8.0)):
            data = impulse(20000, 50, 24000)
            effect, _ = build(data, frequency=centre, q=q,
                              threshold_db=0.0, ratio=1.0)
            out = render(effect.output, 24000)
            print("  T1 impulse f0 %6.0f Q %3.1f -> peak %d at frame %d"
                  % (centre, q, max(abs(v) for v in out),
                     max(range(len(out)), key=lambda i: abs(out[i]))
                     // CHANNELS))
            self.assertEqual(max(abs(v) for v in out), 20000)

    def test_t2_and_t3_the_gain_law(self):
        """T2 and T3. Five levels, each against the law that applies there."""
        worst = 0.0
        for level in (-41.0, -30.0, -21.0, -10.0, -4.0):
            moved = tone_gain(3000.0, level)
            predicted = law(level + 30.0, 4.0)
            print("\n  T2 %7.2f dBFS -> %+8.3f dB (law %+7.3f, d %+0.3f)"
                  % (level, moved, predicted, moved - predicted))
            worst = max(worst, abs(moved - predicted))
            if level == -41.0:
                self.assertLess(abs(moved), 0.05)     # T3
        print("  T2 worst deviation from the law: %0.3f dB" % worst)
        self.assertLess(worst, 1.0)

    def test_t4_out_of_band_is_untouched(self):
        """T4. Two octaves down, idle and hard at work."""
        idle = tone_gain(750.0, -41.0)
        working = tone_gain(750.0, -4.0)
        print("\n  T4 750 Hz idle %+0.4f dB, working %+0.4f dB, delta %0.4f"
              % (idle, working, abs(working - idle)))
        self.assertLess(abs(idle), 0.2)
        self.assertLess(abs(working), 0.2)
        self.assertLess(abs(working - idle), 0.2)

    def test_t5_the_bell_is_the_closed_form(self):
        """T5. One frequency at a time at a fixed level, never a sweep."""
        worst = 0.0
        for hz in (1000., 1500., 2000., 2500., 3000., 3600., 4500., 6000.):
            moved = tone_gain(hz, -10.0)
            predicted = composite_db(hz, 3000.0, 2.0, -10.0, -30.0, 4.0)
            print("\n  T5 %6.0f Hz -> %+8.3f dB (closed form %+8.3f,"
                  " d %+0.3f)" % (hz, moved, predicted, moved - predicted))
            worst = max(worst, abs(moved - predicted))
        print("  T5 worst deviation: %0.3f dB" % worst)
        self.assertLess(worst, 0.5)

    def test_t6_mix_is_the_range_control(self):
        """T6. The composite at f0 against `20 log10((1-m) + m*g1)`, and an
        out-of-band control that must not move at all."""
        g1_db = tone_gain(3000.0, -10.0, mix=1.0)
        g1 = 10.0 ** (g1_db / 20.0)
        worst = 0.0
        for mix in (0.0, 0.25, 0.5, 0.75, 0.9, 1.0):
            moved = tone_gain(3000.0, -10.0, mix=mix)
            predicted = 20.0 * math.log10((1.0 - mix) + mix * g1)
            print("\n  T6 mix %4.2f -> %+8.3f dB (closed form %+8.3f,"
                  " d %+0.3f)" % (mix, moved, predicted, moved - predicted))
            worst = max(worst, abs(moved - predicted))
        print("  T6 worst deviation: %0.4f dB" % worst)
        self.assertLess(worst, 0.2)
        out_of_band = [tone_gain(375.0, -10.0, mix=mix)
                       for mix in (0.0, 0.5, 1.0)]
        print("  T6 375 Hz across the sweep: %s"
              % ", ".join("%+0.4f" % v for v in out_of_band))
        self.assertLess(max(out_of_band) - min(out_of_band), 0.05)
        effect, _ = build(sine(1000.0, amp(-6.0), 2400), mix=0.75)
        self.assertAlmostEqual(effect.range_db, 12.0, places=1)

    def test_expand_cuts_the_band_when_the_band_is_quiet(self):
        """The `expand=True` build, which is the direction S6 calls
        expansion: over the threshold it is a wire, under it the band goes
        away."""
        loud = tone_gain(3000.0, -6.0, expand=True, threshold_db=-30.0,
                         ratio=4.0)
        quiet = tone_gain(3000.0, -46.0, expand=True, threshold_db=-30.0,
                          ratio=4.0)
        print("\n  EXPAND: -6 dBFS -> %+0.3f dB, -46 dBFS -> %+0.3f dB"
              % (loud, quiet))
        self.assertLess(abs(loud), 0.1)
        self.assertLess(quiet, -20.0)


# --------------------------------------------------------------------------
# Metadata and surface


class Surface(unittest.TestCase):
    def test_patch_zero_is_the_constructors_defaults(self):
        """Held to the spans rather than to a hand-copied list."""
        defaults = (3000.0, 2.0, -30.0, 4.0, 2.0, 80.0, 1.0, 0.0)
        spans = module.DynamicEQ._MACRO_RANGES
        expected = tuple(_component.macro_of(spans[index], value)
                         for index, value in enumerate(defaults))
        self.assertEqual(module.DynamicEQ.PATCHES[0][1], expected)

    def test_patch_index_follows_the_contract(self):
        effect, _ = build(sine(1000.0, amp(-6.0), 2400))
        self.assertEqual(effect.patch_index, 0)
        effect.set_macro(2, 100)
        self.assertIsNone(effect.patch_index)
        effect.program_change(3)
        self.assertEqual(effect.patch_index, 3)
        effect.program_change(99)               # a wire index nobody has
        self.assertEqual(effect.patch_index, 3)

    def test_the_surface_is_within_the_ceiling_and_named(self):
        cls = module.DynamicEQ
        self.assertLessEqual(len(cls.MACRO_LABELS), 16)
        self.assertGreater(len(cls.PATCHES), 1)
        self.assertEqual(cls.TIER, _component.AUDIOIF)
        self.assertEqual(cls.REQUIRES,
                         ("audiobiquad", "audiodynamics", "audioroute"))

    def test_listen_solos_the_processed_band(self):
        effect, _ = build(sine(750.0, amp(-10.0), 24000))
        out = render(effect.output, 24000)
        effect.set_macro(7, 127)
        soloed = render(effect.output, 24000)
        print("\n  LISTEN: 750 Hz through, rms %0.1f -> soloed rms %0.1f"
              % (rms(out, 12000), rms(soloed, 12000)))
        self.assertGreater(rms(out, 12000), 100.0)
        self.assertLess(rms(soloed, 12000), rms(out, 12000) * 0.2)


# --------------------------------------------------------------------------
# The planted faults - one of the same kind per demonstrated trait


class PlantedFaults(unittest.TestCase):
    """Each fault is planted in a live instance, so the control and the
    faulted run differ by exactly the thing being tested."""

    def _faulted_gain(self, hz, level_db, mutate, frames=48000, **options):
        data = sine(hz, amp(level_db), frames)
        effect, _ = build(data, **options)
        mutate(effect)
        out = render(effect.output, frames)
        skip = frames // 2
        return gain_db(rms(out, skip), rms(data, skip))

    def _worst_over_the_sweep(self, mutate):
        worst = 0.0
        for hz in T1_SWEEP:
            moved = self._faulted_gain(hz, -20.0, mutate,
                                       threshold_db=0.0, ratio=1.0)
            print("    %8.1f Hz -> %+0.4f dB" % (hz, moved))
            worst = max(worst, abs(moved))
        return worst

    def test_t1_goes_red_when_one_branch_is_detuned(self):
        """T1's fault: 1 % between the two sections, which is what a class
        that pushed Frequency to one branch and not the other would do.

        Read over T1's own sweep, because at f0 the notch is zero and the
        band-pass is unity and a mistune is invisible there. That is the
        whole reason the sweep has skirt points in it.
        """
        def detune(effect):
            effect._band.frequency = effect._notch.frequency * 1.01

        print("\n  T1 fault, band branch detuned 1%:")
        worst = self._worst_over_the_sweep(detune)
        print("  T1 fault worst %0.4f dB against a 0.05 dB bar" % worst)
        self.assertGreater(worst, 0.05)

    def test_t1_goes_red_when_the_widths_diverge(self):
        def widen(effect):
            effect._band.Q = effect._notch.Q * 1.1

        print("\n  T1 fault, Q 10% apart:")
        worst = self._worst_over_the_sweep(widen)
        print("  T1 fault worst %0.4f dB against a 0.05 dB bar" % worst)
        self.assertGreater(worst, 0.05)

    def test_t2_goes_red_when_the_knee_is_dropped(self):
        """T2's fault: a hard knee where the node has a 6 dB soft one. The
        knee probe sits exactly on the threshold, where the law says -0.56 dB
        and a hard knee says 0."""
        clean = tone_gain(3000.0, -30.0)

        def harden(effect):
            effect._cell.set(knee_db=0.0)

        faulted = self._faulted_gain(3000.0, -30.0, harden)
        predicted = law(0.0, 4.0)
        print("\n  T2 fault: law %+0.3f, clean %+0.3f, hard knee %+0.3f"
              % (predicted, clean, faulted))
        self.assertLess(abs(clean - predicted), 1.0)
        self.assertGreater(abs(faulted - predicted), 0.4)

    def test_t2_goes_red_on_a_wrong_ratio(self):
        clean = tone_gain(3000.0, -10.0)

        def wrong(effect):
            effect._cell.set(ratio=2.0)

        faulted = self._faulted_gain(3000.0, -10.0, wrong)
        predicted = law(20.0, 4.0)
        print("  T2 fault: law %+0.3f, clean %+0.3f, ratio 2 %+0.3f"
              % (predicted, clean, faulted))
        self.assertLess(abs(clean - predicted), 1.0)
        self.assertGreater(abs(faulted - predicted), 1.0)

    def test_t3_goes_red_when_the_threshold_is_lifted(self):
        clean = tone_gain(3000.0, -41.0)

        def lift(effect):
            effect._cell.set(threshold_db=-55.0)

        faulted = self._faulted_gain(3000.0, -41.0, lift)
        print("\n  T3 fault: clean %+0.4f dB, threshold -55 %+0.4f dB"
              % (clean, faulted))
        self.assertLess(abs(clean), 0.05)
        self.assertGreater(abs(faulted), 0.05)

    def test_t4_goes_red_on_the_broadband_ducker_topology(self):
        """T4's fault: put the gain cell on the *whole* signal and key it
        from the band, which is a de-esser - the thing S6 says a dynamic EQ
        is not, because its crossover "affects fairly broad frequency areas".

        Keying the cell off the dry tap while leaving it on the band branch
        is **not** this fault and was tried first: out of band the band
        branch carries almost nothing, so ducking it moves the sum by 0.07 dB
        whatever the key hears. The topology is what T4 is about.
        """
        clean_idle = tone_gain(750.0, -41.0)
        clean_work = tone_gain(750.0, -4.0)

        def ducker(effect):
            effect._cell.play(effect._taps[0])
            effect._cell.key(effect._band)
            effect._mixer.voice[0].level = 0.0
            effect._mixer.voice[1].level = 0.0
            effect._mixer.voice[2].level = 1.0

        # The key has to have something in it, so the probe carries the band
        # tone as well as the out-of-band one.
        def two_tone(level_db):
            band = sine(3000.0, amp(level_db), 48000)
            away = sine(750.0, amp(-10.0), 48000)
            return array.array('h', [band[i] + away[i]
                                     for i in range(len(band))])

        results = []
        for level_db, mutate in ((-41.0, None), (-4.0, None),
                                 (-41.0, ducker), (-4.0, ducker)):
            data = two_tone(level_db)
            effect, _ = build(data)
            if mutate is not None:
                mutate(effect)
            out = render(effect.output, 48000)
            results.append(_tone_level_db(out) - _tone_level_db(data))
        print("\n  T4 fault: clean 750 Hz %+0.3f -> %+0.3f dB (delta %0.3f);"
              " ducker %+0.3f -> %+0.3f dB (delta %0.3f)"
              % (results[0], results[1], abs(results[1] - results[0]),
                 results[2], results[3], abs(results[3] - results[2])))
        self.assertLess(abs(clean_work - clean_idle), 0.2)
        self.assertLess(abs(results[1] - results[0]), 0.2)
        self.assertGreater(abs(results[3] - results[2]), 0.2)

    def test_t5_goes_red_when_the_detector_reads_the_wrong_band(self):
        """T5's fault: the detector's selectivity is |H_bp|, so key it from a
        band an octave away and the closed form stops describing the skirt."""
        hz = 2500.0
        clean = tone_gain(hz, -10.0)
        predicted = composite_db(hz, 3000.0, 2.0, -10.0, -30.0, 4.0)

        def mistune(effect):
            effect._cell.set(sidechain_hz=6000.0, sidechain_poles=2)

        faulted = self._faulted_gain(hz, -10.0, mistune)
        print("\n  T5 fault at %0.0f Hz: closed form %+0.3f, clean %+0.3f,"
              " mistuned key %+0.3f" % (hz, predicted, clean, faulted))
        self.assertLess(abs(clean - predicted), 0.5)
        self.assertGreater(abs(faulted - predicted), 0.5)

    def test_t6_goes_red_when_the_dry_voice_is_not_the_complement(self):
        """T6's fault: leave the dry voice at unity while the wet voices
        blend, which is what a class that treated Mix and Range as two
        different mechanisms would do."""
        g1 = 10.0 ** (tone_gain(3000.0, -10.0, mix=1.0) / 20.0)
        mix = 0.5
        clean = tone_gain(3000.0, -10.0, mix=mix)

        def unbalance(effect):
            effect._mixer.voice[0].level = 1.0

        faulted = self._faulted_gain(3000.0, -10.0, unbalance, mix=mix)
        predicted = 20.0 * math.log10((1.0 - mix) + mix * g1)
        print("\n  T6 fault: closed form %+0.3f, clean %+0.3f, dry at unity"
              " %+0.3f" % (predicted, clean, faulted))
        self.assertLess(abs(clean - predicted), 0.2)
        self.assertGreater(abs(faulted - predicted), 0.2)

    def test_wire_goes_red_on_a_one_lsb_dry_path(self):
        """WIRE's fault: 32767/32768 on the dry voice. Inaudible, and the byte
        compare must still refuse it."""
        data = sine(1000.0, amp(-4.4), 24000)
        effect, _ = build(data, mix=0.0)
        effect._mixer.voice[0].level = 32767.0 / 32768.0
        out = render(effect.output, 24000)
        first = None
        for index in range(min(len(out), len(data))):
            if out[index] != data[index]:
                first = index
                break
        print("\n  WIRE fault: first differing sample %r" % (first,))
        self.assertIsNotNone(first)

    def test_tail_goes_red_on_a_held_dc_state(self):
        """TAIL's fault: the audioif#23 shape, a state that never arrives.
        Planted by running the same graph on the ported Q12 biquad."""
        import audiofilters
        import synthio
        data = burst(60.0, amp(-3.0), 9600, 158400, 4800)
        source = audiocore.RawSample(data, sample_rate=RATE, channel_count=2)
        guard = audiofilters.Filter(
            filter=None, mix=1, buffer_size=1024, sample_rate=RATE,
            channel_count=2, bits_per_sample=16, samples_signed=True)
        guard.play(source, loop=False)
        ported = audiofilters.Filter(
            filter=synthio.Biquad(synthio.FilterMode.LOW_PASS,
                                  frequency=60.0, Q=2.0),
            mix=1, buffer_size=1024, sample_rate=RATE, channel_count=2,
            bits_per_sample=16, samples_signed=True)
        ported.play(guard, loop=False)
        out = render(ported, 158400)
        residual = max(abs(v) for v in out[-4800 * CHANNELS:])
        print("  TAIL fault (ported Q12 biquad at 60 Hz): residual %d LSB"
              % residual)
        self.assertGreater(residual, 0)

    def test_click_goes_red_when_latency_is_misreported(self):
        """CLICK's fault: report 256 short with the DSP untouched."""
        data = impulse(20000, 50, 24000)
        effect, _ = build(data)

        class Liar(type(effect)):
            LATENCY_SAMPLES = 256

        effect.__class__ = Liar
        out = render(effect.output, 24000)
        at = 0
        for index in range(len(out) // CHANNELS):
            if abs(out[index * CHANNELS]) == 20000:
                at = index
                break
        print("\n  CLICK fault: measured %d, reported %d"
              % (at - 50, effect.latency_samples))
        self.assertNotEqual(at - 50, effect.latency_samples)

    def test_the_block_ladder_goes_red_without_the_guard(self):
        """The guard's fault, and it is `MultibandCompressor` M5's shape: a
        `Splitter` fed straight off a whole-buffer source loses everything
        past its 8192-frame ring. Built here rather than mutated, because the
        Splitter's source is fixed at construction - the control is the class
        and the fault is the same graph with the guard taken out."""
        import audiobiquad
        import audiodynamics
        import audioroute
        import audiomixer

        def sum_of_a_split(guarded):
            # An impulse near the head, inside a 40000-frame buffer. A
            # continuous tone would *not* catch this: losing the first 32000
            # frames of a sine still leaves a sine, and the peak reads the
            # same either way. The thing that is lost is where the audio
            # started.
            data = impulse(20000, 200, 40000)
            source = audiocore.RawSample(data, sample_rate=RATE,
                                         channel_count=2)
            if guarded:
                import audiofilters
                head = audiofilters.Filter(
                    filter=None, mix=1, buffer_size=256 * 2 * 2,
                    sample_rate=RATE, channel_count=2, bits_per_sample=16,
                    samples_signed=True)
                head.play(source, loop=False)
            else:
                head = source
            split = audioroute.Splitter(head, taps=3)
            notch = audiobiquad.Biquad(mode=audiobiquad.NOTCH,
                                       frequency=3000.0, Q=2.0,
                                       sample_rate=RATE, channel_count=2)
            band = audiobiquad.Biquad(mode=audiobiquad.BAND_PASS,
                                      frequency=3000.0, Q=2.0,
                                      sample_rate=RATE, channel_count=2)
            notch.play(split.tap(1))
            band.play(split.tap(2))
            cell = audiodynamics.Dynamics(
                audiodynamics.DYN_COMPRESS, sample_rate=RATE,
                channel_count=2, threshold_db=-30.0, ratio=4.0)
            cell.play(band)
            mixer = audiomixer.Mixer(voice_count=3, sample_rate=RATE,
                                     channel_count=2, bits_per_sample=16,
                                     samples_signed=True, buffer_size=2048)
            for voice in range(3):
                mixer.voice[voice].level = 1.0 if voice else 0.0
            mixer.play(split.tap(0), voice=0, loop=True)
            mixer.play(notch, voice=1, loop=True)
            mixer.play(cell, voice=2, loop=True)
            return max(abs(v) for v in render(mixer, 3000))

        clean = sum_of_a_split(True)
        faulted = sum_of_a_split(False)
        print("\n  GUARD fault: impulse at frame 200 of a 40000-frame"
              " RawSample, guarded peak %d, unguarded peak %d"
              % (clean, faulted))
        self.assertGreater(clean, 1000)
        self.assertEqual(faulted, 0)

    def test_state_goes_red_when_a_node_is_left_out_of_the_walk(self):
        """STATE's fault: a class whose reset reaches the tail only, which is
        `_core.reset()`'s shape and the defect section 7 names.

        The reset has to land **while the split is still ringing** or the
        measurement is vacuous: a reset taken after the ring-down has already
        reached zero leaves nothing for either version to fail to clear. This
        one resets 32 frames after a 300 Hz burst at Q 12, whose declared
        tail is 7680 samples.
        """
        clean = _reset_residual(lambda effect: effect.reset())
        faulted = _reset_residual(lambda effect: effect._reset_mixer())
        print("\n  STATE fault: class reset leaves %d LSB, tail-only reset"
              " leaves %d LSB" % (clean, faulted))
        self.assertLess(clean, 100)
        self.assertGreater(faulted, 1000)


if __name__ == '__main__':
    unittest.main()
