"""Linn LinnDrum."""

NAME = 'linndrum'
DISPLAY_NAME = 'LinnDrum'
CATEGORIES = ('Drum',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = (
    "Level", "BD Level", "SD Level", "SD Tune", "Rim Level", "Clap Level",
    "Tom Level", "Tom Tune", "Conga Level", "Conga Tune",
    "Cabasa/Tamb Level", "Cowbell Level", "Hats Level", "CH Decay",
    "OH Decay", "Cymbals Level",
)
MACRO_MODES = {
    0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR", 3: "UNIPOLAR",
    4: "UNIPOLAR", 5: "UNIPOLAR", 6: "UNIPOLAR", 7: "BIPOLAR",
    8: "UNIPOLAR", 9: "UNIPOLAR", 10: "UNIPOLAR", 11: "UNIPOLAR",
    12: "UNIPOLAR", 13: "UNIPOLAR", 14: "UNIPOLAR", 15: "UNIPOLAR",
}

# Patch 0 is the sound this instrument's defaults describe. The macro
# surface was rebalanced to the real panel's emphasis (level knobs for
# every voice, tune only where the hardware had tune pots - snare, toms,
# congas); the old pitch/decay macros with no panel ancestor became
# fixed constants calibrated to the measured captures.
PATCHES = {
    0: ("Default", (102, 102, 102, 62, 102, 102, 102, 64, 102, 64, 102,
                 102, 102, 83, 88, 102)),
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
    (49, "Crash"),
    (51, "Ride"),
    (54, "Tambourine"),
    (56, "Cowbell"),
    (62, "Conga Hi"),
    (63, "Conga Mid"),
    (64, "Conga Lo"),
    (69, "Cabasa"),
)

import synthio

from audioinstruments._support import (
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, logmap,
    make_table, noise_table,
)
from audioinstruments._support import Instrument

SINE = make_table(((1, 1.0),))
# ROM drum tones carry body harmonics a bare sine cannot
TONE = make_table(((1, 1.0), (2, 0.25), (3, 0.08)))
COWBELL = make_table(((2, 1.0), (3, 0.7)))
NOISE = noise_table(seed=424242)


def create(sample_rate, channel_count=2, transport=None):
    SR = sample_rate
    NOISE_HZ = SR / 8192.0
    synth = synthio.Synthesizer(sample_rate=SR, channel_count=channel_count)

    master_level = 0.8
    bd_level = 0.8
    sd_level = 0.8
    sd_tune = 151.0
    rim_level = 0.8
    clap_level = 0.8
    tom_level = 0.8
    tom_tune = 1.0       # BIPOLAR ratio around the measured medians
    conga_level = 0.8
    conga_tune = 1.0
    ct_level = 0.8       # cabasa/tambourine shared level
    cowbell_level = 0.8
    hats_level = 0.8
    ch_decay = 0.09
    oh_decay = 0.42
    cym_level = 0.8

    # Fixed circuits: 13 permanent single-Note voices at the ceiling -
    # each LinnDrum voice is one sample through one VCA, so no circuit
    # earns a second Note; the budget buys circuit COUNT instead, which
    # is what a 15-channel machine needs. Crash and Ride are separate
    # circuits again (the reference says so; the old file conflated
    # them). Congas share one circuit and cabasa/tambourine share one -
    # both budget folds, flagged in the dossier, degrade gracefully.
    # Hats share by the hardware's own one-loop-two-envelopes design.
    # Repitch physics per the ROMpler lesson: tune scales the spectrum
    # AND shortens the read, so filters and decays follow the ratio.
    circuits = {}

    def circuit(name, waveforms):
        notes = circuits.get(name)
        if notes is None:
            notes = tuple(synthio.Note(440.0, waveform=w, amplitude=0.0)
                          for w in waveforms)
            circuits[name] = notes
        return notes

    PITCH_CIRCUIT = {
        36: "bd", 38: "sd", 37: "rim", 39: "clap",
        41: "tom_lo", 43: "tom_lo", 45: "tom_mid", 47: "tom_mid",
        48: "tom_hi", 50: "tom_hi",
        62: "congas", 63: "congas", 64: "congas",
        69: "cabtamb", 54: "cabtamb",
        56: "cb", 42: "hat", 44: "hat", 46: "hat",
        49: "crash", 51: "ride",
    }

    def handle_event(event_type, channel, note_id, data0, value0, value1, sample_position):
        nonlocal master_level, bd_level, sd_level, sd_tune, rim_level
        nonlocal clap_level, tom_level, tom_tune, conga_level, conga_tune
        nonlocal ct_level, cowbell_level, hats_level, ch_decay, oh_decay
        nonlocal cym_level

        if event_type == EVENT_NOTE_ON and value0 > 0.0:
            pitch = data0
            amp = master_level * value0
            name = PITCH_CIRCUIT.get(pitch)
            if name is None:
                return

            # Bass Drum - fixed 65 Hz (both reference files land there);
            # decay is the measured ~26 ms tau, not the old 350 ms knob
            if name == "bd":
                (note,) = circuit("bd", (TONE,))
                note.frequency = 65.0
                note.envelope = synthio.Envelope(attack_time=0.004, decay_time=0.08, release_time=0.04, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.LOW_PASS, 450.0, Q=0.8)
                note.amplitude = amp * bd_level * 1.3

            # Snare - one repitchable circuit; the tune knob shifts the
            # whole spectrum and shortens the read together
            elif name == "sd":
                (note,) = circuit("sd", (NOISE,))
                ratio = sd_tune / 151.0
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.1 / ratio, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 4300.0 * ratio, Q=0.75)
                note.amplitude = amp * sd_level

            # Rimshot - fixed (no panel tune)
            elif name == "rim":
                (note,) = circuit("rim", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.07, release_time=0.03, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 2200.0, Q=1.2)
                note.amplitude = amp * rim_level

            # Clap - fixed
            elif name == "clap":
                (note,) = circuit("clap", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.002, decay_time=0.11, release_time=0.04, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 900.0, Q=3.0)
                note.amplitude = amp * clap_level

            # Toms - three circuits at the measured medians, one shared
            # BIPOLAR tune offset (the panel's tune pots, folded)
            elif name in ("tom_lo", "tom_mid", "tom_hi"):
                base, decay = {"tom_lo": (86.0, 0.67), "tom_mid": (162.0, 0.32),
                               "tom_hi": (232.0, 0.21)}[name]
                (note,) = circuit(name, (TONE,))
                note.frequency = base * tom_tune
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=decay / tom_tune, release_time=0.08, attack_level=1.0, sustain_level=0.0)
                note.amplitude = amp * tom_level

            # Congas - one shared circuit (budget fold, flagged);
            # per-note bases from the measured medians
            elif name == "congas":
                base, decay = {62: (409.0, 0.11), 63: (237.0, 0.30),
                               64: (97.0, 0.49)}[pitch]
                (note,) = circuit("congas", (TONE,))
                note.frequency = base * conga_tune
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=decay / conga_tune, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.amplitude = amp * conga_level

            # Cabasa / Tambourine - one shared circuit (budget fold)
            elif name == "cabtamb":
                is_tamb = pitch == 54
                (note,) = circuit("cabtamb", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.15 if is_tamb else 0.03, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 8600.0, Q=1.0)
                note.amplitude = amp * ct_level

            # Cowbell - fixed at the measured 506 Hz (the old macro was
            # mislabeled: it moved pitch, and the panel has no such knob)
            elif name == "cb":
                (note,) = circuit("cb", (COWBELL,))
                note.frequency = 253.0
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.1, release_time=0.03, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 640.0, Q=1.0)
                note.amplitude = amp * cowbell_level

            # Hats - one loop, two envelopes: the hardware's own share
            elif name == "hat":
                is_open = pitch == 46
                (note,) = circuit("hat", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=oh_decay if is_open else ch_decay, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 8000.0, Q=0.8)
                note.amplitude = amp * hats_level

            # Crash / Ride - separate circuits again, per the reference
            elif name == "crash":
                (note,) = circuit("crash", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=1.0, release_time=0.3, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 4800.0, Q=1.0)
                note.amplitude = amp * cym_level

            elif name == "ride":
                (note,) = circuit("ride", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=1.25, release_time=0.3, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 3900.0, Q=1.2)
                note.amplitude = amp * cym_level * 0.9

            synth.press(circuits[name][0])

        elif event_type in (EVENT_NOTE_OFF, EVENT_NOTE_ON):
            name = PITCH_CIRCUIT.get(data0)
            if name is not None and name in circuits:
                for note in circuits[name]:
                    synth.release(note)

        elif event_type == EVENT_PARAMETER:
            if data0 == 0: master_level = value0
            elif data0 == 1: bd_level = value0
            elif data0 == 2: sd_level = value0
            elif data0 == 3: sd_tune = logmap(value0, 90.0, 260.0)
            elif data0 == 4: rim_level = value0
            elif data0 == 5: clap_level = value0
            elif data0 == 6: tom_level = value0
            elif data0 == 7: tom_tune = logmap(value0, 0.6, 1.6)
            elif data0 == 8: conga_level = value0
            elif data0 == 9: conga_tune = logmap(value0, 0.6, 1.6)
            elif data0 == 10: ct_level = value0
            elif data0 == 11: cowbell_level = value0
            elif data0 == 12: hats_level = value0
            elif data0 == 13: ch_decay = logmap(value0, 0.02, 0.2)
            elif data0 == 14: oh_decay = logmap(value0, 0.1, 0.8)
            elif data0 == 15: cym_level = value0

    instrument = Instrument(synth, handle_event, PATCHES, MACRO_LABELS,
                            transport=transport, note_map=NOTE_MAP)
    return instrument
