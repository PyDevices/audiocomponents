"""`BandPass`'s own invariant and planted-fault tests (effects Phase 2).

The dossier is `workspace docs/effects-internal/dossiers/BandPass.md`, traits frozen 2026-09-07; the
evidence pack this file's numbers are read into is
`workspace docs/effects-internal/evidence/BandPass-evidence.md`. Every Tier 1 invariant and every Tier 2
trait the dossier fixed has a test here, and **every one of them has a
planted fault of its own kind beside it**, because a measurement whose
checker has never been shown failing is not a measurement
(`docs/effects-kit-spec.md` section 6).

The measurements are the kit's - `tools/effect_measurements.py` - driven over
in-process renders through `tests/support/kit_probes.py`, so nothing is read
from disk and no stale artifact can be mistaken for a fresh one. The Tier 2
rows that need a tone the committed probe corpus does not carry (T2's -3 dB
edges, T4's skirts, T5's folded pairs) build their own sines rather than
regenerating `tools/effect_probes/probes.json`, which is a golden.

The bar every closed-form comparison is read against is RBJ's own transfer
function evaluated at the running rate, `_closed_form_db` below - not a
recorded curve, and not the 48 kHz curve at another rate (T6).
"""

import cmath
import math
import os
import sys
import unittest
from array import array

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import audiobiquad                                              # noqa: E402
import audiocore                                                # noqa: E402
from audioeffects import bandpass                        # noqa: E402

#: The subject is named directly. `BandPass` has come home to
#: `audioeffects/bandpass.py`; `rebuilt.ADOPTED` no longer lists it. These
#: tests still import the home module so a planted-fault subclass is
#: measured against this file, not only `create()`.
import kit_faults as faults                                     # noqa: E402
import kit_probes as probes                                     # noqa: E402
from tools import effect_measurements as kit                    # noqa: E402

#: The planted-fault classes below are `BandPass` subclasses defined in this
#: module, and `_component`'s metadata check reads `VENDOR` off the module a
#: class is defined in. Without this they fail on their metadata before they
#: can fail on the fault, which would make every one of them a false red.
VENDOR = "PyDevices"

RATES = (48000, 44100, 22050)

#: The class's macro indexes, by name, so a test reads as the panel does.
FREQUENCY, WIDTH, SLOPE, MIX = 0, 1, 2, 3


# --------------------------------------------------------------------------
# Building and rendering


def build(rate=48000, channels=2, block=256, source=None,
          cls=bandpass.BandPass, **options):
    """One `cls` around `source`, through the contract's boundary.

    `cls` is `BandPass` unless a planted fault names its own subclass. It is
    a parameter rather than a hard-coded name because a fault that does not
    go through this constructor does not go through the class - the gate
    audit's T1 ruling.
    """
    if source is None:
        source = probes.ArraySource(probes.silence(1024, channels),
                                    rate=rate, channels=channels, block=block)
    return cls.create(source, rate, **options)


def render_through(data, rate=48000, channels=2, block=256, frames=None,
                   cls=bandpass.BandPass, **options):
    """Render `data` (an int16 array) through a fresh `BandPass`, and return
    (wet, dry) as kit `Render`s over the same frames."""
    frames = frames or len(data) // channels
    source = probes.ArraySource(data, rate=rate, channels=channels,
                                block=block)
    effect = build(rate=rate, channels=channels, block=block, source=source,
                   cls=cls, **options)
    try:
        wet = probes.render(effect.output, frames, rate=rate,
                            channels=channels, block=block,
                            class_name="BandPass",
                            latency_samples=effect.latency_samples)
    finally:
        effect.deinit()
    dry = kit.Render(bytes(array("h", data[:frames * channels])), rate,
                     channels, block=block, interpreter="cpython")
    return wet, dry


def sine(hz, seconds, dbfs, rate=48000, channels=2):
    return probes.sine(hz, seconds, dbfs, rate=rate, channels=channels)


def tone_gain_db(hz, f0, q, rate=48000, sections=1, seconds=None,
                 dbfs=-12.0, settle=0.5, cls=bandpass.BandPass):
    """The class's steady-state gain at `hz`, in dB, against the same tone
    rendered dry. One tone at a time - the excitation the kit's RESPONSE
    takes, and the one a resonator does not smear."""
    if seconds is None:
        # Long enough for two things at once: the ring to settle (eight time
        # constants of Q*F_s/(pi*f0) samples), and the settled half of the
        # render to hold twenty whole cycles of the probe, or the single-bin
        # DFT has nothing to read. A probe an octave below the centre needs
        # the second clause; a high-Q centre needs the first.
        seconds = max(0.25, 8.0 * q / (math.pi * f0) + 0.1, 40.0 / hz)
    data = sine(hz, seconds, dbfs, rate=rate)
    wet, dry = render_through(data, rate=rate, frequency=f0, q=q,
                              sections=sections, cls=cls)
    start = int(wet.frames * settle)
    w = kit.tone_bin(wet.float[start:, 0], rate, hz)
    d = kit.tone_bin(dry.float[start:, 0], rate, hz)
    return kit.db(abs(w) / abs(d))


def _closed_form_db(hz, f0, q, rate, sections=1):
    """RBJ's constant-0 dB-peak band-pass, evaluated at `rate`. The bar every
    magnitude claim in this file is read against."""
    w0 = 2.0 * math.pi * f0 / rate
    alpha = math.sin(w0) / (2.0 * q)
    b0, b1, b2 = alpha, 0.0, -alpha
    a0, a1, a2 = 1.0 + alpha, -2.0 * math.cos(w0), 1.0 - alpha
    z = cmath.exp(-2j * math.pi * hz / rate)
    h = (b0 + b1 * z + b2 * z * z) / (a0 + a1 * z + a2 * z * z)
    return sections * 20.0 * math.log10(abs(h))


