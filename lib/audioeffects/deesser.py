"""The dbx 902 de-esser: sibilance measured against the programme, not
against a threshold knob.

Dossier: `workspace docs/effects-internal/dossiers/DeEsser.md`. Evidence: `workspace docs/effects-internal/evidence/DeEsser-evidence.md`.

**What it is, in a musician's terms.** A de-esser that does not have a
threshold, and does not need one. It listens to how loud the "s" band is
*relative to the whole track* and ducks only when that ratio goes wrong, so
the same setting works on a whispered verse and a belted chorus - the 902's
own claim, and the thing every threshold de-esser gets wrong when the singer
leans in. **Range** is the most it may ever take away, **Frequency** is where
the "s" lives, **Sensitivity** is how close to the full-band level the band
may come before it counts, and **Mode** chooses whether the duck lands on the
whole signal (a vocal) or on the high band alone (the 902's own setting for
picking noise and cymbal edge). **Listen** puts the detector's own band on
the output so you can hear what it is reacting to.

**Portability tier: audioif.** `audiobiquad` for a crossover whose tail
reaches exact zero, `audiodynamics` for the relative-threshold detector that
is the whole point of the circuit, `audioroute` for the parallel routing. It
will not import on a stock CircuitPython board.

**Cost.** Four biquads, one detector pair and one gain cell per frame, plus
three splitter rings and two mixers. Broadband mode runs the four biquads
without using them, because the Mode switch is live.

**Latency: zero.** `latency_samples` is 0 at every setting and there is no
look-ahead option: a de-esser that ducked before the "s" arrived would be a
fault, not a feature. **No option on this class adds latency**, so there is
none to name in milliseconds.

**The traits the palette cannot reach, and the settings the ones it can
reach hold at - stated here because a docstring is where a disconfirmed or
bounded trait has to be visible.**

* **Level independence holds from -6 to -40 dBFS, and not below it.** The
  902's claim, and this class's, is that the same setting works on a
  whisper and a belt. Measured over the Sensitivity macro's whole travel on
  one spectral balance at four absolute levels, the reductions agree within
  **0.316 dB** across -6, -20 and -40 dBFS - well inside the trait's 1 dB -
  and within 0.366 dB at both HF-only patches. Add a **-55 dBFS** take and
  the spread reaches **2.643 dB**, because at that level the `1 - Range`
  dry voice is a handful of LSB and the 16-bit mixer truncates it: the same
  blend with the gain cell muted already spreads 0.643 to 1.253 dB with no
  detector in the sum. So dossier D1 is demonstrated to -40 dBFS and
  disconfirmed at -55; the cause is the palette's int16 path, not the
  relative threshold.
* The 902's release is a constant **925 dB/sec** - a straight *line* in
  dB. `audiodynamics` releases with a one-pole in linear gain, so the rate
  can be tuned to the 902's and the shape cannot. `Release` is therefore in
  milliseconds, and the 3.5 ms default is the setting that lands the rate:
  measured at 48 kHz, 7.01 dB of an 8.12 dB recovery in 7.50 ms, which is
  **935 dB/sec against the 902's 925 - 1.1 % away**, well inside the
  trait's own 10 %, and 912 / 935 / 989 dB/sec at analysis hops of 1.25,
  2.5 and 5.0 ms. **That rate is the default Release's and nothing more:**
  the macro's own 1-200 ms travel dials it from 1643 dB/sec down to 20, and
  three of the six shipped patches sit outside the 10 % bar (690 dB/sec at
  patch 2, 1335 at patch 3, 827 at patch 4). What is wrong on top of that
  is the curve: the recovery departs from a straight dB line by 0.82 dB at
  its worst, where the 902 asks for zero. Dossier D4 is met on rate at the
  shipped Release, bounded by the Release macro, and disconfirmed on shape;
  node ask N-DEESS-2.
* The 902's attack is program-dependent, 2 ms at 10 dB over and 600 us at
  20 dB over. `program_attack=True` is on here and it does shorten the
  attack - measured 6.4 ms down to 5.5 ms across 20 dB of programme level
  at the 5 ms detector this class first shipped, and 2.48 ms down to
  2.03 ms at the 1 ms one it ships now - but nothing like the 902's 3.3x,
  because the option measures its overshoot against the *absolute*
  threshold while `relative_threshold` has moved the gain computer to a
  relative one. The two do not compose, and a de-esser cannot drive itself
  20 dB over without also being 20 dB louder. Dossier D5, node ask
  N-DEESS-7.
* **`detector="rms"` only half-applies here.** With
  `relative_threshold` on, the full-band level the gain computer subtracts
  is a rectified peak follower whatever `detector` says
  (`audioif_dynamics.c:594-600`), so the RMS option governs the band level
  and not the reference. The option is demonstrably working - a 10 %-duty
  train against a sine of the same RMS separates by 4.96 dB on RMS and
  3.54 dB on peak - but dossier D6's own criterion, a matched-RMS sine and
  square landing within 0.5 dB, cannot be *cited* on this class: it reads
  0.41 dB with the RMS detector and 0.46 dB with a peak one, so it tells
  the two apart not at all. Node ask N-DEESS-8.
* The 902 splits at **12 dB/octave, maximally flat**. The audio path here is
  Linkwitz-Riley 4 (two cascaded Butterworth sections a side) because
  HF-only mode sums the two halves and a single 12 dB/octave pair nulls at
  the crossing; the detector's band is `audiodynamics`' own side chain, a
  cascade of two one-poles, which is -6 dB at its corner and about
  10.3 dB/octave. Neither half is the 902's filter and the class claims
  neither. Its `Frequency` control does track both corners, which is the
  half of dossier D2 that is demonstrated.

And one the palette bounds rather than clamps: **Range is an asymptote.**
The reduction is `-20*log10((1 - a) + a * g)` with `a = 1 - 10**(-Range/20)`
and `g` the gain cell's gain, so it rises towards Range and never passes it,
but only reaches it in the limit. `dynamics_gain_db()` bounds nothing above
threshold and `audiomixer` clamps a voice level to 0..1, so the dry blend is
the only bound this palette can build (dossier N-DEESS-6). The bound is the
*blend's*, not `-Range` exactly: on a -55 dBFS take the dry voice at Range
20 is about 6 LSB, and rendering that blend alone - the gain cell's own
voice muted, so there is no detector in the sum at all - reads **-20.547 dB
where -20.000 is asked**. The class reads -20.350 there, inside its own
blend's floor. Above -40 dBFS the floor is 0.003 to 0.124 dB and the
question does not arise.

**The reduction the class can reach is about 11.5 dB, whatever Range says.**
Same asymptote: at Range 12, Sensitivity 34 / 44 / 54 / 64 / 80 / 100 give
-9.580 / -11.162 / -11.463 / -11.463 / -11.463 / -11.463 dB, so the closest
any reachable setting comes to a commanded 12 dB is 0.537 dB - outside the
0.5 dB the dossier's D3 asks for. Turning Range up moves the ceiling, not
the distance to it.
"""

