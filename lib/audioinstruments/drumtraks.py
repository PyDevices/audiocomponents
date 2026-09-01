"""Sequential Circuits Drumtraks."""

NAME = 'drumtraks'
DISPLAY_NAME = 'Drumtraks'
CATEGORIES = ('Drum',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = (
    "Volume", "Kick Tune", "Kick Level", "Snare Tune", "Snare Level",
    "Tom Tune", "Tom Level", "HiHat Tune", "HiHat Level", "Cymbal Tune",
    "Cymbal Level", "Percussion Tune", "Percussion Level", "Overall Decay",
    "Crunch/Bandwidth", "Master Tune",
)
MACRO_MODES = {
    0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR", 3: "UNIPOLAR",
    4: "UNIPOLAR", 5: "UNIPOLAR", 6: "UNIPOLAR", 7: "UNIPOLAR",
    8: "UNIPOLAR", 9: "UNIPOLAR", 10: "UNIPOLAR", 11: "UNIPOLAR",
    12: "UNIPOLAR", 13: "UNIPOLAR", 14: "UNIPOLAR", 15: "BIPOLAR",
}

# Patch 0 is the sound this instrument's defaults describe. The macro
# surface grew 8 -> 16 following the panel evidence: the Drumtraks'
# defining feature was per-voice programmable tune AND level, so every
# voice family carries the pair; Overall Decay and Crunch/Bandwidth stay
# as synthesis-calibration globals (the latter rebound to the machine's
# low-bit/companded character - itself an unconfirmed legacy claim).
PATCHES = {
    0: ("Default", (102, 64, 102, 64, 102, 64, 102, 64, 102, 64, 102, 64,
                 102, 64, 64, 64)),
}

# The hardware's 13 named sounds on a 12-voice architecture. Note
# numbers follow the sibling conventions.
NOTE_MAP = (
    (36, "Kick"),
    (38, "Snare"),
    (37, "Snare Rim"),
    (39, "Clap"),
    (45, "Tom 1"),
    (50, "Tom 2"),
    (42, "Closed Hat"),
    (46, "Open Hat"),
    (49, "Crash"),
    (51, "Ride"),
    (54, "Tambourine"),
    (56, "Cowbell"),
    (69, "Cabasa"),
)

import array
import synthio

from audioinstruments._support import (
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, logmap,
    make_table, noise_table,
)
from audioinstruments._support import Instrument

SINE = make_table(((1, 1.0),))
TONE = make_table(((1, 1.0), (2, 0.3), (3, 0.12)))
COWBELL = make_table(((2, 1.0), (3, 0.7)))
NOISE = noise_table(seed=848484)

# One-Note clap flutter (the proven idiom).
FLUT = array.array("h", [32767, 4800, 30000, 4800, 27500, 8000]
                   + [int(24000 * 2.718281828 ** (-i / 14.0)) for i in range(26)])


def create(sample_rate, channel_count=2, transport=None):
    SR = sample_rate
    NOISE_HZ = SR / 8192.0
    synth = synthio.Synthesizer(sample_rate=SR, channel_count=channel_count)

    volume = 0.8
    kick_tune = 1.0
    kick_level = 0.8
    snare_tune = 1.0
    snare_level = 0.8
    tom_tune = 1.0
    tom_level = 0.8
    hh_tune = 1.0
    hh_level = 0.8
    cym_tune = 1.0
    cym_level = 0.8
    perc_tune = 1.0
    perc_level = 0.8
    decay_scale = 0.5
    crunch = 0.5
    master_tune = 1.0

    # Fixed circuits: 12 resident Notes, matching the hardware's own
    # 12-voice polyphony exactly. Tune macros are playback RATIOS - a
    # ROMpler's tune shifts the whole spectrum and shortens the read
    # together, so filters and decays follow the ratio (the sp1200
    # lesson). Crunch/Bandwidth caps the spectrum via each voice's
    # filter ceiling rather than adding layers. The hat share is
    # moderate-confidence (13-sounds/12-voices arithmetic plus family
    # convention), flagged in the dossier.
    circuits = {}

    def circuit(name, waveforms):
        notes = circuits.get(name)
        if notes is None:
            notes = tuple(synthio.Note(440.0, waveform=w, amplitude=0.0)
                          for w in waveforms)
            circuits[name] = notes
        return notes

    PITCH_CIRCUIT = {
        35: "kick", 36: "kick", 38: "sd", 40: "sd", 37: "rim",
        41: "tom1", 43: "tom1", 45: "tom1", 47: "tom1",
        48: "tom2", 50: "tom2",
        42: "hat", 44: "hat", 46: "hat",
        49: "crash", 51: "ride", 39: "clap", 54: "tamb",
        56: "cb", 69: "cabasa", 70: "cabasa",
    }

    def handle_event(event_type, channel, note_id, data0, value0, value1, sample_position):
        nonlocal volume, kick_tune, kick_level, snare_tune, snare_level
        nonlocal tom_tune, tom_level, hh_tune, hh_level, cym_tune, cym_level
        nonlocal perc_tune, perc_level, decay_scale, crunch, master_tune

        if event_type == EVENT_NOTE_ON and value0 > 0.0:
            pitch = data0
            amp = volume * value0
            dk = 0.5 + decay_scale
            bw = 6000.0 + crunch * 10000.0   # the bandwidth ceiling Crunch sets
            name = PITCH_CIRCUIT.get(pitch)
            if name is None:
                return

            if name == "kick":
                (note,) = circuit("kick", (SINE,))
                r = kick_tune * master_tune
                note.frequency = 58.0 * r
                note.envelope = synthio.Envelope(attack_time=0.002, decay_time=0.16 * dk / r, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.LOW_PASS, min(bw, 380.0 * r), Q=0.8)
                note.amplitude = amp * kick_level
                synth.press(note)

            elif name == "sd":
                body, snap = circuit("sd", (TONE, NOISE))
                r = snare_tune * master_tune
                body.frequency = 170.0 * r
                body.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.07 * dk / r, release_time=0.04, attack_level=1.0, sustain_level=0.0)
                body.amplitude = amp * snare_level * 0.65
                snap.frequency = NOISE_HZ
                snap.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.1 * dk / r, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                snap.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, min(bw, 4200.0 * r), Q=0.7)
                snap.amplitude = amp * snare_level * 0.8
                synth.press(body)
                synth.press(snap)

            elif name == "rim":
                (note,) = circuit("rim", (NOISE,))
                r = perc_tune * master_tune
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.035 * dk, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, min(bw, 2300.0 * r), Q=1.3)
                note.amplitude = amp * perc_level
                synth.press(note)

            elif name in ("tom1", "tom2"):
                base = 120.0 if name == "tom1" else 180.0
                (note,) = circuit(name, (TONE,))
                r = tom_tune * master_tune
                note.frequency = base * r
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.28 * dk / r, release_time=0.08, attack_level=1.0, sustain_level=0.0)
                note.amplitude = amp * tom_level
                synth.press(note)

            elif name == "hat":
                is_open = pitch == 46
                (note,) = circuit("hat", (NOISE,))
                r = hh_tune * master_tune
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=(0.32 if is_open else 0.05) * dk / r, release_time=0.04, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, min(bw * 1.4, 8200.0 * r), Q=0.8)
                note.amplitude = amp * hh_level * 0.8
                synth.press(note)

            elif name in ("crash", "ride"):
                (note,) = circuit(name, (NOISE,))
                r = cym_tune * master_tune
                note.frequency = NOISE_HZ
                base = 1.0 if name == "crash" else 1.25
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=base * dk / r, release_time=0.3, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, min(bw * 1.4, (5500.0 if name == "crash" else 4500.0) * r), Q=0.8 if name == "crash" else 1.0)
                note.amplitude = amp * cym_level * 0.8
                synth.press(note)

            elif name == "clap":
                (note,) = circuit("clap", (NOISE,))
                r = perc_tune * master_tune
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.002, decay_time=0.1 * dk, release_time=0.04, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, min(bw, 1000.0 * r), Q=3.5)
                flut = synthio.LFO(waveform=FLUT, once=True, rate=3.2, scale=1.0, interpolate=True)
                note.amplitude = synthio.Math(synthio.MathOperation.PRODUCT, flut, amp * perc_level * 1.4, 1.0)
                synth.press(note)

            elif name == "tamb":
                (note,) = circuit("tamb", (NOISE,))
                r = perc_tune * master_tune
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.12 * dk, release_time=0.04, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, min(bw * 1.4, 6800.0 * r), Q=1.0)
                note.amplitude = amp * perc_level
                synth.press(note)

            elif name == "cb":
                (note,) = circuit("cb", (COWBELL,))
                r = perc_tune * master_tune
                note.frequency = 270.0 * r
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.1 * dk, release_time=0.03, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, min(bw, 800.0 * r), Q=1.0)
                note.amplitude = amp * perc_level * 0.9
                synth.press(note)

            elif name == "cabasa":
                (note,) = circuit("cabasa", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.025 * dk, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, min(bw * 1.4, 8000.0), Q=1.0)
                note.amplitude = amp * perc_level * 0.9
                synth.press(note)

        elif event_type in (EVENT_NOTE_OFF, EVENT_NOTE_ON):
            name = PITCH_CIRCUIT.get(data0)
            if name is not None and name in circuits:
                for note in circuits[name]:
                    synth.release(note)

        elif event_type == EVENT_PARAMETER:
            if data0 == 0: volume = value0
            elif data0 == 1: kick_tune = logmap(value0, 0.7, 1.45)
            elif data0 == 2: kick_level = value0
            elif data0 == 3: snare_tune = logmap(value0, 0.7, 1.45)
            elif data0 == 4: snare_level = value0
            elif data0 == 5: tom_tune = logmap(value0, 0.7, 1.45)
            elif data0 == 6: tom_level = value0
            elif data0 == 7: hh_tune = logmap(value0, 0.7, 1.45)
            elif data0 == 8: hh_level = value0
            elif data0 == 9: cym_tune = logmap(value0, 0.7, 1.45)
            elif data0 == 10: cym_level = value0
            elif data0 == 11: perc_tune = logmap(value0, 0.7, 1.45)
            elif data0 == 12: perc_level = value0
            elif data0 == 13: decay_scale = value0
            elif data0 == 14: crunch = value0
            elif data0 == 15: master_tune = 0.95 + value0 * 0.1

    instrument = Instrument(synth, handle_event, PATCHES, MACRO_LABELS,
                            transport=transport, note_map=NOTE_MAP)
    return instrument
