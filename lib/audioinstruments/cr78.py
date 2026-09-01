"""Roland CR-78 CompuRhythm."""

NAME = 'cr78'
DISPLAY_NAME = 'CR-78'
CATEGORIES = ('Drum',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = (
    "Level", "Accent", "BD Decay", "BD Pitch", "SD Snappy", "SD Pitch",
    "Rim Level", "Bongo Hi", "Bongo Lo", "Claves Level", "Cowbell Level",
    "Guiro Level", "Tamb Level", "Maracas Level", "Metal Beat", "Hat Tone",
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
    0: ("Default", (102, 64, 49, 76, 51, 61, 102, 74, 62, 102, 102, 102, 102,
                 102, 102, 78)),
}

NOTE_MAP = (
    (36, "Bass Drum"),
    (38, "Snare"),
    (37, "Rimshot"),
    (42, "Closed Hat"),
    (46, "Open Hat"),
    (49, "Cymbal"),
    (54, "Tambourine"),
    (55, "Metal Beat"),
    (56, "Cowbell"),
    (58, "Guiro"),
    (60, "Bongo Hi"),
    (61, "Bongo Lo"),
    (70, "Maracas"),
    (75, "Claves"),
)

import synthio

from audioinstruments._support import (
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, logmap,
    make_table, noise_table,
)
from audioinstruments._support import Instrument
from audioinstruments import _support

import array

SINE = make_table(((1, 1.0),))
SQUARE = make_table([(n, 1.0 / n) for n in range(1, 15, 2)])
NOISE = noise_table(seed=13579)

# The guiro's scrape as the hardware makes it: one noise voice whose
# amplitude ratchets - five ridges ~20 ms apart, then the tail. Played
# once by an amplitude LFO (the idiom tr909's clap flutter proved).
RATCHET = array.array("h", [32767, 3000, 30000, 3000, 27500, 3000, 25000,
                            3000, 22000, 5000]
                      + [int(18000 * 2.718281828 ** (-i / 7.0)) for i in range(22)])


def create(sample_rate, channel_count=2, transport=None):
    SR = sample_rate
    NOISE_HZ = SR / 8192.0
    synth = synthio.Synthesizer(sample_rate=SR, channel_count=channel_count)

    # Master params
    master_level = 0.8
    accent_level = 0.5

    # Params
    bd_decay = 0.2
    bd_pitch = 65.0
    sd_snappy = 0.4
    sd_pitch = 240.0
    rim_level = 0.8
    bongo_hi = 450.0
    bongo_lo = 280.0
    claves_level = 0.8
    cowbell_level = 0.8
    guiro_level = 0.8
    tamb_level = 0.8
    maracas_level = 0.8
    metal_beat = 0.8
    hat_tone = 7000.0

    # Fixed circuits: 13 permanent single-Note voices (the manual's own
    # per-voice trim-pot table argues for dedicated circuits per sound),
    # at the 13-note ceiling. The snare is one resonant band-passed
    # noise voice (SD Snappy is the filter's Q now - no CR-78 evidence
    # of a dual-oscillator snare was found; flagged in the dossier with
    # its fallback) and the hat is one circuit for closed+open (flagged
    # low-confidence, precedent-only; degrades to two if the listen
    # refuses it). The guiro's five staggered notes became one voice
    # under the RATCHET amplitude LFO.
    circuits = {}

    def circuit(name, waveforms):
        notes = circuits.get(name)
        if notes is None:
            notes = tuple(synthio.Note(440.0, waveform=w, amplitude=0.0)
                          for w in waveforms)
            circuits[name] = notes
        return notes

    PITCH_CIRCUIT = {
        35: "bd", 36: "bd", 38: "sd", 40: "sd", 37: "rim",
        42: "hat", 44: "hat", 46: "hat", 49: "cym",
        54: "tamb", 55: "metal", 56: "cb", 58: "guiro",
        60: "bongo_hi", 61: "bongo_lo", 70: "maracas", 75: "claves",
    }

    # The hardware's own limit, layered on top of residency: the CR-78
    # could sound at most FOUR voices at once (its 14 sounds shared a
    # 4-voice output stage). The module's proven trigger/steal machinery
    # realizes it - keyed by circuit, fed the permanent Note tuples.
    # MAX_VOICES is 5, not 4: the steal check fires at
    # len(voices) + len(notes) >= max_voices with 1-Note voices, so 5 is
    # what lands a true steady state of 4 held (hand-traced in the
    # dossier; 4 would cap the steady state at 3). Steal-oldest is a
    # design choice, not a sourced mechanism - flagged for the listen.
    voices = {}
    serial = 0
    MAX_VOICES = 5

    def release_voice(k):
        _support.release_voice(voices, synth, k)

    def trigger_voice(k, notes):
        nonlocal serial
        serial = _support.trigger_voice(voices, synth, serial, MAX_VOICES,
                                        release_voice, k, notes)

    def handle_event(event_type, channel, note_id, data0, value0, value1, sample_position):
        nonlocal master_level, accent_level, bd_decay, bd_pitch, sd_snappy, sd_pitch
        nonlocal rim_level, bongo_hi, bongo_lo, claves_level, cowbell_level
        nonlocal guiro_level, tamb_level, maracas_level, metal_beat, hat_tone

        if event_type == EVENT_NOTE_ON and value0 > 0.0:
            pitch = data0
            vel = value0
            amp = master_level * (vel + accent_level * (1.0 if vel > 0.8 else 0.0))
            name = PITCH_CIRCUIT.get(pitch)
            if name is None:
                return

            # BD
            if name == "bd":
                (note,) = circuit("bd", (SINE,))
                note.frequency = bd_pitch
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=bd_decay, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.LOW_PASS, bd_pitch * 2.0, Q=0.8)
                note.amplitude = amp

            # SD - one resonant band-passed noise voice; Snappy is Q
            elif name == "sd":
                (note,) = circuit("sd", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.09, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, sd_pitch, Q=4.5 - sd_snappy * 3.5)
                note.amplitude = amp * 0.9

            # Bongos
            elif name in ("bongo_hi", "bongo_lo"):
                (note,) = circuit(name, (SINE,))
                note.frequency = bongo_hi if name == "bongo_hi" else bongo_lo
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.2, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.amplitude = amp

            # Rim
            elif name == "rim":
                (note,) = circuit("rim", (SQUARE,))
                note.frequency = 1200.0
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.02, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 1200.0, Q=2.0)
                note.amplitude = amp * rim_level

            # Claves
            elif name == "claves":
                (note,) = circuit("claves", (SINE,))
                note.frequency = 2200.0
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.05, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 2200.0, Q=3.0)
                note.amplitude = amp * claves_level

            # Cowbell
            elif name == "cb":
                (note,) = circuit("cb", (SQUARE,))
                note.frequency = 800.0
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.2, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 800.0, Q=1.5)
                note.amplitude = amp * cowbell_level

            # Guiro - one voice under the RATCHET amplitude LFO
            elif name == "guiro":
                (note,) = circuit("guiro", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.16, release_time=0.03, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 3500.0, Q=1.0)
                scrape = synthio.LFO(waveform=RATCHET, once=True, rate=5.5, scale=1.0, interpolate=True)
                note.amplitude = synthio.Math(synthio.MathOperation.PRODUCT, scrape, amp * guiro_level, 1.0)

            # Tambourine
            elif name == "tamb":
                (note,) = circuit("tamb", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.15, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.HIGH_PASS, 6000.0, Q=0.8)
                note.amplitude = amp * tamb_level

            # Maracas
            elif name == "maracas":
                (note,) = circuit("maracas", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.05, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.HIGH_PASS, 5000.0, Q=1.0)
                note.amplitude = amp * maracas_level

            # Metal Beat
            elif name == "metal":
                (note,) = circuit("metal", (SQUARE,))
                note.frequency = 600.0
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.08, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.HIGH_PASS, 4000.0, Q=1.5)
                note.amplitude = amp * metal_beat

            # Hat (closed 42/44, open 46) - one circuit, retrigger chokes
            elif name == "hat":
                (note,) = circuit("hat", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.3 if pitch == 46 else 0.05, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                # Band-passed per face, not bare HP: the measured capture
                # centroids (CH 10.1 kHz, OH 8.5 kHz) are unreachable
                # from full-band high-passed noise at 48 kHz.
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, hat_tone * (1.1 if pitch == 46 else 1.35), Q=0.8)
                note.amplitude = amp * 0.7

            # Cymbal
            elif name == "cym":
                (note,) = circuit("cym", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.8, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.HIGH_PASS, hat_tone, Q=0.7)
                note.amplitude = amp * 0.7

            # The 4-voice arbiter admits the (single-Note) circuit
            trigger_voice(name, circuits[name])

        elif event_type in (EVENT_NOTE_OFF, EVENT_NOTE_ON):
            name = PITCH_CIRCUIT.get(data0)
            if name is not None and name in voices:
                release_voice(name)

        elif event_type == EVENT_PARAMETER:
            if data0 == 0: master_level = value0
            elif data0 == 1: accent_level = value0
            elif data0 == 2: bd_decay = logmap(value0, 0.1, 0.6)
            elif data0 == 3: bd_pitch = logmap(value0, 40.0, 90.0)
            elif data0 == 4: sd_snappy = value0
            elif data0 == 5: sd_pitch = logmap(value0, 150.0, 400.0)
            elif data0 == 6: rim_level = value0
            elif data0 == 7: bongo_hi = logmap(value0, 300.0, 600.0)
            elif data0 == 8: bongo_lo = logmap(value0, 200.0, 400.0)
            elif data0 == 9: claves_level = value0
            elif data0 == 10: cowbell_level = value0
            elif data0 == 11: guiro_level = value0
            elif data0 == 12: tamb_level = value0
            elif data0 == 13: maracas_level = value0
            elif data0 == 14: metal_beat = value0
            elif data0 == 15: hat_tone = logmap(value0, 4000.0, 10000.0)

    instrument = Instrument(synth, handle_event, PATCHES, MACRO_LABELS,
                            transport=transport, note_map=NOTE_MAP)
    return instrument
