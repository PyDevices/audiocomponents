"""Roland TR-707 Rhythm Composer."""

NAME = 'tr707'
DISPLAY_NAME = 'TR-707'
CATEGORIES = ('Drum',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = (
    "Volume", "Kick Level", "Snare Level", "Tom Level", "HiHat Level",
    "Crash Level", "Overall Decay", "Master Tune", "Rim Level",
    "Cowbell Level", "Clap Level", "Tamb Level", "Ride Level",
)
MACRO_MODES = {
    0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR", 3: "UNIPOLAR",
    4: "UNIPOLAR", 5: "UNIPOLAR", 6: "UNIPOLAR", 7: "UNIPOLAR",
    8: "UNIPOLAR", 9: "UNIPOLAR", 10: "UNIPOLAR", 11: "UNIPOLAR",
    12: "UNIPOLAR",
}

# Patch 0 is the sound this instrument's defaults describe, so a fresh
# instance and patch 0 are the same thing - create() applies it.
PATCHES = {
    0: ("Default", (102, 102, 102, 102, 102, 102, 64, 64, 102, 102, 102,
                 102, 102)),
}

# The hardware's full 15-sound catalogue on its 10 playback channels -
# the module used to cover 8 of them. Note numbers follow the sibling
# modules' conventions (rim 37, clap 39, cowbell 56, ride 51) and GM for
# the tambourine (54).
NOTE_MAP = (
    (36, "Kick 1"),
    (35, "Kick 2"),
    (38, "Snare 1"),
    (40, "Snare 2"),
    (45, "Low Tom"),
    (47, "Mid Tom"),
    (50, "Hi Tom"),
    (37, "Rimshot"),
    (56, "Cowbell"),
    (39, "Clap"),
    (54, "Tambourine"),
    (42, "Closed Hat"),
    (46, "Open Hat"),
    (49, "Crash"),
    (51, "Ride"),
)

import synthio

from audioinstruments._support import (
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, FALL,
    make_table, noise_table,
)
from audioinstruments._support import Instrument

SINE = make_table(((1, 1.0),))
TRIANGLE = make_table([(n, (1.0 / (n*n)) * (-1)**((n-1)//2)) for n in range(1, 11, 2)])
# Mild-harmonic tone for toms (the ROM toms carry a little body grit).
TOMWAVE = make_table(((1, 1.0), (2, 0.25), (3, 0.12)))
# Cowbell: the classic two-partial pair in one table (harmonics 2 and 3
# of a half-frequency fundamental), same trick tr808 proved.
COWBELL = make_table(((2, 1.0), (3, 0.7)))
NOISE = noise_table(seed=707707)


def create(sample_rate, channel_count=2, transport=None):
    SR = sample_rate
    NOISE_HZ = SR / 8192.0
    synth = synthio.Synthesizer(sample_rate=SR, channel_count=channel_count)

    volume = 0.8
    lvl_kick = 0.8
    lvl_snare = 0.8
    lvl_tom = 0.8
    lvl_hh = 0.8
    lvl_crash = 0.8
    decay_scale = 0.5
    master_tune = 1.0
    lvl_rim = 0.8
    lvl_cb = 0.8
    lvl_clap = 0.8
    lvl_tamb = 0.8
    lvl_ride = 0.8

    # Fixed circuits (the tr808/tr909-proven architecture): permanent
    # Note objects retriggered in place, 11 residents for the hardware's
    # 10 playback channels (snare and kick body/noise pairs cost one
    # extra; well under the 13-note charter ceiling). The hardware's
    # channel sharing is modeled as itself: rimshot/cowbell share one
    # channel, clap/tambourine share one, open/closed hat share one and
    # choke by retrigger. Every voice is synthesized to the measured
    # numbers of the BOLT clean-capture pack - the TR-707 is ROM
    # playback, so there is no circuit to model, only the recorded
    # behavior to match; the 6-bit/low-rate ROM texture itself is
    # unmodeled, stated honestly in the dossier.
    circuits = {}

    def circuit(name, waveforms):
        notes = circuits.get(name)
        if notes is None:
            notes = tuple(synthio.Note(440.0, waveform=w, amplitude=0.0)
                          for w in waveforms)
            circuits[name] = notes
        return notes

    PITCH_CIRCUIT = {
        36: "kick", 35: "kick", 38: "sd", 40: "sd",
        45: "tom1", 47: "tom2", 50: "tom3",
        37: "rimcb", 56: "rimcb", 39: "claptamb", 54: "claptamb",
        42: "hat", 44: "hat", 46: "hat", 49: "crash", 51: "ride",
    }

    def handle_event(event_type, channel, note_id, data0, value0, value1, sample_position):
        nonlocal volume, lvl_kick, lvl_snare, lvl_tom, lvl_hh, lvl_crash
        nonlocal decay_scale, master_tune, lvl_rim, lvl_cb, lvl_clap
        nonlocal lvl_tamb, lvl_ride

        if event_type == EVENT_NOTE_ON and value0 > 0.0:
            pitch = data0
            amp = volume * value0
            dk = 0.5 + decay_scale  # Overall Decay: 0.5x-1.5x

            # Kick 1 (36) / Kick 2 (35) - one channel, two ROMs: same
            # circuit, slightly different tune and snap
            if pitch in (35, 36):
                (note,) = circuit("kick", (SINE,))
                base = 54.0 if pitch == 36 else 65.0
                note.frequency = base * master_tune
                note.envelope = synthio.Envelope(attack_time=0.002, decay_time=0.05 * dk, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.bend = synthio.LFO(waveform=FALL, once=True, rate=25.0, scale=0.35, interpolate=True)
                note.filter = synthio.Biquad(synthio.FilterMode.LOW_PASS, 320.0, Q=0.8)
                note.amplitude = amp * lvl_kick
                synth.press(note)

            # Snare 1 (38) / Snare 2 (40)
            elif pitch in (38, 40):
                body, snare = circuit("sd", (SINE, NOISE))
                body.frequency = 150.0 * master_tune
                body.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.06 * dk, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                body.amplitude = amp * lvl_snare * 0.7
                snare.frequency = NOISE_HZ
                snare.envelope = synthio.Envelope(attack_time=0.001, decay_time=(0.08 if pitch == 38 else 0.11) * dk, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                snare.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 3300.0 if pitch == 38 else 3000.0, Q=0.9)
                snare.amplitude = amp * lvl_snare * 0.8
                synth.press(body)
                synth.press(snare)

            # Toms (45, 47, 50) - long ROM toms with a slow settle
            elif pitch in (45, 47, 50):
                name, tune, decay = {
                    45: ("tom1", 128.0, 0.55),
                    47: ("tom2", 150.0, 0.45),
                    50: ("tom3", 193.0, 0.30),
                }[pitch]
                (note,) = circuit(name, (TOMWAVE,))
                note.frequency = tune * master_tune
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=decay * dk, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                note.bend = synthio.LFO(waveform=FALL, once=True, rate=3.0, scale=0.14, interpolate=True)
                note.amplitude = amp * lvl_tom
                synth.press(note)

            # Rimshot (37) - shares its channel with the cowbell
            elif pitch == 37:
                (note,) = circuit("rimcb", (TRIANGLE,))
                note.waveform = TRIANGLE
                note.frequency = 940.0 * master_tune
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.045 * dk, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 2800.0, Q=0.9)
                note.amplitude = amp * lvl_rim
                synth.press(note)

            # Cowbell (56) - the other face of the rim channel
            elif pitch == 56:
                (note,) = circuit("rimcb", (TRIANGLE,))
                # The shared channel's other face: swap the waveform in
                # place (assignable on every runtime - verified).
                note.waveform = COWBELL
                note.frequency = 274.0 * master_tune
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.1 * dk, release_time=0.03, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 800.0, Q=0.9)
                note.amplitude = amp * lvl_cb
                synth.press(note)

            # Clap (39) - shares its channel with the tambourine
            elif pitch == 39:
                (note,) = circuit("claptamb", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.002, decay_time=0.1 * dk, release_time=0.04, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 1150.0, Q=1.0)
                note.amplitude = amp * lvl_clap
                synth.press(note)

            # Tambourine (54)
            elif pitch == 54:
                (note,) = circuit("claptamb", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.13 * dk, release_time=0.04, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 6500.0, Q=1.2)
                note.amplitude = amp * lvl_tamb
                synth.press(note)

            # Hats (42, 44, 46) - one channel; the choke is the retrigger
            elif pitch in (42, 44, 46):
                is_open = pitch == 46
                (note,) = circuit("hat", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=(0.75 if is_open else 0.06) * dk, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 7300.0, Q=0.8)
                note.amplitude = amp * lvl_hh * 0.8
                synth.press(note)

            # Crash (49)
            elif pitch == 49:
                (note,) = circuit("crash", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=1.2 * dk, release_time=0.3, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 3400.0, Q=0.95)
                note.amplitude = amp * lvl_crash * 0.8
                synth.press(note)

            # Ride (51)
            elif pitch == 51:
                (note,) = circuit("ride", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.85 * dk, release_time=0.25, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 7200.0, Q=1.0)
                note.amplitude = amp * lvl_ride * 0.7
                synth.press(note)

            # Fallback - rides the clap/tamb channel
            else:
                (note,) = circuit("claptamb", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.1, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.BAND_PASS, 3000.0, Q=1.0)
                note.amplitude = amp * 0.5
                synth.press(note)

        elif event_type in (EVENT_NOTE_OFF, EVENT_NOTE_ON):
            name = PITCH_CIRCUIT.get(data0)
            if name is not None and name in circuits:
                for note in circuits[name]:
                    synth.release(note)

        elif event_type == EVENT_PARAMETER:
            if data0 == 0: volume = value0
            elif data0 == 1: lvl_kick = value0
            elif data0 == 2: lvl_snare = value0
            elif data0 == 3: lvl_tom = value0
            elif data0 == 4: lvl_hh = value0
            elif data0 == 5: lvl_crash = value0
            elif data0 == 6: decay_scale = value0
            elif data0 == 7: master_tune = 0.95 + value0 * 0.1
            elif data0 == 8: lvl_rim = value0
            elif data0 == 9: lvl_cb = value0
            elif data0 == 10: lvl_clap = value0
            elif data0 == 11: lvl_tamb = value0
            elif data0 == 12: lvl_ride = value0

    instrument = Instrument(synth, handle_event, PATCHES, MACRO_LABELS,
                            transport=transport, note_map=NOTE_MAP)
    return instrument