#: T1's rejection clause, in dB. Three octaves below the centre the closed
#: form is -12.19 dB at the narrowest Q the surface reaches (0.5) and -48.04
#: at the widest (32), so 10 dB separates every reachable setting from a
#: wire, which reads 0.00.
T1_REJECTION_DB = 10.0


def t1_reading(cls=bandpass.BandPass, f0=1000.0, q=2.0, rate=48000,
               sections=1, dbfs=-12.0):
    """T1's measurement: the gain at f0 is 0 dB **and it is a peak**.

    The second half is not decoration. "0 dB at f0" on its own is green on a
    wire - a wire is 0.00 dB at every frequency - so a check with only that
    clause cannot fail, which is the pattern revision's section 1.2 defect.
    `kit_faults.null_build_red()` is run against this function in
    `TierTwo.test_t1_is_red_on_a_null_build`, and it is red only because of
    the rejection clause.
    """
    at_f0 = tone_gain_db(f0, f0, q, rate=rate, sections=sections, dbfs=dbfs,
                         cls=cls)
    skirt = tone_gain_db(f0 / 8.0, f0, q, rate=rate, sections=sections,
                         dbfs=dbfs, cls=cls)
    rejection = at_f0 - skirt
    red = []
    if abs(at_f0) > 0.05:
        red.append("gain at f0 %+.4f dB against a bar of 0.05" % at_f0)
    if rejection < T1_REJECTION_DB:
        red.append("f0 stands only %.4f dB above f0/8 (bar %.1f) - this is "
                   "not a band-pass" % (rejection, T1_REJECTION_DB))
    return {"passed": not red, "red": red,
            "values": {"at_f0_db": at_f0, "skirt_db": skirt,
                       "rejection_db": rejection}}


#: T5's own falsifiability clause. A folded pair r away from the centre sits
#: 1.294 dB down at r = 1.5, the shallowest fold this file takes, and 15.051
#: down at r = 8. A wire's pair sits at 0.000, equal to its own centre, so a
#: 1 dB floor separates every fold measured here from a bypass.
T5_FOLD_DEPTH_DB = 1.0


def t5_reading(cls=bandpass.BandPass, f0=1000.0, ratio=2.0, q=0.707,
               rate=48000):
    """T5's measurement: the folded pair agrees **and the response folds**.

    `|upper - lower| <= 0.05 dB` on its own is green on a wire, whose
    response is flat: 0.000 dB at every frequency, so every fold agrees
    perfectly. The depth clause is what makes the pair a statement about a
    band-pass rather than about arithmetic.
    """
    analog = _prewarp(f0, rate)
    upper = _unwarp(analog * ratio, rate)
    lower = _unwarp(analog / ratio, rate)
    high = tone_gain_db(upper, f0, q, rate=rate, cls=cls)
    low = tone_gain_db(lower, f0, q, rate=rate, cls=cls)
    centre = tone_gain_db(f0, f0, q, rate=rate, cls=cls)
    depth = centre - max(high, low)
    red = []
    if abs(high - low) > 0.05:
        red.append("fold %+.4f vs %+.4f dB, %.4f apart (bar 0.05)"
                   % (high, low, abs(high - low)))
    if depth < T5_FOLD_DEPTH_DB:
        red.append("the pair sits %.4f dB below the centre (bar %.1f) - "
                   "this response does not fold" % (depth, T5_FOLD_DEPTH_DB))
    return {"passed": not red, "red": red,
            "values": {"upper_db": high, "lower_db": low,
                       "apart_db": abs(high - low), "depth_db": depth}}


def _edges(f0, q):
    """T2's closed-form -3 dB edges, `f0 * (sqrt(1 + 1/4Q^2) -+ 1/2Q)`."""
    root = math.sqrt(1.0 + 1.0 / (4.0 * q * q))
    return f0 * (root - 0.5 / q), f0 * (root + 0.5 / q)


def _prewarp(hz, rate):
    return (rate / math.pi) * math.tan(math.pi * hz / rate)


def _unwarp(analog, rate):
    return (rate / math.pi) * math.atan(math.pi * analog / rate)


# --------------------------------------------------------------------------
# The faults this class plants for itself (the kit's own twenty live in
# tests/test_effect_kit.py; these are BandPass's).


def under_reporting(samples):
    """CLICK's fault: the same DSP, `latency_samples` reported `samples`
    short. Both renders must be byte-identical, so a latency check that only
    fires when the sound changes too stays silent here."""
    cls = bandpass.BandPass
    return type("BandPassReporting%d" % samples, (cls,),
                {"LATENCY_SAMPLES": int(samples)})


class NoResetSections(bandpass.BandPass):
    """STATE's first fault: the resonator left ringing after `reset()`.

    The base walks the node list `_own()` built; this one keeps everything
    else and skips exactly that walk, which is the shape the vision names
    for a delay line and which for a band-pass is a tail that survives.
    """

    def reset(self):
        self._check_live()
        self.program_change(0)


class LiveFirstSection(bandpass.BandPass):
    """STATE's second fault: an intermediate node left live after `deinit()`.

    The first section is built but not enumerated for release, so `deinit()`
    reaches the tail and leaves the node in front of it running.
    """

    def _build(self, **options):
        bandpass.BandPass._build(self, **options)
        self._deinits[0] = False


