"""Roland TR-909 Rhythm Composer."""

NAME = 'tr909'
DISPLAY_NAME = 'TR-909'
CATEGORIES = ('Drum',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = (
    "Level", "Accent", "BD Tune", "BD Attack", "BD Decay", "SD Tune",
    "SD Tone", "SD Snappy", "LT Tune", "MT Tune", "HT Tune", "Tom Decay",
    "Clap/Rim", "CH Decay", "OH Decay", "Cymbal Tune",
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
    0: ("Default", (102, 64, 51, 64, 76, 56, 60, 64, 74, 71, 71, 85, 64, 100,
                 64, 74)),
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
)

import synthio

from audioinstruments._support import (
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, FALL, logmap,
    make_table, noise_table,
)
from audioinstruments._support import Instrument

import array

SINE = make_table(((1, 1.0),))
# The tom/kick VCO passes a shaper on hardware; a couple of soft
# harmonics carry the measured spectral centroid a bare sine cannot.
TOMWAVE = make_table(((1, 1.0), (2, 0.35), (3, 0.18), (4, 0.10)))
NOISE = noise_table(seed=909090)

# The clap's flutter, as the hardware makes it: one noise chain whose VCA
# is driven by a sawtooth envelope (service notes block diagram) - not
# three staggered notes. Three bumps ~12 ms apart, then the tail; played
# once over ~400 ms by an amplitude LFO.
FLUTTER = array.array("h", [32767, 4800, 31000, 4800, 29000, 9800]
                     + [int(27000 * 2.718281828 ** (-i / 16.0)) for i in range(58)])


def create(sample_rate, channel_count=2, transport=None):
    SR = sample_rate
    NOISE_HZ = SR / 8192.0
    synth = synthio.Synthesizer(sample_rate=SR, channel_count=channel_count)

    # Master params
    master_level = 0.8
    accent_level = 0.5

    # BD params (macro ranges retuned to the Audiorealism known-settings
    # grids - see docs/dossiers/tr909.md section 6)
    bd_tune = 50.0
    bd_attack = 0.5
    bd_decay = 0.15

    # SD params
    sd_tune = 180.0
    sd_tone = 1500.0
    sd_snappy = 0.5

    # Toms
    lt_tune = 90.0
    mt_tune = 110.0
    ht_tune = 130.0
    tom_decay = 0.2

    # Others
    clap_rim_level = 0.5
    ch_decay = 0.05
    oh_decay = 0.12
    cym_tune = 6000.0

    # Fixed circuits, exactly like the hardware (and like tr808's proven
    # rebuild): every voice is a permanent set of Note objects retriggered
    # in place. Nothing is allocated at strike time and nothing is
    # released mid-play, so the kit resides at 13 Notes - exactly the
    # ceiling the charter sets (synthio's core caps at 14 simultaneous
    # notes on every runtime; audioif#8/#9 make 13 the safe maximum).
    # The 13th is a single stick-click shared by all three toms - the
    # dossier's stretch slot, spent there rather than on the snare's
    # second VCO because the reference captures' tom centroid is
    # unreachable from a bare tone (the schematic's noise source is
    # labeled "Tom Noise" and sits on the tom board).
    # The sharing is the hardware's own: one PCM engine plays open AND
    # closed hat, and one plays crash AND ride (service notes block
    # diagram; the crash/ride choke is the dossier's moderate-confidence
    # call - degrade to separate circuits if the batch listen refuses it).
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
        41: "tom_lo", 43: "tom_lo", 45: "tom_mid", 47: "tom_mid",
        48: "tom_hi", 50: "tom_hi",
        42: "hat", 44: "hat", 46: "hat",
        49: "cym", 51: "cym", 57: "cym", 59: "cym",
        39: "clap", 37: "rim",
    }

    def handle_event(event_type, channel, note_id, data0, value0, value1, sample_position):
        nonlocal master_level, accent_level, bd_tune, bd_attack, bd_decay
        nonlocal sd_tune, sd_tone, sd_snappy, lt_tune, mt_tune, ht_tune, tom_decay
        nonlocal clap_rim_level, ch_decay, oh_decay, cym_tune

        if event_type == EVENT_NOTE_ON and value0 > 0.0:
            pitch = data0
            vel = value0
            amp = master_level * (vel + accent_level * (1.0 if vel > 0.8 else 0.0))

            # BD (35, 36) - a VCO with a CV pitch-drop envelope plus a
            # separate gated click layer (service notes block diagram:
            # CV Gen -> VCO -> shaper -> VCA, ENV3 pulling the CV down
            # from an elevated onset; Pulse Gen + noise -> VCA under the
            # Attack pot). NOT a bridged-T like the 808: one downward
            # sweep is the correct shape, and the measured drop ratio
            # grows with the tune setting (1.5x at the bottom of the
            # knob, 2.0x at the top), so the sweep depth follows bd_tune.
            if pitch in (35, 36):
                body, click = circuit("bd", (SINE, NOISE))
                body.frequency = bd_tune
                body.envelope = synthio.Envelope(attack_time=0.004, decay_time=bd_decay, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                drop_oct = 0.585 + 0.415 * (bd_tune - 46.0) / 38.0
                body.bend = synthio.LFO(waveform=FALL, once=True, rate=25.0, scale=drop_oct, interpolate=True)
                body.filter = synthio.Biquad(synthio.FilterMode.LOW_PASS, bd_tune * 3.2, Q=0.9)
                body.amplitude = amp * 0.72
                click.frequency = NOISE_HZ
                click.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.015, release_time=0.01, attack_level=1.0, sustain_level=0.0)
                # LOW-passed, as the schematic draws it (noise through a
                # low-pass into the click VCA): a dull knock that raises
                # the onset peak - the Attack knob's measured effect, a
                # ~4 dB span on hardware - without the high-frequency
                # mass that a high-passed click smeared over the kick's
                # very dark spectrum (reference trimmed centroid ~160 Hz).
                click.filter = synthio.Biquad(synthio.FilterMode.LOW_PASS, 900.0, Q=1.0)
                click.amplitude = amp * bd_attack * 2.2
                synth.press(body)
                synth.press(click)

            # SD (38, 40) - tone body plus a noise path whose high-pass
            # cutoff is the Tone knob's real target (block diagram: CV
            # Gen IC35 sets the noise HP; Snappy blends the noise in)
            elif pitch in (38, 40):
                body, snare = circuit("sd", (SINE, NOISE))
                body.frequency = sd_tune
                body.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.12, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                body.bend = synthio.LFO(waveform=FALL, once=True, rate=35.0, scale=0.3, interpolate=True)
                body.amplitude = amp * 0.8
                snare.frequency = NOISE_HZ
                snare.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.22, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                # Band-passed rather than bare high-passed noise: the
                # Tone macro still positions the band (x4 keeps its
                # 800-3000 Hz panel range meaningful), and the measured
                # snare centroid (~8.5 kHz) is reachable, which bare HP
                # noise at 48 kHz is not.
                snare.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, sd_tone * 4.0, Q=0.55)
                snare.amplitude = amp * sd_snappy
                synth.press(body)
                synth.press(snare)

            # Toms (41/43, 45/47, 48/50) - pure VCO+VCA+ENV per the block
            # diagram: NO noise layer (the old per-tom noise click had no
            # schematic counterpart and is gone). One shared Decay pot,
            # as on the panel. Tune ranges retuned to the measured 11x11
            # grids.
            elif pitch in (41, 43, 45, 47, 48, 50):
                if pitch in (41, 43):
                    name, tune = "tom_lo", lt_tune
                elif pitch in (45, 47):
                    name, tune = "tom_mid", mt_tune
                else:
                    name, tune = "tom_hi", ht_tune
                (note,) = circuit(name, (TOMWAVE,))
                note.frequency = tune
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=tom_decay, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                note.bend = synthio.LFO(waveform=FALL, once=True, rate=30.0, scale=0.5, interpolate=True)
                note.amplitude = amp
                click = circuit("tom_click", (NOISE,))[0]
                click.frequency = NOISE_HZ
                click.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.018, release_time=0.01, attack_level=1.0, sustain_level=0.0)
                click.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 2600.0, Q=0.8)
                click.amplitude = amp * (0.6 if name == "tom_lo" else (0.08 if name == "tom_mid" else 0.03))
                synth.press(note)
                synth.press(click)

            # Hats (42, 44, 46) - one PCM engine on hardware (one Memory/
            # D-A/VCA chain, one Multi Out jack): open and closed share
            # the circuit and choke by retrigger.
            elif pitch in (42, 44, 46):
                is_open = pitch == 46
                (note,) = circuit("hat", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=oh_decay if is_open else ch_decay, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 7100.0 if is_open else 9000.0, Q=0.8 if is_open else 0.7)
                note.amplitude = amp * 0.7
                synth.press(note)

            # Cymbals (Crash 49/57, Ride 51/59) - one PCM engine, two
            # output taps on hardware; the Tune knob is the engine's
            # clock, so raising it shortens decay as it raises pitch -
            # the measured tune-linked-decay coupling, kept here.
            elif pitch in (49, 51, 57, 59):
                is_ride = pitch in (51, 59)
                (note,) = circuit("cym", (NOISE,))
                note.frequency = NOISE_HZ
                clock = 6000.0 / cym_tune
                base = 0.72 if is_ride else 0.70
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=base * clock, release_time=0.2, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, cym_tune * (1.3 if is_ride else 1.5), Q=1.0 if is_ride else 0.75)
                note.amplitude = amp * 0.6
                synth.press(note)

            # Clap (39) - one noise chain whose amplitude is shaped by
            # the sawtooth flutter envelope, exactly as the block diagram
            # draws it; not three staggered notes.
            elif pitch == 39:
                (note,) = circuit("clap", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.45, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 950.0, Q=1.1)
                flut = synthio.LFO(waveform=FLUTTER, once=True, rate=2.5, scale=1.0, interpolate=True)
                note.amplitude = synthio.Math(synthio.MathOperation.PRODUCT, flut, amp * clap_rim_level * 1.6, 1.0)
                synth.press(note)

            # Rimshot (37) - filtered noise through parallel band-passes
            # and a clipper on hardware (three bands; two Notes is the
            # controlled simplification), NOT tuned oscillators.
            elif pitch == 37:
                low, high = circuit("rim", (NOISE, NOISE))
                # A short burst into resonant bands, so the filters ring
                # like the hardware's F1/F2/F3 bank instead of being fed
                # noise for the whole envelope.
                env = synthio.Envelope(attack_time=0.001, decay_time=0.062, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                low.frequency = NOISE_HZ
                low.envelope = env
                low.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 520.0, Q=7.0)
                low.amplitude = amp * clap_rim_level * 1.1
                high.frequency = NOISE_HZ
                high.envelope = env
                high.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 1100.0, Q=6.0)
                high.amplitude = amp * clap_rim_level * 0.08
                synth.press(low)
                synth.press(high)

            # Fallback (other percussion) - rides the rimshot circuit
            else:
                low, _high = circuit("rim", (NOISE, NOISE))
                low.frequency = NOISE_HZ
                low.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.1, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                low.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 3000.0, Q=1.0)
                low.amplitude = amp * 0.5
                synth.press(low)

        elif event_type in (EVENT_NOTE_OFF, EVENT_NOTE_ON):
            name = PITCH_CIRCUIT.get(data0)
            if name is not None and name in circuits:
                for note in circuits[name]:
                    synth.release(note)

        elif event_type == EVENT_PARAMETER:
            if data0 == 0: master_level = value0
            elif data0 == 1: accent_level = value0
            elif data0 == 2: bd_tune = logmap(value0, 46.0, 84.0)
            elif data0 == 3: bd_attack = value0
            elif data0 == 4: bd_decay = logmap(value0, 0.09, 0.28)
            elif data0 == 5: sd_tune = logmap(value0, 120.0, 240.0)
            elif data0 == 6: sd_tone = logmap(value0, 800.0, 3000.0)
            elif data0 == 7: sd_snappy = value0
            elif data0 == 8: lt_tune = logmap(value0, 60.0, 120.0)
            elif data0 == 9: mt_tune = logmap(value0, 75.0, 145.0)
            elif data0 == 10: ht_tune = logmap(value0, 90.0, 175.0)
            elif data0 == 11: tom_decay = logmap(value0, 0.12, 0.38)
            elif data0 == 12: clap_rim_level = value0
            elif data0 == 13: ch_decay = logmap(value0, 0.028, 0.095)
            elif data0 == 14: oh_decay = logmap(value0, 0.04, 0.25)
            elif data0 == 15: cym_tune = logmap(value0, 4000.0, 8000.0)

    instrument = Instrument(synth, handle_event, PATCHES, MACRO_LABELS,
                            transport=transport, note_map=NOTE_MAP)
    return instrument
