"""`StereoWidener`'s trait and planted-fault tests.

Six traits: H1-H3 for Haas, M1-M2 for Mid/Side, W for the wire. Each has
its measurement, run over the cells listed with it, and the same
measurement shown red on a planted fault of the same kind. `KIT_PLANTS`
hands the plants to the kit, which shows each one differs from the clean
class and that no knob stop or patch reproduces it.

Every law a measurement checks against is written out here, never taken
from the class: the whole-frame Delay, the Haas levels, the Mid/Side
matrix.

The module is numpy-free and imports on MicroPython and CircuitPython,
where `unittest` is absent: the kit reads `KIT_PLANTS` there, and running
the file prints each trait's figures on whichever interpreter runs it:

    MICROPYPATH=lib:tests/support micropython \\
        tests/test_cpython_effects_stereowidener.py
"""

import math
import sys
from array import array

try:
    import unittest
    TestCase = unittest.TestCase
except ImportError:                     # a native interpreter
    unittest = None
    TestCase = object

try:
    import os
    _HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(_HERE, "support"))
    sys.path.insert(0, os.path.join(_HERE, "..", "lib"))
except (ImportError, AttributeError, NameError):   # no os.path natively
    pass

import audiocore                                            # noqa: E402
import audioecho                                            # noqa: E402
import audiomixer                                           # noqa: E402
from audioeffects import _component                         # noqa: E402
import audioeffects                                         # noqa: E402

VENDOR = "PyDevices"

RATES = (48000, 22050)
BLOCK = 256
WIDTH_I, DELAY_I, CHARACTER_I = range(3)

StereoWidener = audioeffects.StereoWidener


# --------------------------------------------------------------------------
# The card's laws, written out independently of the class


def law_frames(ms, rate):
    """Section 2: tau = max(1, round(Delay ms x rate / 1000))."""
    return max(1, int(math.floor(ms * rate / 1000.0 + 0.5)))


def law_delay_ms(midi):
    """Section 3: Delay is 1-40 ms, log, on the 0-127 grid."""
    return 40.0 ** (midi / 127.0)


#: Section 3's patch Delays, by MIDI step: a patch plays the round number.
PATCH_DELAYS = {62: 6.0, 91: 14.0, 111: 25.0}


def law_step_ms(midi):
    """What Delay on a whole MIDI step plays: a patch's round number on its
    step, the log law elsewhere."""
    return PATCH_DELAYS.get(midi, law_delay_ms(midi))


def delay_midi(ms):
    """The float MIDI position that stands for `ms` exactly."""
    return 127.0 * math.log(ms) / math.log(40.0)


def width_midi(width):
    """The float MIDI position for a Width, by the BIPOLAR law (MIDI 64 is
    1.0, each half its own slope)."""
    position = width / 2.0
    if position >= 0.5:
        return 64.0 + (position - 0.5) * 126.0
    return 64.0 - (0.5 - position) * 128.0


def haas_expect(width):
    """Section 2's Haas law, per unit input: (left gain, right's own gain,
    the copy's gain)."""
    return min(1.0, 1.0 / width), max(0.0, 1.0 - width), min(width, 1.0)


# --------------------------------------------------------------------------
# Material and rendering: integer arithmetic, the same on every interpreter


def lcg_noise(frames, channels, seed, peak=32767):
    """Seeded noise in -peak-1 .. peak (full scale at 32767), each channel
    its own draw."""
    out = array("h", bytes(2 * frames * channels))
    state = (seed * 2654435761 + 1) & 0x7FFFFFFF
    span = 2 * peak + 2 if peak == 32767 else 2 * peak + 1
    low = -peak - 1 if peak == 32767 else -peak
    for i in range(frames * channels):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        out[i] = low + (state >> 7) % span
    return out


def rint(x):
    """Round half away from zero, symmetric, so -x rounds to -round(x)."""
    if x >= 0:
        return int(x + 0.5)
    return -int(-x + 0.5)


def sine(frames, hz, rate, amp, start=0.0, channels=2):
    """The same sine in every channel; `start` shifts its phase in frames."""
    out = array("h", bytes(2 * frames * channels))
    w = 2.0 * math.pi * hz / rate
    for n in range(frames):
        v = rint(amp * math.sin(w * (n - start)))
        for c in range(channels):
            out[channels * n + c] = v
    return out


def source(values, rate, channels=2):
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def pull(effect, frames, moves=None):
    """Render `frames` frames of `effect.output`; `moves` maps a block
    index to a callable run on the effect before that block is pulled."""
    channels = effect.channel_count
    out = array("h")
    block = 0
    done = False
    while len(out) < frames * channels:
        if moves and block in moves:
            moves[block](effect)
        if done:
            out.extend(array("h", bytes(2 * BLOCK * channels)))
        else:
            result, data = audiocore.get_buffer(effect.output)
            out.extend(array("h", bytes(data)))
            done = result == GET_BUFFER_DONE
        block += 1
    return out[:frames * channels]


def render(cls, values, rate, channels=2, frames=None, moves=None,
           **options):
    if frames is None:
        frames = len(values) // channels
    e = cls(source(values, rate, channels), **options)
    try:
        return pull(e, frames, moves)
    finally:
        e.deinit()


# --------------------------------------------------------------------------
# Planted faults


class CopyFromMid(StereoWidener):
    """H1: the copy is built from the mid (`input_pan=+1`), not the right:
    the line is fed both channels, and folds them into its right."""

    def _build_graph(self):
        StereoWidener._build_graph(self)
        self._line.set(input_pan=1.0)

    def _wire(self):
        StereoWidener._wire(self)
        self._feed.voice[0].panning = 0.0


class BackwardsPan(StereoWidener):
    """H2: the lead voice's panning sign flipped, so it turns the left down
    where it should turn the right down."""

    def _levels(self):
        StereoWidener._levels(self)
        voice = self._mixer.voice[0]
        voice.panning = -voice.panning


