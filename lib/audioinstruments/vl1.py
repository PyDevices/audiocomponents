"""Yamaha VL1 physical modelling synthesizer."""

NAME = 'vl1'
DISPLAY_NAME = 'VL1'
CATEGORIES = ('Synth',)
VERSION = '0.0.1'
VENDOR = "PyDevices"

MACRO_LABELS = (
    "Volume", "Breath Pressure", "Embouchure", "Growl Rate", "Growl Depth",
    "Attack", "Decay", "Sustain", "Release", "Master Tune",
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
    0: ('Default', (102, 102, 64, 25, 0, 85, 71, 102, 72, 64)),
}

import synthio

from audioinstruments._support import (
    EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PARAMETER, EVENT_POLY_PRESSURE,
    EVENT_CHANNEL_PRESSURE, gain, key_of, live, logmap, make_table,
)
from audioinstruments._support import Instrument
from audioinstruments import _support

# Complex FM carrier base for wind modeling
WAVE_WIND = make_table(((1, 1.0), (2, 0.4), (3, 0.2), (4, 0.1)), fast=False)
SINE = make_table(((1, 1.0),), fast=False)


def create(sample_rate, channel_count=2, transport=None):
    SR = sample_rate
    synth = _support.synthesizer(SR, channel_count)

    # Macros. The live ones are blocks every sounding note reads, so turning
    # the knob reaches a held note; the rest are read when a note starts.
    volume = live(0.8)
    breath = live(0.8)
    embouchure = live(0.5)
    # Normalised 0..1, not Hz: the macro sets this straight from value0 and the
    # LFO reads rate = 1.0 + growl_rate * 20.0. Written as 5.0 it meant 5 Hz,
    # which is both unreachable from the macro and a 101 Hz "growl". 0.2 gives
    # the 5 Hz that was plainly intended.
    growl_rate = live(0.2)
    growl_depth = live(0.0)
    amp_a = 0.1
    amp_d = 0.5
    amp_s = 0.8
    amp_r = 0.3
    master_tune = 1.0

    voices = {}
    serial = 0
    MAX_VOICES = 1 # Wind instruments are monophonic


    def release_voice(k):
        _support.release_voice(voices, synth, k)

    def steal_oldest():
        _support.steal_oldest(voices, release_voice)

    def handle_event(event_type, channel, note_id, data0, value0, value1, sample_position):
        nonlocal amp_a, amp_d, amp_s, amp_r, master_tune
        nonlocal serial

        k = key_of(channel, note_id, data0)

        if event_type == EVENT_NOTE_ON and value0 > 0.0:
            if len(voices) >= MAX_VOICES:
                steal_oldest()

            hz = synthio.midi_to_hz(data0 + value1) * master_tune

            # Breath pressure affects volume and filter cutoff simultaneously
            actual_amp = gain(volume, value0, breath)

            env = synthio.Envelope(attack_time=amp_a, decay_time=amp_d, release_time=amp_r, attack_level=1.0, sustain_level=amp_s)

            # Channel pressure retunes the breath-to-cutoff span (input b).
            cutoff = synthio.Math(synthio.MathOperation.SCALE_OFFSET, breath, 4000.0, 500.0)
            q = synthio.Math(synthio.MathOperation.SCALE_OFFSET, embouchure, 2.0, 1.0)
            lp = synthio.Biquad(synthio.FilterMode.LOW_PASS, cutoff, Q=q)

            # Growl is simulated via fast vibrato/FM. It reaches a held note
            # only if Growl Depth was up when the note started.
            growl_lfo = None
            if growl_depth.a > 0.01:
                growl_hz = synthio.Math(synthio.MathOperation.SCALE_OFFSET, growl_rate, 20.0, 1.0)
                growl_lfo = synthio.LFO(waveform=SINE, rate=growl_hz, scale=gain(growl_depth, 0.1))

            # Embouchure affects pitch slightly and harmonic content (via another layered note)
            n1 = synthio.Note(hz, waveform=WAVE_WIND, envelope=env, filter=lp, amplitude=gain(actual_amp, 0.7), bend=growl_lfo)
            n2 = synthio.Note(hz * 2.0, waveform=SINE, envelope=env, filter=lp, amplitude=gain(actual_amp, embouchure, 0.3), bend=growl_lfo)

            serial += 1
            voices[k] = ((n1, n2), serial, cutoff)
            synth.press(n1)
            synth.press(n2)

        elif event_type in (EVENT_NOTE_OFF, EVENT_NOTE_ON):
            release_voice(k)

        elif event_type in (EVENT_CHANNEL_PRESSURE, EVENT_POLY_PRESSURE):
            # The VL1 is a real physical-modeled wind instrument: it's played
            # with a breath controller, so ongoing breath pressure re-shapes
            # the tone of a note already sounding, not just its initial hit
            pressure = value0
            for voice in voices.values():
                voice[2].b = 2000.0 + pressure * 3000.0

        elif event_type == EVENT_PARAMETER:
            if data0 == 0: volume.a = value0
            elif data0 == 1: breath.a = value0
            elif data0 == 2: embouchure.a = value0
            elif data0 == 3: growl_rate.a = value0
            elif data0 == 4: growl_depth.a = value0
            # Time is heard as a ratio, so these travel logarithmically:
            # the steps crowd into the fast end, where a few milliseconds
            # change the articulation, instead of stepping over it.
            elif data0 == 5: amp_a = logmap(value0, 0.001, 1.001)
            elif data0 == 6: amp_d = logmap(value0, 0.05, 3.05)
            elif data0 == 7: amp_s = value0
            elif data0 == 8: amp_r = logmap(value0, 0.01, 4.01)
            elif data0 == 9: master_tune = 0.95 + value0 * 0.1

    instrument = Instrument(synth, handle_event, PATCHES, MACRO_LABELS,
                            transport=transport,
                            voices=MAX_VOICES)
    return instrument
