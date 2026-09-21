"""One equaliser band that only moves when there is something in it.

Dossier: `workspace docs/effects-internal/dossiers/DynamicEQ.md`. Evidence:
`workspace docs/effects-internal/evidence/DynamicEQ-evidence.md`.

**What it is, in a musician's terms.** A bell you dial in the ordinary way -
frequency, width - which does nothing at all until the sound *in that band*
crosses the threshold, and then cuts by however far the compressor law says.
It is the tool for a singer who is fine until she pushes and then goes hard
at 3 kHz, for a bass that booms only on the low F, for a cymbal whose edge is
right except on the loud hits. A plain EQ cut fixes the loud moment and
hollows out everything else; this one leaves everything else exactly as it
was, because when the detector is idle **it is a wire and not an
approximation of one**.

**Two branches, and their sum is the input.** The band is split with an RBJ
notch and an RBJ band-pass at the same frequency and the same Q, whose
numerators `(1, -2cos w0, 1)` and `(alpha, 0, -alpha)` add up to their shared
denominator, so `H_notch + H_bandpass` is exactly 1 at every frequency. The
band-pass branch goes through the gain cell and both are summed back. Idle,
that sum measures **0.0000 dB from unity** at 100 Hz through 12 kHz - not
0.015 dB, which is what the same topology gives on the Q12 ported biquad, and
the difference is why this class is built on `audiobiquad`.

**Mix is also the Range control, and that is arithmetic rather than a
saving.** Writing `B` for the band-pass's response and `g` for the gain
cell's gain, the whole class is `1 + m*B*(g - 1)` at blend `m`. A blend
against the dry input and a "how far may this band ever move" limit on the
band branch are therefore the *same number*, and shipping both would be two
knobs for one thing. So `Mix` at `m` caps the deepest cut at
`-20*log10(1 - m)` dB: **6.0 dB at 0.5, 12.0 at 0.75, 20.0 at 0.9, and no
limit at 1**, which is where it ships. `Mix` 0 is a real bypass, and it is
byte-identical to the source rather than merely flat: there is **no mixer in
the path** at all there, because a mixer voice at level 1.0 is not unity -
upstream's Q15 level is `1.0 * 32768` and the kernel divides by 32767, so
the dry tap at unity came out one LSB high at every sample from 32736 up
(audiodsp#95, three of 16384 on a full-scale ramp). The mixer's voices take
their sources the first time Mix leaves 0, with their level gates opened on
one block of silence first.

**`expand=True` is a build, not a knob.** `audiodynamics.Dynamics` fixes its
mode at construction, and a class that carried both a compressor and an
expander would pay for both every block whichever one was selected - so the
direction S6 calls "compression/expansion" is a constructor argument.
`expand=False` (the default) cuts the band when the band goes **over** the
threshold; `expand=True` cuts it when the band falls **under**, which is a
per-band gate for hiss, rumble and room tone. Neither one boosts: a bell that
*lifts* when the band arrives needs a target gain that would fight the
threshold-and-ratio law this class is held to, and the palette route for it
(`makeup_db` against `depth_db`) is recorded in the dossier rather than
half-built here.

**Portability tier: audiodsp.** `audiobiquad` for a split whose two branches
sum to unity and whose tail reaches exact zero; `audiodynamics` for the gain
cell and its detector; `audioroute` for the fan-out. It will not import on a
stock CircuitPython board - the module loads, and construction raises.

**Latency: zero, at every setting, and nothing here can add any.** Both
branches are IIR - they rotate phase, they do not delay onset - and
`audiodynamics`' `lookahead_ms` is deliberately not exposed, because a
dynamic EQ that ducked before the note arrived would be a different
instrument. There is therefore **no latency-adding option to name in
milliseconds**: `latency_samples` is 0 for the life of the instance.

**Cost, and it went up.** Two biquads, one detector-and-gain-cell, a
three-tap splitter ring, a three-voice mixer, a block-sized guard and an
identity `MidSide`, on a graph that runs in 256-frame blocks throughout.
Measured on the desktop against the class this replaces, five interleaved
repeats of each: **1.46-1.56 ms per 256-frame stereo block against
1.10-1.15**, about **45 % more**. Three of those nodes are new - the guard,
the dry tap and the tail. Two of them still earn it: `Mix` 0 is not a real
bypass without the dry tap, and CircuitPython renders silence without the
tail. The guard's reason has expired - it was there because a long source
vanished into the Splitter's ring, and audiodsp#87 removed that ring limit,
so at `977ef26` the graph renders the same bytes without it. It is a node
this class could drop, once a board is free to re-take the row. The single
256-frame block size keeps every
node doing the same work per pull; it is not a saving, and the first
measurement in this session said it was only because the machine was loaded.
Neither figure is a board figure.

**One thing measured here that the dossier had wrong.** With a tone sitting
on the band centre, the composite reads about **0.42 dB above** the gain
computer's law. The seed put that down to the notch branch passing a little
of the tone; the notch branch at `f0` measures **exactly zero** (RMS 0.00 of
a 10360 LSB source), and the real cause is the detector: a one-pole peak
follower with a 2 ms attack never quite reaches the peak of a 3 kHz sine, so
`env_db` reads about 0.6 dB low and the cell cuts that much less. It moves
with the attack time (0.23 dB short at 0.1 ms, 1.18 dB at 10 ms) and with
frequency (0.49 dB at 200 Hz, 1.23 dB at 8 kHz), which is what a lagging
follower does and what notch leakage would not.

**Two bounds, measured.** The composite law (T2, and T5 which is built on
it) holds inside 1 dB only at short attack: patch 3 "Low End Tamer" (20 ms)
reads **+1.439 dB** and the macro's 100 ms end reads **+4.269 dB** at ratio
20. The two-octave isolation bar (T4, 0.2 dB) and T6's out-of-band clause
hold at Q 2 and miss below it: patch 5 "Half Measure" at shipped Q 1.01
reads **0.271 dB**. Those traits stay disconfirmed at those settings; they
are not dropped.
"""

