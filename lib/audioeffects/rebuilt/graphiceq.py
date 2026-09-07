"""Ten octave bands and two level sliders, after the MXR M-108 Ten Band.

Dossier: `docs/effects/GraphicEQ.md`. Evidence:
`docs/effects/GraphicEQ-evidence.md`.

The M-108 is not ten filters in parallel. It is **one op-amp stage whose gain
is varied across a tuned circuit**, nine gyrator bells at 31.25 Hz doubling to
8 kHz and a shelf at 16 kHz, with a mechanical **centre detent** at which each
band is out of the circuit. Two more sliders, GAIN and VOLUME, sit around the
bank.

**The bands get wider as you back off, and that is the whole character.**
Because the slider loads the tuned circuit, the M-108's Q moves with it: a
band is narrow only near the ends of its travel and, a couple of dB in, has
"degraded into something nearer to a 10-band octave equalizer" (Bohn, JAES
34(9)). This class does the same thing arithmetically -- `Q` is computed from
each band's gain on every macro move, holding a 1 dB skirt still while the
peak grows. At `Band Q` 2.0 the 1 kHz band is 1.8 octaves wide at +3 dB and
0.71 at +12. Turn `Constant Q` on and every band keeps one width at every
setting, which is the other half of Bohn's paper and sounds like a studio
graphic rather than a pedal.

**Bands overlap and add.** Three adjacent sliders at +6 dB do not give you
+6 dB: measured, they give **+8.78 dB across 2.6 octaves**. That is what a
musician hears when they draw a curve on this pedal, and it is why the two
level sliders exist. All ten at +6 dB reach **+8.70 dB on average from 60 Hz
to 8 kHz, with 2.35 dB of ripple** between the centres -- the bank is hot and
not quite flat, and the dossier records both as measured rather than as
intended.

**The 16k slider is a shelf, and its corner sits below its label.** A shelf's
named frequency is where it has reached *half* its gain, so a corner on
16 kHz would move 16 kHz by 6 dB of a 12 dB request and put the rest above
hearing. Half an octave down puts **+10.91 dB at 16 kHz** and +11.94 at
20 kHz, and lifts the 8 kHz slider's own centre by less than 2 dB.

**A band at its detent is a wire, byte for byte.** `mix` goes to zero on any
band inside 0.1 dB of centre -- one macro step at +/-12 dB is 0.189 dB, so
codes 63 and 64 are the detent and nothing else is. This matters more than it
sounds: a *flat* biquad section at 31.25 Hz is not bit-transparent in float32
(Direct Form I, poles that close to z = 1, up to 5 LSB over 24 000 frames),
so a band left "at zero" with `mix = 1` would quietly rewrite the bottom
octave.

**Latency: zero, at every setting and every rate.** Twelve biquads, nothing
that looks ahead. No option on this class adds any -- there is no lookahead,
no partition and no window to add, so the table of latency-adding options is
empty on purpose.

**Tail: 465 ms**, set by the 31.25 Hz band's ring-down at full boost, and
constant in time across rates. `tail_samples` reports the rate-scaled bound.

**It is loud, and it clips where the pedal clips.** `Gain` sits before the
bank and `Volume` after, as the panel reads; each node writes int16 between
sections and saturates at full scale, so +12 dB of Gain into a hot source
clips at the first section -- an M-108's op-amps do too. Pull `Volume` down
when you push `Gain` up, or push the bank instead.

**`audioif` tier: it needs `audiobiquad`.** The ported `synthio.Biquad` holds
DC after silence at exactly this bank's bottom two bands -- +7 LSB at 31.25 Hz
and +5 LSB with all ten engaged, for ever (audioif#23). Those are the numbers
that made the DC-clean node (audioif#39); on it every one of them is exact
zero.

**Cost.** Twelve biquad sections run at every setting -- a flat band is muted,
not skipped -- which is about two thirds of an ESP32-S3's stereo block and
under two fifths of an ESP32-P4's. There is no lean patch, because a patch
cannot change the node count.
"""

VENDOR = "PyDevices"

import math

from .. import _component

try:
    import audiobiquad
except ImportError:      # a stock CircuitPython board, or an old audioif
    audiobiquad = None