class PeakingNumerator(bandpass.BandPass):
    """T1's fault: a different numerator behind the same surface.

    T1 is the claim that RBJ's `(alpha, 0, -alpha)` numerator puts the peak
    at exactly 0 dB whatever the width. The fault swaps it for `PEAKING_EQ`
    at `gain_db = 1`, which is the shape a band-pass with the wrong numerator
    takes: the skirts still look like a band-pass and the peak does not sit
    at unity. It goes through `BandPass._build`, so the red it produces
    passes through the class - which the fault this replaces did not: it
    built a bare `audiobiquad.Biquad` outside the class entirely (gate audit,
    T1's ruling).

    Unreachable from the surface: no macro and no shipped patch writes a
    section's mode. Asserted, not asserted-by-hand, in
    `TierTwo.test_t1_fault_is_not_a_position_of_the_surface`.
    """

    _SECTION = {"mode": audiobiquad.PEAKING_EQ, "gain_db": 1.0}


class WrongWidth(bandpass.BandPass):
    """T2's fault: the width knob 10 % off what it reports.

    The class is asked for a Q and builds one 10 % away from it, so the two
    predicted -3 dB crossings must move off -3 dB by more than the row's
    0.15 dB bar while the peak gain, which is 0 dB at every Q, stays green.
    """

    SKEW = 1.10

    def _push_q(self):
        q = self._value(WIDTH) * self.SKEW
        if self._steep():
            q *= self._CASCADE_Q
        for section in self._sections:
            section.Q = q


class UncompensatedCascade(bandpass.BandPass):
    """T4's and T2's cascade fault: the second section switched in without
    the `sqrt(sqrt(2) - 1)` compensation.

    This is the shape the dossier's own seed had - it says "divide", which is
    this fault's reciprocal - so the test that catches it is the test that
    would have caught the document.
    """

    _CASCADE_Q = 1.0


# --------------------------------------------------------------------------
# Tier 1 - the invariants