VENDOR = "PyDevices"

import math
from array import array

import audiocore
import audiofilters
import audiomixer

from . import _component

try:
    import audiobiquad
except ImportError:      # a stock CircuitPython board, or an old audiodsp
    audiobiquad = None
try:
    import audiodynamics
except ImportError:
    audiodynamics = None
try:
    import audioroute
except ImportError:
    audioroute = None


#: Frames the guard hands back in one call, and so the block size the whole
#: graph runs in. 256 is what `audiobiquad` and `audiodynamics` hand out
#: themselves, so nothing in the chain re-blocks anything else. It used to
#: have to be at or under the Splitter's 8192-frame ring as well; audiodsp#87
#: took that limit out, so the clause no longer binds.
_GUARD_FRAMES = 256

#: The highest fraction of the sample rate a corner may reach. Both branches
#: are RBJ sections and their `alpha` is `sin(w0) / (2Q)`, so a corner pushed
#: at Nyquist has `alpha -> 0`, a pole radius at 1 and a tail that never
#: arrives. `_component.NYQUIST_MARGIN` (0.98) is the contract's ceiling and
#: is far too close for a resonator; 0.4 is the dossier's own number and it
#: is a clamp, never a refusal (the rate-honesty invariant).
_MAX_CORNER = 0.4

#: Ring-down of one pole pair, in periods of `Q / f0`, from a full-scale DC
#: burst to the last non-zero sample. Measured on `audiobiquad.Biquad` at the
#: corners of both spans; the float state is flushed to exact zero below
#: 1e-20, so this is a real number and not an asymptote. The margin above
#: what was measured is there because `tail_samples` may be long and may
#: never be short.
_TAIL_PERIODS = 4.0