class JumpDelay(StereoWidener):
    """H3: `delay_slew=0`, so a Delay move jumps the read head."""

    def _build_graph(self):
        StereoWidener._build_graph(self)
        self._line.set(delay_slew=0.0)


class LevelWidth(StereoWidener):
    """M1: Mid/Side Width done as a Mixer level, 1 - |w - 1| / 2, on the
    unwidened pair, instead of the MidSide matrix."""

    def _build_graph(self):
        StereoWidener._build_graph(self)
        self._flat = self._own(audiomixer.Mixer(
            voice_count=1, buffer_size=BLOCK * 2 * 4, channel_count=2,
            bits_per_sample=16, samples_signed=True,
            sample_rate=self._sample_rate), reset=False)
        self._flat_wired = False

    def _route(self):
        StereoWidener._route(self)
        if not self._mid_side():
            return
        width = self._width()
        self._ms.set(width=1.0)
        voice = self._flat.voice[0]
        voice.level = 1.0 - abs(width - 1.0) / 2.0
        if not self._flat_wired:
            _component.open_level_gates(self._flat, self._flat.voice,
                                        self._silence)
            voice.play(self._ms)
            self._flat_wired = True
        self._output = self._flat


class LateMatrix(StereoWidener):
    """M2: the Mid/Side matrix composed through a one-frame line, so the
    widened pair comes out a frame late, at every Width but the wire."""

    def _build_graph(self):
        StereoWidener._build_graph(self)
        self._late = self._own(audioecho.FeedbackDelay(
            sample_rate=self._sample_rate, channel_count=2, max_delay_ms=2.0,
            delay_frames=1, feedback=0.0, mix=2.0), reset=self._late_clear)
        self._late.play(self._ms)

    def _late_clear(self):
        self._late.clear()

    def _route(self):
        StereoWidener._route(self)
        if self._mid_side() and self._width() != 1.0:
            self._output = self._late


class FixedCopy(StereoWidener):
    """W: the old class's copy at a fixed level of 0.8 whatever the Width,
    with no route around the copy at Width 0."""

    def _levels(self):
        StereoWidener._levels(self)
        self._mixer.voice[1].level = 0.8

    def _route(self):
        if self._mid_side() or self._width() > 0.0:
            StereoWidener._route(self)
            return
        self._ms.set(width=1.0)
        if not self._wired:
            self._wire()
        else:
            self._levels()
            self._rejoin(keep=(self._ms,))
        self._output = self._tail


#: The kit's plant table: a plant for a Mid/Side trait is judged at patch 4,
#: the first Mid/Side patch.
KIT_PLANTS = {
    "H1": CopyFromMid,
    "H2": BackwardsPan,
    "H3": JumpDelay,
    "M1": (LevelWidth, 4),
    "M2": (LateMatrix, 4),
    "W": FixedCopy,
}


# --------------------------------------------------------------------------
# The measurements


def h1_read(cls, rate, seed, frames=4096, width=None, delay_ms=None,
            patch=None, delay_grid=None):
    """H1(b): (left frames differing, right frames differing from R(n - tau)
    and zero before tau, tau) on seeded full-scale noise."""
    values = lcg_noise(frames, 2, seed)
    options = {}
    if width is not None:
        options["width"] = width
    if delay_ms is not None:
        options["delay_ms"] = delay_ms
    if patch is not None:
        options["patch"] = patch
    moves = None
    if delay_grid is not None:
        moves = {0: lambda e: e.set_macro(DELAY_I, delay_grid)}
    e = cls(source(values, rate), **options)
    try:
        if delay_grid is not None:
            ms = law_step_ms(delay_grid)
        elif patch is not None:
            ms = law_step_ms(StereoWidener.PATCHES[patch][1][DELAY_I])
        else:
            ms = 14.0 if delay_ms is None else delay_ms
        tau = law_frames(ms, rate)
        out = pull(e, frames, moves)
    finally:
        e.deinit()
    left = right = 0
    for n in range(frames):
        if out[2 * n] != values[2 * n]:
            left += 1
        want = values[2 * (n - tau) + 1] if n >= tau else 0
        if out[2 * n + 1] != want:
            right += 1
    return left, right, tau


def fold_rms(cls, rate, hz, frames=8192, amp=8192, **options):
    """H1(b), the mono fold: RMS of L' + R' (integers) after tau frames,
    for a centred sine at `hz`."""
    values = sine(frames, hz, rate, amp)
    e = cls(source(values, rate), **options)
    try:
        tau = law_frames(options.get("delay_ms", 14.0), rate)
        out = pull(e, frames)
    finally:
        e.deinit()
    total = 0
    count = 0
    for n in range(tau + 1024, frames):
        s = out[2 * n] + out[2 * n + 1]
        total += s * s
        count += 1
    return math.sqrt(total / count)


def notch_hz(rate, tau, k):
    """The mono fold's k-th notch: fs / (2 tau) x (2k + 1)."""
    return rate / (2.0 * tau) * (2 * k + 1)


def h2_read(cls, rate, width, delay_ms, click=16384):
    """H2(b): (L'[100], R'[300], R'[300 + tau]) for a click of `click` in
    the left at frame 100 and in the right at frame 300."""
    frames = 300 + law_frames(delay_ms, rate) + 512
    values = array("h", bytes(4 * frames))
    values[200] = click
    values[601] = click
    tau = law_frames(delay_ms, rate)
    out = render(cls, values, rate, frames=frames, width=width,
                 delay_ms=delay_ms)
    return out[200], out[601], out[2 * (300 + tau) + 1]


def h2_errors(cls, rate, delay_ms, widths=(0.25, 0.5, 0.75, 1.0, 1.5, 2.0),
              click=16384):
    """H2(d): the largest error, in LSB, of the three reads against the law,
    over `widths`."""
    worst = 0.0
    for w in widths:
        got = h2_read(cls, rate, w, delay_ms, click)
        want = [click * g for g in haas_expect(w)]
        for g, x in zip(got, want):
            worst = max(worst, abs(g - x))
    return worst