VENDOR = "PyDevices"

import array

import audiocore
import audiomixer

from . import _component

try:
    import audiobiquad
except ImportError:      # a stock CircuitPython board, or an old audioif
    audiobiquad = None
try:
    import audiodynamics
except ImportError:
    audiodynamics = None
try:
    import audioroute
except ImportError:
    audioroute = None


#: A Butterworth section; two cascaded a side make the Linkwitz-Riley 4 pair
#: whose halves recombine flat (dossier A-D1, V-D2).
_BUTTERWORTH_Q = 0.7071067811865476

#: `sidechain_poles=2` is two cascaded one-poles, not a Butterworth section,
#: so its magnitude is `w^2 / (w^2 + wc^2)`: -6 dB at `fc`, and -3 dB at
#: `1.5538 * fc`. Asking for `fc / 1.5538` therefore puts the detector's
#: -3 dB point on the audio split's corner, so one Frequency macro means one
#: thing in both paths. Derivation: `workspace docs/effects-internal/dossiers/DeEsser.md`, App. R from 4.
_DETECTOR_CORNER = 1.0 / 1.5537739740300374

#: What a reset has to push through a Splitter's ring. The ring is 8192
#: frames (`audioif/src/shared/audioif_splitter.h:20`) and one take is at
#: most 256 (`audioif_splitter.c:64-70`), so this many pulls a tap empties
#: any backlog it can be holding.
_FLUSH_PULLS = 8192 // 256 + 1

