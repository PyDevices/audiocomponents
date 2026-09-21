"""An acoustic drum kit, by modal synthesis.

Every other drum in this library is a *machine* - a TR-808, a LinnDrum, a
DrumTraks - and they are good at being machines. This one is not a machine at
all. It is what a struck drum head does: a bank of decaying sinusoids at
frequencies that are not harmonics of anything, excited by a short burst that
stands in for the stick.

That is `audiomodal.Bank`, which audiodsp carries for this. The kit is two
banks and one excitation: the hi-hat has its own so that closing it can choke
what was ringing, and everything else shares one, because nothing else in a
kit silences anything else.

**But a bank is not the whole of a drum, and the first version of this file
believed it was.** Brad listened to it and said the kick was not convincing
and the snare sounded like a tuned tom. Both were true, and both were things
a resonator bank structurally cannot do:

- **A kick is a pitch envelope.** Its fundamental starts near 100 Hz and falls
  to around 50 in the first tenth of a second, and that fall is most of what
  makes it read as a kick rather than as a low tom. A bank's modes sit where
  they were put: measured on the first version, the kick's f0 was 56.2 Hz at
  5 ms, at 60 ms and at 150 ms alike - a drop of exactly 0.0%.
- **Snare wires are noise.** Dozens of them rattle against the head, broadband
  and untuned. The first version modelled them as two resonators at 1.9 and
  3.3 kHz, which measured a spectral flatness of 0.001 in that band - white
  noise measures 0.542 on the same scale and a single pure tone measures
  0.000. They were two tones, they carried 4% of the energy, and they were
  gone by 40 ms. What was left was a pitched 325 Hz body, which is a tom.

So the kit is a hybrid now, and deliberately: the bank does pitched inharmonic
bodies, which is what it is good at and what a tom *is*, and a second synth
carries the pitch-dropping fundamentals and the noise layers beside it. That
is the same shape the ten drum machines in this library already use - the
TR-909's kick is a sine with a `FALL` bend and a low-passed noise click, and
its snare is a tone plus band-passed noise - and the reason is the same.

**The sound is not sampled and not pretending to be.** There are no captures
here and could not be - the library ships no binary assets - so the mode
tables are physics and published measurement. Read
`docs/effects-internal/dossiers/instruments/acoustickit.md` in the workspace
anchor for what is measured and what is not, because the honest answer is
"mostly not": the snare's six modes and their damping come from Skrodzka,
Hojan and Proksza (2006) and are real; every other drum here is the general
membrane scaling law with frequencies chosen to sit where that size of drum
sits. Those are engineering numbers, not findings, and they are marked so.

**Why a hard hit sounds different rather than merely louder.** Each mode
carries a `tilt`, and its amplitude follows `velocity ** (1 + tilt)`. High
modes get a bigger tilt, so striking harder pulls the spectrum up as well as
out - which is the thing a three-layer sample library approximates with three
steps and a crossfade. The per-hit jitter on frequency and decay is the other
half: a real drummer never hits the same spot twice, and nothing here needs a
round-robin because no two strikes are the same to begin with.

**The cymbals are the weakest part of this kit, and that is known rather than
discovered.** Skare and Abel (DAFx-19) put a convincing cymbal wash at
"hundreds or even thousands" of modes, and run 1600 to 1900 per cymbal on a
GPU; they also name what a linear bank cannot do at any mode count - the
attack "clearly lacks the interesting 'bloom'" as energy cascades up through
the plate's nonlinear regime. This bank holds 64 modes on a microcontroller.
So the ride and the crash are *credible*, they are not photoreal, and the
dossier's section 6 is what to judge them against rather than a real crash.

The excitation is deliberately plain. A resonator bank is linear, so exciting
mode *i* with a burst shaped to have amplitude A at that frequency is the same
as exciting it with a flat burst and folding A into the mode's gain - which is
where all of the shaping lives. One noise burst therefore serves every drum,
and two drums struck in the same block share it, which is both cheap and
closer to true than giving them independent noise.
"""

