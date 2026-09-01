"""Oberheim DMX."""

NAME = 'dmx'
DISPLAY_NAME = 'DMX'
CATEGORIES = ('Drum',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = (
    "Level", "BD Pitch", "BD Decay", "SD Pitch", "SD Snappy", "Rim Pitch",
    "Clap Decay", "LT Pitch", "MT Pitch", "HT Pitch", "Tambourine",
    "Shaker", "Cowbell", "Cymbal Pitch", "CH Decay", "OH Decay",
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
    0: ("Default", (102, 64, 67, 56, 76, 80, 89, 84, 97, 84, 102, 102, 68, 56,
                 58, 78)),
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
    (54, "Tambourine"),
    (56, "Cowbell"),
    (70, "Shaker"),
)

import array
import synthio

from audioinstruments._support import (
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, FALL, logmap,
    make_table, noise_table,
)
from audioinstruments._support import Instrument

def crush_noise(length=8192, seed=1234567, levels=48, hold=3):
    # low-bit-depth, low-sample-rate stair-stepped noise - the DMX's crunchy,
    # gritty sample chip character, distinct from LinnDrum's cleaner samples.
    # sequential LCG state, doesn't vectorize with ulab
    out = array.array("h", bytearray(length * 2))
    state = seed
    step_size = 65536 // levels
    held = 0
    for i in range(length):
        if i % hold == 0:
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            raw = ((state >> 15) & 0xFFFF) - 32768
            held = (raw // step_size) * step_size
        out[i] = held
    return out




SINE = make_table(((1, 1.0), (2, 0.1)))
TRIANGLE = make_table([(n, (1.0 / (n*n)) * (-1)**((n-1)//2)) for n in range(1, 11, 2)])
SQUARE = make_table([(n, 1.0 / n) for n in range(1, 15, 2)])
NOISE = noise_table(seed=121212)
GRIT = crush_noise(seed=121212)
COWBELL = make_table(((2, 1.0), (3, 0.7)))

# The clap's multi-burst flutter on one Note (the tr909-proven idiom).
FLUT = array.array("h", [32767, 4800, 30000, 4800, 27500, 8000]
                   + [int(24000 * 2.718281828 ** (-i / 14.0)) for i in range(26)])


def create(sample_rate, channel_count=2, transport=None):
    SR = sample_rate
    NOISE_HZ = SR / 8192.0
    synth = synthio.Synthesizer(sample_rate=SR, channel_count=channel_count)

    # Master params
    master_level = 0.8

    # BD
    bd_pitch = 60.0
    bd_decay = 0.3

    # SD
    sd_pitch = 180.0
    sd_snappy = 0.6

    # Rim
    rim_pitch = 1000.0

    # Clap
    clap_decay = 0.35

    # Toms
    lt_pitch = 100.0
    mt_pitch = 150.0
    ht_pitch = 200.0

    # Perc
    tamb_level = 0.8
    shaker_level = 0.8
    cowbell_pitch = 800.0

    # Hats/Cymbal
    cymbal_pitch = 6000.0
    ch_decay = 0.05
    oh_decay = 0.3

    # Fixed circuits on the hardware's own EIGHT voice cards (service
    # manual: 8-voice polyphony, TR1-TR16 trigger bus = 8 cards x 2
    # lines): sounds sharing a card choke each other. Card-level
    # sharing is manual-quoted for the Cymbal (Dual slot); which toms
    # pair and which percussion sounds pair are the dossier's own
    # low-confidence groupings, flagged there. 11 resident notes.
    circuits = {}

    def circuit(name, waveforms):
        notes = circuits.get(name)
        if notes is None:
            notes = tuple(synthio.Note(440.0, waveform=w, amplitude=0.0)
                          for w in waveforms)
            circuits[name] = notes
        return notes

    PITCH_CIRCUIT = {
        35: "bd", 36: "bd", 38: "sd", 40: "sd",
        41: "tomA", 43: "tomA", 45: "tomA", 47: "tomA",
        48: "tomB", 50: "tomB",
        42: "hat", 44: "hat", 46: "hat",
        49: "cym", 51: "cym", 57: "cym", 59: "cym",
        37: "percA", 54: "percA",
        70: "percB", 82: "percB", 39: "percB", 56: "percB",
    }

    def handle_event(event_type, channel, note_id, data0, value0, value1, sample_position):
        nonlocal master_level, bd_pitch, bd_decay, sd_pitch, sd_snappy, rim_pitch, clap_decay
        nonlocal lt_pitch, mt_pitch, ht_pitch, tamb_level, shaker_level, cowbell_pitch
        nonlocal cymbal_pitch, ch_decay, oh_decay

        if event_type == EVENT_NOTE_ON and value0 > 0.0:
            pitch = data0
            amp = master_level * value0
            name = PITCH_CIRCUIT.get(pitch)
            if name is None:
                return

            # BD - sampled tone plus gritty low-bit transient
            if name == "bd":
                body, grit = circuit("bd", (SINE, GRIT))
                body.frequency = bd_pitch
                body.envelope = synthio.Envelope(attack_time=0.001, decay_time=bd_decay, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                body.filter = synthio.Biquad(synthio.FilterMode.LOW_PASS, bd_pitch * 3.0, Q=0.8)
                body.amplitude = amp
                grit.frequency = NOISE_HZ
                grit.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.04, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                grit.filter = synthio.Biquad(synthio.FilterMode.LOW_PASS, bd_pitch * 7.0, Q=0.7)
                grit.amplitude = amp * 0.4
                synth.press(body)
                synth.press(grit)

            # SD - crunchy low-bit snap
            elif name == "sd":
                body, snare = circuit("sd", (TRIANGLE, GRIT))
                body.frequency = sd_pitch
                body.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.1, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                body.amplitude = amp * 0.7
                snare.frequency = NOISE_HZ
                snare.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.15, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                snare.filter = synthio.Biquad(synthio.FilterMode.HIGH_PASS, 1800.0, Q=1.0)
                snare.amplitude = amp * sd_snappy
                synth.press(body)
                synth.press(snare)

            # Toms - card A (Low+Mid choke) and card B (Hi)
            elif name in ("tomA", "tomB"):
                tune = ht_pitch if name == "tomB" else (lt_pitch if pitch in (41, 43) else mt_pitch)
                (note,) = circuit(name, (TRIANGLE,))
                note.frequency = tune
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.3, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                note.bend = synthio.LFO(waveform=FALL, once=True, rate=20.0, scale=0.15, interpolate=True)
                note.amplitude = amp
                synth.press(note)

            # Hats - one card, retrigger chokes
            elif name == "hat":
                is_open = pitch == 46
                (note,) = circuit("hat", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=oh_decay if is_open else ch_decay, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, cymbal_pitch * 1.3, Q=0.8)
                note.amplitude = amp * 0.7
                synth.press(note)

            # Cymbal - the Dual card: Ride and Crash share it (manual)
            elif name == "cym":
                lo, hi = circuit("cym", (NOISE, NOISE))
                env = synthio.Envelope(attack_time=0.001, decay_time=1.0, release_time=0.3, attack_level=1.0, sustain_level=0.0)
                lo.frequency = NOISE_HZ
                lo.envelope = env
                lo.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, cymbal_pitch * 0.8, Q=0.5)
                lo.amplitude = amp * 0.5
                hi.frequency = NOISE_HZ
                hi.envelope = env
                hi.filter = synthio.Biquad(synthio.FilterMode.HIGH_PASS, cymbal_pitch * 1.2, Q=0.7)
                hi.amplitude = amp * 0.5
                synth.press(lo)
                synth.press(hi)

            # Perc card A: Rimshot / Tambourine share, waveform swapped
            elif name == "percA":
                (note,) = circuit("percA", (SQUARE,))
                if pitch == 37:
                    note.waveform = SQUARE
                    note.frequency = rim_pitch
                    note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.03, release_time=0.01, attack_level=1.0, sustain_level=0.0)
                    note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, rim_pitch, Q=1.5)
                    note.amplitude = amp
                else:
                    note.waveform = NOISE
                    note.frequency = NOISE_HZ
                    note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.1, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                    note.filter = synthio.Biquad(synthio.FilterMode.HIGH_PASS, 6000.0, Q=0.8)
                    note.amplitude = amp * tamb_level
                synth.press(note)

            # Perc card B: Shaker / Clap / Cowbell share
            elif name == "percB":
                (note,) = circuit("percB", (NOISE,))
                note.bend = None
                if pitch == 56:
                    # the two-oscillator pair in one table (harmonics 2+3)
                    note.waveform = COWBELL
                    note.frequency = cowbell_pitch * 0.5
                    note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.25, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                    note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, cowbell_pitch, Q=1.2)
                    note.amplitude = amp * 0.8
                elif pitch == 39:
                    note.waveform = NOISE
                    note.frequency = NOISE_HZ
                    note.envelope = synthio.Envelope(attack_time=0.002, decay_time=clap_decay, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                    note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 1200.0, Q=1.0)
                    flut = synthio.LFO(waveform=FLUT, once=True, rate=3.0, scale=1.0, interpolate=True)
                    note.amplitude = synthio.Math(synthio.MathOperation.PRODUCT, flut, amp * 1.4, 1.0)
                    synth.press(note)
                    return
                else:
                    note.waveform = NOISE
                    note.frequency = NOISE_HZ
                    note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.05, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                    note.filter = synthio.Biquad(synthio.FilterMode.HIGH_PASS, 7000.0, Q=0.8)
                    note.amplitude = amp * shaker_level
                synth.press(note)

        elif event_type in (EVENT_NOTE_OFF, EVENT_NOTE_ON):
            name = PITCH_CIRCUIT.get(data0)
            if name is not None and name in circuits:
                for note in circuits[name]:
                    synth.release(note)

        elif event_type == EVENT_PARAMETER:
            if data0 == 0: master_level = value0
            elif data0 == 1: bd_pitch = logmap(value0, 45.0, 90.0)
            elif data0 == 2: bd_decay = logmap(value0, 0.15, 0.6)
            elif data0 == 3: sd_pitch = logmap(value0, 140.0, 260.0)
            elif data0 == 4: sd_snappy = value0
            elif data0 == 5: rim_pitch = logmap(value0, 700.0, 1500.0)
            elif data0 == 6: clap_decay = logmap(value0, 0.2, 0.6)
            elif data0 == 7: lt_pitch = logmap(value0, 70.0, 140.0)
            elif data0 == 8: mt_pitch = logmap(value0, 110.0, 200.0)
            elif data0 == 9: ht_pitch = logmap(value0, 150.0, 280.0)
            elif data0 == 10: tamb_level = value0
            elif data0 == 11: shaker_level = value0
            elif data0 == 12: cowbell_pitch = logmap(value0, 500.0, 1200.0)
            elif data0 == 13: cymbal_pitch = logmap(value0, 4000.0, 9000.0)
            elif data0 == 14: ch_decay = logmap(value0, 0.02, 0.12)
            elif data0 == 15: oh_decay = logmap(value0, 0.1, 0.6)

    instrument = Instrument(synth, handle_event, PATCHES, MACRO_LABELS,
                            transport=transport, note_map=NOTE_MAP)
    return instrument