#: Detector averaging. The manual gives none ("dbx patented RMS level
#: detectors" and no time constant), so this is a design choice, and it was
#: measured rather than picked: the RMS filter sits *before* the attack
#: follower, so it puts a floor under how fast the class can react. At 5 ms
#: the measured time to 63 % of the reduction was 6.4 ms whatever the
#: overshoot - the 902's own attack is 0.6 to 2 ms - and at 1 ms it is
#: about 2.4 ms and moves with the overshoot again. One millisecond is also
#: a full cycle at 1 kHz, so it is still an RMS and not a rectifier: the
#: equal-RMS sine and square of dossier D6 measure 0.18 dB apart with it
#: and 0.90 dB apart on a peak detector.
_RMS_MS = 1.0


class DeEsser(_component.Component):
    """De-essing by comparing the sibilant band with the programme."""

    NAME = 'DeEsser'
    DISPLAY_NAME = 'De-Esser'
    CATEGORIES = ('Dynamics',)
    VERSION = '0.1.0'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiobiquad", "audiodynamics", "audioroute")

    #: `()`, and the dossier's reason: sibilance has nothing to do with
    #: tempo. Nothing in this class reads `self._transport()`.
    CAPABILITIES = ()

    #: A VCA under a detector. The IIR split delays phase, never onset, and
    #: no look-ahead is offered.
    LATENCY_SAMPLES = 0

    #: One node block, as a bound on what was measured. Broadband mode has
    #: no tail at all - the audio never enters a filter - and HF-only mode's
    #: longest is the Butterworth pair at the bottom of the Frequency span:
    #: 170 samples at a 800 Hz corner at 48 kHz, 51 at 2.5 kHz, 14 at 8 kHz,
    #: every one of them reaching exact zero, which is what `audiobiquad`
    #: exists for. The numbers are in the evidence pack.
    TAIL_SAMPLES = 256

    MACRO_LABELS = ("Frequency", "Range", "Sensitivity", "Mode", "Release",
                    "Attack", "Listen")
    MACRO_MODES = {0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR", 3: "TOGGLE",
                   4: "UNIPOLAR", 5: "UNIPOLAR", 6: "TOGGLE"}
    _MACRO_RANGES = ((800.0, 8000.0, "log"),   # 902 Frequency
                     (0.0, 20.0),              # 902 Range
                     (0.0, 48.0),              # dB below full band
                     (0.0, 1.0),               # 0 broadband, 1 HF only
                     (1.0, 200.0, "log"),      # ms
                     (0.1, 10.0, "log"),       # ms
                     (0.0, 1.0))               # Listen
    PATCHES = {
        0: ("Vocal", (63, 76, 79, 0, 30, 83, 0)),
        1: ("Bright Vocal", (89, 102, 90, 0, 30, 83, 0)),
        2: ("Whispered Verse", (63, 51, 58, 0, 39, 94, 0)),
        3: ("Guitar Pick Noise", (101, 76, 79, 127, 17, 64, 0)),
        4: ("Cymbal Edge", (111, 102, 90, 127, 33, 75, 0)),
        5: ("Hard De-Ess", (63, 127, 64, 0, 30, 64, 0)),
    }

    # Macro indexes, so the routing below reads as itself.
    _FREQUENCY = 0
    _RANGE = 1
    _SENSITIVITY = 2
    _MODE = 3
    _RELEASE = 4
    _ATTACK = 5
    _LISTEN = 6

    def _build(self, frequency=2500.0, range_db=12.0, sensitivity_db=30.0,
               hf_only=False, release_ms=3.5, attack_ms=2.0, listen=False,
               patch=None):
        """Build the graph the dossier's section 4 draws.

        `source -> MidSide(width=1) -> Splitter A` fans the stream four ways:
        the detector's key, the two halves of the crossover, and a raw pair.
        The gain cell takes either the raw stream or the high band, and the
        output mixer blends its result against the dry at the level `Range`
        sets.
        """
        rate, channels = self._sample_rate, self._channel_count

        # The block adapter. `audioroute.MidSide` at width 1 is the exact
        # identity (its own docstring says so, and it is measured in the
        # evidence pack), it re-blocks any source to 256 frames - which is
        # what keeps a 32768-frame source from overrunning a Splitter's
        # 8192-frame ring - and its `play()` does not reset its source,
        # where `audiofilters.Filter.play()` does. The reset flush below
        # depends on that.
        adapter = audioroute.MidSide(width=1.0, sample_rate=rate,
                                     channel_count=channels)
        adapter.play(self._source)

        top = audioroute.Splitter(adapter, taps=4)
        raw = audioroute.Splitter(top.tap(3), taps=2)

        corner = self._hz(frequency)
        lows = [audiobiquad.Biquad(mode=audiobiquad.LOW_PASS,
                                   frequency=corner, Q=_BUTTERWORTH_Q,
                                   sample_rate=rate, channel_count=channels)
                for _ in range(2)]
        highs = [audiobiquad.Biquad(mode=audiobiquad.HIGH_PASS,
                                    frequency=corner, Q=_BUTTERWORTH_Q,
                                    sample_rate=rate, channel_count=channels)
                 for _ in range(2)]
        lows[0].play(top.tap(1))
        lows[1].play(lows[0])
        highs[0].play(top.tap(2))
        highs[1].play(highs[0])
        band = audioroute.Splitter(highs[1], taps=2)

        # Which stream the one gain cell works on: the whole signal in
        # broadband mode, the high band alone in HF-only. A mixer rather than
        # a re-`play()`, because `play()` on a live graph drops the pending
        # bytes and clicks.
        pre = audiomixer.Mixer(voice_count=2, **self._pcm(1024))
        # The levels go on before anything is played, and that ordering is
        # load-bearing: `audiomixer.MixerVoice.play()` fetches a chunk from
        # its source there and then, so `out.voice[3].play(duck)` below
        # renders this mixer's first 256 frames during construction - with
        # whatever levels it has at that moment. Left at `MixerVoice`'s
        # default 1.0, that made the gain cell's first 256 frames the sum of
        # the raw stream and the high band, which measured as an output
        # peaking at 21090 LSB against an 11000 LSB source. `_route()` sets
        # the same two numbers from the macros a few lines further down;
        # these are the constructor's own answer, in force before the first
        # pull.
        band_only = bool(hf_only) or bool(listen)
        pre.voice[0].level = 0.0 if band_only else 1.0
        pre.voice[1].level = 1.0 if band_only else 0.0
        pre.voice[0].play(raw.tap(0))
        pre.voice[1].play(band.tap(0))

        duck = audiodynamics.Dynamics(
            audiodynamics.DYN_LIMIT,
            # The 902 has no threshold control; this one is the *relative*
            # allowance, and `relative_threshold` is what makes it relative.
            threshold_db=-sensitivity_db,
            attack_ms=attack_ms, release_ms=release_ms,
            relative_threshold=1,      # dossier D1, the trait that defines it
            program_attack=1,          # dossier D5
            detector="rms", rms_ms=_RMS_MS,   # dossier D6
            sidechain_hz=corner * _DETECTOR_CORNER,
            sidechain_poles=2,         # dossier D2, detector half
            sample_rate=rate, channel_count=channels)
        duck.play(pre)
        # The detector reads the *untouched, full-band* stream: the relative
        # comparison needs the whole signal, so the key cannot be the band.
        duck.key(top.tap(0))

        out = audiomixer.Mixer(voice_count=4, **self._pcm(1024))
        out.voice[0].play(raw.tap(1))    # the dry, broadband
        out.voice[1].play(lows[1])       # the low half, HF-only
        out.voice[2].play(band.tap(1))   # the dry high half, HF-only
        out.voice[3].play(duck)          # the ducked stream, both modes

        # The class does NOT end in a mixer, and that is not decoration.
        # On CircuitPython `audiomixer.Mixer.reset_buffer` *stops* every
        # voice rather than rewinding it, permanently - audioif fixed that
        # in its own port and deliberately did not patch it into the
        # oracle build (`upstream-diff.md`, "Resetting a Mixer silenced it,
        # permanently"), and the consequence recorded there is that a class
        # ending in a Mixer "can be the last node in a chain there, but not
        # the middle of one". Anything upstream - a host, the next effect's
        # `play()`, `tools/render_effect.py:717` - resets what it is handed,
        # so ending in a mixer would make this class silent on a board the
        # moment something was chained after it. Measured: it rendered
        # silence on `circuitpython-effects` for every probe until this node
        # existed. `audioroute.MidSide` at width 1 is the exact identity and
        # its `reset_buffer` clears its own cursor and nothing else.
        tail = audioroute.MidSide(width=1.0, sample_rate=rate,
                                  channel_count=channels)
        tail.play(out)

        self._adapter = adapter
        self._lows = lows
        self._highs = highs
        self._duck = duck
        self._pre = pre
        self._out = out
        self._tail = tail
        self._splitters = (top, raw, band)
        # What each mixer voice plays, in the order a reset has to re-prime
        # them: `pre` before `out`, because `out`'s voice 3 pulls through
        # `pre`. `MixerVoice.play()` is the only clear a mixer has that
        # works on all three interpreters - see `_reset_chain`.
        self._voices = ((pre, 0, raw.tap(0)), (pre, 1, band.tap(0)),
                        (out, 0, raw.tap(1)), (out, 1, lows[1]),
                        (out, 2, band.tap(1)), (out, 3, duck))
        self._taps = (top.tap(0), top.tap(1), top.tap(2), top.tap(3),
                      raw.tap(0), raw.tap(1), band.tap(0), band.tap(1))
        self._silence = audiocore.RawSample(
            array.array("h", bytes(2 * 2 * channels)),
            sample_rate=rate, channel_count=channels)

        # `deinit()` walks this list backwards, tail first, which is what
        # the order below is for. `reset()` cannot use the same walk, and
        # the reason is worth stating rather than discovering: a
        # `Splitter`'s ring cannot be cleared - the type exposes `tap()` and
        # nothing else on every target, and `SplitterTap.reset_buffer` is
        # "deliberately nothing" - so the rings have to be pushed empty
        # against a silent source, and `audiomixer.Mixer._reset_buffer`
        # refetches a chunk into every voice, so both mixers have to be
        # cleared *while* that silent source is still on. One ordered
        # routine can express that and a per-node walk cannot, so the tail
        # carries `_reset_chain` and every other node declines its own
        # reset. Nothing is skipped: `_reset_chain` names all seven
        # resettable nodes explicitly, and the list below is what the class
        # is held to.
        self._own(tail, reset=self._reset_chain)
        self._own(out, reset=False)
        self._own(pre, reset=False)
        self._own(duck, reset=False)
        for node in (highs[1], highs[0], lows[1], lows[0]):
            self._own(node, reset=False)
        for splitter in (band, raw, top):
            # No `reset_buffer` and no `clear`, so `_reset_chain()` is what
            # clears these. `deinit()` it does have, since audioif#58, and
            # asking for one an older audioif lacks is skipped by `getattr`.
            self._own(splitter, reset=False)
        self._own(adapter, reset=False)
        # The eight taps and the silent filler are nodes this class built
        # too, and they belong on the list for the reason the paragraph
        # above gives: `deinit()` walks it, and a node missing from it is a
        # node nothing releases. Both decline their own reset - a tap's
        # `reset_buffer` is deliberately nothing and `_reset_chain()` empties
        # the rings by pulling them, and the filler holds no state to clear.
        # `Splitter.tap(n)` returns the same object each call, so these are
        # the same eight taps `self._voices` plays.
        for tap in self._taps:
            self._own(tap, reset=False)
        self._own(self._silence, reset=False)

        self._output = tail
        self._init_macros((frequency, range_db, sensitivity_db,
                           1.0 if hf_only else 0.0, release_ms, attack_ms,
                           1.0 if listen else 0.0), patch)

    # -- reset ---------------------------------------------------------

    def _reset_chain(self):
        """Clear every node this class built, in the one order that works.

        Measured on the way to this routine, and the reason it is not a
        per-node walk: clearing every node but the rings still replayed
        **19999 LSB** of stale audio and did not reach an all-zero block
        until frame 512; clearing the rings first but restoring the source
        before the mixers still left **3024 LSB**, because
        `audiomixer.Mixer._reset_buffer` refetches a chunk into every voice
        and that fetch pulled live audio through.

        So: the silent sample goes on first, every tap is pulled until its
        backlog is gone, every clearable node is cleared while the silence
        is still there - the mixers' refetch then fetches silence - and the
        borrowed source goes back on last. The source itself is never reset
        and never rewound; `audioroute.MidSide.play()` sets its source and
        drops its own pending bytes, and does nothing else.
        """
        self._adapter.play(self._silence)
        for tap in self._taps:
            for _ in range(_FLUSH_PULLS):
                audiocore.get_buffer(tap)
        for node in (self._lows[0], self._lows[1], self._highs[0],
                     self._highs[1], self._duck):
            audiocore.reset_buffer(node)
        # The mixers are re-primed rather than reset. `reset_buffer` on a
        # Mixer stops every voice for good on CircuitPython (see `_build`),
        # and `MixerVoice.play()` is what does the same job on all three: it
        # resets the voice's own source and refills the voice, which is
        # exactly a rewind. It runs while the silent sample is still on the
        # adapter, so what the voices refill with is silence.
        for mixer, index, sample in self._voices:
            mixer.voice[index].play(sample)
        self._adapter.play(self._source)
        audiocore.reset_buffer(self._adapter)
        audiocore.reset_buffer(self._tail)

    # -- macros --------------------------------------------------------

    def _apply_macro(self, index, position):
        value = _component.macro_value(self._MACRO_RANGES[index], position)
        if index == self._FREQUENCY:
            corner = self._hz(value)
            for node in self._lows:
                node.frequency = corner
            for node in self._highs:
                node.frequency = corner
            self._duck.set(sidechain_hz=corner * _DETECTOR_CORNER)
        elif index == self._SENSITIVITY:
            self._duck.set(threshold_db=-value)
        elif index == self._RELEASE:
            self._duck.set(release_ms=value)
        elif index == self._ATTACK:
            self._duck.set(attack_ms=value)
        elif index == self._LISTEN:
            # `key_listen` puts the detector's own band on the node's output
            # at unity, which is what "listen" has to mean on a de-esser
            # whose detector is the interesting part.
            self._duck.set(key_listen=1.0 if value >= 0.5 else 0.0)
            self._route()
        else:                       # Range and Mode are both routing
            self._route()

    def _route(self):
        """Push Range, Mode and Listen into the two mixers.

        `alpha` is the wet fraction, and it is the whole Range mechanism:
        the reduction the class can reach is `-20*log10(1 - alpha)` and no
        more, because `1 - alpha` of the dry signal is always in the sum.
        """
        spans = self._MACRO_RANGES
        range_db = _component.macro_value(spans[self._RANGE],
                                          self._macros[self._RANGE])
        alpha = 1.0 - _component.db_to_gain(-range_db)
        hf_only = self._macros[self._MODE] >= 0.5
        listening = self._macros[self._LISTEN] >= 0.5

        # The gain cell works on the high band in HF-only mode, on the whole
        # signal otherwise. In Listen it does not matter what it works on -
        # `key_listen` replaces its output with the detector's band - but the
        # high band is the honest thing to leave selected.
        self._pre.voice[0].level = 0.0 if (hf_only or listening) else 1.0
        self._pre.voice[1].level = 1.0 if (hf_only or listening) else 0.0

        if listening:
            # Only the detector's band is audible, at unity.
            self._out.voice[0].level = 0.0
            self._out.voice[1].level = 0.0
            self._out.voice[2].level = 0.0
            self._out.voice[3].level = 1.0
        elif hf_only:
            # low + (1 - alpha) * high + alpha * duck(high)
            self._out.voice[0].level = 0.0
            self._out.voice[1].level = 1.0
            self._out.voice[2].level = 1.0 - alpha
            self._out.voice[3].level = alpha
        else:
            # (1 - alpha) * source + alpha * duck(source); at Range 0 that is
            # the source itself, byte for byte.
            self._out.voice[0].level = 1.0 - alpha
            self._out.voice[1].level = 0.0
            self._out.voice[2].level = 0.0
            self._out.voice[3].level = alpha

    # -- a meter, for a host that wants one ----------------------------

    def gain_reduction_db(self):
        """What the gain cell did to the last frame, in dB.

        This is the cell's own number, before the Range blend, so it is the
        detector's reading rather than what reached the output. The output's
        reduction is `20*log10((1 - alpha) + alpha * 10**(cell/20))`.
        """
        self._check_live()
        return self._duck.gain_reduction_db()
