# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Play a short tune on a classic electric piano and save it as a WAV file.

The program builds one instrument by name, plays four notes and writes
what comes out to a WAV file you can open in any audio player. Then it
lists the instrument's knobs, which inst.set_macro() turns. Change
INSTRUMENT to hear another of the fifty-five.

Needs: audioinstruments and audiodsp. Both are built into the PyDevices
MicroPython firmware; on CPython, pip install pydevices-audioinstruments.

Run it:
    micropython audioinstruments_simpletest.py

Tested on: the unix port of MicroPython and CPython 3.12 on Linux.
"""

import struct

import audiocore
import audioinstruments

# Change these to match your setup.
FILENAME = "tune.wav"
INSTRUMENT = "rhodes"  # try "juno106", "minimoog", "dx7" or "tr808"
NOTES = (60, 64, 67, 72)  # MIDI note numbers: C, E, G and the C above
NOTE_SECONDS = 0.4
SAMPLE_RATE = 22050

# Build the instrument, in mono, on its default patch.
inst = audioinstruments.create(INSTRUMENT, SAMPLE_RATE, channel_count=1)

# Write the WAV header now; the data size is filled in at the end.
out = open(FILENAME, "wb")
out.write(b"RIFF\0\0\0\0WAVEfmt ")
out.write(struct.pack("<IHHIIHH", 16, 1, 1, SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16))
out.write(b"data\0\0\0\0")
size = 0


# Pull audio out of the instrument for the given number of seconds.
def record(seconds):
    global size
    end = size + int(seconds * SAMPLE_RATE) * 2
    while size < end:
        status, block = audiocore.get_buffer(inst.output)
        size += out.write(block)


# Play each note, let it go, and leave a second for the last one to fade.
for note in NOTES:
    inst.note_on(note)
    record(NOTE_SECONDS)
    inst.note_off(note)
record(1)

# Go back and fill in the two sizes.
out.seek(4)
out.write(struct.pack("<I", 36 + size))
out.seek(40)
out.write(struct.pack("<I", size))
out.close()
print("Wrote", FILENAME)

# Each knob is a macro, set from 0 to 127 by its place in this list:
# inst.set_macro(inst.macro_labels.index("Tone"), 90), for example.
print("Knobs:", ", ".join(inst.macro_labels))
