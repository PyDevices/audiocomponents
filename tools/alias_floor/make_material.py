"""Build the waveshaper alias-floor material on CPython, once, as data.

    python3 tools/alias_floor/make_material.py [work_dir]

The curve and the two probe tones are computed HERE and shipped as bytes to
both boards and to the desktop leg. That is the point rather than a
convenience: `audioshaper.Waveshaper` takes its curve as int16 Q15 *data*, so
the table a board shapes against can be made byte-identical to the desktop's
instead of being recomputed through a second libm, and the same goes for the
sine. A difference in the measured floor is then the node's arithmetic and
never the material's.

The window length per rate is chosen so that both 1010 Hz and 3700 Hz complete
a whole number of cycles in it (101 and 370), which is the method the drive
dossiers state for themselves - Overdrive T7: "4800 samples at 48 kHz, no
window (101 exact periods, so every harmonic lands on a bin)".

Hashes of what this writes, as measured on 2026-09-07:

    curve.bin              87fbf34fa0bd3e3e9dca97c82824d44e0eaffa487d3a0bbccdf7340308691908
    sine_48000_1010.raw    7e4df439c0264a12d0aad4fe9069aa8560035c60c229e9f3d596b97e558e258c
    sine_48000_3700.raw    5459ca9edeb0e59803df5129b3065ef7ecec7db6962e2c405077111186c8faed
    sine_44100_1010.raw    6fade41c36450940a456b2c029c089e1cd5661ab5a7892f73aea9eb400073069
    sine_44100_3700.raw    8f758a5745e7baa4d626c9241704a483e5abe0d6f0965281b313f3c0ad00c259
"""

import hashlib
import math
import os
import sys
from array import array

POINTS = 1024
#: window frames per rate; both tones complete a whole number of cycles in it
RATES = {48000: 4800, 44100: 4410}
FREQS = (1010, 3700)


def clamp15(value):
    return max(-32768, min(32767, value))


def hard_clip_curve():
    """y = clamp(4x, -1, +1): linear to |x| = 0.25, flat past it.

    A hard clipper is the worst case the drive dossiers name - Distortion A1
    calls the near-square "the harder of the two" characters - so it is what
    the oversampling factor has to be measured against, not a gentle knee
    that would flatter it. With a full-scale sine in and `pre_gain` 1.0 the
    input sits 12 dB into the flat region, which is harder than any dossier's
    own probe (they specify -6 or -20 dBFS).
    """
    last = POINTS - 1
    table = array("h")
    for index in range(POINTS):
        x = (2.0 * index - last) / last
        table.append(clamp15(int(round(max(-1.0, min(1.0, 4.0 * x)) * 32768))))
    return table


def sine(rate, hz, frames):
    """`2 * frames` samples: a settle half and the half that is measured."""
    cycles = hz * frames // rate
    assert cycles * rate == hz * frames, (rate, hz, frames)
    values = array("h")
    for index in range(2 * frames):
        values.append(clamp15(int(round(
            32767 * math.sin(2.0 * math.pi * cycles * index / frames)))))
    return values, cycles


def main(out):
    os.makedirs(out, exist_ok=True)

    def write(name, blob):
        path = os.path.join(out, name)
        with open(path, "wb") as handle:
            handle.write(blob)
        print("%-22s %6d bytes  %s"
              % (name, len(blob), hashlib.sha256(blob).hexdigest()))

    write("curve.bin", hard_clip_curve().tobytes())
    for rate, frames in RATES.items():
        for hz in FREQS:
            values, cycles = sine(rate, hz, frames)
            write("sine_%d_%d.raw" % (rate, hz), values.tobytes())
            print("    %d cycles in %d frames = %d Hz at %d Hz"
                  % (cycles, frames, hz, rate))


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "work"))