#: The M-108's own centres: exact octave doublings from 31.25 Hz, not the ISO
#: preferred series (G1 and G2's Filtering line, and the panel legend).
DEFAULT_CENTRES = (31.25, 62.5, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0,
                   8000.0, 16000.0)

#: The band travel, and therefore the width of the detent. One step on the
#: 0-127 grid is 24/127 = 0.189 dB, so codes 63 and 64 sit at -/+0.094 dB and
#: code 65 at +0.283: a 0.1 dB dead band is exactly the two centre codes.
_BAND_DB = 12.0
_DETENT_DB = 0.1

#: The shelf's half-gain corner sits this far below its named band.
#:
#: An RBJ shelf's `frequency` is where it has reached *half* its dB gain, so a
#: shelf whose corner is its own band centre gives that band only +6.00 dB of
#: a +12 dB request and puts the rest above 20 kHz -- measured, and most of it
#: past hearing. Half an octave lower puts **+10.91 dB at 16 kHz** and +11.94
#: at 20 kHz, while lifting the 8 kHz bell's centre by only 1.96 dB, so the
#: top slider does what its label says and the two bands stay apart.
_SHELF_CORNER_RATIO = 2.0 ** 0.5

#: A shelf takes `Q` as a resonance, not a bandwidth, and 1.4 makes it
#: overshoot: at 16 kHz and +12 dB it measures **-2.37 dB at 12 kHz** and
#: +13.94 at 20 kHz -- a cut below the corner and 1.9 dB past the asymptote
#: above it. 0.707 is the flat shelf a level slider means.
_SHELF_Q = 0.7071067811865475

#: The corner of the two level sections. A `HIGH_SHELF` is the only shape on
#: this palette that can give gain above unity (`audiomixer` clamps its level
#: to 1.0 silently, `audiomath.Multiply` can only attenuate), and 5 Hz is the
#: corner at which +12 dB measures +12.00 dB at 30 Hz as well as at 10 kHz.
#: At 10 Hz the 30 Hz reading is already 0.22 dB short.
_LEVEL_CORNER_HZ = 5.0

#: The proportional-Q law's skirt: the level, in dB, whose crossing frequency
#: is held still while the peak grows (`ParametricEQ.md` Appendix A).
_SKIRT_DB = 1.0

#: The anchor gain the `Band Q` macro names the Q of.
_ANCHOR_DB = 12.0

#: `audioif_filter_f32.c:99-100` clamps Q into this band for stability; the class
#: clamps to the same numbers so a macro cannot ask for what the kernel will
#: silently refuse.
_Q_MIN = 0.05
_Q_MAX = 60.0

#: The worst-case ring-down, in seconds: all ten bands at +12 dB, measured at
#: 464.9 / 465.3 / 465.4 ms at 48000 / 44100 / 22050 Hz. Reported with margin,
#: so `tail_samples` is a bound rather than a coincidence at one rate.
_TAIL_SECONDS = 0.47

_SKIRT = 10.0 ** (_SKIRT_DB / 20.0)
_ANCHOR_A = 10.0 ** (_ANCHOR_DB / 40.0)
_ANCHOR_NUM = _ANCHOR_A ** 2 - (_SKIRT ** 2) / (_ANCHOR_A ** 2)


def band_q(gain_db, anchor):
    """The Q a band of `gain_db` gets, for a bank anchored at `anchor`.

    `ParametricEQ.md` Appendix A's law, rearranged so the anchor is the
    macro: holding the +/-1 dB skirt at one frequency while the peak grows
    means `Q(G) = anchor * sqrt((A^2 - L^2/A^2) / (A12^2 - L^2/A12^2))` with
    `A = 10^(|G|/40)`. Below +1 dB there is no root -- a 1 dB skirt cannot sit
    on a 1 dB bell -- and Q floors at the kernel's own minimum, which is the
    limit of the law rather than a special case.
    """
    amplitude = 10.0 ** (abs(gain_db) / 40.0)
    numerator = amplitude ** 2 - (_SKIRT ** 2) / (amplitude ** 2)
    if numerator <= 0.0:
        return _Q_MIN
    return min(_Q_MAX, max(_Q_MIN,
                           anchor * math.sqrt(numerator / _ANCHOR_NUM)))


