"""The desktop leg of the same render: identical material, identical node.

    audiocomponents/.venv/bin/python tools/alias_floor/render_desktop.py [work_dir]

Same settings and same order as `render_alias.py`, so the three legs are
comparable segment for segment. It exists so the board's PCM has a desktop
render to be held against - the audioif in `audiocomponents/.venv` is the
same commit the firmware was built from.
"""

import os
import sys
from array import array

import audiocore
import audioshaper

HERE = os.path.dirname(os.path.abspath(__file__))
RATES = ((48000, 4800), (44100, 4410))
FREQS = (1010, 3700)
FACTORS = (1, 2, 4, 8)
PRE_GAIN = 1.0
POST_GAIN = 0.5


def load(path):
    values = array("h")
    values.frombytes(open(path, "rb").read())
    return values


def main(work):
    out_dir = os.path.join(work, "alias_out_desktop")
    os.makedirs(out_dir, exist_ok=True)
    curve = load(os.path.join(work, "curve.bin"))
    for rate, frames in RATES:
        handle = open(os.path.join(out_dir, "out_%d.raw" % rate), "wb")
        for hz in FREQS:
            source = load(os.path.join(work, "sine_%d_%d.raw" % (rate, hz)))
            for factor in FACTORS:
                node = audioshaper.Waveshaper(
                    sample_rate=rate, channel_count=1, oversample=factor,
                    curve=curve, pre_gain=PRE_GAIN, bias=0.0,
                    post_gain=POST_GAIN, mix=1.0)
                node.play(audiocore.RawSample(source, sample_rate=rate,
                                              channel_count=1))
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
                handle.write(bytes(buffer[frames * 2:want]))
                print("%d %d x%d frames=%d pulls=%d"
                      % (rate, hz, factor, len(buffer) // 2, pulls))
        handle.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "work"))