class TierOne(unittest.TestCase):

    def test_wire_mix_zero_is_byte_identical_at_every_rate(self):
        for rate in RATES:
            for sections in (1, 2):
                with self.subTest(rate=rate, sections=sections):
                    data = probes.ramp_fs(8192)
                    wet, dry = render_through(data, rate=rate, mix=0.0,
                                              sections=sections)
                    result = kit.wire(wet, dry, latency_samples=0)
                    self.assertTrue(result["passed"], result["red"])
                    self.assertEqual(
                        result["values"]["differing_samples"], 0)

    def test_planted_fault_one_lsb_on_the_dry_path(self):
        data = probes.ramp_fs(8192)
        source = probes.ArraySource(data, rate=48000, channels=2)
        effect = build(source=source, mix=0.0)
        try:
            faulted = faults.OneLsbScale(effect.output)
            wet = probes.render(faulted, 8192, class_name="BandPass")
        finally:
            effect.deinit()
        dry = kit.Render(bytes(array("h", data)), 48000, 2)
        red = kit.wire(wet, dry, latency_samples=0)
        self.assertFalse(red["passed"])
        self.assertGreater(red["values"]["differing_samples"], 0)
        # ... and the control, the same comparison without the fault.
        green, control_dry = render_through(data, mix=0.0)
        self.assertTrue(kit.wire(green, control_dry)["passed"])

    def test_tail_reaches_exact_zero_at_every_rate(self):
        for rate in RATES:
            for sections in (1, 2):
                with self.subTest(rate=rate, sections=sections):
                    data, burst_end = probes.burst_silence(
                        hz=1000.0, on_ms=200.0, total_s=1.5, dbfs=-6.0,
                        rate=rate)
                    effect = build(rate=rate, sections=sections)
                    declared = effect.tail_samples
                    effect.deinit()
                    wet, _ = render_through(data, rate=rate,
                                            sections=sections)
                    result = kit.tail(
                        wet, burst_end_frame=burst_end,
                        declared_tail_samples=declared)
                    self.assertTrue(result["passed"], result["red"])
                    self.assertEqual(result["values"]["residual_lsb"], 0)

    def test_tail_reaches_exact_zero_at_the_lowest_centre(self):
        # The dossier's A3 shape, at the setting that was red on the stock
        # palette: a low centre with a high Q, read while the source is
        # still supplying silence.
        for f0, q in ((80.0, 4.0), (40.0, 8.0), (20.0, 32.0)):
            with self.subTest(f0=f0, q=q):
                data, burst_end = probes.burst_silence(
                    hz=440.0, on_ms=90.0, total_s=3.1, dbfs=-8.0)
                wet, _ = render_through(data, frequency=f0, q=q)
                result = kit.tail(wet, burst_end_frame=burst_end)
                self.assertEqual(result["values"]["residual_lsb"], 0,
                                 result["values"])

    def test_planted_fault_one_lsb_of_stuck_dc(self):
        data, burst_end = probes.burst_silence(hz=1000.0, on_ms=200.0,
                                               total_s=1.5, dbfs=-6.0)
        source = probes.ArraySource(data, rate=48000, channels=2)
        effect = build(source=source)
        try:
            faulted = faults.StuckDc(effect.output, residue_lsb=1)
            wet = probes.render(faulted, len(data) // 2,
                                class_name="BandPass")
        finally:
            effect.deinit()
        red = kit.tail(wet, burst_end_frame=burst_end)
        self.assertFalse(red["passed"])
        self.assertEqual(red["values"]["residual_lsb"], 1)
        green, _ = render_through(data)
        self.assertTrue(kit.tail(green, burst_end_frame=burst_end)["passed"])

    def test_dc_step_settles_to_zero_while_the_source_still_supplies(self):
        # T3's DC half, and Tier 1's held-DC row: the offset is removed
        # while the source is still handing over frames, so the reading is
        # the filter's state and not `Filter.c`'s empty-source memset.
        data, removed = probes.dc_step(level=0.5, hold_s=0.5, total_s=1.5)
        wet, _ = render_through(data, frequency=80.0, q=4.0)
        result = kit.tail(wet, burst_end_frame=int(48000 * 0.02),
                          dc_render=wet, dc_removed_frame=removed)
        self.assertTrue(result["passed"], result["red"])
        self.assertEqual(result["values"]["dc_residual_lsb"], 0)

    def test_level_is_honest_through_the_dry_path(self):
        data = probes.quiet_chord(seconds=0.5)
        wet, dry = render_through(data, mix=0.0)
        result = kit.level(wet, dry, tolerance_db=0.05)
        self.assertTrue(result["passed"], result["red"])

    def test_planted_fault_a_tenth_of_a_decibel_of_hidden_gain(self):
        data = probes.quiet_chord(seconds=0.5)
        source = probes.ArraySource(data, rate=48000, channels=2)
        effect = build(source=source, mix=0.0)
        try:
            faulted = faults.HiddenGain(effect.output, gain_db=0.1)
            wet = probes.render(faulted, len(data) // 2,
                                class_name="BandPass")
        finally:
            effect.deinit()
        dry = kit.Render(bytes(array("h", data)), 48000, 2)
        self.assertFalse(kit.level(wet, dry, tolerance_db=0.05)["passed"])

    def test_click_matches_the_reported_latency(self):
        for rate in (48000, 44100):
            with self.subTest(rate=rate):
                data = probes.click_stereo(frames=8192, offset=256)
                wet, dry = render_through(data, rate=rate)
                result = kit.click(wet, dry, 0, tolerance_samples=1.0,
                                   subsample=False)
                self.assertTrue(result["passed"], result["red"])

    def test_planted_fault_latency_reported_256_short(self):
        data = probes.click_stereo(frames=8192, offset=256)
        wet, dry = render_through(data)
        red = kit.click(wet, dry, 256, tolerance_samples=1.0,
                        subsample=False)
        self.assertFalse(red["passed"])
        # The DSP is untouched by the fault: the class that reports 256 and
        # the class that reports 0 render the same bytes.
        source = probes.ArraySource(data, rate=48000, channels=2)
        wrong = under_reporting(256).create(source, 48000)
        try:
            other = probes.render(wrong.output, 8192, class_name="BandPass")
        finally:
            wrong.deinit()
        self.assertEqual(other.digest, wet.digest)

    def test_state_reset_deinit_capabilities_and_allocation(self):
        for rate in RATES:
            with self.subTest(rate=rate):
                result = self._state(bandpass.BandPass, rate=rate)
                self.assertTrue(result["passed"], result["red"])
                self.assertEqual(result["values"]["capabilities"], [])
                self.assertEqual(result["values"]["reset_residual_lsb"], 0)
                self.assertEqual(
                    result["values"]["live_nodes_after_deinit"], [])

    def test_planted_fault_the_resonator_still_rings_after_reset(self):
        red = self._state(NoResetSections)
        self.assertFalse(red["passed"])
        self.assertGreater(red["values"]["reset_residual_lsb"], 0)

    def test_planted_fault_an_intermediate_node_left_live(self):
        red = self._state(LiveFirstSection)
        self.assertFalse(red["passed"])
        self.assertTrue(red["values"]["live_nodes_after_deinit"])

    def _state(self, cls, rate=48000):
        """STATE over `cls`, with a probe loud enough and long enough that
        the resonator is still ringing when `reset()` is called - a probe
        that has already decayed would make a skipped reset look clean."""
        data = probes.sine(200.0, 4.0, -6.0, rate=rate)
        holder = probes.SwitchableSource(
            probes.ArraySource(data, rate=rate, channels=2))
        quiet = probes.ArraySource(probes.silence(rate * 4), rate=rate,
                                   channels=2)
        effect = cls.create(holder, rate, frequency=200.0, q=24.0)
        nodes = [("section%d" % index, node)
                 for index, node in enumerate(effect._nodes)]
        return kit.state(
            effect,
            pull=lambda blocks: probes.render(effect.output, blocks * 256,
                                              rate=rate,
                                              class_name="BandPass"),
            swap=holder.swap, probe_source=holder.inner,
            silent_source=quiet, blocks=64, nodes=nodes)

    def test_rate_honesty_clamps_and_never_refuses(self):
        # A 16 kHz centre on a 22.05 kHz graph is the highest centre that
        # rate has, not a ValueError in the middle of a piece.
        for rate in RATES:
            with self.subTest(rate=rate):
                effect = build(rate=rate, frequency=16000.0)
                try:
                    self.assertLessEqual(effect.centre_hz,
                                         min(16000.0, 0.4 * rate) + 1e-6)
                    effect.set_macro(FREQUENCY, 127)
                    self.assertLessEqual(effect.centre_hz,
                                         min(16000.0, 0.4 * rate) + 1e-6)
                    result, data = audiocore.get_buffer(effect.output)
                    self.assertTrue(len(data) > 0)
                finally:
                    effect.deinit()

    def test_every_invariant_also_holds_at_one_channel(self):
        for rate in RATES:
            with self.subTest(rate=rate):
                data = probes.ramp_fs(8192, channels=1)
                wet, dry = render_through(data, rate=rate, channels=1,
                                          mix=0.0)
                self.assertTrue(kit.wire(wet, dry)["passed"])
                # The tail is the same tail in mono, and reaches zero.
                burst, end = probes.burst_silence(hz=1000.0, on_ms=200.0,
                                                  total_s=1.5, dbfs=-6.0,
                                                  rate=rate, channels=1)
                wet, _ = render_through(burst, rate=rate, channels=1)
                self.assertEqual(
                    kit.tail(wet, burst_end_frame=end)["values"]
                    ["residual_lsb"], 0)
                # And the filter is the same filter, to the closed form at
                # the running rate.
                mono = sine(1000.0, 0.5, -12.0, rate=rate, channels=1)
                wet, dry = render_through(mono, rate=rate, channels=1,
                                          frequency=1000.0, q=2.0)
                start = wet.frames // 2
                measured = kit.db(
                    abs(kit.tone_bin(wet.float[start:, 0], rate, 1000.0))
                    / abs(kit.tone_bin(dry.float[start:, 0], rate, 1000.0)))
                self.assertLess(abs(measured), 0.05)