#: H3's half cycle of 1 kHz, in frames, and the window the peak sits in.
H3_HALF = {48000: 24, 22050: 11}
H3_WINDOW = {48000: 4, 22050: 2}


def h3_read(cls, rate, seed, up):
    """H3(b): (ratio of the largest step over the move to the largest
    steady step before it, frames differing from R(n - tau') after
    B + 1024). Patch 0, a 1 kHz sine at -6 dBFS; the Delay move lands at a
    block boundary B, with a peak of the copy within the window of B."""
    state = (seed * 2654435761 + 7) & 0x7FFFFFFF
    state = (state * 1103515245 + 12345) & 0x7FFFFFFF
    window = H3_WINDOW[rate]
    offset = (state >> 8) % (2 * window + 1) - window
    state = (state * 1103515245 + 12345) & 0x7FFFFFFF
    tau = law_frames(14.0, rate)
    first = (tau + 1024) // BLOCK + 1
    block = first + (state >> 8) % 8
    b = block * BLOCK
    quarter = rate / 4000.0
    # The copy at frame b + offset is the source at b + offset - tau: put a
    # peak of the sine there.
    start = b + offset - tau - quarter
    frames = b + 4096
    values = sine(frames, 1000.0, rate, 16384, start=start)
    new_tau = tau + (H3_HALF[rate] if up else -H3_HALF[rate])
    target = new_tau * 1000.0 / rate
    moves = {block: lambda e: e.set_macro(DELAY_I, delay_midi(target))}
    out = render(cls, values, rate, frames=frames, moves=moves, patch=0)
    steady = 0
    for n in range(b - 512, b):
        steady = max(steady, abs(out[2 * n + 1] - out[2 * n - 1]))
    moving = 0
    for n in range(b, b + 1024):
        moving = max(moving, abs(out[2 * n + 1] - out[2 * n - 1]))
    late = 0
    for n in range(b + 1024, frames):
        if out[2 * n + 1] != values[2 * (n - new_tau) + 1]:
            late += 1
    ratio = float("inf") if steady == 0 else moving / steady
    return ratio, late


def side_target(width):
    """M1(d): the side's gain, the node's Q14 width."""
    return rint(width * 16384) / 16384.0


def m1_read(cls, rate, seed, width, frames=4096, patch=None):
    """M1(b): (largest |(L' + R') - (L + R)|, largest |(L' - R') - g (L - R)|)
    on seeded independent noise peaking at -6.02 dBFS. Built at `patch`
    (or in Mid/Side), with Width set before the first pull."""
    values = lcg_noise(frames, 2, seed, peak=16384)
    if patch is None:
        e = cls(source(values, rate), width=width, character="mid_side")
    else:
        e = cls(source(values, rate), patch=patch)
        e.set_macro(WIDTH_I, width_midi(width))
    try:
        out = pull(e, frames)
    finally:
        e.deinit()
    g = side_target(width)
    worst_sum = 0
    worst_side = 0.0
    for n in range(frames):
        l, r = values[2 * n], values[2 * n + 1]
        lo, ro = out[2 * n], out[2 * n + 1]
        worst_sum = max(worst_sum, abs((lo + ro) - (l + r)))
        worst_side = max(worst_side, abs((lo - ro) - g * (l - r)))
    return worst_sum, worst_side


M1_WIDTHS = (0.0, 0.25, 0.5, 1.0, 1.5, 2.0)


def m1_random_width(seed):
    state = (seed * 2654435761 + 3) & 0x7FFFFFFF
    state = (state * 1103515245 + 12345) & 0x7FFFFFFF
    return ((state >> 8) % 2001) / 1000.0


def m2_read(cls, rate, width, click=8192, at=100):
    """M2(b): (L', R') at a hard-left click of `click`."""
    frames = at + 512
    values = array("h", bytes(4 * frames))
    values[2 * at] = click
    out = render(cls, values, rate, frames=frames, width=width,
                 character="mid_side")
    return out[2 * at], out[2 * at + 1]


M2_WIDTHS = (0.0, 0.5, 1.0, 1.5, 2.0)


def m2_errors(cls, rate, click=8192):
    """M2(d): (largest error against (1 +- w) / 2 x click, the R' read at
    1.5 and 2)."""
    worst = 0.0
    inverted = []
    for w in M2_WIDTHS:
        lo, ro = m2_read(cls, rate, w, click)
        worst = max(worst, abs(lo - (1.0 + w) / 2.0 * click),
                    abs(ro - (1.0 - w) / 2.0 * click))
        if w > 1.0:
            inverted.append(ro)
    return worst, inverted


def w_differing(cls, rate, seed, channels, frames=4096, **options):
    """W(b): samples differing from the input, on seeded full-scale noise."""
    values = lcg_noise(frames, channels, seed)
    out = render(cls, values, rate, channels, frames=frames, **options)
    return sum(1 for i in range(len(values)) if out[i] != values[i])


def w_mono_cells():
    """W(c), mono: every patch, both characters, Width 0 and 2, Delay 1 and
    40 ms."""
    cells = []
    for patch in sorted(StereoWidener.PATCHES):
        cells.append({"patch": patch})
    for character in ("haas", "mid_side"):
        for width in (0.0, 2.0):
            for delay in (1.0, 40.0):
                cells.append({"character": character, "width": width,
                              "delay_ms": delay})
    return cells


SEEDS = tuple(range(1, 9))

#: `audiocore.GET_BUFFER_DONE`, which a native audiocore does not export.
GET_BUFFER_DONE = getattr(audiocore, "GET_BUFFER_DONE", 0)


# --------------------------------------------------------------------------
# The tests


def _same_after(a, b):
    return sum(1 for i in range(len(a)) if a[i] != b[i])