NAME = 'acoustickit'
DISPLAY_NAME = 'Acoustic Kit'
CATEGORIES = ('Drum',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = (
    "Level", "Hardness", "Kick Tune", "Kick Decay", "Kick Level",
    "Snare Tune", "Snare Snap", "Snare Level", "Tom Tune", "Tom Decay",
    "Tom Level", "Hat Decay", "Hat Level", "Ride Decay", "Crash Decay",
    "Cymbal Level",
)
MACRO_MODES = {
    0: "UNIPOLAR",
    1: "UNIPOLAR",
    2: "UNIPOLAR",
    3: "UNIPOLAR",
    4: "UNIPOLAR",
    5: "UNIPOLAR",
    6: "UNIPOLAR",
    7: "UNIPOLAR",
    8: "UNIPOLAR",
    9: "UNIPOLAR",
    10: "UNIPOLAR",
    11: "UNIPOLAR",
    12: "UNIPOLAR",
    13: "UNIPOLAR",
    14: "UNIPOLAR",
    15: "UNIPOLAR",
}

#: GM percussion, and only the notes this kit actually has a voice for. A hit
#: it has no voice for makes no sound, which is the library's rule: a pattern
#: with a splash in it loses the splash rather than turning into noise.
NOTE_MAP = (
    (35, "Acoustic Bass Drum"),
    (36, "Bass Drum 1"),
    (37, "Side Stick"),
    (38, "Acoustic Snare"),
    (41, "Low Floor Tom"),
    (42, "Closed Hi Hat"),
    (44, "Pedal Hi-Hat"),
    (45, "Low Tom"),
    (46, "Open Hi-Hat"),
    (47, "Low-Mid Tom"),
    (48, "Hi-Mid Tom"),
    (49, "Crash Cymbal 1"),
    (51, "Ride Cymbal 1"),
    (53, "Ride Bell"),
)

#: Level macros sit at 127 by default. The headroom a kit needs for several
#: drums at once is kept in `_TARGET_PEAK` below, once, rather than a second
#: time in every patch - a patch that quietly halved the kit would just make
#: the whole instrument sound timid next to the machines beside it.
PATCHES = {
    0: ("Studio Kit", (127, 64, 64, 64, 127, 64, 64, 127, 64, 64, 127, 64,
                       127, 64, 64, 127)),
    1: ("Dry and Close", (127, 80, 64, 34, 127, 64, 80, 127, 64, 38, 127, 40,
                          127, 40, 44, 112)),
    2: ("Big Room", (127, 70, 58, 96, 127, 58, 58, 127, 58, 104, 127, 84,
                     127, 96, 110, 127)),
    3: ("Jazz Brushes", (118, 34, 70, 54, 108, 70, 40, 112, 70, 60, 112, 54,
                         120, 80, 74, 127)),
    4: ("Hard Hitter", (127, 118, 60, 70, 127, 60, 110, 127, 60, 70, 127, 60,
                        127, 70, 74, 120)),
}

import math

import synthio

from audioinstruments._support import FALL, make_table, noise_table
from audioinstruments._support import Instrument
from audioinstruments import _support

import audiomixer
import audiomodal
import audioroute

#: ln(1000): a mode's decay is its 60 dB time, and a published modal damping
#: ratio converts as T60 = ln(1000) / (zeta * 2 * pi * f).
_LN1000 = 6.907755278982137

SINE = make_table(((1, 1.0),))
#: A touch of second and third: a real drum head's fundamental is not a
#: bare sine, and a bare sine reads as a synth tom.
BODY = make_table(((1, 1.0), (2, 0.18), (3, 0.06)))
NOISE = noise_table(seed=515151)

#: Ideal circular membrane, relative to the (0,1) mode. Real drums are pulled
#: toward harmonic by air loading and shell coupling; where this file uses
#: these ratios it is using theory, not a measurement of a drum.
_MEMBRANE = (1.000, 1.594, 2.136, 2.296, 2.653, 2.918)


def _damped(rows):
    """Published `(frequency Hz, damping %, relative amplitude, tilt)` rows to
    the bank's `(frequency, decay seconds, gain, tilt)`."""
    out = []
    for frequency, damping, gain, tilt in rows:
        zeta = damping / 100.0
        decay = _LN1000 / (zeta * 2.0 * math.pi * frequency)
        out.append((frequency, decay, gain, tilt))
    return tuple(out)


def _membrane(f0, decay, count=6, decay_power=1.6, tilt0=0.35, tilt_step=0.22):
    """A drum head from theory: the ideal ratios, with higher modes decaying
    faster and following velocity harder."""
    out = []
    for index in range(count):
        ratio = _MEMBRANE[index]
        out.append((f0 * ratio, decay / (ratio ** decay_power),
                    1.0 / (1.0 + 1.6 * index), tilt0 + tilt_step * index))
    return tuple(out)


def _attack(frequencies, decay, gain, tilt=2.4):
    """The stick or beater on the head. Same primitive as a body mode - a
    resonator with a very short decay - so it costs the bank nothing extra,
    and its steep tilt is most of what makes a hard hit read as hard."""
    return tuple((frequency, decay, gain / (1.0 + 0.6 * index), tilt)
                 for index, frequency in enumerate(frequencies))


# --------------------------------------------------------------- the drums --
#
# MEASURED. Skrodzka, Hojan & Proksza (2006), a 14" snare: six modes with
# their modal damping ratios. Note what it says about decay - the (0,1)
# fundamental damps at 5.07% and dies in about a tenth of a second while the
# modes above it damp near 1% and ring three times longer. A snare is a thud
# with a ring on top, not a ring that fades evenly, and a model that made
# decay fall off smoothly with frequency would have got this backwards.
_SNARE_BODY = _damped((
    (224.0, 5.07, 1.00, 0.30),
    (322.0, 1.10, 0.62, 0.45),
    (457.0, 1.07, 0.44, 0.60),
    (566.0, 1.16, 0.32, 0.75),
    (616.0, 1.24, 0.26, 0.90),
    (734.0, 0.77, 0.20, 1.05),
))

#: What a bank cannot be: pitch-dropping fundamentals and noise.
#:
#: Each row is one `synthio` voice played beside the bank rather than through
#: it, because neither of these is a resonance. The fields are
#: `(waveform, frequency, filter mode, filter Hz, Q, attack, decay, amplitude,
#: bend rate, bend octaves, tilt)` - `tilt` following velocity the same way a
#: mode's does, so the layers brighten with a hard hit as the bank does.
#:
#: `frequency` is in hertz except for a NOISE row, where it is set to the rate
#: that reads the table one sample per sample and the value here is ignored.
_LOW, _BAND, _HIGH = 0, 2, 1

LAYERS = {
    # The kick, properly. A fundamental at 52 Hz bent up almost an octave at
    # the strike and falling back over about 60 ms - which is the whole of why
    # a kick reads as a kick - plus a low-passed beater knock. Both shapes are
    # the TR-909's, whose own bass drum is a FALL-bent sine and a low-passed
    # noise click, because the physics it was imitating is the physics here.
    "kick": (
        ("body", BODY, 50.0, _LOW, 230.0, 0.9, 0.002, 0.36, 1.00, 22.0, 1.20,
         0.25),
        # Low-passed at 2.4 kHz: a knock rather than a click. The TR-909's own
        # bass drum note warns that a high-passed click smears over a kick's
        # very dark spectrum, and that holds here - but 1.4 kHz was muffled
        # enough that the drum lost most of its velocity brightness (the
        # attack centroid spread only 2.7x across velocity against 4.1x at
        # 2.4 kHz), while the whole hit's centroid moves only 287 -> 292 Hz
        # between the two. Dark is kept; the knock is audible again.
        ("beater", NOISE, None, _LOW, 2400.0, 1.0, 0.0008, 0.016, 0.38, 0.0,
         0.0, 2.2),
    ),
    # The snare's wires: band-passed noise, low Q so it is broad, and lasting
    # a fifth of a second rather than the 60 ms two resonators managed. This
    # is the layer whose absence made the drum a tom.
    "snare": (
        ("wires", NOISE, None, _BAND, 3200.0, 0.55, 0.0006, 0.26, 0.80, 0.0,
         0.0, 1.1),
        ("stick", NOISE, None, _BAND, 5200.0, 0.9, 0.0004, 0.012, 0.45, 0.0,
         0.0, 2.3),
    ),
    # The side stick is nearly all click; give it one.
    "sidestick": (
        ("click", NOISE, None, _BAND, 2600.0, 1.2, 0.0004, 0.010, 0.55, 0.0,
         0.0, 2.0),
    ),
}

#: `voice -> mode table`. Every frequency below except the snare's is an
#: engineering number: the membrane law placed where that size of drum sits.
VOICES = {
    # NOT MEASURED. 22" kick. The bank now carries only the shell's own
    # inharmonic colour, briefly: the voice is the pitch-dropping fundamental
    # in LAYERS below. The six long membrane modes that used to be here, at
    # 92 to 169 Hz with decays of a quarter-second, were what made it a tom -
    # a real kick is nearly all fundamental within 30 ms, and measured at
    # 120 ms this one had 0.3% of its energy left between 80 and 250 Hz while
    # sounding like it had far more.
    "kick": ((92.0, 0.075, 0.30, 0.6), (137.0, 0.045, 0.18, 0.9)),
    # MEASURED body (above). The wires are NOT modes and are not here any
    # more - see LAYERS. The head is real and stays; what changed is that it
    # is no longer the whole drum.
    "snare": _SNARE_BODY,
    # NOT MEASURED. A stick on the rim: almost all click, almost no body.
    "sidestick": ((680.0, 0.045, 1.00, 1.2), (1950.0, 0.022, 0.70, 1.8),
                  (4200.0, 0.012, 0.45, 2.2)),
    # NOT MEASURED. Four toms, 10" to 16", ringing longer as they get bigger.
    "tom_hi": _membrane(180.0, 0.60, count=5, decay_power=1.5)
              + _attack((2600.0,), 0.008, 0.26),
    "tom_himid": _membrane(146.0, 0.70, count=5, decay_power=1.5)
                 + _attack((2500.0,), 0.008, 0.26),
    "tom_lomid": _membrane(122.0, 0.82, count=5, decay_power=1.5)
                 + _attack((2400.0,), 0.008, 0.26),
    "tom_lo": _membrane(86.0, 1.10, count=5, decay_power=1.5)
              + _attack((2000.0,), 0.009, 0.24),
    # NOT MEASURED, and see the module docstring: a linear bank of this width
    # is not going to be a convincing cymbal, and these are chosen to be
    # credible in a mix rather than to imitate a particular instrument.
    "ride": ((522.0, 2.10, 1.00, 0.5), (1180.0, 1.80, 0.55, 0.9),
             (2340.0, 1.50, 0.40, 1.3), (3820.0, 1.20, 0.30, 1.7),
             (5600.0, 0.90, 0.22, 2.1)),
    "ridebell": ((905.0, 1.60, 1.00, 0.6), (2180.0, 1.30, 0.70, 1.0),
                 (3640.0, 1.05, 0.48, 1.4), (5900.0, 0.80, 0.32, 1.8)),
    "crash": ((410.0, 2.60, 0.55, 0.5), (980.0, 2.40, 0.70, 0.9),
              (1760.0, 2.20, 0.85, 1.2), (2910.0, 1.95, 1.00, 1.5),
              (4300.0, 1.65, 0.85, 1.8), (6100.0, 1.30, 0.62, 2.1),
              (8200.0, 0.95, 0.40, 2.4)),
}

#: The hi-hat lives in its own bank so that a strike can choke what was
#: ringing. Two cymbals clamped together are one instrument in three states,
#: and an open hat that went on ringing under a closed one would be the most
#: obvious thing in the kit to get wrong.
HAT_VOICES = {
    "hat_closed": ((3400.0, 0.055, 1.00, 1.4), (5100.0, 0.045, 0.80, 1.7),
                   (7300.0, 0.035, 0.60, 2.0), (9900.0, 0.026, 0.40, 2.3)),
    "hat_pedal": ((3100.0, 0.038, 1.00, 1.2), (5400.0, 0.030, 0.70, 1.5),
                  (8100.0, 0.022, 0.45, 1.8)),
    "hat_open": ((3300.0, 0.95, 1.00, 1.3), (4900.0, 0.85, 0.85, 1.6),
                 (6800.0, 0.72, 0.68, 1.9), (8600.0, 0.58, 0.50, 2.2),
                 (11200.0, 0.42, 0.34, 2.5)),
}

#: `pitch -> voice`. Sharing is by construction rather than by budget: 45 and
#: 47 are different toms, and every note here has its own voice.
PITCH_VOICE = {
    35: "kick", 36: "kick", 37: "sidestick", 38: "snare",
    41: "tom_lo", 45: "tom_lomid", 47: "tom_himid", 48: "tom_hi",
    49: "crash", 51: "ride", 53: "ridebell",
    42: "hat_closed", 44: "hat_pedal", 46: "hat_open",
}


#: How far one strike moves a mode from where the table put it, as a fraction.
#: This is the round-robin, and it is free here: a sample library needs several
#: captures per drum to stop a repeated hit sounding mechanical, and a bank
#: only needs its poles to land somewhere slightly different each time. Small
#: enough that no single hit is out of tune - 1.2% is a fifth of a semitone -
#: and audible immediately on a fast snare roll, which is where the machine-gun
#: effect lives.
_JITTER = 0.012

#: What one drum at full velocity, trim 1.0, is aimed at. Well under full
#: scale because a kit plays several voices at once: a kick, a snare and an
#: open hat together are three of these summing into one output, and the bank
#: quantises once at the end where anything over the rail is simply lost.
_TARGET_PEAK = 14000.0

#: One scale over the whole kit, bank and layers alike, so the balance between
#: them is set once and the headroom is set once somewhere else. It exists
#: because the layers arrived after the bank was already levelled and pushed
#: the kick and snare about 5 dB up, which is exactly the amount that made
#: eight drums at full velocity clip. Scaling both paths together keeps the
#: balance that was tuned by ear and by measurement; scaling only one would
#: have quietly retuned it.
_KIT_LEVEL = 0.58

#: MEASURED, here, not guessed: the peak each voice reaches at unit mode gains
#: from one stick burst, rendered at low gain and scaled up because the bank is
#: linear. The first attempt normalised by the *sum* of a voice's mode gains
#: instead, and it was wrong by 11 dB across the kit - the ride bell came out
#: louder than the kick - because a sum says nothing about how the modes phase
#: against each other. High modes align inside the excitation window and low
#: ones do not.
#:
#: TWO TABLES, because one is not enough and the first version of this said it
#: was. A resonator's response to a burst depends on its bandwidth relative to
#: the sample rate, so the same voice does not peak in the same place at 24 kHz
#: as at 48 kHz - and not by a common factor either. Measured ratios across the
#: kit run from 0.55 on the pedal hat to 1.56 on the ride, which on a board
#: running at 24 kHz put the snare 4.3 dB under the kick where at 48 kHz they
#: were level. Rates between the two interpolate; outside them, the nearer
#: table is used unchanged.
_UNIT_PEAK_48K = {
    "crash": 546200.0, "hat_closed": 228000.0, "hat_open": 381200.0,
    "hat_pedal": 321200.0, "kick": 112000.0, "ride": 198800.0,
    "ridebell": 382600.0, "sidestick": 141600.0, "snare": 234200.0,
    "tom_hi": 121000.0, "tom_himid": 128200.0, "tom_lo": 112200.0,
    "tom_lomid": 128400.0,
}
_UNIT_PEAK_24K = {
    "crash": 476000.0, "hat_closed": 237400.0, "hat_open": 392800.0,
    "hat_pedal": 176200.0, "kick": 121600.0, "ride": 311000.0,
    "ridebell": 265000.0, "sidestick": 117200.0, "snare": 158200.0,
    "tom_hi": 141800.0, "tom_himid": 145400.0, "tom_lo": 122800.0,
    "tom_lomid": 130200.0,
}


def _unit_peak(voice, rate):
    if rate <= 24000:
        return _UNIT_PEAK_24K[voice]
    if rate >= 48000:
        return _UNIT_PEAK_48K[voice]
    blend = (rate - 24000.0) / 24000.0
    return (_UNIT_PEAK_24K[voice] * (1.0 - blend)
            + _UNIT_PEAK_48K[voice] * blend)


#: Where each voice sits in the kit once they are all the same loudness -
#: taste rather than measurement, and separated from `_UNIT_PEAK` on purpose
#: so that the two can be argued about one at a time. A side stick is a quiet
#: sound and a kick is not; the level macros move a whole group, and this
#: moves one drum inside its group.
_TRIM = {
    "kick": 1.00, "snare": 0.92, "sidestick": 0.55,
    "tom_hi": 0.85, "tom_himid": 0.85, "tom_lomid": 0.85, "tom_lo": 0.85,
    "hat_closed": 0.50, "hat_pedal": 0.35, "hat_open": 0.60,
    "ride": 0.50, "ridebell": 0.62, "crash": 0.80,
}

def _norms(rate):
    """One multiply per mode at strike time instead of three."""
    return {name: _KIT_LEVEL * _TARGET_PEAK * _TRIM[name]
            / _unit_peak(name, rate) for name in _TRIM}


def create(sample_rate, channel_count=2, transport=None):
    SR = sample_rate
    NOISE_HZ = SR / 8192.0
    NORM = _norms(SR)
    _FILTER_MODES = (synthio.FilterMode.LOW_PASS,
                     synthio.FilterMode.HIGH_PASS,
                     synthio.FilterMode.BAND_PASS)
    synth = _support.synthesizer(SR, channel_count)

    master_level = 0.8
    hardness = 0.5
    kick_tune, kick_decay, kick_level = 1.0, 1.0, 0.8
    snare_tune, snare_snap, snare_level = 1.0, 0.5, 0.8
    tom_tune, tom_decay, tom_level = 1.0, 1.0, 0.8
    hat_decay, hat_level = 1.0, 0.8
    ride_decay, crash_decay, cymbal_level = 1.0, 1.0, 0.8

    # Lay the main bank out once: every voice gets a contiguous run of mode
    # slots and keeps it for the life of the instrument. Nothing is allocated
    # at strike time, which is the same rule every drum machine here follows
    # for the same reason - a sequencer cannot wait for a malloc mid-bar.
    def layout(table):
        slots, flat = {}, []
        for name in sorted(table):
            slots[name] = (len(flat), len(flat) + len(table[name]))
            for frequency, decay, _gain, _tilt in table[name]:
                flat.append((frequency, decay))
        return slots, tuple(flat)

    MAIN_SLOTS, MAIN_FLAT = layout(VOICES)
    HAT_SLOTS, HAT_FLAT = layout(HAT_VOICES)
    main_modes, hat_modes = len(MAIN_FLAT), len(HAT_FLAT)

    main_bank = audiomodal.Bank(modes=main_modes, sample_rate=SR,
                                channel_count=channel_count)
    hat_bank = audiomodal.Bank(modes=hat_modes, sample_rate=SR,
                               channel_count=channel_count)

    # One excitation, split to both banks. A bank is linear, so what a strike
    # puts into each mode is the mode's own gain - the burst only has to carry
    # energy everywhere, not carry a shape.
    split = audioroute.Splitter(_support.node(synth), taps=2)
    main_bank.play(split.tap(0))
    hat_bank.play(split.tap(1))

    # A second synthesizer, played straight into the mixer rather than into a
    # bank. It has to be a second one: the first is the banks' excitation, and
    # anything pressed there would be resonated rather than heard.
    direct = _support.synthesizer(SR, channel_count)

    mixer = audiomixer.Mixer(voice_count=3, buffer_size=2048,
                             channel_count=channel_count, sample_rate=SR,
                             bits_per_sample=16, samples_signed=True)
    mixer.voice[0].play(main_bank, loop=True)
    mixer.voice[1].play(hat_bank, loop=True)
    mixer.voice[2].play(_support.node(direct), loop=True)
    mixer.voice[0].level = 1.0
    mixer.voice[1].level = 1.0
    mixer.voice[2].level = 1.0

    # Fixed circuits again: one permanent Note per layer, built once and
    # retriggered in place, so a strike allocates nothing.
    layer_notes = {}
    for voice, rows in LAYERS.items():
        notes = []
        for (_name, waveform, frequency, mode, cutoff, q, attack, decay,
             amplitude, bend_rate, bend_oct, tilt) in rows:
            note = synthio.Note(
                NOISE_HZ if frequency is None else frequency,
                waveform=waveform, amplitude=0.0,
                envelope=synthio.Envelope(
                    attack_time=attack, decay_time=decay,
                    release_time=decay * 0.5, attack_level=1.0,
                    sustain_level=0.0))
            note.filter = synthio.Biquad(_FILTER_MODES[mode], cutoff, Q=q)
            notes.append(note)
        layer_notes[voice] = tuple(notes)

    # The stick: four permanent Notes, used in rotation. Its envelope is about
    # four milliseconds long, which is short against every decay in the kit, so
    # what the ear hears is the bank and not the burst.
    #
    # Four rather than one, and this was measured rather than assumed. Pressing
    # a single Note again while synthio still had it does NOT cleanly restart
    # its envelope: the first strike of a fresh kit came out with a 1779 Hz
    # attack centroid and every strike after it with 1040 Hz, so the second
    # snare in any bar was audibly duller than the first and stayed that way.
    # Rotating gives each burst a Note that has finished, and the release is
    # 1.6 ms against a rotation of four, so nothing is ever reused in flight.
    STICKS = tuple(
        synthio.Note(
            NOISE_HZ, waveform=NOISE, amplitude=1.0,
            envelope=synthio.Envelope(attack_time=0.0004, decay_time=0.0022,
                                      release_time=0.0016, attack_level=1.0,
                                      sustain_level=0.0))
        for _ in range(4))
    stick_at = [0]

    # A strike counter through a plain LCG, so the jitter is different every
    # hit and identical every render. A drum whose renders did not reproduce
    # could not be held to a digest by anything downstream.
    entropy = [0x2F6E2B1]

    def wobble():
        entropy[0] = (entropy[0] * 1103515245 + 12345) & 0x7FFFFFFF
        return 1.0 + _JITTER * ((entropy[0] >> 8 & 0xFFFF) / 32768.0 - 1.0)

    def tune_for(voice):
        if voice == "kick":
            return kick_tune
        if voice in ("snare", "sidestick"):
            return snare_tune
        if voice.startswith("tom"):
            return tom_tune
        return 1.0

    def decay_for(voice):
        if voice == "kick":
            return kick_decay
        if voice.startswith("tom"):
            return tom_decay
        if voice.startswith("hat"):
            return hat_decay
        if voice in ("ride", "ridebell"):
            return ride_decay
        if voice == "crash":
            return crash_decay
        return 1.0

    def level_for(voice):
        if voice == "kick":
            return kick_level
        if voice in ("snare", "sidestick"):
            return snare_level
        if voice.startswith("tom"):
            return tom_level
        if voice.startswith("hat"):
            return hat_level
        return cymbal_level

    def load(bank, slots, table, voice, velocity):
        """Arm one voice and silence the rest, then the burst plays only it.

        Setting another voice's gain to zero does NOT stop it ringing: the
        gain is how new signal enters a mode, and a mode already in motion
        carries on decaying from its own state. That is the whole reason one
        bank can hold a kit - a crash goes on sounding underneath the next
        four kicks without any of them feeding it.
        """
        start, stop = slots[voice]
        flat = MAIN_FLAT if slots is MAIN_SLOTS else HAT_FLAT
        tune = tune_for(voice)
        stretch = decay_for(voice)
        gain = level_for(voice)
        # Hardness bends how much the tilt bites: at 0 every mode follows
        # velocity linearly and the kit is even, at 1 the high modes pull
        # away hard and it reads as a heavier stick.
        bite = 0.25 + 1.5 * hardness
        snap = 1.0
        for index, (frequency, decay, amplitude, tilt) in enumerate(table):
            if voice == "snare" and frequency >= 1500.0:
                snap = 0.4 + 1.2 * snare_snap
            scaled = (amplitude * (velocity ** (1.0 + tilt * bite))
                      * gain * NORM[voice])
            bank.set_mode(start + index, frequency * tune * wobble(),
                          decay * stretch * wobble(), scaled * snap)
            snap = 1.0
        for index in range(0, start):
            _silence(bank, flat, index)
        for index in range(stop, bank.modes):
            _silence(bank, flat, index)

    def _silence(bank, flat, index):
        """Mute a mode without stopping it.

        The pole has to go back in unchanged. Setting the frequency to zero
        here as well - which is the obvious way to write "off" - takes the
        recursion with it, and every other drum in the bank stops dead the
        instant this one is struck rather than ringing on underneath. Measured
        when it was wrong: a whisper-quiet kick cut a ringing crash from 7584
        to 61.
        """
        frequency, decay = flat[index]
        bank.set_mode(index, frequency, decay, 0.0)

    def strike(pitch, velocity):
        voice = PITCH_VOICE.get(pitch)
        if voice is None:
            return
        if voice in HAT_VOICES:
            # Closing a hi-hat silences what the open one was doing. This is
            # the choke, and it is why the hat has a bank to itself.
            hat_bank.clear()
            load(hat_bank, HAT_SLOTS, HAT_VOICES[voice], voice, velocity)
        else:
            load(main_bank, MAIN_SLOTS, VOICES[voice], voice, velocity)
        rows = LAYERS.get(voice)
        if rows is not None:
            gain = level_for(voice)
            bite = 0.25 + 1.5 * hardness
            for row, note in zip(rows, layer_notes[voice]):
                (_name, _wave, frequency, _mode, _cut, _q, _att, _dec,
                 amplitude, bend_rate, bend_oct, tilt) = row
                note.amplitude = (amplitude * gain * _KIT_LEVEL
                                  * (velocity ** (1.0 + tilt * bite)))
                if bend_oct:
                    # A fresh one-shot LFO per strike: `once=True` means it
                    # runs down and stays there, so a retrigger needs a new
                    # one. This is the only allocation a strike makes, and it
                    # is two small objects on the drums that have a bend.
                    note.bend = synthio.LFO(
                        waveform=FALL, once=True, rate=bend_rate,
                        scale=bend_oct * (0.55 + 0.45 * velocity),
                        interpolate=True)
                direct.release(note)
                direct.press(note)

        note = STICKS[stick_at[0]]
        stick_at[0] = (stick_at[0] + 1) % len(STICKS)
        synth.release(note)
        synth.press(note)

    def handle_event(event_type, channel, note_id, data0, value0, value1,
                     sample_position):
        nonlocal master_level, hardness, kick_tune, kick_decay, kick_level
        nonlocal snare_tune, snare_snap, snare_level, tom_tune, tom_decay
        nonlocal tom_level, hat_decay, hat_level, ride_decay, crash_decay
        nonlocal cymbal_level
        if event_type == 1 and value0 > 0.0:
            strike(data0, max(value0, 0.02))
        elif event_type == 6:
            value = value0
            if data0 == 0:
                master_level = value
                mixer.voice[0].level = value
                mixer.voice[1].level = value
            elif data0 == 1:
                hardness = value
            elif data0 == 2:
                kick_tune = 0.5 + value
            elif data0 == 3:
                kick_decay = 0.25 + 1.75 * value
            elif data0 == 4:
                kick_level = value
            elif data0 == 5:
                snare_tune = 0.5 + value
            elif data0 == 6:
                snare_snap = value
            elif data0 == 7:
                snare_level = value
            elif data0 == 8:
                tom_tune = 0.5 + value
            elif data0 == 9:
                tom_decay = 0.25 + 1.75 * value
            elif data0 == 10:
                tom_level = value
            elif data0 == 11:
                hat_decay = 0.25 + 1.75 * value
            elif data0 == 12:
                hat_level = value
            elif data0 == 13:
                ride_decay = 0.25 + 1.75 * value
            elif data0 == 14:
                crash_decay = 0.25 + 1.75 * value
            elif data0 == 15:
                cymbal_level = value

    # NOT SCHEDULABLE, and the reason is `strike()` above: a hit here is
    # `bank.set_mode()` on a modal bank that is already running, which injects
    # the energy the moment it is called. That is a C state change, not a
    # press, so no queue can hold it back - and deferring only the two
    # `direct.press()` calls would split one drum in half. See
    # docs/spikes/live-audio-path-sequenced.md.
    return Instrument(synth, handle_event, PATCHES, MACRO_LABELS,
                      output=mixer, transport=transport, note_map=NOTE_MAP,
                      schedulable=False)