# --------------------------------------------------------------------------
# Tier 2 - the circuit traits, in the dossier's own numbering


def response_over(frequencies, f0, q, rate=48000, sections=1, dbfs=-12.0,
                  **expected):
    """The kit's RESPONSE over a set of steady tones, one render each.

    Steady tones rather than a sweep, which is the excitation the spec's
    selection rule names for anything holding a resonance a sweep would drag
    along with it.
    """
    wet_by_hz, dry_by_hz = {}, {}
    for hz in frequencies:
        seconds = max(0.25, 8.0 * q / (math.pi * f0) + 0.1)
        data = sine(hz, seconds, dbfs, rate=rate)
        wet, dry = render_through(data, rate=rate, frequency=f0, q=q,
                                  sections=sections)
        wet_by_hz[hz], dry_by_hz[hz] = wet, dry
    return kit.response(wet_by_hz, dry_by_hz, reference_hz=f0,
                        expected=expected or None,
                        **({"slope_octave": expected.pop("slope_octave")}
                           if "slope_octave" in expected else {}))


def octave_grid(low, high, points=5):
    return [low * (high / low) ** (index / (points - 1.0))
            for index in range(points)]


class TierTwo(unittest.TestCase):

    # -- T1: 0 dB peak, at every Q ------------------------------------
    #
    # DISCONFIRMED below 100 Hz once Q >= 4, and the cause is the kernel's
    # float32 recursion, not this class (audioif#64; audiocomponents#39; the
    # decomposition and the map are workspace docs/effects-internal/probes/phase2_probes/bandpass_lowcorner.py).
    # The four tests below are the bound: where the row holds, where it does
    # not, that the fault fires through the class, and that the measurement
    # can fail at all.

    #: Where T1 holds, measured rather than assumed: every width the surface
    #: reaches at f0 >= 100 Hz, and every centre it reaches at Q <= 2.
    T1_HOLDS_ABOVE_HZ = 100.0
    T1_HOLDS_BELOW_Q = 2.0

    def test_t1_zero_db_peak_where_the_bound_says_it_holds(self):
        # The dossier row says Q 0.1 to 100. The Width knob reaches 0.5 to 32
        # and the node's kernel clamps Q to 0.05..60, so those two ends are
        # what this can honestly speak for; the pack says so rather than
        # reporting a range nothing exercised.
        for q in (0.5, 0.707, 2.0, 8.0, 32.0):
            for f0 in (100.0, 1000.0, 4800.0):
                with self.subTest(q=q, f0=f0, half="f0 >= 100 Hz"):
                    measured = tone_gain_db(f0, f0, q)
                    self.assertLess(abs(measured), 0.05,
                                    "%.4f dB at f0=%g Q=%g" % (measured, f0,
                                                               q))
        for f0 in (20.0, 25.0, 63.0):
            for q in (0.5, 0.707, 2.0):
                with self.subTest(q=q, f0=f0, half="Q <= 2"):
                    measured = tone_gain_db(f0, f0, q)
                    self.assertLess(abs(measured), 0.05,
                                    "%.4f dB at f0=%g Q=%g" % (measured, f0,
                                                               q))

    def test_t1_holds_with_the_second_section_switched_in(self):
        for q in (0.707, 2.0, 8.0):
            with self.subTest(q=q):
                measured = tone_gain_db(1000.0, 1000.0, q, sections=2)
                self.assertLess(abs(measured), 0.05)

    def test_t1_is_disconfirmed_at_the_two_macro_stops(self):
        """The disconfirmation, kept as a test so it cannot come back green
        without anyone noticing - and so that the day audioif#64 lands, this
        is the test that says so.

        The sweep is the kit's own driver over the spans T1 quantifies over,
        in the class's macro units, and it is run at the stops first because
        that is where the worst cell is.
        """
        effect = build(frequency=1000.0, q=0.707)

        def measure_at(settings):
            del settings
            f0 = effect.centre_hz
            return tone_gain_db(f0, f0, f0 / effect.bandwidth_hz)

        try:
            swept = kit.macro_sweep(
                effect,
                [kit.MacroSpan(FREQUENCY, 0, 127, midpoints=1),
                 kit.MacroSpan(WIDTH, 0, 127, midpoints=1)],
                measure_at, bar=0.05, unit="dB", name="T1")
        finally:
            effect.deinit()
        self.assertFalse(swept["passed"], swept["values"])
        self.assertTrue(swept["values"]["at_a_stop"])
        self.assertEqual(swept["values"]["at_units"],
                         {"Frequency": 20.0, "Width": 32.0})
        self.assertLess(swept["values"]["worst"], -0.4)

    def test_planted_fault_t1_a_numerator_that_is_not_the_constant_zero_db(
            self):
        """`PeakingNumerator` is `BandPass` with `PEAKING_EQ` sections at
        `gain_db = 1` - a different numerator behind the same surface, built
        by the class's own `_build`, so the red passes through `BandPass`."""
        faulted = t1_reading(cls=PeakingNumerator)
        clean = t1_reading()
        self.assertFalse(faulted["passed"], faulted["values"])
        self.assertTrue(clean["passed"], clean["values"])
        self.assertGreater(abs(faulted["values"]["at_f0_db"]), 0.05)
        self.assertLess(abs(clean["values"]["at_f0_db"]), 0.05)

    def test_t1_fault_is_not_a_position_of_the_surface(self):
        """The FAULT-REACHABILITY check: no macro position and no shipped
        patch writes a section's mode, so `PeakingNumerator` is a fault and
        not a disconfirmation waiting to be written down."""
        checked = faults.fault_reachability(
            bandpass.BandPass, PeakingNumerator,
            lambda effect: effect._sections[0].mode,
            lambda cls: build(cls=cls, frequency=1000.0, q=2.0),
            label="BandPass T1")
        self.assertNotEqual(checked["target"], checked["clean"])
        self.assertGreater(checked["checked"], 4 * 17)

    def test_t1_is_red_on_a_null_build(self):
        """The NULL-BUILD RED check. "0 dB at f0" alone is green on a wire -
        a wire is 0.00 dB everywhere - so T1's reading carries a rejection
        clause, and this is what shows the pair can fail."""
        both = faults.null_build_red(
            bandpass.BandPass,
            lambda cls: t1_reading(cls=cls),
            label="BandPass T1")
        self.assertFalse(both["null"]["passed"])
        self.assertTrue(both["control"]["passed"])
        self.assertAlmostEqual(both["null"]["values"]["rejection_db"], 0.0,
                               places=3)

    # -- T2: the width is f0/Q ----------------------------------------

    def test_t2_minus_three_db_edges_are_the_closed_form(self):
        for q in (0.707, 2.0, 8.0):
            low, high = _edges(1000.0, q)
            self.assertAlmostEqual(high - low, 1000.0 / q, places=6)
            for hz in (low, high):
                with self.subTest(q=q, hz=round(hz, 2)):
                    self.assertLess(abs(tone_gain_db(hz, 1000.0, q) + 3.0),
                                    0.15)

    def test_t2_holds_across_the_cascade_with_the_compensation(self):
        for q in (0.707, 2.0, 8.0):
            low, high = _edges(1000.0, q)
            for hz in (low, high):
                with self.subTest(q=q, hz=round(hz, 2)):
                    measured = tone_gain_db(hz, 1000.0, q, sections=2)
                    self.assertLess(abs(measured + 3.0), 0.15,
                                    "%.3f dB" % measured)

    def test_planted_fault_t2_a_width_knob_ten_per_cent_out(self):
        low, high = _edges(1000.0, 2.0)
        data = sine(low, 0.3, -12.0)
        source = probes.ArraySource(data, rate=48000, channels=2)
        wrong = WrongWidth.create(source, 48000, frequency=1000.0, q=2.0)
        try:
            wet = probes.render(wrong.output, len(data) // 2,
                                class_name="BandPass")
        finally:
            wrong.deinit()
        dry = kit.Render(bytes(array("h", data)), 48000, 2)
        start = wet.frames // 2
        measured = kit.db(
            abs(kit.tone_bin(wet.float[start:, 0], 48000, low))
            / abs(kit.tone_bin(dry.float[start:, 0], 48000, low)))
        self.assertGreater(abs(measured + 3.0), 0.15,
                           "the skewed width read %.3f dB" % measured)
        self.assertLess(abs(tone_gain_db(low, 1000.0, 2.0) + 3.0), 0.15)

    def test_planted_fault_t2_the_cascade_without_its_compensation(self):
        # The dossier's own seed said "divide" where the cascade needs a
        # multiply. This is that filter, and the width row must catch it.
        low, _ = _edges(1000.0, 2.0)
        data = sine(low, 0.3, -12.0)
        source = probes.ArraySource(data, rate=48000, channels=2)
        wrong = UncompensatedCascade.create(source, 48000, frequency=1000.0,
                                            q=2.0, sections=2)
        try:
            wet = probes.render(wrong.output, len(data) // 2,
                                class_name="BandPass")
        finally:
            wrong.deinit()
        dry = kit.Render(bytes(array("h", data)), 48000, 2)
        start = wet.frames // 2
        measured = kit.db(
            abs(kit.tone_bin(wet.float[start:, 0], 48000, low))
            / abs(kit.tone_bin(dry.float[start:, 0], 48000, low)))
        self.assertGreater(abs(measured + 3.0), 0.15,
                           "the uncompensated cascade read %.3f dB"
                           % measured)

    # -- T3: exact zeros at DC and Nyquist ----------------------------

    def test_t3_nyquist_alternation_settles_to_zero(self):
        data = probes.alt_fs(frames=8192)
        wet, _ = render_through(data, frequency=1000.0, q=0.707)
        settled = wet.data[wet.frames // 2:]
        self.assertEqual(int(abs(settled).max()), 0)

    def test_t3_a_held_dc_offset_settles_to_zero_at_every_centre(self):
        data, _ = probes.dc_step(level=0.5, hold_s=1.0, total_s=1.2)
        for f0 in (20.0, 80.0, 1000.0, 16000.0):
            with self.subTest(f0=f0):
                wet, _ = render_through(data, frequency=f0, q=4.0)
                window = wet.data[int(48000 * 0.9):int(48000 * 1.0)]
                self.assertEqual(int(abs(window).max()), 0)

    def test_t3_and_t6_are_red_on_a_null_build(self):
        """The NULL-BUILD RED check on the other two demonstrated rows.

        Neither needed a new clause and this is the run that says so. T3
        reads the held DC while the source is still supplying it, and a wire
        passes 16 384 LSB of it; T6 reads the rendered gain against the
        closed form at the running rate, and a wire is 0.00 dB where the
        form is not.
        """
        data, _ = probes.dc_step(level=0.5, hold_s=1.0, total_s=1.2)

        def t3(cls):
            wet, _ = render_through(data, frequency=1000.0, q=4.0, cls=cls)
            window = wet.data[int(48000 * 0.9):int(48000 * 1.0)]
            residual = int(abs(window).max())
            return {"passed": residual == 0,
                    "red": [] if residual == 0 else ["%d LSB" % residual],
                    "values": {"residual_lsb": residual}}

        def t6(cls):
            worst = 0.0
            for hz in (500.0, 1000.0, 2000.0):
                measured = tone_gain_db(hz, 1000.0, 2.0, cls=cls)
                deviation = measured - _closed_form_db(hz, 1000.0, 2.0, 48000)
                worst = max(worst, abs(deviation))
            return {"passed": worst <= 0.1, "red": [],
                    "values": {"worst_db": worst}}

        for name, measure in (("T3", t3), ("T6", t6)):
            with self.subTest(row=name):
                both = faults.null_build_red(bandpass.BandPass, measure,
                                             label="BandPass " + name)
                self.assertFalse(both["null"]["passed"])
                self.assertTrue(both["control"]["passed"])

    # -- T4: the two skirts -------------------------------------------

    def test_t4_low_skirt_is_six_db_per_octave(self):
        for f0 in (100.0, 500.0, 1000.0, 2000.0):
            with self.subTest(f0=f0):
                grid = octave_grid(f0 / 8.0, f0 / 4.0, 5)
                result = response_over(grid, f0, 0.707,
                                       slope_octave=(f0 / 8.0, f0 / 4.0))
                slope = result["values"]["slope_db_per_octave"]
                self.assertTrue(5.7 <= slope <= 6.3,
                                "%.3f dB/octave at f0=%g" % (slope, f0))

    def test_t4_the_one_over_q_law_at_a_hundredth_of_the_centre(self):
        # f0/100 has to be a frequency a render can hold whole cycles of, so
        # the reading starts at a 500 Hz centre; at f0 = 100 Hz the probe
        # would be 1 Hz, which is a statement about the closed form and not
        # a measurement anything here can make.
        for f0 in (500.0, 1000.0, 2000.0):
            with self.subTest(f0=f0):
                measured = tone_gain_db(f0 / 100.0, f0, 0.707)
                self.assertLess(abs(measured + 37.0), 0.1,
                                "%.3f dB at f0/100, f0=%g" % (measured, f0))

    def test_t4_the_one_over_q_law_is_disconfirmed_at_high_centres(self):
        """T4's `-37.0 +- 0.1 dB at every f0` clause, disconfirmed - and the
        cause, measured, is the bilinear warp and not this class.

        The trait-critic pass (dossier A12) caught exactly this for T4's
        *high skirt* and left the f0/100 clause saying "at every f0". It is
        not true at every f0: the closed form itself walks away from
        -37.0 dB as f0 climbs, because f0/100 is read on a warped axis too.
        The class tracks the closed form at the running rate to better than
        0.01 dB the whole way, which is what says the deviation is the
        prototype's and not the build's.
        """
        for f0 in (4800.0, 8000.0, 16000.0):
            with self.subTest(f0=f0):
                measured = tone_gain_db(f0 / 100.0, f0, 0.707)
                ideal = _closed_form_db(f0 / 100.0, f0, 0.707, 48000)
                self.assertGreater(abs(measured + 37.0), 0.1,
                                   "%.3f dB at f0=%g is inside the row's "
                                   "band after all" % (measured, f0))
                self.assertLess(abs(measured - ideal), 0.02,
                                "%.3f dB measured against %.3f dB from the "
                                "closed form" % (measured, ideal))

    def test_t4_high_skirt_is_six_db_per_octave_below_six_hundred_hertz(self):
        for f0 in (100.0, 250.0, 500.0, 600.0):
            with self.subTest(f0=f0):
                grid = octave_grid(4.0 * f0, 8.0 * f0, 5)
                result = response_over(grid, f0, 0.707,
                                       slope_octave=(4.0 * f0, 8.0 * f0))
                slope = result["values"]["slope_db_per_octave"]
                self.assertTrue(-6.3 <= slope <= -5.7,
                                "%.3f dB/octave at f0=%g" % (slope, f0))

    def test_planted_fault_t4_the_cascade_read_against_the_one_section_bar(
            self):
        # A slope fault of the same kind: two sections are +-12 dB/octave,
        # and the row's own band must refuse them.
        f0 = 500.0
        grid = octave_grid(f0 / 8.0, f0 / 4.0, 5)
        result = response_over(grid, f0, 0.707, sections=2,
                               slope_octave=(f0 / 8.0, f0 / 4.0))
        slope = result["values"]["slope_db_per_octave"]
        self.assertFalse(5.7 <= slope <= 6.3,
                         "the cascade fitted %.3f dB/octave" % slope)
        # It is the *pair* of sections that is being read, so the fit is
        # roughly twice the single section's - not exactly, because the
        # compensated Q moves the curvature inside the fitted octave and
        # f0/8..f0/4 is not yet the asymptote.
        self.assertGreater(slope, 10.0, "%.3f dB/octave" % slope)

    # -- T5: geometric symmetry about the prewarped centre -------------

    def test_t5_symmetry_is_exact_on_the_prewarped_axis(self):
        for f0 in (100.0, 1000.0, 4800.0):
            analog = _prewarp(f0, 48000)
            for ratio in (1.5, 2.0, 4.0, 8.0):
                upper = _unwarp(analog * ratio, 48000)
                lower = _unwarp(analog / ratio, 48000)
                if upper >= 48000 * 0.49:
                    continue
                with self.subTest(f0=f0, ratio=ratio):
                    high = tone_gain_db(upper, f0, 0.707)
                    low = tone_gain_db(lower, f0, 0.707)
                    self.assertLess(abs(high - low), 0.05,
                                    "%.4f vs %.4f dB" % (high, low))

    def test_t5_is_red_on_a_null_build(self):
        """The NULL-BUILD RED check on T5. A wire folds perfectly - 0.000 dB
        against 0.000 dB at every ratio - so the agreement clause alone
        cannot fail; `t5_reading` carries a fold-depth clause with it."""
        both = faults.null_build_red(
            bandpass.BandPass, lambda cls: t5_reading(cls=cls),
            label="BandPass T5")
        self.assertFalse(both["null"]["passed"])
        self.assertTrue(both["control"]["passed"])
        self.assertAlmostEqual(both["null"]["values"]["apart_db"], 0.0,
                               places=3)
        self.assertAlmostEqual(both["null"]["values"]["depth_db"], 0.0,
                               places=3)

    def test_planted_fault_t5_the_fold_taken_about_the_wrong_centre(self):
        # Folding about 1.1*f0 is the same measurement with one number
        # wrong, and the 0.05 dB bar must refuse it.
        f0 = 1000.0
        analog = _prewarp(f0 * 1.1, 48000)
        upper = _unwarp(analog * 2.0, 48000)
        lower = _unwarp(analog / 2.0, 48000)
        high = tone_gain_db(upper, f0, 0.707)
        low = tone_gain_db(lower, f0, 0.707)
        self.assertGreater(abs(high - low), 0.05,
                           "%.4f vs %.4f dB" % (high, low))

    # -- T6: rate honesty ----------------------------------------------

    def test_t6_matches_the_closed_form_at_the_running_rate(self):
        for rate in RATES:
            for f0 in (100.0, 1000.0):
                for probe in (f0 / 2.0, f0, f0 * 2.0):
                    if probe >= rate * 0.45:
                        continue
                    with self.subTest(rate=rate, f0=f0, probe=probe):
                        measured = tone_gain_db(probe, f0, 2.0, rate=rate)
                        ideal = _closed_form_db(probe, f0, 2.0, rate)
                        self.assertLess(abs(measured - ideal), 0.1,
                                        "%.4f vs %.4f dB" % (measured,
                                                             ideal))

    def test_t6_the_centre_does_not_move_with_the_rate(self):
        for rate in RATES:
            with self.subTest(rate=rate):
                self.assertLess(abs(tone_gain_db(1000.0, 1000.0, 2.0,
                                                 rate=rate)), 0.05)

    def test_planted_fault_t6_read_against_the_forty_eight_kilohertz_curve(
            self):
        # The row the trait-critic pass replaced: at 22.05 kHz the same
        # centre is up to 0.23 dB from its 48 kHz shape, so a bar of 0.1 dB
        # against the 48 kHz curve is unreachable at any centre - which is
        # what makes it the wrong bar, and this is the reading that says so.
        worst = 0.0
        for f0 in (100.0, 250.0, 500.0, 1000.0, 2000.0):
            measured = tone_gain_db(f0 / 2.0, f0, 2.0, rate=22050)
            against_48k = _closed_form_db(f0 / 2.0, f0, 2.0, 48000)
            worst = max(worst, abs(measured - against_48k))
        self.assertGreater(worst, 0.1, "worst %.4f dB" % worst)


# --------------------------------------------------------------------------
# DIGEST - the axes a render has to state before it can be compared


class Digests(unittest.TestCase):

    def test_the_source_block_size_does_not_change_the_bytes(self):
        # `MultibandCompressor` M5 is the reason this row exists: a class
        # holding a ring shorter than the block it is handed renders nothing.
        # This class holds no ring, and the ladder must be byte-identical.
        data = probes.noise_det(frames=32768)
        renders = {}
        for block in (256, 8192, 16384, 20000, 32768):
            wet, _ = render_through(data, block=block, frames=32768)
            renders["block%d" % block] = wet
        result = kit.digest(renders, mode="identical")
        self.assertTrue(result["passed"], result["red"])

    def test_two_settings_render_different_bytes(self):
        # The control beside the row above: a digest comparison that cannot
        # tell two renders apart is not a comparison.
        data = probes.noise_det(frames=8192)
        one, _ = render_through(data, frequency=200.0, q=2.0)
        other, _ = render_through(data, frequency=4000.0, q=2.0)
        self.assertNotEqual(one.digest, other.digest)