class TheAdoption(TestCase):
    def test_adopted_is_what_the_package_serves(self):
        """Adopted on 2026-10-13, so `create()` serves this one. Serve another class under the name and this goes red."""
        import audiocore
        import audioeffects
        from array import array
        self.assertIs(audioeffects.StereoWidener, StereoWidener)
        served = audioeffects.create(
            "StereoWidener",
            audiocore.RawSample(array("h", [0, 0] * 64), sample_rate=48000,
                                channel_count=2),
            48000)
        self.assertIsInstance(served, StereoWidener)
        served.deinit()


class TheSurface(TestCase):
    def test_macros_patches_tier_latency(self):
        self.assertEqual(StereoWidener.MACRO_LABELS,
                         ("Width", "Delay", "Character"))
        self.assertEqual(StereoWidener.MACRO_MODES,
                         {0: "BIPOLAR", 1: "UNIPOLAR", 2: "TOGGLE"})
        self.assertEqual(StereoWidener.TIER, _component.AUDIODSP)
        e = StereoWidener(source(array("h", bytes(16)), 48000))
        try:
            self.assertEqual(e.latency_samples, 0)
            self.assertEqual(e.capabilities, ())
        finally:
            e.deinit()

    def test_patches_are_the_card_settings_on_the_grid(self):
        table = {0: (1.0, 14.0, 0), 1: (1.0, 6.0, 0), 2: (1.0, 25.0, 0),
                 3: (1.5, 14.0, 0), 4: (1.5, 14.0, 1), 5: (0.5, 14.0, 1),
                 6: (0.0, 14.0, 1)}
        spans = StereoWidener._MACRO_RANGES
        for patch, (w, ms, ch) in table.items():
            want = (_component.macro_of(spans[0], w, "BIPOLAR"),
                    _component.macro_of(spans[1], ms),
                    127 * ch)
            self.assertEqual(StereoWidener.PATCHES[patch][1], want, patch)

    def test_a_fresh_instance_reads_patch_0(self):
        e = StereoWidener(source(array("h", bytes(16)), 48000))
        try:
            fresh = [e.get_macro(i) for i in range(3)]
            self.assertEqual(fresh, [float(v) for v in
                                     StereoWidener.PATCHES[0][1]])
        finally:
            e.deinit()

    def test_the_constructor_delay_plays_exactly(self):
        # 14.0 ms is 672 frames at 48 kHz; its grid step, 14.06 ms, is 675.
        for rate in (48000, 44100, 22050):
            for patch in (None, 0):
                left, right, tau = h1_read(StereoWidener, rate, 1, 2048,
                                           patch=patch)
                self.assertEqual((left, right), (0, 0), (rate, patch))
                self.assertEqual(tau, law_frames(14.0, rate))

    def test_patches_play_their_delay_whatever_the_constructor_said(self):
        for rate in (48000, 44100, 22050):
            for ctor in (14.0, 14.03, 13.95, 20.0, 6.02, 25.0):
                e = StereoWidener(source(array("h", bytes(16)), rate),
                                  delay_ms=ctor)
                try:
                    self.assertEqual(e._frames, law_frames(ctor, rate))
                    e.set_macro(DELAY_I, e.get_macro(DELAY_I))
                    self.assertEqual(e._frames, law_frames(ctor, rate))
                    for patch, (_, values) in StereoWidener.PATCHES.items():
                        e.program_change(patch)
                        want = law_frames(law_step_ms(values[DELAY_I]), rate)
                        self.assertEqual(e._frames, want, (rate, ctor, patch))
                    e.reset()
                    self.assertEqual(e._frames, law_frames(14.0, rate))
                finally:
                    e.deinit()

    def test_the_constructor_delay_plays_until_delay_moves(self):
        e = StereoWidener(source(array("h", bytes(16)), 48000),
                          delay_ms=13.95)
        try:
            self.assertEqual(e.get_macro(DELAY_I), 91.0)
            self.assertEqual(e.macro(DELAY_I), 13.95)
            self.assertEqual(e._frames, 670)
            e.set_macro(DELAY_I, 90)
            e.set_macro(DELAY_I, 91)
            self.assertEqual(e.macro(DELAY_I), 14.0)
            self.assertEqual(e._frames, 672)
            e.set_macro(DELAY_I, 92)
            self.assertAlmostEqual(e.macro(DELAY_I), law_delay_ms(92))
        finally:
            e.deinit()

    def test_delay_does_nothing_in_mid_side(self):
        values = lcg_noise(2048, 2, 5, peak=16384)
        base = render(StereoWidener, values, 48000, width=1.5,
                      character="mid_side")
        for midi in (0, 40, 127):
            moved = render(StereoWidener, values, 48000, width=1.5,
                           character="mid_side",
                           moves={0: lambda e: e.set_macro(DELAY_I, midi)})
            self.assertEqual(_same_after(base, moved), 0, midi)

    def test_bad_character_raises(self):
        with self.assertRaises(ValueError):
            StereoWidener(source(array("h", bytes(16)), 48000),
                          character="wide")

    def test_tail_samples(self):
        values = array("h", bytes(16))
        e = StereoWidener(source(values, 48000))
        try:
            self.assertEqual(e.tail_samples, 673)
            e.set_macro(DELAY_I, 0)                  # falling: keeps 672
            self.assertEqual(e.tail_samples, 673)
            e.set_macro(DELAY_I, 127)                # 40 ms, 1920 frames
            self.assertEqual(e.tail_samples, 1921)
            e.set_macro(WIDTH_I, 0)
            self.assertEqual(e.tail_samples, 0)
            e.set_macro(WIDTH_I, 96)
            e.set_macro(CHARACTER_I, 127)
            self.assertEqual(e.tail_samples, 0)
            e.reset()
            self.assertEqual(e.tail_samples, 673)
        finally:
            e.deinit()
        mono = StereoWidener(source(array("h", bytes(8)), 48000, 1))
        try:
            self.assertEqual(mono.tail_samples, 0)
        finally:
            mono.deinit()

    def test_the_output_is_silent_after_the_tail(self):
        for rate in RATES:
            for patch in sorted(StereoWidener.PATCHES):
                # Noise, then silence: a RawSample asked again after its
                # end plays again, so the silence is part of the material.
                frames = 2048 + 4096
                values = lcg_noise(frames, 2, 3)
                for i in range(2 * 2048, 2 * frames):
                    values[i] = 0
                e = StereoWidener(source(values, rate), patch=patch)
                try:
                    out = pull(e, frames)
                    bound = 2048 + e.tail_samples + e.latency_samples
                finally:
                    e.deinit()
                last = max([n for n in range(frames)
                            if out[2 * n] or out[2 * n + 1]] or [0])
                self.assertLess(last, bound, (rate, patch))

    def test_reset_empties_the_line_and_returns_to_patch_0(self):
        rate = 48000
        values = lcg_noise(4096, 2, 9)
        e = StereoWidener(source(values, rate), patch=2)
        try:
            pull(e, 1024)
            e.reset()
            self.assertEqual(e.patch_index, 0)
            self.assertEqual([e.get_macro(i) for i in range(3)],
                             [float(v) for v in StereoWidener.PATCHES[0][1]])
            out = pull(e, 1024)
        finally:
            e.deinit()
        tau = law_frames(14.0, rate)
        # The right comes back out of silence tau frames later, then plays
        # the source's own right channel tau late.
        for n in range(tau):
            self.assertEqual(out[2 * n + 1], 0, n)
        for n in range(tau, 1024):
            self.assertEqual(out[2 * n + 1],
                             values[2 * (1024 + n - tau) + 1], n)

    def test_without_get_buffer_plays_what_it_plays_with_it(self):
        # Both channels, byte for byte, from the first frame.
        for rate in (48000, 16000, 8000):
            for what, build, moves in GET_BUFFER_CASES:
                with self.subTest(rate=rate, what=what):
                    _, plain = without_get_buffer(build, moves, rate=rate,
                                                  hide=False)
                    _, hidden = without_get_buffer(build, moves, rate=rate)
                    self.assertEqual(differing_frames(plain, hidden),
                                     [(0, [], [])] * 2)

    def test_a_refused_program_change_keeps_every_macro(self):
        values = array("h", bytes(4 * 512))
        refused = (dict(index=1, sample_position=-5), dict(index=0.0),
                   dict(index=1.0), dict(index=True), dict(index=-1))
        for call in refused:
            e = StereoWidener(source(values, 48000), delay_ms=20.0)
            try:
                before = [e.macro(i) for i in range(3)]
                frames = e._frames
                with self.assertRaises(ValueError):
                    e.program_change(**call)
                self.assertEqual([e.macro(i) for i in range(3)], before,
                                 call)
                self.assertEqual(e.macro(1), 20.0, call)
                self.assertEqual(e._frames, frames, call)
                e.set_macro(0, 63)
                self.assertEqual(e.macro(1), 20.0, call)
                self.assertEqual(e._frames, frames, call)
            finally:
                e.deinit()

    def test_the_tempo_is_never_read(self):
        reads = []

        def transport():
            reads.append(1)
            return (True, 0.0, 120.0, 4, 4)

        e = StereoWidener.create(source(array("h", bytes(16)), 48000),
                                 48000, transport=transport)
        try:
            for i in range(3):
                for v in (0, 64, 127):
                    e.set_macro(i, v)
                    e.transport_changed()
            for patch in StereoWidener.PATCHES:
                e.program_change(patch)
            e.reset()
            self.assertEqual(e.capabilities, ())
        finally:
            e.deinit()
        self.assertEqual(reads, [])

    def test_no_latency_in_either_character(self):
        for character in ("haas", "mid_side"):
            values = array("h", bytes(4 * 512))
            values[200] = 12000
            out = render(StereoWidener, values, 48000, character=character)
            self.assertEqual(out[200], 12000, character)
            self.assertEqual(out[198], 0, character)
            e = StereoWidener(source(values, 48000), character=character)
            try:
                self.assertEqual(e.latency_samples, 0)
            finally:
                e.deinit()


