"""Roland TR-606 Drumatix."""

NAME = 'tr606'
DISPLAY_NAME = 'TR-606'
CATEGORIES = ('Drum',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = (
    "Level", "Accent", "BD Level", "BD Decay", "BD Pitch", "SD Level",
    "SD Snappy", "SD Pitch", "LT Pitch", "HT Pitch", "Cym Level",
    "Cym Decay", "Tom Level", "Hat Level", "CH Decay", "OH Decay",
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
    0: ("Default", (102, 64, 98, 61, 64, 98, 76, 70, 65, 72, 88, 69, 90, 88,
                 58, 78)),
}

NOTE_MAP = (
    (36, "Bass Drum"),
    (38, "Snare"),
    (41, "Low Tom"),
    (48, "Hi Tom"),
    (42, "Closed Hat"),
    (46, "Open Hat"),
    (49, "Cymbal"),
)

import synthio

from audioinstruments._support import (
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, FALL, logmap,
    make_table, noise_table,
)
from audioinstruments._support import Instrument

SINE = make_table(((1, 1.0),))
TRIANGLE = make_table([(n, (1.0 / (n*n)) * (-1)**((n-1)//2)) for n in range(1, 11, 2)])
NOISE = noise_table(seed=606060)


def create(sample_rate, channel_count=2, transport=None):
    SR = sample_rate
    NOISE_HZ = SR / 8192.0
    synth = synthio.Synthesizer(sample_rate=SR, channel_count=channel_count)

    # Master params
    master_level = 0.8
    accent_level = 0.5

    # Voice Levels (the real panel's whole tone-shaping surface is six
    # mix pots; Tom Level is the one that was missing - it replaced
    # "Cym Tone", whose bands are a fixed bridged-T design on hardware)
    bd_level = 1.0
    sd_level = 1.0
    cym_level = 0.8
    hat_level = 0.8
    tom_level = 0.8

    # Synthesis-calibration globals (no panel counterpart; kept honest)
    bd_decay = 0.3
    bd_pitch = 60.0
    sd_snappy = 0.6
    sd_pitch = 220.0
    lt_pitch = 100.0
    ht_pitch = 160.0
    cym_decay = 0.6
    ch_decay = 0.05
    oh_decay = 0.3

    #: The cymbal's two parallel band-pass chains off the shared
    #: oscillator bank sit at fixed centers (schematic + Baratatronix).
    CYM_HI = 7100.0
    CYM_LO = 3440.0

    # Fixed circuits, 8 resident Notes across the hardware's own FIVE
    # simultaneous circuit-groups (schematic p.4): BD = two independent
    # oscillators summed at one level; SD = tone + noise; the two toms
    # share one ENV+LPF+VCA chain - one circuit, retuned per hit, so LT
    # and HT genuinely choke each other (the old code let them ring
    # together, which the hardware could not); cymbal = two parallel
    # band chains; open/closed hat share one VCA+HPF and choke by
    # retrigger, as the old code already had right. The BD's second
    # oscillator's interval/level is calibration (the schematic shows
    # the pair, not their tuning).
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
        41: "tom", 43: "tom", 45: "tom", 47: "tom", 48: "tom", 50: "tom",
        42: "hat", 44: "hat", 46: "hat", 49: "cym", 51: "cym",
    }

    def handle_event(event_type, channel, note_id, data0, value0, value1, sample_position):
        nonlocal master_level, accent_level
        nonlocal bd_level, bd_decay, bd_pitch
        nonlocal sd_level, sd_snappy, sd_pitch
        nonlocal lt_pitch, ht_pitch, tom_level
        nonlocal cym_level, cym_decay, hat_level, ch_decay, oh_decay

        if event_type == EVENT_NOTE_ON and value0 > 0.0:
            pitch = data0
            vel = value0
            base_amp = master_level * (vel + accent_level * (1.0 if vel > 0.8 else 0.0))

            # BD (35, 36) - two oscillators summed
            if pitch in (35, 36):
                amp = base_amp * bd_level
                osc1, osc2 = circuit("bd", (SINE, SINE))
                env = synthio.Envelope(attack_time=0.001, decay_time=bd_decay, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                drop = synthio.LFO(waveform=FALL, once=True, rate=25.0, scale=0.3, interpolate=True)
                lp = synthio.Biquad(synthio.FilterMode.LOW_PASS, bd_pitch * 4.0, Q=0.7)
                osc1.frequency = bd_pitch
                osc1.envelope = env
                osc1.filter = lp
                osc1.bend = drop
                osc1.amplitude = amp * 0.7
                osc2.frequency = bd_pitch * 1.35
                osc2.envelope = env
                osc2.filter = lp
                osc2.amplitude = amp * 0.4
                synth.press(osc1)
                synth.press(osc2)

            # SD (38, 40) - tone + noise
            elif pitch in (38, 40):
                amp = base_amp * sd_level
                body, snare = circuit("sd", (TRIANGLE, NOISE))
                body.frequency = sd_pitch
                body.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.1, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                body.bend = synthio.LFO(waveform=FALL, once=True, rate=40.0, scale=0.15, interpolate=True)
                body.amplitude = amp * 0.8
                snare.frequency = NOISE_HZ
                snare.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.15, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                snare.filter = synthio.Biquad(synthio.FilterMode.HIGH_PASS, 2000.0, Q=1.0)
                snare.amplitude = amp * sd_snappy
                synth.press(body)
                synth.press(snare)

            # Toms (41-50) - ONE shared circuit: the schematic's two
            # oscillators share ENV+LPF+VCA, so LT and HT choke each
            # other by retrigger, exactly as the hardware forced
            elif pitch in (41, 43, 45, 47, 48, 50):
                amp = base_amp * tom_level
                (note,) = circuit("tom", (SINE,))
                note.frequency = lt_pitch if pitch < 48 else ht_pitch
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.3, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                note.bend = synthio.LFO(waveform=FALL, once=True, rate=20.0, scale=0.2, interpolate=True)
                note.amplitude = amp
                synth.press(note)

            # Hats (42, 44, 46) - one VCA+HPF; retrigger is the choke.
            # (On hardware the open decay follows the sequencer tempo;
            # oh_decay is the closest reachable approximation - stated
            # divergence.)
            elif pitch in (42, 44, 46):
                amp = base_amp * hat_level
                is_open = pitch == 46
                (note,) = circuit("hat", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=oh_decay if is_open else ch_decay, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, CYM_HI, Q=0.8)
                note.amplitude = amp * 0.8
                synth.press(note)

            # Cymbal (49, 51) - two parallel fixed band chains
            elif pitch in (49, 51):
                amp = base_amp * cym_level
                hi, lo = circuit("cym", (NOISE, NOISE))
                env = synthio.Envelope(attack_time=0.001, decay_time=cym_decay, release_time=0.2, attack_level=1.0, sustain_level=0.0)
                hi.frequency = NOISE_HZ
                hi.envelope = env
                hi.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, CYM_HI, Q=0.9)
                hi.amplitude = amp * 0.55
                lo.frequency = NOISE_HZ
                lo.envelope = env
                lo.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, CYM_LO, Q=0.9)
                lo.amplitude = amp * 0.45
                synth.press(hi)
                synth.press(lo)

        elif event_type in (EVENT_NOTE_OFF, EVENT_NOTE_ON):
            name = PITCH_CIRCUIT.get(data0)
            if name is not None and name in circuits:
                for note in circuits[name]:
                    synth.release(note)

        elif event_type == EVENT_PARAMETER:
            if data0 == 0: master_level = value0
            elif data0 == 1: accent_level = value0
            elif data0 == 2: bd_level = value0
            elif data0 == 3: bd_decay = logmap(value0, 0.1, 0.6)
            elif data0 == 4: bd_pitch = logmap(value0, 45.0, 90.0)
            elif data0 == 5: sd_level = value0
            elif data0 == 6: sd_snappy = value0
            elif data0 == 7: sd_pitch = logmap(value0, 150.0, 350.0)
            elif data0 == 8: lt_pitch = logmap(value0, 70.0, 140.0)
            elif data0 == 9: ht_pitch = logmap(value0, 110.0, 220.0)
            elif data0 == 10: cym_level = value0
            elif data0 == 11: cym_decay = logmap(value0, 0.2, 1.2)
            elif data0 == 12: tom_level = value0
            elif data0 == 13: hat_level = value0
            elif data0 == 14: ch_decay = logmap(value0, 0.02, 0.12)
            elif data0 == 15: oh_decay = logmap(value0, 0.1, 0.6)

    instrument = Instrument(synth, handle_event, PATCHES, MACRO_LABELS,
                            transport=transport, note_map=NOTE_MAP)
    return instrument
