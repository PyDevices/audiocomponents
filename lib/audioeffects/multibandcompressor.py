"""Split-band compression: a crossover, one compressor per band, one sum.

Dossier: `workspace docs/effects-internal/dossiers/MultibandCompressor.md`. Evidence:
`workspace docs/effects-internal/evidence/MultibandCompressor-evidence.md`.

There is no unit behind this class. Split-band compression is a *topology* -
RaneNote 155 draws it as a general variation on the compressor (Fig. 7),
"divides the incoming signal into two or more frequency bands ... After
dynamics processing, the individual bands are re-combined into one signal" -
and the crossover it needs is a published alignment, Linkwitz-Riley, whose two
properties are "in-phase outputs (0 degrees between outputs) at all
frequencies" and "the outputs sum to unity at all frequencies" (RaneNote 160).

**The topology, at three bands.**

    source -> guard -> Splitter(taps=4)
                         tap 0  ------------------------------> dry  voice 0
                         tap 1  LP LP ---------------> Dynamics low  voice 1
                         tap 2  HP HP LP LP ---------> Dynamics mid  voice 2
                         tap 3  HP HP ---------------> Dynamics high voice 3
                                                              Mixer -> output

Every crossover is **LR4** - two cascaded Butterworth sections a side, Q =
0.7071 - which is why no band is polarity-inverted: RaneNote 160's rule is
that LR-2 and LR-6 need an inversion and LR-4 and LR-8 do not.

**Three things this class had to measure rather than reason about.**

* **The bands are `audiobiquad`, not `audiofilters`.** A `synthio.Biquad`
  cascade inside `audiofilters.Filter` keeps its state in Q12 sample units
  and rounds to nearest with no dither, so the recursion has fixed points:
  measured here, a 256-frame DC burst through a LOW_PASS pair holds **2 LSB
  for ever at 100 Hz and 8 LSB at 40 Hz**, while the same pair on
  `audiobiquad.Biquad` reaches exact zero at frame 1895 and 3987. That is
  audiodsp#23, and it is the Tier 1 invariant this family is held to first.
  The dossier's section 4 mapped the ported node; the palette has had the
  float one since Phase 1.

* **The sum is flat but it is not a wire.** A Linkwitz-Riley network
  "behaves like an all-pass": unity magnitude, rotating phase. So `Mix` at
  zero is a **real bypass** and not "the bands, summed, which ought to be
  the same thing". It is not the same thing, and the byte compare would say
  so. Nor is the dry tap at unity enough: a mixer voice at level 1.0 scales
  by 32768/32767 on every target (audiodsp#95), so `_refresh_output` hands
  back the borrowed source itself and puts no node of this class's in the
  path at all.

* **How close the two crossovers may get.** The three-way parallel split has
  a floor that is a function of the crossover *ratio*, not of the
  frequencies: measured on these nodes, the sum deviates by 0.19 dB at 8:1,
  0.99 dB at 4:1 and **7.96 dB at 2:1**. The upper crossover is therefore
  clamped to at least eight times the lower one. It is a clamp and never a
  refusal, in the shape the rate-honesty invariant asks for, and
  `crossover_high_hz` reports what was actually applied.

**Latency: zero, at every setting, and nothing here can add any.** The
crossover is IIR and the detectors do not look ahead. `audiodynamics` offers
a lookahead of up to 50 ms; this class does not expose it, because a
multiband's job is the balance between bands and the ceiling belongs to
`Limiter`, which is built on that lookahead and reports it.

**One thing the dossier asked for that this class does not deliver, and it
is arithmetic rather than a bug.** M3 asks that driving one band to 12 dB of
reduction move that band's whole passband by 12 dB within half a decibel.
**No band does it, and no crossover-plus-compressor can.** A band's own
skirt takes it below unity towards its corners, and a fixed threshold then
buys `(1 - 1/ratio)` of that shortfall less reduction there. Measured at
200/2000 Hz, ratio 4, soloed, each band read across **its own passband, out
to its own -6 dB corners**:

    band   window        per-tone reduction        mean      tilt
    low    30..141 Hz    -12.51 .. -10.69 dB      -11.91    1.82 dB
    mid    283..1414     -11.89 .. -10.58         -11.27    1.31 dB
    high   2828..16000   -12.01 .. -10.58         -11.64    1.42 dB

against a 0.5 dB bar on both the depth and the tilt. The arithmetic is exact
for the mid band: its window edges sit **1.75 dB** below its own peak, and
`(1 - 1/4) x 1.75 = 1.31`. At the -6 dB corner itself the band is 6 dB down
and the shortfall is 4.5 dB.

The low band carries a second effect on top of that one. Below about 50 Hz
the RMS detector's 10 ms window is shorter than one period of the tone, so
its envelope ripples and the gain follows it: lengthening the window to
30 ms takes the low band's tilt from **1.82 to 1.58 dB**, which is the
control that separates the two causes.

An earlier window sat an octave inside each corner - 400 to 1000 Hz of the
mid band's 200 to 2000, 1.3 of its 3.3 octaves - and reported 0.73 / 0.27 /
0.37 dB. That is where the "within 0.25 dB" this docstring used to claim
came from. The window was chosen after the trait was frozen; the table above
is the trait's own words, and M3's depth and evenness clauses are
**disconfirmed** in the evidence pack, with this cause.

What *does* hold is the clause the name is about: driving any band moves no
other band - **0.00 dB** on a soloed read, **0.30 dB** worst on the harder
read, the summed output with nothing muted. In practice a band compresses to
the number you dial in the middle of its range and about a decibel less than
that at its edges.

**Two bands or three is a constructor option, not a knob.** `bands=2` builds
one crossover, four biquads and two detectors; `bands=3` builds two, eight and
three. A knob that muted the middle band would still pay for it every block -
the Mixer pulls a voice at level 0 exactly as hard as one at unity - so the
cheap build has to be a different build. At two bands the split is at
**Crossover Low**, the upper band is the High macros, and Crossover High and
the three Mid macros are inert; the class says so in `macro_is_live()`.
"""

