"""Farfisa Compact combo organ."""

NAME = 'farfisa'
DISPLAY_NAME = 'Farfisa Compact'
CATEGORIES = ('Synth',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = (
    "Volume", "Bass", "Strings", "Flute", "Oboe", "Trumpet",
    "Multi-Tone Booster", "Vibrato Rate", "Vibrato Depth", "Master Tune",
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
    9: "BIPOLAR",
}

# Patch 0 is the sound this instrument's defaults describe, so a fresh
# instance and patch 0 are the same thing - create() applies it. A macro
# a caller does not set resolves here rather than to the middle of its
# range.
PATCHES = {
    0: ("Default", (102, 127, 127, 127, 64, 64, 0, 75, 0, 64)),
}

import synthio

from audioinstruments._support import (
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, gain, key_of, live,
    make_table,
)
from audioinstruments._support import Instrument
from audioinstruments import _support

# Various Farfisa-like transistor waves
WAVE_STR = make_table([(n, 1.0 / n) for n in range(1, 40)], fast=False)
WAVE_FLUTE = make_table(((1, 1.0), (3, 0.2)), fast=False)
WAVE_OBOE = make_table([(n, 1.0 / n) for n in range(1, 40, 2)], fast=False)
WAVE_TRUMPET = make_table(((1, 1.0), (2, 0.8), (3, 0.6), (4, 0.4)), fast=False)
SINE = make_table(((1, 1.0),), fast=False)

# Boosted (Multi-Tone Booster engaged) versions with asymmetric clipping
WAVE_STR_BOOST = make_table([(n, 1.0 / n) for n in range(1, 40)], asym=0.3, fast=False)
WAVE_FLUTE_BOOST = make_table(((1, 1.0), (3, 0.2)), asym=0.3, fast=False)
WAVE_OBOE_BOOST = make_table([(n, 1.0 / n) for n in range(1, 40, 2)], asym=0.3, fast=False)
WAVE_TRUMPET_BOOST = make_table(((1, 1.0), (2, 0.8), (3, 0.6), (4, 0.4)), asym=0.3, fast=False)


def create(sample_rate, channel_count=2, transport=None):
    SR = sample_rate
    synth = _support.synthesizer(SR, channel_count)

    # Macros. The live ones are blocks every sounding note reads, so turning
    # the knob reaches a held note; the rest are read when a note starts.
    volume = live(0.8)
    bass = live(1.0)
    strings = live(1.0)
    flute = live(1.0)
    oboe = live(0.5)
    trumpet = live(0.5)
    multi_tone = 0.0
    vib_rate = live(6.0)
    vib_depth = live(0.0)
    master_tune = 1.0

    voices = {}
    serial = 0
    MAX_VOICES = 8


    def release_voice(k):
        _support.release_voice(voices, synth, k)

    def steal_oldest():
        _support.steal_oldest(voices, release_voice)

    def handle_event(event_type, channel, note_id, data0, value0, value1, sample_position):
        nonlocal multi_tone, master_tune
        nonlocal serial

        k = key_of(channel, note_id, data0)

        if event_type == EVENT_NOTE_ON and value0 > 0.0:
            release_voice(k)
            if len(voices) >= MAX_VOICES:
                steal_oldest()

            hz = synthio.midi_to_hz(data0 + value1) * master_tune
            amp = gain(volume, value0)

            env = synthio.Envelope(attack_time=0.01, decay_time=0.1, release_time=0.1, attack_level=1.0, sustain_level=1.0)

            # Multi-tone booster is a gritty overdrive stage (asymmetric clip
            # waveforms) that also brightens the tone with a hotter highpass
            boosted = multi_tone > 0.5
            cutoff = 5000.0 if boosted else 15000.0
            filter_mode = synthio.FilterMode.HIGH_PASS if boosted else synthio.FilterMode.LOW_PASS
            lp = synthio.Biquad(filter_mode, cutoff, Q=1.0)

            # Vibrato Depth and Rate reach a held note only if the vibrato
            # was on when the note started.
            vib_lfo = synthio.LFO(waveform=SINE, rate=vib_rate, scale=gain(vib_depth, 0.02)) if vib_depth.a > 0.01 else None

            w_str = WAVE_STR_BOOST if boosted else WAVE_STR
            w_flute = WAVE_FLUTE_BOOST if boosted else WAVE_FLUTE
            w_oboe = WAVE_OBOE_BOOST if boosted else WAVE_OBOE
            w_trumpet = WAVE_TRUMPET_BOOST if boosted else WAVE_TRUMPET

            # A tab at zero adds no note, so it reaches a held note only if
            # it was up when the note started.
            notes = []
            if bass.a > 0.01: notes.append(synthio.Note(hz * 0.5, waveform=w_str, envelope=env, filter=lp, amplitude=gain(amp, bass, 0.2), bend=vib_lfo))
            if strings.a > 0.01: notes.append(synthio.Note(hz, waveform=w_str, envelope=env, filter=lp, amplitude=gain(amp, strings, 0.2), bend=vib_lfo))
            if flute.a > 0.01: notes.append(synthio.Note(hz, waveform=w_flute, envelope=env, filter=lp, amplitude=gain(amp, flute, 0.2), bend=vib_lfo))
            if oboe.a > 0.01: notes.append(synthio.Note(hz, waveform=w_oboe, envelope=env, filter=lp, amplitude=gain(amp, oboe, 0.2), bend=vib_lfo))
            if trumpet.a > 0.01: notes.append(synthio.Note(hz, waveform=w_trumpet, envelope=env, filter=lp, amplitude=gain(amp, trumpet, 0.2), bend=vib_lfo))

            serial += 1
            voices[k] = (tuple(notes), serial)
            for n in notes:
                synth.press(n)

        elif event_type in (EVENT_NOTE_OFF, EVENT_NOTE_ON):
            release_voice(k)

        elif event_type == EVENT_PARAMETER:
            if data0 == 0: volume.a = value0
            elif data0 == 1: bass.a = value0
            elif data0 == 2: strings.a = value0
            elif data0 == 3: flute.a = value0
            elif data0 == 4: oboe.a = value0
            elif data0 == 5: trumpet.a = value0
            elif data0 == 6: multi_tone = value0
            elif data0 == 7: vib_rate.a = 0.1 + value0 * 10.0
            elif data0 == 8: vib_depth.a = value0
            elif data0 == 9: master_tune = 0.95 + value0 * 0.1

    instrument = Instrument(synth, handle_event, PATCHES, MACRO_LABELS,
                            transport=transport)
    return instrument