class DynamicEQ(_component.Component):
    """A bell that only appears when the band it sits on crosses a threshold.

    `audiodsp` tier: `audiobiquad` for the complementary split, `audiodynamics`
    for the gain cell, `audioroute` for the fan-out.
    """

    NAME = 'DynamicEQ'
    DISPLAY_NAME = 'Dynamic EQ'
    CATEGORIES = ('EQ',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audiobiquad", "audiodynamics", "audioroute")

    #: `()`, and the dossier's reason (D10): attack and release are absolute
    #: milliseconds and nothing on this class is measured in bars, so
    #: `self._transport()` is never read.
    CAPABILITIES = ()

    #: Zero at every setting. Both branches are IIR and no look-ahead is
    #: offered, so there is no option whose milliseconds need naming.
    LATENCY_SAMPLES = 0

    #: Overridden as a property below: the ring-down is the pole pair's, so
    #: it depends on the rate and on where Frequency and Width are.
    TAIL_SAMPLES = 0

    MACRO_LABELS = ("Frequency", "Width", "Threshold", "Ratio", "Attack",
                    "Release", "Mix", "Listen")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR",
                   3: "UNIPOLAR", 4: "UNIPOLAR", 5: "UNIPOLAR",
                   6: "UNIPOLAR", 7: "TOGGLE"}
    _MACRO_RANGES = (
        (30.0, 16000.0, "log"),     # Frequency, clamped to 0.4 * rate
        (0.5, 12.0, "log"),         # Width, as Q
        (-60.0, 0.0),               # Threshold, dBFS
        (1.0, 20.0, "log"),         # Ratio
        (0.1, 100.0, "log"),        # Attack, ms
        (5.0, 1000.0, "log"),       # Release, ms
        (0.0, 1.0),                 # Mix, which is also Range
        (0.0, 1.0),                 # Listen
    )
    #: Patch 0 is the constructor's defaults on the 0-127 grid;
    #: `tests/test_cpython_effects_dynamiceq.py` holds it to them span by
    #: span rather than to a hand-copied list.
    PATCHES = {
        0: ("Wide Band", (93, 55, 64, 59, 55, 66, 127, 0)),
        1: ("Boxiness Control", (52, 64, 76, 47, 85, 82, 127, 0)),
        2: ("Harshness Control", (94, 72, 68, 59, 42, 60, 127, 0)),
        3: ("Low End Tamer", (20, 35, 85, 59, 97, 94, 127, 0)),
        4: ("Sibilance", (110, 83, 64, 88, 13, 50, 127, 0)),
        5: ("Half Measure", (93, 28, 55, 76, 72, 88, 64, 0)),
    }

    # Macro indexes, so the routing below reads as itself.
    _FREQUENCY = 0
    _WIDTH = 1
    _THRESHOLD = 2
    _RATIO = 3
    _ATTACK = 4
    _RELEASE = 5
    _MIX = 6
    _LISTEN = 7

    # -- construction --------------------------------------------------

    def _build(self, frequency=3000.0, q=2.0, threshold_db=-30.0, ratio=4.0,
               attack_ms=2.0, release_ms=80.0, mix=1.0, listen=False,
               expand=False, patch=None):
        """Build the exactly complementary split the dossier's section 4 draws.

            source -> guard -> Splitter(taps=3)
                                 tap 0 --------------------------> dry   voice 0
                                 tap 1  Biquad NOTCH ------------> notch voice 1
                                 tap 2  Biquad BAND_PASS -> Dynamics -> voice 2
                                                                   Mixer -> out

        `expand` fixes the gain law and is not a macro: `audiodynamics`
        settles its mode at construction and an unused second detector would
        cost a full block's work every block. Nothing here adds latency at
        any setting, so there is no millisecond figure to name.
        """
        rate, channels = self._sample_rate, self._channel_count
        self._expand = bool(expand)
        self._corner_hz = 0.0

        # The guard, which no longer guards the head. A Splitter used to
        # write whatever its immediate source handed back in one call into an
        # 8192-frame ring and drag every cursor past the overflow, and
        # `audiocore.RawSample.get_buffer()` hands back its whole array in one
        # call - so an impulse inside a 40000-frame probe reached this class
        # as silence unless something blocked the source first. audiodsp#87
        # took the ring limit out: at `977ef26` the unguarded split passes
        # that impulse at full height, measured in
        # `test_the_block_ladder_no_longer_needs_the_guard`.
        #
        # What it still does is set the block size the whole graph runs in,
        # and it is the node the class was costed with, so it stays until a
        # board is available to re-take the row without it.
        # `audiofilters.Filter` with no filter is a copy, and it is the
        # cheapest node on the palette that hands out its own block size. Its
        # `reset_buffer` drops its pending bytes and does **not** reset its
        # source (`audiodsp/src/audiofilters/Filter.c:133-149`), which is what
        # keeps the borrowed source untouched by `reset()`.
        guard = audiofilters.Filter(
            filter=None, mix=1, buffer_size=_GUARD_FRAMES * channels * 2,
            sample_rate=rate, channel_count=channels,
            bits_per_sample=16, samples_signed=True)
        guard.play(self._source, loop=False)
        #: What the Splitter pulls from, and what Mix 0 hands back.
        self._head = guard

        split = audioroute.Splitter(guard, taps=3)
        taps = [split.tap(index) for index in range(3)]

        notch = audiobiquad.Biquad(
            mode=audiobiquad.NOTCH, frequency=1000.0, Q=q,
            sample_rate=rate, channel_count=channels)
        band = audiobiquad.Biquad(
            mode=audiobiquad.BAND_PASS, frequency=1000.0, Q=q,
            sample_rate=rate, channel_count=channels)
        notch.play(taps[1])
        band.play(taps[2])

        cell = audiodynamics.Dynamics(
            audiodynamics.DYN_EXPAND if self._expand
            else audiodynamics.DYN_COMPRESS,
            sample_rate=rate, channel_count=channels,
            threshold_db=threshold_db, ratio=ratio,
            attack_ms=attack_ms, release_ms=release_ms)
        # The detector reads what it processes: the band-pass branch itself.
        # That is the whole selectivity story - the reduction applied at any
        # frequency is the gain law evaluated at `L + |H_bp(f)|`, which is
        # why the audible bell is narrower than f0/Q (dossier T5).
        cell.play(band)

        mixer = audiomixer.Mixer(
            voice_count=3, sample_rate=rate, channel_count=channels,
            bits_per_sample=16, samples_signed=True, buffer_size=2048)

        # The class does **not** end in the Mixer, and that is not decoration.
        # On upstream CircuitPython `audiomixer.Mixer.reset_buffer` *stops*
        # every voice rather than rewinding it, permanently; audiodsp fixed
        # that in its own port and deliberately did not patch it into the
        # CircuitPython build (`upstream-diff.md`, "Resetting a Mixer
        # silenced it, permanently"). Anything upstream resets what it is
        # handed - a host, the next effect's `play()`, and
        # `tools/render_effect.py:717` before every render - so a class
        # ending in a Mixer renders **silence** there. Measured: every kit
        # render of this class on `cmods/bin/circuitpython-effects` came back
        # `sum 0 SILENT` until this node existed, on a class the smoke and a
        # hand-pumped probe both passed. `audioroute.MidSide` at width 1 is
        # the exact identity - `outL = (2L+1) >> 1` is `L` for every int16
        # (`audiodsp_midside.c`, and audiodsp's own section on it) - and its
        # `reset_buffer` clears its own cursor and nothing else.
        tail = audioroute.MidSide(width=1.0, sample_rate=rate,
                                  channel_count=channels)
        tail.play(mixer)

        self._tail = tail
        self._guard = guard
        self._split = split
        self._taps = taps
        self._notch = notch
        self._band = band
        self._cell = cell
        self._mixer = mixer

        # Registration order is reset order, reversed: `reset()` and
        # `deinit()` walk this list tail first. So the guard is owned last
        # and cleared first (its stale block goes before anything downstream
        # re-reads it), the mixer is owned first and cleared last (its
        # re-prime then pulls through nodes that are already silent), and the
        # filters and the cell sit between them. The identity tail is owned
        # before the mixer so that it is cleared after it, once the mixer's
        # re-prime has already run.
        self._own(tail)
        self._own(mixer, reset=self._reset_mixer)
        for tap in taps:
            # `audioroute.SplitterTap.reset_buffer` is deliberately nothing -
            # rewinding one branch would desynchronise the others - so this
            # registers them for `deinit()` and the reset is a no-op that is
            # still visible in the walk rather than an omission.
            self._own(tap)
        # `reset=False` and nothing else: a `Splitter`'s ring cannot be
        # rewound - its Python surface is `tap()`, and a tap's `reset_buffer`
        # is a documented no-op, "the cursors belong to the Splitter and the
        # other taps are still reading from them"
        # (`audiodsp/src/audioroute/SplitterTap.c`). It **can** be released:
        # `deinit()` landed in audiodsp#58, and it releases the taps with it.
        # This used to read `deinit=False`, which was honest while the palette
        # had nothing to call but left the Tier 1 row unmeasurable. Asking for
        # a release the node may not have is safe either way -
        # `_component.deinit()` looks the method up with `getattr` and skips
        # what is not there - so this is correct against the pinned audiodsp as
        # well as the current one.
        self._own(split, reset=False)
        self._own(cell)
        self._own(band)
        self._own(notch)
        self._own(guard)

        #: The silence the level gates open on. Two frames, because a
        #: one-frame mono sample is smaller than the packed word the native
        #: mixer consumes and `get_buffer` never returns on it (audiodsp#85).
        #: It holds no state, so it declines its own reset.
        self._silence = self._own(audiocore.RawSample(
            array("h", bytes(2 * 2 * channels)),
            sample_rate=rate, channel_count=channels), reset=False)
        self._tail = tail
        self._output = tail
        self._primed = False
        self._ready = False

        self._init_macros((frequency, q, threshold_db, ratio, attack_ms,
                           release_ms, mix, 1.0 if listen else 0.0), patch)

        # After the macros, and that ordering is a measurement rather than a
        # preference: `audiomixer.MixerVoice.play()` resets its new source and
        # pulls a chunk from it there and then, so a voice played before
        # `_init_macros` would hold 512 frames rendered through two biquads
        # still sitting at their construction frequency. That head is on
        # every render and no later macro move can reach it.
        self._play_voices()
        self._ready = True
        self._refresh_output()

    def _play_voices(self):
        """Hand every voice its source. Also the second half of `reset()`.

        The gates open first, on one block of silence. Since CircuitPython
        10.3.0 a fresh voice starts at level 0 and takes its level only when
        its signal reaches or crosses zero, so on material that offers none
        the head of the render was a hole: measured, 8 frames of silence at
        the top of a full-scale ramp at every Mix setting, and 256 at Mix 0.

        **At Mix 0 the voices are left on that silence.** `_refresh_output`
        hands the bypass back off `self._head`, and a voice playing tap 0
        would drag a block of the head through the Splitter on `play()`
        alone. Nothing behind this mixer is pulled while Mix is 0.
        """
        _component.open_level_gates(
            self._mixer,
            [self._mixer.voice[0], self._mixer.voice[1],
             self._mixer.voice[2]],
            self._silence)
        if self.macro(self._MIX) <= 0.0 \
                and self._macros[self._LISTEN] < 0.5:
            self._primed = False
            return
        self._mixer.play(self._taps[0], voice=0, loop=True)
        self._mixer.play(self._notch, voice=1, loop=True)
        self._mixer.play(self._cell, voice=2, loop=True)
        self._primed = True

    def _refresh_output(self):
        """Mix 0 is the class's input, and there is no mixer in the path.

        A mixer voice at level 1.0 is not unity: upstream's Q15 level is
        `1.0 * 32768` and the kernel divides by 32767, so the dry tap at
        unity came out one LSB high at every sample from 32736 up - three of
        16384 on a full-scale ramp, all in the right channel, and both on a
        mono mixer (audiodsp#95).

        What is handed back is `self._head`, not `self._source`, and the
        difference is one node wide: the guard is an `audiofilters.Filter`
        and `Filter.play()` resets its source and fetches a block from it on
        the spot, so by the end of construction the first 256 frames of the
        source are inside the guard. Handing back the source would start the
        bypass 256 frames in; the guard has those frames, and a `Filter`
        with no filter is a copy - measured bit-exact against a full-scale
        ramp. It is also the node the Splitter reads, so a Mix move off 0
        picks the graph up on the sample the bypass stopped on.

        Listen is not a bypass: it replaces the output with the detector's
        own band, which is the mixer's third voice.
        """
        if not self._ready:
            return
        if self.macro(self._MIX) <= 0.0 \
                and self._macros[self._LISTEN] < 0.5:
            self._output = self._head
            return
        if not self._primed:
            self._play_voices()
        self._output = self._tail

    def _reset_mixer(self):
        """Clear the Mixer, then hand its voices back their sources.

        `audiodsp`'s `audiomixer` rewinds a voice on reset; **upstream
        CircuitPython's stops it, permanently** (audiodsp's
        `docs/upstream-diff.md`, "Resetting a Mixer silenced it,
        permanently"), and a class that only called `reset_buffer` here would
        work on this port and render silence for ever after its first
        `reset()` on a stock board. Re-playing is what the fixed node does
        anyway: `play()` rewinds the source and takes a chunk. Because the
        Mixer is owned first and so walked last, that chunk comes through
        nodes this reset has already cleared.
        """
        audiocore.reset_buffer(self._mixer)
        self._play_voices()

    # -- the live surface ---------------------------------------------

    @property
    def expand(self):
        """Whether the band is cut when it goes *under* the threshold
        (`True`) rather than over it. Fixed at construction; see the class
        docstring for why it is not a macro."""
        self._check_live()
        return self._expand

    @property
    def frequency_hz(self):
        """The centre actually applied, after the rate clamp. It can sit
        below what `macro(0)` reports - that is the clamp doing its job at a
        lower sample rate."""
        self._check_live()
        return self._corner_hz

    @property
    def range_db(self):
        """The deepest the band can ever be moved, in dB, at this `Mix`.

        `-20*log10(1 - Mix)`, and `inf` at Mix 1. This is the Range control
        S6 names; it is not a separate macro because in an exactly
        complementary split a dry/wet blend and a band-range limit are the
        same arithmetic (dossier T6).
        """
        self._check_live()
        mix = self.macro(self._MIX)
        if mix >= 1.0:
            return float('inf')
        return -20.0 * math.log10(1.0 - mix)

    @property
    def tail_samples(self):
        """How long the split rings, in samples at this rate.

        The only memory in this class is the two biquads', and they share a
        denominator, so one pole pair sets it. A resonator rings for about
        `Q` periods of its centre; measured on `audiobiquad.Biquad` from a
        full-scale DC burst to the last non-zero sample, the constant is
        under 4 across both spans, and the float state is flushed to exact
        zero below 1e-20 so the tail really does arrive.

        The detector holds no audio: `audiodynamics` multiplies its input by
        a gain, so silence in is silence out whatever the release is doing,
        and the release therefore adds nothing here.
        """
        self._check_live()
        corner = self._corner_hz or 1.0
        return int(_TAIL_PERIODS * self.macro(self._WIDTH)
                   * self._sample_rate / corner) + 1

    def gain_reduction_db(self):
        """What the gain cell did to the last frame of the band, in dB.

        The cell's own number, before the Mix blend, so it is the detector's
        reading and not what reached the output. At blend `m` the output's
        move at the centre is `20*log10((1 - m) + m * 10**(cell/20))`.
        """
        self._check_live()
        return self._cell.gain_reduction_db()

    # -- macros --------------------------------------------------------

    def _apply_macro(self, index, position):
        value = _component.macro_value(self._MACRO_RANGES[index], position)
        if index in (self._FREQUENCY, self._WIDTH):
            # Both sections take the same two numbers from one place, so the
            # branches cannot drift out of complement: an f0 or a Q that
            # reached one and not the other would break T1 silently, which is
            # exactly the class's planted fault.
            self._corner_hz = self._corner(self.macro(self._FREQUENCY))
            width = self.macro(self._WIDTH)
            for section in (self._notch, self._band):
                section.frequency = self._corner_hz
                section.Q = width
        elif index == self._THRESHOLD:
            self._cell.set(threshold_db=value)
        elif index == self._RATIO:
            self._cell.set(ratio=value)
        elif index == self._ATTACK:
            self._cell.set(attack_ms=value)
        elif index == self._RELEASE:
            self._cell.set(release_ms=value)
        else:                       # Mix and Listen are both routing
            self._route()

    def _corner(self, frequency):
        """A centre frequency, clamped into the running rate's usable band.

        `self._hz()` is the contract's clamp and stops at 0.98 of Nyquist,
        which is far too close for a pole pair; this one stops at
        `_MAX_CORNER`. Both clamp and neither refuses, which is what
        rate-honesty asks for: a 16 kHz band on a 22.05 kHz graph becomes the
        highest band that rate has.
        """
        ceiling = self._sample_rate * _MAX_CORNER
        frequency = self._hz(frequency)
        return ceiling if frequency > ceiling else frequency

    def _route(self):
        """Push Mix and Listen into the mixer.

        At Mix 0 the dry tap is at unity and the two branches are at zero,
        which is a byte compare against the source rather than a claim about
        the split being flat. In Listen only the processed band is audible,
        so you can hear what the detector is working on.
        """
        mix = self.macro(self._MIX)
        if self._macros[self._LISTEN] >= 0.5:
            self._mixer.voice[0].level = 0.0
            self._mixer.voice[1].level = 0.0
            self._mixer.voice[2].level = 1.0
        else:
            self._mixer.voice[0].level = 1.0 - mix
            self._mixer.voice[1].level = mix
            self._mixer.voice[2].level = mix
        self._refresh_output()