VENDOR = "PyDevices"

from array import array

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

import audiocore
import audiofilters


#: Butterworth Q. Two sections at this Q cascaded is one LR4 half, which is
#: the alignment whose two halves sum to unity with no polarity inversion
#: (RaneNote 160: "LR-2 and LR-6 need inverting, while LR-4 and LR-8 do not").
_BUTTERWORTH_Q = 0.7071067811865475

#: How close the two crossovers may get, at three bands. The parallel
#: three-way's worst deviation is a function of this ratio and of nothing
#: else: measured on these nodes, 0.19 dB at 8:1, 0.99 dB at 4:1 and 7.96 dB
#: at 2:1, against a trait that allows 0.25 dB.
MIN_CROSSOVER_RATIO = 8.0

#: The tail of one LR4 half, in periods of its corner frequency, measured on
#: `audiobiquad.Biquad` from a full-scale DC burst to the last non-zero
#: sample. The float state decays geometrically and is flushed to exact zero
#: below 1e-20, so this is a real number and not an asymptote; the margin
#: above the measured 2.90 is there because `tail_samples` may be long but
#: may never be short.
_TAIL_PERIODS = 3.6

#: Frames the guard hands back in one call. 256 is what every other node on
#: the palette hands out, so the graph runs in one block size. It used to
#: have to be at or under the Splitter's 8192-frame ring as well; since
#: audiodsp#87 the Splitter takes any call in pieces and that clause is gone.
_GUARD_FRAMES = 256