class GraphicEQ(_component.Component):
    """A ten-band octave graphic EQ with proportional Q, after the MXR M-108.

    `audioif` tier: it needs `audiobiquad`, whose float state is what lets a
    31.25 Hz band reach exact zero after silence.

    Twelve `audiobiquad.Biquad` nodes in series -- `Gain`, nine bells, the
    16 kHz shelf, `Volume`. A band inside the detent is crossfaded out
    (`mix = 0`), so it is a wire byte for byte while its knob still turns.
    """

    NAME = 'GraphicEQ'
    DISPLAY_NAME = 'Graphic EQ'
    CATEGORIES = ('EQ',)
    VERSION = '0.0.1'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiobiquad",)

    #: The transport is never read: nothing here is tempo-dependent, and a
    #: filter bank has no rate to lock to.
    CAPABILITIES = ()

    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = int(48000 * _TAIL_SECONDS)

    MACRO_LABELS = ("31", "63", "125", "250", "500", "1k", "2k", "4k", "8k",
                    "16k Shelf", "Gain", "Volume", "Band Q", "Constant Q")
    MACRO_MODES = {0: "BIPOLAR", 1: "BIPOLAR", 2: "BIPOLAR", 3: "BIPOLAR",
                   4: "BIPOLAR", 5: "BIPOLAR", 6: "BIPOLAR", 7: "BIPOLAR",
                   8: "BIPOLAR", 9: "BIPOLAR", 10: "BIPOLAR", 11: "BIPOLAR",
                   12: "UNIPOLAR", 13: "TOGGLE"}
    _MACRO_RANGES = (((-_BAND_DB, _BAND_DB),) * 12
                     + ((0.7, 2.5), (0.0, 1.0)))

    #: Every band macro at 64 is the detent, so patch 0 is a wire.
    #:
    #: The three boosting patches carry a `Volume` trim, and it is not
    #: decoration: measured on an 11000-peak source, `Scooped Mids` reaches
    #: 21574 at the detent, `Pushed Mids` 17893 and `Full Boost` 26741 -- the
    #: last of those clips a source only 3 dB hotter. Each trim is the one
    #: that brings its patch back to roughly `Flat`'s own level, so a player
    #: hears the curve rather than the volume when they step through them.
    #: That is what the VOLUME slider is for on the pedal.
    _FLAT = 64
    PATCHES = {
        0: ("Flat", (64,) * 12 + (92, 0)),
        1: ("Scooped Mids", (95, 95, 79, 48, 32, 32, 48, 79, 95, 95,
                             64, 32, 92, 0)),
        2: ("Pushed Mids", (48, 48, 64, 79, 95, 95, 95, 79, 64, 48,
                            64, 40, 92, 0)),
        3: ("Trimmed Bottom", (16, 32, 48, 64, 64, 64, 64, 64, 64, 64,
                               64, 64, 92, 0)),
        4: ("Rolled Top", (64, 64, 64, 64, 64, 64, 64, 48, 32, 16,
                           64, 64, 92, 0)),
        5: ("Full Boost", (95,) * 10 + (64, 24, 92, 0)),
    }

    #: Macro indexes, named so the arithmetic below reads.
    _FIRST_BAND = 0
    _BANDS = 10
    _GAIN = 10
    _VOLUME = 11
    _BAND_Q = 12
    _CONSTANT_Q = 13

    def _build(self, gains_db=None, gain_db=0.0, volume_db=0.0, band_q=2.0,
               constant_q=False, centres=None, patch=None):
        """Build the twelve sections, head to tail.

        `gains_db` sets the whole curve in one call -- up to ten numbers in
        dB, in the order the panel reads, low to high; a short list leaves the
        rest of the bank at its detent. `centres` retunes the bank and
        must be **exactly ten ascending frequencies**: the macro surface is
        fixed at fourteen, so a shorter list would leave knobs addressing
        nothing. The 16 kHz shelf is always `centres[9]`, so it stays the top
        band through any retune.
        """
        centres = DEFAULT_CENTRES if centres is None else tuple(
            float(hz) for hz in centres)
        if len(centres) != self._BANDS:
            raise ValueError("centres must name exactly %d frequencies, "
                             "low to high" % self._BANDS)
        for index in range(1, self._BANDS):
            if centres[index] <= centres[index - 1]:
                raise ValueError("centres must ascend")
        self._centres = centres

        # Fewer than ten sets the bottom of the bank and leaves the rest at
        # the detent, which is what the old class's `zip(ISO_BANDS, gains_db)`
        # did and what the callers that already pass five expect. More than
        # ten is a caller who thinks this bank is a different size, and that
        # is an error rather than a truncation.
        gains_db = () if gains_db is None else tuple(
            float(db) for db in gains_db)
        if len(gains_db) > self._BANDS:
            raise ValueError("gains_db names %d bands; this bank has %d"
                             % (len(gains_db), self._BANDS))
        gains_db = gains_db + (0.0,) * (self._BANDS - len(gains_db))

        # `_hz()` clamps to 0.98 x Nyquist rather than refusing: at 22.05 kHz
        # the 16 kHz shelf has nowhere to sit, and a biquad asked for a corner
        # over Nyquist rails into a full-scale square wave at fs/4 while
        # raising nothing. What was clamped is reported, never dropped.
        # The top band is a shelf, so what goes into the filter is its
        # half-gain corner rather than the band's own name.
        asked = tuple(list(centres[:self._BANDS - 1])
                      + [centres[self._BANDS - 1] / _SHELF_CORNER_RATIO])
        self._built_hz = tuple(self._hz(hz) for hz in asked)
        self._clamped = tuple(index for index in range(self._BANDS)
                              if self._built_hz[index] != asked[index])

        # Head: Gain, before the bank, as the panel reads.
        self._gain = self._own(self._section(audiobiquad.HIGH_SHELF,
                                             _LEVEL_CORNER_HZ, _SHELF_Q))
        self._gain.play(self._source)
        previous = self._gain

        # The bank: nine bells and the shelf on top.
        self._sections = []
        for index in range(self._BANDS):
            shelf = index == self._BANDS - 1
            mode = audiobiquad.HIGH_SHELF if shelf else audiobiquad.PEAKING_EQ
            # A bell's Q is replaced on every macro move by the law; the
            # shelf's is not a bandwidth and stays where it is put.
            node = self._own(self._section(mode, self._built_hz[index],
                                           _SHELF_Q if shelf else 1.4))
            node.play(previous)
            self._sections.append(node)
            previous = node

        # Tail: Volume, after the bank.
        self._volume = self._own(self._section(audiobiquad.HIGH_SHELF,
                                               _LEVEL_CORNER_HZ, _SHELF_Q))
        self._volume.play(previous)
        self._output = self._volume

        self._init_macros(
            tuple(gains_db) + (float(gain_db), float(volume_db),
                               float(band_q), 1.0 if constant_q else 0.0),
            patch)

    def _section(self, mode, frequency, q):
        """One node, muted. Every section starts as a wire and `_apply_macro`
        is the only thing that ever un-mutes one, so the constructor and a
        later `set_macro` cannot disagree about what a detent means."""
        return audiobiquad.Biquad(mode=mode, frequency=frequency, Q=q,
                                  gain_db=0.0, mix=0.0,
                                  sample_rate=self._sample_rate,
                                  channel_count=self._channel_count)

    def _apply_macro(self, index, position):
        if index < self._BANDS:
            self._retune(index)
        elif index == self._GAIN:
            self._level(self._gain, self._GAIN)
        elif index == self._VOLUME:
            self._level(self._volume, self._VOLUME)
        else:
            # Band Q and Constant Q are the law, not a band: both move every
            # bell at once. The shelf keeps its own Q, which is not a
            # bandwidth.
            for band in range(self._BANDS):
                self._retune(band)

    def _retune(self, band):
        gain_db = _component.macro_value(self._MACRO_RANGES[band],
                                         self._macros[band])
        node = self._sections[band]
        if abs(gain_db) < _DETENT_DB:
            # `mix = 0` makes the kernel compute `1.0f * x + 0.0f * y`, which
            # is the input sample exactly. A `gain_db = 0` section is *not*
            # that: at 31.25 Hz it drifts up to 5 LSB over 24000 frames.
            node.mix = 0.0
            return
        self._wake(node)
        if band < self._BANDS - 1:
            node.Q = self._q_for(gain_db)
        node.gain_db = gain_db
        node.mix = 1.0

    @staticmethod
    def _wake(node):
        """Clear a section that is leaving the detent.

        The kernel runs the recursion even at `mix = 0`
        (`audioif_filter_f32.c:216-241` has no short-circuit), so a muted
        section's state is a filter nobody heard, tracking the input through
        coefficients nobody chose. Handing that state to the filter about to
        run is what makes a patch change slam: measured on a 220 Hz tone at
        peak 11000, `Flat` to `Full Boost` peaks at **32752 and stays above
        its own steady level for 344 ms** without this, and at **13575 for
        0 ms** with it -- the level shelves sit at 5 Hz, so their stale state
        takes a third of a second to leave. Live-to-live gain changes are not
        cleared: those states mean something, and the same measurement puts
        that transient at 19 ms.
        """
        if node.mix == 0.0:
            node.clear()

    def _q_for(self, gain_db):
        anchor = _component.macro_value(self._MACRO_RANGES[self._BAND_Q],
                                        self._macros[self._BAND_Q])
        if self._macros[self._CONSTANT_Q] >= 0.5:
            return min(_Q_MAX, max(_Q_MIN, anchor))
        return band_q(gain_db, anchor)

    def _level(self, node, index):
        gain_db = _component.macro_value(self._MACRO_RANGES[index],
                                         self._macros[index])
        if abs(gain_db) < _DETENT_DB:
            node.mix = 0.0
            return
        self._wake(node)
        node.gain_db = gain_db
        node.mix = 1.0

    def program_change(self, index, channel=0, note_id=-1,
                       sample_position=0):
        """Jump to a patch, and start the new curve from a clean bank.

        The difference between this and `set_macro` is deliberate, and it is
        the difference between a jump and a sweep. A slider being pushed
        should ride through on the state it has; a patch change is ten
        sliders arriving somewhere else at once, and handing that jump a
        bank full of the old curve's memory is what makes it slam. Measured
        on a 220 Hz tone at peak 11000, `Full Boost` to `Scooped Mids`
        peaks at **32767 and stays above its own steady level for 306 ms**
        without this, and at **5826 for 8 ms** with it.
        """
        if type(self).PATCHES.get(index) is None:
            return _component.Component.program_change(
                self, index, channel=channel, note_id=note_id,
                sample_position=sample_position)
        result = _component.Component.program_change(
            self, index, channel=channel, note_id=note_id,
            sample_position=sample_position)
        for node in self._nodes:
            node.clear()
        return result

    @property
    def tail_samples(self):
        """The worst-case ring-down at the running rate.

        A bound, not a coincidence at 48 kHz: the 31.25 Hz band's decay is
        465 ms whatever the rate, so the sample count has to scale with it or
        it is wrong at two rates out of three.
        """
        self._check_live()
        return int(self._sample_rate * _TAIL_SECONDS)

    @property
    def centres(self):
        """The band centres this instance was asked for, in Hz."""
        self._check_live()
        return self._centres

    @property
    def built_centres(self):
        """What is actually in the filters: nine bell centres and, in the
        tenth slot, the **shelf's half-gain corner** -- half an octave below
        its named band, so the band gets 10.91 dB of a 12 dB request rather
        than 6.00.

        At a rate too low to hold the top of the bank the values are clamped
        as well: at 22.05 kHz the shelf's corner sits at 10804.5 Hz rather
        than 11313.7. `clamped` says which, so a caller reads the clamp
        rather than inferring it from a response it did not ask for.
        """
        self._check_live()
        return self._built_hz

    @property
    def clamped(self):
        """The indexes of the bands whose centre was clamped below Nyquist.

        Empty at 48 kHz and 44.1 kHz. The old class dropped those bands
        silently instead; nothing said so, which is absence reading as
        agreement.
        """
        self._check_live()
        return self._clamped
