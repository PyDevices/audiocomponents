"""E-mu SP-1200."""

NAME = 'sp1200'
DISPLAY_NAME = 'SP-1200'
CATEGORIES = ('Drum',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = (
    "Volume", "Kick Pitch", "Kick Ring", "Snare Pitch", "Snare Snap",
    "Hihat Pitch", "SP Crunch", "Master Tune",
)
MACRO_MODES = {
    0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR", 3: "UNIPOLAR",
    4: "UNIPOLAR", 5: "UNIPOLAR", 6: "UNIPOLAR", 7: "UNIPOLAR",
}

PATCHES = {
    0: ("Default", (102, 64, 64, 64, 64, 64, 64, 64)),
}

# The hardware's eight playback channels (service manual Fig. 2: eight
# parallel Demux -> S/H -> Filter -> Mix paths; channels 7 and 8 are
# direct outs, the rest filtered). Note numbers follow the sibling
# conventions (rim 37, clap 39, cowbell 56; tom 41 as tr808/tr909).
NOTE_MAP = (
    (36, "Kick"),
    (38, "Snare"),
    (42, "Closed Hat"),
    (46, "Open Hat"),
    (37, "Rimshot"),
    (39, "Clap"),
    (41, "Tom"),
    (56, "Cowbell"),
)

import synthio

from audioinstruments._support import (
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, FALL, logmap,
    make_table, noise_table,
)
from audioinstruments._support import Instrument

SINE = make_table(((1, 1.0),))
PULSE = make_table([(n, 1.0 / n) for n in range(1, 15)])
COWBELL = make_table(((2, 1.0), (3, 0.7)))
NOISE = noise_table(seed=1200)

#: The anti-alias ceiling: ~26.04 kHz sampling means nothing above
#: ~13 kHz ever left the real converters (service manual p.41 memory
#: math; Yeh ICMC'07 measured ~26 kHz on the sibling SP-12).
BANDWIDTH = 13000.0


def create(sample_rate, channel_count=2, transport=None):
    SR = sample_rate
    NOISE_HZ = SR / 8192.0
    synth = synthio.Synthesizer(sample_rate=SR, channel_count=channel_count)

    volume = 0.8
    kick_p = 1.0      # pitch RATIOS, spanning Yeh's measured extremes
    kick_ring = 0.5
    snare_p = 1.0
    snare_snap = 0.5
    hh_p = 1.0
    crunch = 0.5
    master_tune = 1.0

    # Fixed circuits: one permanent Note group per hardware channel -
    # the 8-voice ceiling is the architecture, exactly as the manual
    # draws it ("if it had 8 channels in real life, it has 8 voice
    # slots here"). 12 resident Notes: kick body+grit, snare body+snap,
    # CH, OH, rim, clap, tom, cowbell, plus the 12-bit noise-floor
    # proxy under kick and snare. Channels 1-6 pass a modeled SSM2044
    # (an attack-time exponential cutoff sweep - the release_filter
    # idiom run forward); channels 7-8 (tom, cowbell) are direct outs
    # with only the anti-alias ceiling, exactly per the manual, even
    # though a filtered tom would sound more "natural".
    circuits = {}

    def circuit(name, waveforms):
        notes = circuits.get(name)
        if notes is None:
            notes = tuple(synthio.Note(440.0, waveform=w, amplitude=0.0)
                          for w in waveforms)
            circuits[name] = notes
        return notes

    def vcf(rest, q=0.9):
        # SSM2044 behavior per Yeh: cutoff opens at trigger and decays
        # approximately exponentially to rest; Q barely moves. SP Crunch
        # is the sweep's depth - 0 leaves the filter static at rest.
        depth = rest * crunch * 2.5
        lfo = synthio.LFO(waveform=FALL, once=True, rate=9.0, interpolate=True)
        cutoff = synthio.Math(synthio.MathOperation.SCALE_OFFSET, lfo, depth, rest)
        return synthio.Biquad(synthio.FilterMode.LOW_PASS, cutoff, Q=q)

    def qlevel(a):
        # The level DAC is 8-bit on hardware: 256 discrete amplitudes,
        # modeled exactly (manual p.41).
        step = round(a * 255.0)
        return step / 255.0

    PITCH_CIRCUIT = {
        36: "kick", 38: "sd", 42: "ch", 46: "oh",
        37: "rim", 39: "clap", 41: "tom", 56: "cb",
    }

    def handle_event(event_type, channel, note_id, data0, value0, value1, sample_position):
        nonlocal volume, kick_p, kick_ring, snare_p, snare_snap, hh_p
        nonlocal crunch, master_tune

        if event_type == EVENT_NOTE_ON and value0 > 0.0:
            pitch = data0
            amp = qlevel(volume * value0)

            # Kick (36) - channel 1, filtered. Pitch and decay are one
            # control on a sampler: raising playback rate shortens the
            # read (Yeh Figs. 6-7: 2/3x length at max up, 1.56x at max
            # down) - the ratio drives both.
            if pitch == 36:
                body, grit, floor = circuit("kick", (SINE, PULSE, NOISE))
                ratio = kick_p * master_tune
                body.frequency = 52.0 * ratio
                base_decay = 0.28 + kick_ring * 0.35
                body.envelope = synthio.Envelope(attack_time=0.002, decay_time=base_decay / ratio, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                body.bend = synthio.LFO(waveform=FALL, once=True, rate=20.0, scale=0.4, interpolate=True)
                body.filter = vcf(4200.0)
                body.amplitude = amp
                grit.frequency = 52.0 * ratio
                grit.envelope = synthio.Envelope(attack_time=0.002, decay_time=0.06 / ratio, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                grit.filter = vcf(1400.0, q=0.8)
                grit.amplitude = amp * 0.12
                floor.frequency = NOISE_HZ
                # The 12-bit converter's noise floor outlasts the sound
                # itself on hardware; the proxy decays slower than the
                # body so the voice settles into it (~-72 dBFS tail).
                floor.envelope = synthio.Envelope(attack_time=0.002, decay_time=1.3, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                floor.filter = synthio.Biquad(synthio.FilterMode.LOW_PASS, BANDWIDTH, Q=0.7)
                floor.amplitude = 0.0012
                synth.press(body)
                synth.press(grit)
                synth.press(floor)

            # Snare (38) - channel 2, filtered. Two Notes approximate
            # ONE recorded sample's spectrum (the hardware plays a
            # single sample; the split is a synthesis convenience, not
            # a hardware fact).
            elif pitch == 38:
                body, snap, floor = circuit("sd", (SINE, NOISE, NOISE))
                ratio = snare_p * master_tune
                body.frequency = 165.0 * ratio
                body.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.09 / ratio, release_time=0.04, attack_level=1.0, sustain_level=0.0)
                body.amplitude = amp * 0.7
                snap.frequency = NOISE_HZ
                snap.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.11 / ratio, release_time=0.05, attack_level=1.0, sustain_level=0.0)
                snap.filter = vcf(3400.0, q=0.9)
                snap.amplitude = amp * (0.4 + snare_snap * 0.6)
                floor.frequency = NOISE_HZ
                floor.envelope = synthio.Envelope(attack_time=0.001, decay_time=1.3, release_time=0.1, attack_level=1.0, sustain_level=0.0)
                floor.filter = synthio.Biquad(synthio.FilterMode.LOW_PASS, BANDWIDTH, Q=0.7)
                floor.amplitude = 0.0012
                synth.press(body)
                synth.press(snap)
                synth.press(floor)

            # Hats (42, 46) - channels 3 and 4: separate samples on
            # separate channels on this machine (a sampler, not the
            # 707/909's shared engine), so no choke is modeled.
            elif pitch in (42, 46):
                is_open = pitch == 46
                (note,) = circuit("oh" if is_open else "ch", (NOISE,))
                ratio = hh_p * master_tune
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=(0.45 if is_open else 0.05) / ratio, release_time=0.04, attack_level=1.0, sustain_level=0.0)
                note.filter = vcf(min(BANDWIDTH, 9500.0 * ratio), q=0.8)
                note.amplitude = amp * 0.6
                synth.press(note)

            # Rimshot (37) - channel 5, filtered
            elif pitch == 37:
                (note,) = circuit("rim", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.03, release_time=0.02, attack_level=1.0, sustain_level=0.0)
                note.filter = vcf(2400.0, q=1.2)
                note.amplitude = amp * 0.8
                synth.press(note)

            # Clap (39) - channel 6, filtered; one recorded sample on
            # hardware, so one Note is the accurate count here
            elif pitch == 39:
                (note,) = circuit("clap", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.002, decay_time=0.1, release_time=0.04, attack_level=1.0, sustain_level=0.0)
                note.filter = vcf(1300.0, q=1.0)
                note.amplitude = amp * 0.9
                synth.press(note)

            # Tom (41) - channel 7, DIRECT out: no VCF, only the
            # anti-alias ceiling
            elif pitch == 41:
                (note,) = circuit("tom", (SINE,))
                note.frequency = 110.0 * master_tune
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.25, release_time=0.08, attack_level=1.0, sustain_level=0.0)
                note.bend = synthio.LFO(waveform=FALL, once=True, rate=8.0, scale=0.2, interpolate=True)
                note.filter = synthio.Biquad(synthio.FilterMode.LOW_PASS, BANDWIDTH, Q=0.7)
                note.amplitude = amp
                synth.press(note)

            # Cowbell (56) - channel 8, DIRECT out
            elif pitch == 56:
                (note,) = circuit("cb", (COWBELL,))
                note.frequency = 270.0 * master_tune
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.09, release_time=0.03, attack_level=1.0, sustain_level=0.0)
                note.filter = synthio.Biquad(synthio.FilterMode.LOW_PASS, BANDWIDTH, Q=0.7)
                note.amplitude = amp * 0.8
                synth.press(note)

            # Fallback - rides the clap channel
            else:
                (note,) = circuit("clap", (NOISE,))
                note.frequency = NOISE_HZ
                note.envelope = synthio.Envelope(attack_time=0.001, decay_time=0.08, release_time=0.04, attack_level=1.0, sustain_level=0.0)
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
            # Pitch macros are RATIOS spanning Yeh's measured extremes:
            # 0.64x (1.56x length) up to 1.5x (2/3 length).
            elif data0 == 1: kick_p = logmap(value0, 0.64, 1.5)
            elif data0 == 2: kick_ring = value0
            elif data0 == 3: snare_p = logmap(value0, 0.64, 1.5)
            elif data0 == 4: snare_snap = value0
            elif data0 == 5: hh_p = logmap(value0, 0.64, 1.5)
            elif data0 == 6: crunch = value0
            elif data0 == 7: master_tune = 0.95 + value0 * 0.1

    instrument = Instrument(synth, handle_event, PATCHES, MACRO_LABELS,
                            transport=transport, note_map=NOTE_MAP)
    return instrument