class MultibandCompressor(_component.Component):
    """Two or three bands, each with its own compressor, summed back flat.

    `audiodsp` tier: `audiobiquad` for a crossover whose tail reaches exact
    zero, `audiodynamics` for the per-band detectors, `audioroute` for the
    fan-out.

    **What it is for.** One compressor on a full mix is a compressor the bass
    drives: every kick pumps the vocal. Splitting the band first gives the
    low end its own threshold and leaves the rest of the mix where it was.
    Patch 1 ("Bass Control") is that, at its plainest - the low band working
    and the others idle.

    **Flat at rest, to a fraction of a decibel, and measured.** Every band at
    unity, 30 Hz to 20 kHz: **+0.001 / -0.119 dB** at the 200/2000 Hz split
    and **+0.000 / -0.000 dB** at two bands. The three-band floor is the
    topology's own - the low band never passes through the upper crossover's
    all-pass - and it is why the two crossovers are held eight to one apart.

    **Bands do not bleed into each other**: driving any one band to 12 dB of
    reduction moves the others by **0.00 dB** soloed and at worst 0.30 dB on
    the summed output. **The driven band does not move evenly**, and no
    band does: across its own passband, out to its own -6 dB corners, the
    reduction tilts **1.82 dB** (low), **1.31 dB** (mid) and **1.42 dB**
    (high) against a 0.5 dB bar, and the mean lands 0.09 / 0.73 / 0.36 dB
    short of the 12 asked for. That is the band's own skirt against a fixed
    threshold - `(1 - 1/ratio)` of the shortfall at each tone - and the
    module docstring has the arithmetic. Dial the number you want in the
    middle of a band and expect about a decibel less at its edges.

    **`Mix` at zero is a true bypass**, byte-identical to the source,
    because a Linkwitz-Riley network at unity is an all-pass and not a wire.
    There is **no mixer in the path** there - `output` is the class's input
    node, a `Filter` with no filter, which is a copy - because a mixer voice
    at level 1.0 is not unity on any target: upstream's Q15 level is
    `1.0 * 32768` and the kernel then divides by 32767, so every sample at
    or above 32736 comes out one LSB larger (audiodsp#95). Through the dry
    voice this class's Mix 0 differed from its source on 15 of 32768 samples
    of a full-scale ramp; it is now exact at 22.05, 44.1 and 48 kHz, mono
    and stereo, on all three interpreters. In between, Mix is parallel
    compression: the dry tap and the summed bands, crossfaded.

    **Latency 0 at every setting**, and no option here can add any. The
    crossover is IIR; the detectors do not look ahead.

    **Cost.** This is the most expensive class in the Dynamics family, and
    it is over its budget on both boards: measured 2026-09-07 at
    construction defaults, **44.3 % of a 256-frame stereo block on an
    ESP32-P4 and 83.6 % on an ESP32-S3**, against a dossier budget of 25 %
    and 45 %. It runs in real time on both - the S3 figure is 4.910 ms of a
    5.333 ms block - and it leaves 8 % of that block for everything else on
    the chip. At three bands it owns **18 nodes**, eight of them biquads,
    and pulls 72 of them per eight blocks; `bands=2` is the cheaper build
    at **12 nodes and 48 pulls** - four biquads, two detectors, three mixer
    voices - and on the desktop it measured between 75 % and 79 % of the
    three-band cost over three runs on a loaded host.

    **There is no lean patch and there cannot be one.** Every macro
    position and every shipped patch was walked - 243 of them - and the
    graph is the same 18 nodes and 72 pulls at all of them, because the
    Mixer pulls a voice at level 0 exactly as hard as one at unity. The one
    position that is not is **Mix 0**, where `output` is the source and
    nothing this class owns is pulled at all; no shipped patch sits there.
    Only the constructor can make a *working* instance cheaper.
    """

    NAME = 'MultibandCompressor'
    DISPLAY_NAME = 'Multiband Compressor'
    CATEGORIES = ('Dynamics',)
    VERSION = '0.1.0'

    TIER = _component.AUDIODSP
    REQUIRES = ("audiobiquad", "audiodynamics", "audioroute")

    #: No band's behaviour refers to tempo, so the transport is never read
    #: (dossier App. I, D10).
    CAPABILITIES = ()

    #: Zero at every setting: an IIR crossover rotates phase, it does not
    #: delay onset, and no detector here looks ahead.
    LATENCY_SAMPLES = 0

    #: Overridden as a property below - the ring-down is the lower
    #: crossover's, so it depends on the rate and on where that macro is.
    TAIL_SAMPLES = 0

    MACRO_LABELS = (
        "Crossover Low", "Crossover High",
        "Low Threshold", "Mid Threshold", "High Threshold",
        "Low Ratio", "Mid Ratio", "High Ratio",
        "Low Gain", "Mid Gain", "High Gain",
        "Attack", "Release", "Mix",
    )
    MACRO_MODES = {
        0: "UNIPOLAR", 1: "UNIPOLAR",
        2: "UNIPOLAR", 3: "UNIPOLAR", 4: "UNIPOLAR",
        5: "UNIPOLAR", 6: "UNIPOLAR", 7: "UNIPOLAR",
        8: "BIPOLAR", 9: "BIPOLAR", 10: "BIPOLAR",
        11: "UNIPOLAR", 12: "UNIPOLAR", 13: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (40.0, 800.0, "log"), (800.0, 8000.0, "log"),
        (-60.0, 0.0), (-60.0, 0.0), (-60.0, 0.0),
        (1.0, 20.0, "log"), (1.0, 20.0, "log"), (1.0, 20.0, "log"),
        (-12.0, 12.0), (-12.0, 12.0), (-12.0, 12.0),
        (0.1, 100.0, "log"), (5.0, 1000.0, "log"),
        (0.0, 1.0),
    )
    #: Patch 0 is the constructor's defaults on the 0-127 grid, to the
    #: nearest grid point. A BIPOLAR gain of exactly 0 dB is MIDI 64 exactly
    #: since audiocomponents#87 -- it used to sit at 63.5, unreachable, and
    #: 64 stood for 0.09 dB. `tests/test_cpython_effects_multiband.py` holds
    #: the table to that, span by span, rather than to a hand-copied list.
    PATCHES = {
        0: ("Master Glue",
            (68, 51, 89, 89, 89, 47, 47, 47, 64, 64, 64, 85, 82, 127)),
        1: ("Bass Control",
            (47, 51, 76, 127, 127, 59, 0, 0, 64, 64, 64, 97, 88, 127)),
        2: ("Vocal Bus",
            (78, 73, 85, 93, 89, 39, 39, 39, 64, 64, 64, 92, 76, 127)),
        3: ("De-Boom",
            (34, 51, 64, 127, 127, 76, 0, 0, 64, 64, 64, 72, 94, 127)),
        4: ("Loudness",
            (68, 51, 76, 76, 76, 29, 29, 29, 79, 71, 79, 85, 88, 76)),
    }

    #: Which macros do something at each band count. At two bands there is no
    #: middle band and no upper crossover, and a host that greys a control
    #: out reads this rather than guessing from the label.
    _LIVE_AT_TWO = (0, 2, 4, 5, 7, 8, 10, 11, 12, 13)

    # -- construction --------------------------------------------------

    def _build(self, bands=3, crossover_low_hz=200.0,
               crossover_high_hz=2000.0,
               low_threshold_db=-18.0, mid_threshold_db=-18.0,
               high_threshold_db=-18.0,
               low_ratio=3.0, mid_ratio=3.0, high_ratio=3.0,
               low_gain_db=0.0, mid_gain_db=0.0, high_gain_db=0.0,
               attack_ms=10.0, release_ms=150.0, mix=1.0, patch=None):
        """`bands` is 2 or 3 and fixes the topology; everything else is a
        macro. Nothing here adds latency at any setting, so there is no
        millisecond figure to name: `latency_samples` is 0 for the life of
        the instance."""
        if bands not in (2, 3):
            raise ValueError("bands must be 2 or 3, not %r" % (bands,))
        self._bands = bands
        self._low_hz = 0.0
        self._high_hz = 0.0
        #: Where Mix is, whether the band voices are on their sources, and
        #: whether the graph is wired up at all yet. `_refresh_output` reads
        #: all three and is a no-op until `_build` says so.
        self._mix = 1.0
        self._primed = False
        self._ready = False

        rate = self._sample_rate
        channels = self._channel_count

        #: What the Splitter pulls from, and what `Mix` 0 hands back.
        self._head = head = self._build_input()

        taps = bands + 1
        #: `reset=False`: `audioroute.Splitter` is a container, not an
        #: `audiosample`, and has no `reset_buffer`. After a reset every
        #: cursor is still at `write_pos`, so the audio left in the ring is
        #: behind every reader and is never heard. It does have `deinit()`
        #: since audiodsp#58, and releasing it releases the taps owned below;
        #: on an audiodsp without one, `getattr` skips the call.
        self._split = self._own(audioroute.Splitter(head, taps=taps),
                                reset=False)
        self._taps = [self._own(self._split.tap(index))
                      for index in range(taps)]

        #: Owned **first**, so the reverse walk resets it **last**, and this
        #: is not a style choice. `audiomixer`'s reset does not only clear a
        #: voice: it resets that voice's source and then pulls a fresh chunk
        #: through it (`audiomixer/MixerVoice.c:97`, and the CPython shim's
        #: `MixerVoice.reset` line for line). Reset tail-first, as everything
        #: else here is, and that pull runs through eight biquads that have
        #: not been cleared yet and lands their ring-down in the voice's own
        #: buffer, where nothing later in the walk can reach it: measured,
        #: 4775 LSB from the low band and 2985 from the mid, gone after a
        #: second `reset()`. Reset last and the chunk it pulls comes through
        #: filters that are already silent.
        self._mixer = self._own(audiomixer_mixer(rate, channels, taps),
                                reset=self._reset_mixer)
        #: The silence `_play_voices` opens the mixer's level gates on. It
        #: holds no state, so it declines its own reset.
        self._silence = self._own(audiocore.RawSample(
            array("h", bytes(2 * 2 * channels)),
            sample_rate=rate, channel_count=channels), reset=False)
        self._sections = []
        self._detectors = []
        for band in range(bands):
            chain = self._band_chain(band)
            detector = self._own(audiodynamics.Dynamics(
                audiodynamics.DYN_COMPRESS,
                sample_rate=rate, channel_count=channels,
                detector="rms",
                attack_ms=attack_ms, release_ms=release_ms))
            detector.play(chain)
            self._detectors.append(detector)
        self._output = self._mixer

        self._init_macros(
            (crossover_low_hz, crossover_high_hz,
             low_threshold_db, mid_threshold_db, high_threshold_db,
             low_ratio, mid_ratio, high_ratio,
             low_gain_db, mid_gain_db, high_gain_db,
             attack_ms, release_ms, mix), patch)

        #: The voices are played **after** the macros, and that ordering is a
        #: measurement. `MixerVoice.play` resets its new source and pulls a
        #: chunk from it on the spot (`audiomixer/MixerVoice.c:75-79`), so a
        #: voice played before `_init_macros` holds 256 frames rendered
        #: through eight biquads still sitting at their construction
        #: frequency of 1 kHz. That is the head of every render, on every
        #: instance, and no macro move can reach it afterwards.
        self._play_voices()
        self._ready = True
        self._refresh_output()

    def _build_input(self):
        """The node the Splitter pulls from, which is never the source.

        **This guard no longer guards anything.** It was built because the
        Splitter wrote whatever its immediate source handed back in one call
        into an 8192-frame ring and dragged every cursor past it, so a
        whole-buffer source - `audiocore.RawSample` hands its entire array
        back in one `get_buffer` - lost the first n - 8192 frames of it.
        Since audiodsp#87 the Splitter takes a call bigger than its ring in
        pieces, and the head arrives. Measured at audiodsp `977ef26`: the
        class renders the same bytes with this node and without it, at every
        source block from 256 to 32768 frames, and burst material survives
        unguarded (`tests/test_cpython_effects_multiband.py`,
        `test_m5_the_guard_no_longer_changes_the_render`).

        It is kept for now, not because it is needed, but because dropping a
        node changes the graph a shipped class was costed on and the board
        rows cannot be re-taken until the P4 and S3 are plugged in. It is a
        `Filter` with no filter, which is a copy, and it is the cheapest node
        on the palette.

        It is still its own method because it is the seam the `NoGuard`
        fixture cuts - which is now the *equality* test above, not a fault.
        M5's live fault is a source that keeps only its last ring.
        """
        self._guard = self._own(audiofilters.Filter(
            filter=None, mix=1,
            buffer_size=_GUARD_FRAMES * self._channel_count * 2,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            bits_per_sample=16, samples_signed=True))
        self._guard.play(self._source, loop=False)
        return self._guard

    def _band_modes(self, band):
        """The biquad modes for one band, low to high.

        Two sections a side is LR4, which is the alignment that needs no
        polarity inversion. One a side is LR2, which does - and which is the
        M2 planted fault, cut at this method.
        """
        low_pass = audiobiquad.LOW_PASS
        high_pass = audiobiquad.HIGH_PASS
        if band == 0:
            return (low_pass, low_pass)
        if band == self._bands - 1:
            return (high_pass, high_pass)
        return (high_pass, high_pass, low_pass, low_pass)

    def _band_chain(self, band):
        """The biquad cascade for one band, played off its own tap.

        Band 0 is LP4 at the lower corner; the last band is HP4 at the upper
        one; the middle band, when there is one, is HP4 at the lower corner
        into LP4 at the upper. Every section is created here and re-tuned in
        place by `_apply_crossovers`, so a crossover move allocates nothing.
        """
        modes = self._band_modes(band)
        node = self._taps[band + 1]
        built = []
        for mode in modes:
            section = self._own(audiobiquad.Biquad(
                mode=mode, frequency=1000.0, Q=_BUTTERWORTH_Q,
                sample_rate=self._sample_rate,
                channel_count=self._channel_count))
            section.play(node)
            built.append(section)
            node = section
        self._sections.append(built)
        return node

    def _play_voices(self):
        """Hand every voice its source. Also the second half of `reset()`.

        The gates open first, on one block of silence, so the dry voice is
        at unity from its first sample (`_component.open_level_gates`);
        without it a Mix 0 bypass rendered its first 256 frames silent on a
        ramp. This runs after the macros, so the levels it opens at are the
        ones the class was built with.

        **At Mix 0 the voices are left on that silence.** `_refresh_output`
        hands the bypass back off `self._head`, and a voice playing tap 0
        would drag a block of the head through the Splitter on `play()`
        alone (`MixerVoice.play` fetches there and then) - so the bypass
        would start one block in. Leaving them silent also means the whole
        graph behind this mixer is never pulled while Mix is 0.
        """
        _component.open_level_gates(
            self._mixer,
            [self._mixer.voice[index] for index in range(self._bands + 1)],
            self._silence)
        if self._mix <= 0.0:
            self._primed = False
            return
        self._mixer.play(self._taps[0], voice=0, loop=True)
        for band in range(self._bands):
            self._mixer.play(self._detectors[band], voice=band + 1,
                             loop=True)
        self._primed = True

    def _reset_mixer(self):
        """Clear the Mixer, then hand its voices back their sources.

        `audiodsp`'s `audiomixer` rewinds a voice on reset; **upstream
        CircuitPython's stops it**, and a stopped voice never plays again
        (audiodsp's `docs/upstream-diff.md`, "Resetting a Mixer silenced it,
        permanently"). audiodsp fixed that in its own copy, so a class that
        only calls `reset_buffer` here works on this port and is silent for
        ever after its first `reset()` on a stock board -- measured on
        `cmods/bin/circuitpython-effects`, where `voice[0].playing` is
        `False` after the reset and the render is zeros from there on.

        Re-playing is what the fixed node does anyway: `play()` rewinds the
        source and takes a chunk. Because the Mixer is owned first and so
        walked last, that chunk comes through nodes this reset has already
        cleared.
        """
        audiocore.reset_buffer(self._mixer)
        self._play_voices()

    # -- the live surface ---------------------------------------------

    @property
    def bands(self):
        """2 or 3, as the constructor was asked for. It is not a macro: see
        the class docstring."""
        self._check_live()
        return self._bands

    @property
    def crossover_low_hz(self):
        """The lower corner actually applied, after the Nyquist clamp."""
        self._check_live()
        return self._low_hz

    @property
    def crossover_high_hz(self):
        """The upper corner actually applied, after the eight-to-one clamp
        and the Nyquist clamp; `None` at two bands, where there is no upper
        crossover. It can sit above the Crossover High macro's own value -
        that is the clamp doing its job, and `macro(1)` still reports what
        was asked for."""
        self._check_live()
        return self._high_hz if self._bands == 3 else None

    @property
    def tail_samples(self):
        """How long the crossover rings, in samples at this rate.

        The only memory in this class is the biquads': the detectors hold an
        envelope and no audio, and neither the Mixer nor the Splitter holds a
        line. The lowest corner is the slowest, and a float recursion flushed
        to zero below 1e-20 really does arrive - measured, one LR4 half at
        40 Hz rings for 2.90 periods of its corner and one at 100 Hz for
        2.88, from a full-scale DC burst.
        """
        self._check_live()
        return int(_TAIL_PERIODS * self._sample_rate / self._low_hz) + 1

    def macro_is_live(self, index):
        """Whether macro `index` does anything at this band count. Every
        macro is live at three bands; at two, Crossover High and the three
        Mid macros are not."""
        self._check_live()
        self._macro_index(index)
        return self._bands == 3 or index in self._LIVE_AT_TWO

    # -- macros --------------------------------------------------------

    def _apply_macro(self, index, position):
        if index <= 1:
            self._apply_crossovers()
        elif index <= 4:
            self._set_band(index - 2, threshold_db=self.macro(index))
        elif index <= 7:
            self._set_band(index - 5, ratio=self.macro(index))
        elif index <= 10:
            self._set_band(index - 8, makeup_db=self.macro(index))
        elif index == 11:
            for detector in self._detectors:
                detector.set(attack_ms=self.macro(11))
        elif index == 12:
            for detector in self._detectors:
                detector.set(release_ms=self.macro(12))
        else:
            self._apply_mix(_component.macro_value(self._MACRO_RANGES[13],
                                                   position))

    def _set_band(self, band, **options):
        """A per-band setting. `band` is the macro's band - 0 low, 1 mid,
        2 high - which is the detector's index only at three bands. At two
        there is no middle band and the Mid macros land nowhere."""
        if self._bands == 3:
            target = band
        elif band == 1:
            return
        else:
            target = 0 if band == 0 else 1
        self._detectors[target].set(**options)

    def _apply_crossovers(self):
        """Re-tune every section in place, with the ratio clamp applied.

        The lower corner is authoritative and the upper one is pushed up to
        meet it, rather than the two arguing: a mutual clamp has no defined
        answer when both macros move. Neither is ever refused - a corner
        above the running rate's usable band becomes the highest that rate
        has, which is the rate-honesty invariant's shape.
        """
        self._low_hz = self._hz(self.macro(0))
        if self._bands == 2:
            self._high_hz = self._low_hz
            self._tune(0, (self._low_hz, self._low_hz))
            self._tune(1, (self._low_hz, self._low_hz))
            return
        wanted = self._hz(self.macro(1))
        floor = self._hz(self._low_hz * MIN_CROSSOVER_RATIO)
        self._high_hz = wanted if wanted > floor else floor
        self._tune(0, (self._low_hz, self._low_hz))
        self._tune(1, (self._low_hz, self._low_hz,
                       self._high_hz, self._high_hz))
        self._tune(2, (self._high_hz, self._high_hz))

    def _tune(self, band, frequencies):
        """Re-tune one band's cascade.

        `frequencies` names one corner per LR4 section; a build with fewer
        sections a side (the M2 fault) takes them in the same order, which
        is why this walks the sections and not the list.
        """
        sections = self._sections[band]
        wanted = list(frequencies)
        while len(wanted) > len(sections):
            del wanted[len(wanted) // 2]
        for index in range(len(sections)):
            sections[index].frequency = wanted[index]

    def _apply_mix(self, mix):
        """Dry against the summed bands. At 0 this is the whole bypass: the
        band voices contribute exactly nothing and the dry tap is at unity,
        which is a byte compare against the source and not a claim about the
        sum being flat."""
        self._mix = mix
        self._mixer.voice[0].level = 1.0 - mix
        for band in range(self._bands):
            self._mixer.voice[band + 1].level = mix
        self._refresh_output()

    def _refresh_output(self):
        """At Mix 0 the output is the class's input, not a path through it.

        A mixer voice at level 1.0 is not unity: upstream's Q15 level is
        `1.0 * 32768` and the kernel divides by 32767, so on a stereo mixer
        the right channel - and on a mono one both - comes out one LSB
        larger at every sample from 32736 up (audiodsp#95). Through the dry
        voice this class's Mix 0 differed from its source on 15 of 32768
        samples of a full-scale ramp. So Mix 0 puts no mixer in the path at
        all, which is the answer `Fuzz` and `Overdrive` already give.

        **What is handed back is `self._head`, not `self._source`, and the
        difference is one node wide.** `_build_input`'s guard is an
        `audiofilters.Filter`, and `Filter.play()` resets its source and
        fetches a block from it on the spot - so by the end of construction
        the first 256 frames of the source are inside the guard. Handing
        back the source would start the bypass 256 frames in; handing back
        the guard hands back those frames, and the guard is a `Filter` with
        no filter, which is a copy: measured bit-exact against a full-scale
        ramp on all three interpreters, at both channel counts. It is also
        the node the Splitter reads, so a Mix move off 0 picks the graph up
        at exactly the sample the bypass stopped on. `NoGuard` sets
        `_head` to the source itself, and there the bypass *is* the borrowed
        source, which is what audiodsp#87 finally allows.

        Coming back off 0, the voices are handed their sources with the
        level gates opened first. Since CircuitPython 10.3.0 a voice takes a
        level change only at a zero crossing and a freshly played one starts
        at zero, so without that block of silence the first frames after the
        move would be silent and the level would step in at the block
        boundary - which is the click this avoids
        (`_component.open_level_gates`). `_apply_mix` sets the levels before
        it calls here, so the gates open at the levels Mix just asked for.
        """
        if not self._ready:
            return
        if self._mix <= 0.0:
            self._output = self._head
            return
        if not self._primed:
            self._play_voices()
        self._output = self._mixer


def audiomixer_mixer(rate, channels, voices):
    """The summing node, imported at call time.

    `audiomixer` is a ported CircuitPython module and is on every build this
    library runs on, so it is not in `REQUIRES`; it is imported here rather
    than at module level only to keep the guarded audiodsp imports together
    at the top.
    """
    import audiomixer
    return audiomixer.Mixer(voice_count=voices, sample_rate=rate,
                            channel_count=channels, bits_per_sample=16,
                            samples_signed=True)