def without_get_buffer(build, moves, frames=4096, seed=3, rate=48000,
                       hide=True):
    """Render with `audiocore.get_buffer` hidden from the class, as on a
    CircuitPython board build, while it builds and while it moves; with
    `hide` false, the same render with it in place."""
    import types
    from audioeffects import stereowidener as module
    real = module.audiocore
    fake = types.ModuleType("audiocore")
    for name in dir(real):
        if name != "get_buffer" or not hide:
            setattr(fake, name, getattr(real, name))

    def hidden(action):
        def run(e):
            module.audiocore = _component.audiocore = fake
            try:
                action(e)
            finally:
                module.audiocore = _component.audiocore = real
        return run

    values = lcg_noise(frames, 2, seed)
    module.audiocore = _component.audiocore = fake
    try:
        e = build(source(values, rate))
    finally:
        module.audiocore = _component.audiocore = real
    try:
        out = pull(e, frames, dict((k, hidden(f)) for k, f in moves.items()))
    finally:
        e.deinit()
    return values, out


def differing_frames(a, b):
    """For each channel, (how many frames differ, the first, the last)."""
    found = []
    for channel in (0, 1):
        frames = [n for n in range(len(a) // 2)
                  if a[2 * n + channel] != b[2 * n + channel]]
        found.append((len(frames), frames[:1], frames[-1:]))
    return found


#: Whatever the class is asked, with `get_buffer` hidden or not: (what,
#: build, moves). Each way out of Haas before its first block, each reset
#: a voice could meet holding a block it primed, and a constructor Delay
#: that patch 0 replaces.
GET_BUFFER_CASES = (
    ("reset before the first pull", StereoWidener,
     {0: lambda e: e.reset()}),
    ("reset twice before the first pull", StereoWidener,
     {0: lambda e: (e.reset(), e.reset())}),
    ("built at 1 ms, reset before the first pull",
     lambda src: StereoWidener(src, delay_ms=1.0),
     {0: lambda e: e.reset()}),
    ("leave Haas before its first block, come back", StereoWidener,
     {0: lambda e: e.program_change(4), 4: lambda e: e.program_change(0)}),
    ("leave Haas before its first block, reset", StereoWidener,
     {0: lambda e: e.program_change(4), 6: lambda e: e.reset()}),
    ("leave Haas before its first block, reset twice", StereoWidener,
     {0: lambda e: e.program_change(4),
      6: lambda e: (e.reset(), e.reset())}),
    ("leave Haas before its first block, program_change(0) and reset",
     StereoWidener,
     {0: lambda e: e.program_change(4),
      6: lambda e: (e.program_change(0), e.reset())}),
    ("leave Haas after playing, program_change(0) and reset", StereoWidener,
     {2: lambda e: e.program_change(4),
      6: lambda e: (e.program_change(0), e.reset())}),
    ("Width 0 before the first block, reset", StereoWidener,
     {0: lambda e: e.set_macro(0, 0), 6: lambda e: e.reset()}),
    ("Character before the first block, reset", StereoWidener,
     {0: lambda e: e.set_macro(2, 127), 6: lambda e: e.reset()}),
    ("built at Mid/Side, then Haas",
     lambda src: StereoWidener(src, patch=4),
     {4: lambda e: e.program_change(0)}),
    ("leave Haas after playing, come back", StereoWidener,
     {2: lambda e: e.program_change(4), 6: lambda e: e.program_change(0)}),
)


class H1TheCopy(TestCase):
    def test_the_copy_is_the_right_exactly_delay_late(self):
        cells = []
        for rate in RATES:
            for patch in (0, 1, 2):
                cells.append(dict(rate=rate, patch=patch))
            for ms in (1.0, 5.0, 14.0, 30.0, 40.0):
                cells.append(dict(rate=rate, delay_ms=ms))
        for seed in SEEDS:
            for cell in cells:
                left, right, tau = h1_read(StereoWidener, seed=seed,
                                           frames=2048 + 2048, **cell)
                self.assertEqual((left, right), (0, 0), (seed, cell, tau))

    def test_random_grid_delays(self):
        for seed in SEEDS:
            midi = (seed * 37 + 11) % 128
            for rate in RATES:
                left, right, tau = h1_read(StereoWidener, rate, seed,
                                           frames=4096, delay_grid=midi)
                self.assertEqual((left, right), (0, 0), (seed, rate, midi))

    def test_the_right_half_above_width_1(self):
        for seed in SEEDS:
            for rate in RATES:
                for width in (1.5, 2.0):
                    _, right, tau = h1_read(StereoWidener, rate, seed,
                                            width=width)
                    self.assertEqual(right, 0, (seed, rate, width))

    def test_the_mono_fold_notches(self):
        for rate in RATES:
            tau = law_frames(14.0, rate)
            for k in range(4):
                self.assertLessEqual(
                    fold_rms(StereoWidener, rate, notch_hz(rate, tau, k)),
                    1.0, (rate, k))
            peak = fold_rms(StereoWidener, rate, rate / tau)
            self.assertGreater(peak, 11000.0, rate)

    def test_the_default_notches_are_where_the_text_says(self):
        tau = law_frames(14.0, 48000)
        self.assertEqual([round(notch_hz(48000, tau, k), 1)
                          for k in range(3)], [35.7, 107.1, 178.6])

    def test_copy_from_mid_is_red(self):
        _, right, _ = h1_read(CopyFromMid, 48000, 1)
        self.assertGreater(right, 1000)
        left, _, _ = h1_read(CopyFromMid, 48000, 1)
        self.assertEqual(left, 0)
        tau = law_frames(14.0, 48000)
        self.assertLessEqual(
            fold_rms(CopyFromMid, 48000, notch_hz(48000, tau, 0)), 1.0)


class H2TheWidthLaw(TestCase):
    def test_width_moves_the_right_to_its_copy(self):
        for rate in RATES:
            for ms in (1.0, 14.0):
                self.assertLessEqual(h2_errors(StereoWidener, rate, ms), 1.0,
                                     (rate, ms))

    def test_six_db_down_at_width_2(self):
        left, own, copy = h2_read(StereoWidener, 48000, 2.0, 14.0)
        self.assertEqual((left, own, copy), (8192, 0, 16384))

    def test_backwards_pan_is_red(self):
        for w in (0.25, 0.5, 0.75, 1.0, 1.5, 2.0):
            got = h2_read(BackwardsPan, 48000, w, 14.0)
            want = [16384 * g for g in haas_expect(w)]
            self.assertGreater(max(abs(g - x) for g, x in zip(got, want)),
                               1000.0, w)

    def test_the_comb_is_deepest_at_half_width(self):
        rate = 48000
        tau = law_frames(14.0, rate)
        hz = notch_hz(rate, tau, 0)
        rms = {}
        for w in (0.25, 0.5, 0.75):
            values = sine(8192, hz, rate, 8192)
            out = render(StereoWidener, values, rate, width=w)
            total = sum(out[2 * n + 1] ** 2 for n in range(tau + 1024, 8192))
            rms[w] = math.sqrt(total / (8192 - tau - 1024))
        self.assertLessEqual(rms[0.5], 1.0)
        self.assertGreater(rms[0.25], 2000.0)
        self.assertGreater(rms[0.75], 2000.0)


class H3TheGlide(TestCase):
    def test_a_delay_move_glides(self):
        for rate in RATES:
            for up in (True, False):
                for seed in SEEDS:
                    ratio, late = h3_read(StereoWidener, rate, seed, up)
                    self.assertLessEqual(ratio, 1.25, (rate, up, seed))
                    self.assertEqual(late, 0, (rate, up, seed))

    def test_jump_delay_is_red(self):
        for rate in RATES:
            for up in (True, False):
                ratio, _ = h3_read(JumpDelay, rate, 1, up)
                self.assertGreater(ratio, 1.25, (rate, up))


class M1TheMonoSum(TestCase):
    def test_the_sum_holds_and_the_side_follows(self):
        for rate in RATES:
            for seed in SEEDS:
                widths = M1_WIDTHS + (m1_random_width(seed),)
                for w in widths:
                    s, side = m1_read(StereoWidener, rate, seed, w)
                    self.assertLessEqual(s, 1, (rate, seed, w))
                    self.assertLessEqual(side, 1.0, (rate, seed, w))

    def test_at_the_mid_side_patches(self):
        for rate in RATES:
            for seed in SEEDS:
                widths = M1_WIDTHS + (m1_random_width(seed),)
                for patch in (4, 5, 6):
                    for w in widths:
                        s, side = m1_read(StereoWidener, rate, seed, w,
                                          frames=2048, patch=patch)
                        self.assertLessEqual(s, 1, (rate, seed, patch, w))
                        self.assertLessEqual(side, 1.0,
                                             (rate, seed, patch, w))

    def test_a_centred_part_is_unchanged(self):
        values = lcg_noise(2048, 1, 4)
        pair = array("h", bytes(4 * 2048))
        for n in range(2048):
            pair[2 * n] = pair[2 * n + 1] = values[n]
        for w in M1_WIDTHS:
            out = render(StereoWidener, pair, 48000, width=w,
                         character="mid_side")
            self.assertEqual(_same_after(out, pair), 0, w)

    def test_below_half_scale_never_clips(self):
        # Half of full scale is 16384; below it is 16383 and down, which
        # INPUT_CEILING_DBFS (-6.03 dBFS, 16366) sits under.
        peak = 16383
        self.assertLessEqual(
            rint(32767 * 10 ** (StereoWidener.INPUT_CEILING_DBFS / 20.0)),
            peak)
        for character in ("haas", "mid_side"):
            for w in (0.0, 0.5, 1.0, 1.5, 2.0):
                for shape in ("anti", "left", "noise"):
                    if shape == "noise":
                        values = lcg_noise(2048, 2, 6, peak=peak)
                    else:
                        values = array("h", bytes(4 * 2048))
                        for n in range(2048):
                            v = peak if (n // 37) % 2 else -peak
                            values[2 * n] = v
                            values[2 * n + 1] = -v if shape == "anti" else 0
                    out = render(StereoWidener, values, 48000, width=w,
                                 character=character)
                    self.assertLess(max(abs(x) for x in out), 32767,
                                    (character, w, shape))
        # At half scale itself the bound is met: anti-phase 16384 at Width
        # 2 doubles to 32768, one past the rail.
        values = array("h", bytes(4 * 512))
        for n in range(512):
            v = 16384 if (n // 37) % 2 else -16384
            values[2 * n] = v
            values[2 * n + 1] = -v
        out = render(StereoWidener, values, 48000, width=2.0,
                     character="mid_side")
        self.assertIn(32767, out)

    def test_level_width_is_red(self):
        for w in M1_WIDTHS:
            s, side = m1_read(LevelWidth, 48000, 1, w)
            if w == 1.0:
                self.assertLessEqual(max(s, side), 1.0)
            else:
                self.assertGreater(max(s, side), 1.0, w)


class M2TheMatrix(TestCase):
    def test_the_textbook_matrix(self):
        for rate in RATES:
            worst, inverted = m2_errors(StereoWidener, rate)
            self.assertLessEqual(worst, 1.0, rate)
            self.assertTrue(all(r < 0 for r in inverted), inverted)

    def test_late_matrix_is_red(self):
        for w in M2_WIDTHS:
            lo, ro = m2_read(LateMatrix, 48000, w)
            err = max(abs(lo - (1.0 + w) / 2.0 * 8192),
                      abs(ro - (1.0 - w) / 2.0 * 8192))
            if w == 1.0:
                self.assertLessEqual(err, 1.0)
            else:
                self.assertGreater(err, 1.0, w)


class WTheWire(TestCase):
    def test_a_mono_source_is_a_wire(self):
        for rate in RATES:
            for seed in SEEDS:
                for cell in w_mono_cells():
                    self.assertEqual(
                        w_differing(StereoWidener, rate, seed, 1, 1024,
                                    **cell), 0, (rate, seed, cell))

    def test_the_neutral_widths_are_wires(self):
        for rate in RATES:
            for seed in SEEDS:
                self.assertEqual(w_differing(StereoWidener, rate, seed, 2,
                                             width=0.0), 0, (rate, seed))
                self.assertEqual(w_differing(StereoWidener, rate, seed, 2,
                                             width=1.0,
                                             character="mid_side"),
                                 0, (rate, seed))

    def test_fixed_copy_is_red(self):
        self.assertGreater(w_differing(FixedCopy, 48000, 1, 2, width=0.0),
                           1000)


#: Every claim sentence of the class docstring and the test that holds it.
CLAIMS = (
    ("Delay is how late the Haas copy is, and only Haas uses it.",
     ("test_delay_does_nothing_in_mid_side",)),
    ("At Width 1 the left channel passes untouched and the right channel is "
     "your right channel, exactly Delay late.",
     ("test_the_copy_is_the_right_exactly_delay_late",
      "test_random_grid_delays", "test_copy_from_mid_is_red")),
    ("Between Width 0 and 1 the right channel crossfades from itself to its "
     "late copy, which colours it most at 0.5.",
     ("test_width_moves_the_right_to_its_copy",
      "test_the_comb_is_deepest_at_half_width", "test_backwards_pan_is_red")),
    ("Width 0 is a wire.",
     ("test_the_neutral_widths_are_wires", "test_fixed_copy_is_red")),
    ("Above Width 1 the copy stays where it is and the left turns down, "
     "6 dB at Width 2, to pull back the image the left's early arrival "
     "leans its way.",
     ("test_width_moves_the_right_to_its_copy", "test_six_db_down_at_width_2",
      "test_the_right_half_above_width_1")),
    ("Turning Delay glides the copy to the new time instead of clicking, "
     "bending its pitch while it moves.",
     ("test_a_delay_move_glides", "test_jump_delay_is_red")),
    ("Haas folds to mono as a comb filter: at Width 1 with the default "
     "14 ms, the mono sum has full-depth notches at 35.7, 107 and 179 Hz "
     "and on up.",
     ("test_the_mono_fold_notches",
      "test_the_default_notches_are_where_the_text_says")),
    ("Summed to mono, the output is the same at every Width, within one "
     "LSB.",
     ("test_the_sum_holds_and_the_side_follows", "test_at_the_mid_side_patches",
      "test_level_width_is_red")),
    ("Width 0 is mono, 1 is a wire and 2 doubles the sides.",
     ("test_the_textbook_matrix", "test_the_neutral_widths_are_wires",
      "test_the_sum_holds_and_the_side_follows")),
    ("Above Width 1, a part panned hard left shows up inverted on the right.",
     ("test_the_textbook_matrix", "test_late_matrix_is_red")),
    ("A part that is the same in both channels comes out unchanged.",
     "test_a_centred_part_is_unchanged"),
    ("Peaks below half of full scale never clip at any Width.",
     "test_below_half_scale_never_clips"),
    ("A one-channel source comes out exactly as it went in, whatever the "
     "controls say.",
     "test_a_mono_source_is_a_wire"),
    ("A click in the left comes out on the frame it went in: there is no "
     "latency.",
     ("test_no_latency_in_either_character",
      "test_width_moves_the_right_to_its_copy")),
    ("`tail_samples` is the copy's reach in Haas, and 0 in Mid/Side or at "
     "Width 0.",
     ("test_tail_samples", "test_the_output_is_silent_after_the_tail")),
    ("`reset()` empties the line and returns to patch 0.",
     "test_reset_empties_the_line_and_returns_to_patch_0"),
    ("The class never reads the host's tempo.",
     "test_the_tempo_is_never_read"),
    ("A control that jumps, Width or Character, makes the output step: move "
     "it in small steps from the host if you need it smooth.",
     "DECLARED:StereoWidener,E4-m0=,P5"),
)


# --------------------------------------------------------------------------
# The figures on whichever interpreter runs this file


def figures(seeds=SEEDS):
    """Print each trait's numbers: the evidence pack's per-interpreter
    rows."""
    name = sys.implementation.name
    for rate in RATES:
        worst = [0, 0]
        cells = 0
        for seed in seeds:
            for ms in (1.0, 5.0, 14.0, 30.0, 40.0):
                left, right, _ = h1_read(StereoWidener, rate, seed,
                                         delay_ms=ms)
                worst[0] += left
                worst[1] += right
                cells += 1
        tau = law_frames(14.0, rate)
        notches = [fold_rms(StereoWidener, rate, notch_hz(rate, tau, k))
                   for k in range(4)]
        print("%s|H1|%d|cells %d|left differing %d|right differing %d|"
              "fold notch rms max %.3f|peak %.1f"
              % (name, rate, cells, worst[0], worst[1], max(notches),
                 fold_rms(StereoWidener, rate, rate / tau)))
        print("%s|H1-plant|%d|right differing %d" % (
            name, rate, h1_read(CopyFromMid, rate, 1)[1]))
        print("%s|H2|%d|worst err 1ms %.3f|14ms %.3f|plant %.1f" % (
            name, rate, h2_errors(StereoWidener, rate, 1.0),
            h2_errors(StereoWidener, rate, 14.0),
            h2_errors(BackwardsPan, rate, 14.0)))
        for up in (True, False):
            ratios = []
            lates = 0
            for seed in seeds:
                ratio, late = h3_read(StereoWidener, rate, seed, up)
                ratios.append(ratio)
                lates += late
            print("%s|H3|%d|%s|ratio %.3f-%.3f|late mismatches %d|plant "
                  "%.2f" % (name, rate, "up" if up else "down", min(ratios),
                            max(ratios), lates,
                            h3_read(JumpDelay, rate, 1, up)[0]))
        sums = 0
        sides = 0.0
        for seed in seeds:
            for w in M1_WIDTHS + (m1_random_width(seed),):
                s, side = m1_read(StereoWidener, rate, seed, w)
                sums = max(sums, s)
                sides = max(sides, side)
        plant = min(max(m1_read(LevelWidth, rate, 1, w)) for w in M1_WIDTHS
                    if w != 1.0)
        print("%s|M1|%d|sum worst %d|side worst %.4f|plant min %.1f"
              % (name, rate, sums, sides, plant))
        worst, inverted = m2_errors(StereoWidener, rate)
        print("%s|M2|%d|worst %.3f|R' at 1.5, 2: %r" % (name, rate, worst,
                                                          inverted))
        mono = 0
        for seed in seeds:
            for cell in w_mono_cells():
                mono += w_differing(StereoWidener, rate, seed, 1, 1024,
                                    **cell)
        stereo = 0
        for seed in seeds:
            stereo += w_differing(StereoWidener, rate, seed, 2, width=0.0)
            stereo += w_differing(StereoWidener, rate, seed, 2, width=1.0,
                                  character="mid_side")
        print("%s|W|%d|mono differing %d|stereo differing %d|plant %d"
              % (name, rate, mono, stereo,
                 w_differing(FixedCopy, rate, 1, 2, width=0.0)))


if __name__ == "__main__":
    if unittest is not None and "--figures" not in sys.argv:
        unittest.main()
    else:
        # By name, not as __main__: a plant reads VENDOR from the module
        # that defines it, and natively __main__ is not one it can find.
        import test_cpython_effects_stereowidener as module
        module.figures()
