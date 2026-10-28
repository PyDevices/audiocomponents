# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Run plucked notes through a tape echo and a hall, and save a WAV file.

A synthio Synthesizer plays short notes, a TapeDelay repeats them and a
Reverb puts them in a hall. Each effect takes the one before it as its
input, and the program writes the end of the chain to a WAV file you can
open in any audio player. Change the names to hear any of the forty-five.

Needs: audioeffects and audiodsp. Both are built into the PyDevices
MicroPython firmware; on CPython, pip install pydevices-audioeffects.

Run it:
    micropython audioeffects_simpletest.py

Tested on: the unix port of MicroPython and CPython 3.12 on Linux.
"""

import struct

import audiocore
import audioeffects
import synthio

# Change these to match your setup.
FILENAME = "echoes.wav"
NOTES = (60, 67, 64, 72)  # MIDI note numbers
NOTE_SECONDS = 0.6
SAMPLE_RATE = 22050
ECHO_MS = 300  # time between the repeats

# A synthesizer whose notes die away quickly, so the echoes stand out.
envelope = synthio.Envelope(attack_time=0.005, decay_time=0.2, sustain_level=0)
synth = synthio.Synthesizer(sample_rate=SAMPLE_RATE, envelope=envelope)

# A tape echo fed by the synthesizer, then a hall fed by the echo.
echo = audioeffects.create("TapeDelay", synth, SAMPLE_RATE,
                           time_ms=ECHO_MS, feedback=0.4, mix=0.35)
hall = audioeffects.create("Reverb", echo.output, SAMPLE_RATE,
                           character="hall", mix=0.3)

# Write the WAV header now; the data size is filled in at the end.
out = open(FILENAME, "wb")
out.write(b"RIFF\0\0\0\0WAVEfmt ")
out.write(struct.pack("<IHHIIHH", 16, 1, 1, SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16))
out.write(b"data\0\0\0\0")
size = 0


# Pull audio from the end of the chain for the given number of seconds.
def record(seconds):
    global size
    end = size + int(seconds * SAMPLE_RATE) * 2
    while size < end:
        status, block = audiocore.get_buffer(hall.output)
        size += out.write(block)


# Pluck each note, then leave two seconds for the echoes and the hall.
for note in NOTES:
    synth.press(note)
    record(NOTE_SECONDS)
    synth.release(note)
record(2)

# Go back and fill in the two sizes.
out.seek(4)
out.write(struct.pack("<I", 36 + size))
out.seek(40)
out.write(struct.pack("<I", size))
out.close()
print("Wrote", FILENAME)
