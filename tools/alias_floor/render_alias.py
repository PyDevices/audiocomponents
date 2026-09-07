"""Render the alias-floor matrix ON THE BOARD and leave the PCM in a file.

    mpftp mkdir -d COM4 /alias
    mpftp put -d COM4 <work>/curve.bin /alias/curve.bin --verify
    mpftp put -d COM4 <work>/sine_48000_1010.raw /alias/sine_48000_1010.raw --verify
    ... (all four sines)
    mpftp put -d COM4 tools/alias_floor/render_alias.py /alias_render.py --verify
    mpftp run -d COM4 tools/alias_floor/render_alias.py --follow
    mpftp get -d COM4 /alias/out_48000.raw <work>/alias_out_COM4/out_48000.raw --verify
    mpftp get -d COM4 /alias/out_44100.raw <work>/alias_out_COM4/out_44100.raw --verify

One output file per sample rate, eight segments each, in this order:

    for hz in (1010, 3700): for oversample in (1, 2, 4, 8)

Each segment is `frames` mono int16 frames - the second half of a
`2 * frames` render, so the first half is settle and the half kept is a whole
number of cycles of steady state. Mono because the alias floor is a
per-channel reading and half the bytes is half the serial transfer.

Nothing is analysed here. The board's job is to render; the FFT is the host's,
in `analyse_alias.py`, with the kit's own measurement.
"""

import gc
import struct
from array import array

import audiocore
import audioshaper

RATES = ((48000, 4800), (44100, 4410))
FREQS = (1010, 3700)
FACTORS = (1, 2, 4, 8)

#: The drive settings. `pre_gain` 1.0 against a curve that clips at a quarter
#: of full scale is 12 dB into a hard clip on a full-scale sine - a harder
#: probe than any drive dossier's own. `post_gain` 0.5 keeps the near-square
#: off the int16 rails, so nothing the measurement reads is output clipping.
PRE_GAIN = 1.0
POST_GAIN = 0.5


def load(path):
    """MicroPython's `array` has no `frombytes`, so unpack the file.

    The bytes came from CPython; unpacking them little-endian here is the
    same int16 sequence, which is the whole point of shipping the material
    rather than recomputing it on the board.
    """
    with open(path, "rb") as handle:
        data = handle.read()
    return array("h", struct.unpack("<%dh" % (len(data) // 2), data))


def main():
    curve = load("/alias/curve.bin")
    log = open("/alias/log.txt", "w")
    for rate, frames in RATES:
        out = open("/alias/out_%d.raw" % rate, "wb")
        for hz in FREQS:
            source = load("/alias/sine_%d_%d.raw" % (rate, hz))
            for factor in FACTORS:
                gc.collect()
                node = audioshaper.Waveshaper(
                    sample_rate=rate, channel_count=1, oversample=factor,
                    curve=curve, pre_gain=PRE_GAIN, bias=0.0,
                    post_gain=POST_GAIN, mix=1.0)
                node.play(audiocore.RawSample(
                    source, sample_rate=rate, channel_count=1))
                want = 2 * frames * 2
                buffer = bytearray()
                pulls = 0
                while len(buffer) < want and pulls < 4096:
                    _result, block = audiocore.get_buffer(node)
                    pulls += 1
                    if block is None:
                        break
                    if len(block) == 0:
                        continue
                    buffer += bytes(block)
                out.write(bytes(buffer[frames * 2:want]))
                line = "%d %d x%d frames=%d pulls=%d" % (
                    rate, hz, factor, len(buffer) // 2, pulls)
                print(line)
                log.write(line + "\n")
                log.flush()
                del node, buffer
        out.close()
        source = None
    log.write("DONE\n")
    log.close()
    print("DONE")


main()
