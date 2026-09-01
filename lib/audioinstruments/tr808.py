"""Roland TR-808 Rhythm Composer."""

NAME = 'tr808'
DISPLAY_NAME = 'TR-808'
CATEGORIES = ('Drum',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = (
    "Level", "Accent", "BD Tune", "BD Decay", "BD Tone", "SD Tune",
    "SD Snappy", "SD Tone", "Low Tom", "Mid Tom", "Hi Tom", "Clap Decay",
    "Cowbell", "Cymbal Decay", "CH Decay", "OH Decay",
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

# Patch 0 is the sound this instrument's defaults describe, so a fresh
# instance and patch 0 are the same thing - create() applies it. A macro
# a caller does not set resolves here rather than to the middle of its
# range.
PATCHES = {
    0: ("Default", (102, 64, 51, 59, 67, 56, 64, 64, 74, 71, 71, 67, 68, 76,
                 58, 85)),
}

NOTE_MAP = (
    (36, "Bass Drum"),
    (38, "Snare"),
    (37, "Rimshot"),
    (39, "Clap"),
    (41, "Low Tom"),
    (45, "Mid Tom"),
    (48, "Hi Tom"),
    (42, "Closed Hat"),
    (46, "Open Hat"),
    (49, "Cymbal"),
    (56, "Cowbell"),
    (75, "Claves"),
    (62, "Conga Hi"),
    (63, "Conga Mid"),
    (64, "Conga Lo"),
    (70, "Maracas"),
)

import synthio

from audioinstruments._support import (
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, FALL, logmap,
    make_table, noise_table,
)
from audioinstruments._support import Instrument

SINE = make_table(((1, 1.0),))
TRIANGLE = make_table([(n, (1.0 / (n*n)) * (-1)**((n-1)//2)) for n in range(1, 11, 2)])
SQUARE = make_table([(n, 1.0 / n) for n in range(1, 23, 2)])
NOISE = noise_table(seed=808080)

# The real 808's hi-hats/cymbals come from six square-wave oscillators mixed
# together, not noise - build that same inharmonic square bank here (ratios
# approximate the real circuit's ~205/304/369/421/497/619 Hz bank) and drive
# each partial with a few of its own odd harmonics for square-wave grit.
_METAL_TONES = ((10, 1.0), (15, 0.85), (18, 0.75), (21, 0.65), (24, 0.55), (30, 0.45))
_METAL_PARTS = [(m * h, a * (1.0 / h)) for m, a in _METAL_TONES for h in (1, 3, 5)]
METAL = make_table(_METAL_PARTS, length=2048)
METAL_HZ = 90.0

# The cowbell's two-oscillator pair in one wavetable: the hardware ratio
# is 800/540 = 1.48, within 1.3% of 3:2, so harmonics 2 and 3 of a half-
# frequency fundamental carry the pair in a single core channel. The
# ratio rounds to exactly 1.5 as a result - a hair cleaner than the real
# pair's beat - which is the price of the one-slot cowbell that keeps
# the whole kit at 13 resident notes (see the circuits comment below).
COWBELL = make_table(((2, 1.0), (3, 0.72)))


def create(sample_rate, channel_count=2, transport=None):
    SR = sample_rate
    NOISE_HZ = SR / 8192.0
    synth = synthio.Synthesizer(sample_rate=SR, channel_count=channel_count)

    # Master params
    master_level = 0.8
    accent_level = 0.5

    # BD params
    bd_tune = 50.0
    bd_decay = 0.4
    bd_tone = 300.0

    # SD params
    sd_tune = 180.0
    sd_snappy = 0.5
    sd_tone = 2000.0

    # Toms
    lt_tune = 90.0
    mt_tune = 130.0
    ht_tune = 180.0

    # Others
    clap_decay = 0.3
    cowbell_tune = 620.0
    cym_decay = 0.8
    ch_decay = 0.05
    oh_decay = 0.4

    # Conga tunings: fixed relative to the paired tom channel (the
    # hardware's tom/conga switch selects, it does not add a knob), set
    # from the cross-check pack's per-conga medians (HC 366 / MC 258 /
    # LC 194 Hz).
    hc_tune = 360.0
    mc_tune = 258.0
    lc_tune = 190.0

    # Fixed circuits, exactly like the hardware: every voice is a
    # permanent set of Note objects retriggered in place (synthio
    # restarts a pressed note on press). Nothing new is ever allocated
    # at strike time and no release tail ever occupies a core channel.
    # The synthio core keeps at most 14 simultaneous notes (verified
    # identical on CPython, MicroPython, and the CircuitPython oracle)
    # and silently retires the OLDEST beyond that - the bass drum, in a
    # full-kit hit. The kit resides at 13 notes, deliberately one below
    # that cap: the CPython extension additionally mishandles an at-cap
    # re-press (it evicts a bystander and leaks a slot - a core
    # divergence from the oracle, filed as audioif#8), and at 13 every
    # retrigger stays below the cap on every runtime. The shared
    # circuits are the hardware's own sharing: tom/conga, claves/
    # rimshot, maracas/clap, and open/closed hat each ride one circuit
    # and choke each other by retrigger, exactly as the real machine's
    # switch and choke behavior did.
    circuits = {}

    def circuit(name, waveforms):
        notes = circuits.get(name)
        if notes is None:
            notes = tuple(synthio.Note(440.0, waveform=w, amplitude=0.0)
                          for w in waveforms)
            circuits[name] = notes
        return notes

    #: Which circuit a MIDI pitch drives - the note-off path releases by
    #: circuit, and the alternates on one line share that circuit.
    PITCH_CIRCUIT = {
        35: "bd", 36: "bd", 38: "sd", 40: "sd",
        37: "rim", 75: "rim", 39: "cm", 70: "cm",
        41: "tom_lo", 43: "tom_lo", 64: "tom_lo",
        45: "tom_mid", 47: "tom_mid", 63: "tom_mid",
        48: "tom_hi", 50: "tom_hi", 62: "tom_hi",
        42: "hat", 44: "hat", 46: "hat",
        49: "cym", 51: "cym", 57: "cym", 59: "cym",
        56: "cb",
    }

    def handle_event(event_type, channel, note_id, data0, value0, value1, sample_position):
        nonlocal master_level, accent_level, bd_tune, bd_decay, bd_tone
        nonlocal sd_tune, sd_snappy, sd_tone, lt_tune, mt_tune, ht_tune
        nonlocal clap_decay, cowbell_tune, cym_decay, ch_decay, oh_decay

        if event_type == EVENT_NOTE_ON and value0 > 0.0:
            pitch = data0
            vel = value0
            amp = master_level * (vel + accent_level * (1.0 if vel > 0.8 else 0.0))

            # BD (35, 36)
            if pitch in (35, 36):
                body, click = circuit("bd", (SINE, NOISE))
                body.frequency = bd_tune
                body.envelope = synthio.Envelope(attack_time=0.001, decay_time=bd_decay, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                # Bridged-T behavior, re-derived from the DAFx-14 analysis
                # (never copied): the retriggering pulse briefly raises the
                # center frequency by more than an octave - the attack
                # click - and leakage then lets the pitch sigh down onto
                # the settled fundamental. Two one-shot falls, summed.
                # LFOs tick at control rate (one value per 256-sample
                # block, advanced BEFORE sampling), so a fall faster than
                # ~2 blocks never reaches the audio; rate=45/scale=1.65 is
                # the block-honest translation whose rendered first
                # half-cycle clears a full octave over the settled pitch.
                jump = synthio.LFO(waveform=FALL, once=True, rate=45.0, scale=1.65, interpolate=True)
                sigh = synthio.LFO(waveform=FALL, once=True, rate=4.0, scale=0.11, interpolate=True)
                body.bend = synthio.Math(synthio.MathOperation.SUM, jump, sigh, 0.0)
                body.filter = synthio.Biquad(synthio.FilterMode.LOW_PASS, bd_tone, Q=0.8)
                body.amplitude = amp
                click.frequency = NOISE_HZ
                click.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.01, release_time=0.01, attack_level=1.0, sustain_level=0.0)
                click.filter = synthio.Biquad(synthio.FilterMode.HIGH_PASS, 3000.0, Q=0.7)
                click.amplitude = amp * 0.5
                synth.press(body)
                synth.press(click)

            # SD (38, 40)
            elif pitch in (38, 40):
                body, snare = circuit("sd", (SINE, NOISE))
                body.frequency = sd_tune
                body.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.1, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                body.bend = synthio.LFO(waveform=FALL, once=True, rate=30.0, scale=0.2, interpolate=True)
                body.amplitude = amp * 1.1
                snare.frequency = NOISE_HZ
                snare.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.2, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                snare.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, sd_tone, Q=1.4)
                snare.amplitude = amp * sd_snappy
                synth.press(body)
                synth.press(snare)

            # Toms and congas (one circuit per line; the hardware's
            # tom/conga switch selects which sound the line makes)
            elif pitch in (41, 43, 64, 45, 47, 63, 48, 50, 62):
                if pitch in (41, 43, 64):
                    name, tom_tune, conga_tune = "tom_lo", lt_tune, lc_tune
                elif pitch in (45, 47, 63):
                    name, tom_tune, conga_tune = "tom_mid", mt_tune, mc_tune
                else:
                    name, tom_tune, conga_tune = "tom_hi", ht_tune, hc_tune
                is_conga = pitch in (62, 63, 64)
                (note,) = circuit(name, (SINE,))
                if is_conga:
                    note.frequency = conga_tune
                    decay = {"tom_lo": 0.24, "tom_mid": 0.13, "tom_hi": 0.14}[name]
                    note.envelope = synthio.Envelope(attack_time=0.001, decay_time=decay, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                    note.bend = synthio.LFO(waveform=FALL, once=True, rate=25.0, scale=0.04, interpolate=True)
                    note.amplitude = amp * 0.9
                else:
                    note.frequency = tom_tune
                    note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.3, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                    note.bend = synthio.LFO(waveform=FALL, once=True, rate=15.0, scale=0.1, interpolate=True)
                    note.amplitude = amp
                synth.press(note)

            # Hats (42, 44, 46) - one circuit; open and closed are the
            # same voice with different decay, so retrigger IS the choke
            elif pitch in (42, 44, 46):
                is_open = pitch == 46
                (note,) = circuit("hat", (METAL,))
                note.frequency = METAL_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=oh_decay if is_open else ch_decay, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.HIGH_PASS, 8000.0, Q=0.8)
                note.amplitude = amp * 0.7
                synth.press(note)

            # Cymbal (49, 51, 57, 59)
            elif pitch in (49, 51, 57, 59):
                (note,) = circuit("cym", (METAL,))
                note.frequency = METAL_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=cym_decay, release_time=0.2, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 8000.0, Q=1.2)
                note.amplitude = amp * 0.85
                synth.press(note)

            # Clap (39) - shares its circuit with maracas
            elif pitch == 39:
                burst1, burst2 = circuit("cm", (NOISE, NOISE))
                bp = synthio.Biquad(synthio.FilterMode.BAND_PASS, 1200.0, Q=1.0)
                for note, attack, level in ((burst1, 0.001, 1.0), (burst2, 0.02, 0.75)):
                    note.frequency = NOISE_HZ
                    note.envelope = synthio.Envelope(attack_time=attack, decay_time=clap_decay, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                    note.filter = bp
                    note.amplitude = amp * level
                    synth.press(note)

            # Maracas (70) - the other face of the clap circuit
            elif pitch == 70:
                burst1, burst2 = circuit("cm", (NOISE, NOISE))
                burst1.frequency = NOISE_HZ
                burst1.envelope = synthio.Envelope(attack_time=0.004, decay_time=0.09, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                burst1.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 6800.0, Q=1.4)
                burst1.amplitude = amp * 0.6
                # The shared circuit chokes: silence the clap's second
                # burst rather than letting it ring under the maracas.
                burst2.amplitude = 0.0
                synth.press(burst1)

            # Cowbell (56) - the two-oscillator pair lives in the
            # COWBELL wavetable (harmonics 2 and 3), one core channel
            elif pitch == 56:
                (note,) = circuit("cb", (COWBELL,))
                note.frequency = cowbell_tune * 0.5
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.4, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                # Band centered on the pair itself, not its upper
                # harmonics: the hardware identity is the ~540/800 Hz
                # pair, and the lower partner leads.
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 640.0, Q=1.0)
                note.amplitude = amp * 0.8
                synth.press(note)

            # Rimshot (37) - shares its circuit with claves
            elif pitch == 37:
                (note,) = circuit("rim", (TRIANGLE,))
                note.frequency = 450.0
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.05, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 1600.0, Q=2.0)
                note.amplitude = amp * 0.8
                synth.press(note)

            # Claves (75) - the other face of the rimshot circuit
            elif pitch == 75:
                (note,) = circuit("rim", (TRIANGLE,))
                note.frequency = 2500.0
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.08, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 2500.0, Q=3.0)
                note.amplitude = amp
                synth.press(note)

            # Fallback (other percussion) - rides the clap circuit
            else:
                burst1, _burst2 = circuit("cm", (NOISE, NOISE))
                burst1.frequency = NOISE_HZ
                burst1.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.1, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                burst1.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 3000.0, Q=1.0)
                burst1.amplitude = amp * 0.5
                synth.press(burst1)

        elif event_type in (EVENT_NOTE_OFF, EVENT_NOTE_ON):
            name = PITCH_CIRCUIT.get(data0)
            if name is not None and name in circuits:
                for note in circuits[name]:
                    synth.release(note)

        elif event_type == EVENT_PARAMETER:
            if data0 == 0: master_level = value0
            elif data0 == 1: accent_level = value0
            elif data0 == 2: bd_tune = logmap(value0, 40.0, 70.0)
            elif data0 == 3: bd_decay = logmap(value0, 0.05, 3.0)
            elif data0 == 4: bd_tone = logmap(value0, 100.0, 800.0)
            elif data0 == 5: sd_tune = logmap(value0, 120.0, 300.0)
            elif data0 == 6: sd_snappy = value0
            elif data0 == 7: sd_tone = logmap(value0, 1000.0, 4000.0)
            elif data0 == 8: lt_tune = logmap(value0, 60.0, 120.0)
            elif data0 == 9: mt_tune = logmap(value0, 100.0, 160.0)
            elif data0 == 10: ht_tune = logmap(value0, 140.0, 220.0)
            elif data0 == 11: clap_decay = logmap(value0, 0.1, 0.8)
            elif data0 == 12: cowbell_tune = logmap(value0, 400.0, 900.0)
            elif data0 == 13: cym_decay = logmap(value0, 0.5, 5.0)
            elif data0 == 14: ch_decay = logmap(value0, 0.02, 0.15)
            elif data0 == 15: oh_decay = logmap(value0, 0.1, 0.8)

    instrument = Instrument(synth, handle_event, PATCHES, MACRO_LABELS,
                            transport=transport, note_map=NOTE_MAP)
    return instrument
