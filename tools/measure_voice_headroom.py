"""How many voices can this board actually render in real time?

    mpremote run tools/measure_voice_headroom.py

Runs on the device. Prints a table and one verdict line.

WHY THIS EXISTS
---------------
The voice ceiling was raised from 14 to 64 (audioif#31). On desktop that is
free. On a microcontroller it may not be, and nobody has measured it.

The ceiling used to be an accidental CPU governor. At 14, a patch too heavy
for the board could not ask for more voices than the board could render --
the engine refused the press and the sound quietly thinned. At 64 it will
accept the press and try, and if the block does not finish inside its
deadline the result is not a thinner sound, it is a dropout. That is a worse
failure and a louder one.

So the question is not "does it work" but "how many voices does this board
render before it stops keeping up", and the answer is a number per board.

WHAT IT MEASURES
----------------
Wall-clock time to render a fixed number of audio blocks with N voices
sounding, against the wall-clock time those blocks represent. The ratio is a
real-time factor:

    rt = audio_seconds_produced / seconds_spent_producing

rt = 1.0 means exactly keeping up with no margin, which in practice is
already too slow -- an interrupt, a GC pause or a flash read will push it
under. rt >= SAFE_FACTOR is the number to trust.

It sweeps N upward and reports the largest N that still meets the bar.

WHAT IT DOES NOT MEASURE
------------------------
Real audio output. This renders into a buffer and never opens an I2S device,
because a dropout at the DAC is what we are trying to PREDICT, not reproduce.
A board that passes here can still glitch on a driver that steals time. Treat
the number as an upper bound.

It also measures ONE instrument at a time. A full arrangement mixes several,
and the mixer costs more than the sum -- so derate.
"""

import gc
import sys
import time

try:
    import synthio
    import audiocore
except ImportError as exc:                        # pragma: no cover - device
    raise SystemExit("no audio engine on this board: %s" % exc)

SAMPLE_RATE = 48000
CHANNELS = 2

#: Real-time factor a voice count must beat to be called usable. 2.0 means
#: the board renders a second of audio in half a second, leaving half the
#: CPU for everything else -- USB, display, the program itself. Below about
#: 1.5 a board is technically keeping up and audibly fragile.
SAFE_FACTOR = 2.0

#: Blocks per measurement. Enough that a GC pause lands inside the window
#: rather than dominating one short run.
BLOCKS = 200

#: Voice counts to try. Stops early once one fails, since the curve is
#: monotonic -- more voices is never faster.
LADDER = (1, 2, 4, 8, 12, 14, 16, 20, 24, 32, 40, 48, 56, 64)


def _ceiling():
    return synthio.Synthesizer(sample_rate=SAMPLE_RATE).max_polyphony


def _render(synth, blocks):
    """Seconds spent, and audio-seconds produced, rendering `blocks`."""
    frames = 0
    gc.collect()
    start = time.ticks_us() if hasattr(time, "ticks_us") else int(
        time.monotonic() * 1_000_000)
    for _ in range(blocks):
        _result, buf = audiocore.get_buffer(synth)
        frames += len(bytes(buf)) // (2 * CHANNELS)
    if hasattr(time, "ticks_diff"):
        spent = time.ticks_diff(time.ticks_us(), start) / 1_000_000
    else:
        spent = int(time.monotonic() * 1_000_000) / 1_000_000 - (
            start / 1_000_000)
    return spent, frames / float(SAMPLE_RATE)


def _voices(synth, count):
    """Press `count` distinct notes and return them, or None if refused.

    A refusal is a finding, not an error: it means the compiled ceiling is
    below what we were asked to try, and the sweep should stop there rather
    than silently measure fewer voices than it reports.
    """
    notes = [synthio.Note(frequency=110.0 * (1.0 + 0.031 * i))
             for i in range(count)]
    synth.press(notes)
    sounding = len(synth.pressed)
    if sounding < count:
        synth.release_all()
        return None, sounding
    return notes, sounding


def main():
    cap = _ceiling()
    print("voice headroom, %d Hz, %d ch" % (SAMPLE_RATE, CHANNELS))
    print("compiled ceiling: %d voices" % cap)
    print("bar: real-time factor >= %.1f" % SAFE_FACTOR)
    print("")
    print("%6s %10s %12s %s" % ("voices", "rt factor", "ms/block", "verdict"))

    best = 0
    for count in LADDER:
        if count > cap:
            print("%6d %10s %12s %s" % (count, "-", "-",
                                        "above the compiled ceiling"))
            break
        synth = synthio.Synthesizer(sample_rate=SAMPLE_RATE,
                                    channel_count=CHANNELS)
        notes, sounding = _voices(synth, count)
        if notes is None:
            print("%6d %10s %12s refused at %d sounding"
                  % (count, "-", "-", sounding))
            break
        spent, produced = _render(synth, BLOCKS)
        synth.release_all()
        del synth, notes
        gc.collect()

        rt = produced / spent if spent > 0 else 0.0
        ms = spent * 1000.0 / BLOCKS
        if rt >= SAFE_FACTOR:
            verdict = "ok"
            best = count
        elif rt >= 1.0:
            verdict = "KEEPS UP BUT FRAGILE"
        else:
            verdict = "TOO SLOW - would drop out"
        print("%6d %10.2f %12.2f %s" % (count, rt, ms, verdict))
        if rt < 1.0:
            break

    print("")
    print("largest voice count meeting the bar: %d" % best)
    if best >= cap:
        print("this board sustains the full compiled ceiling of %d" % cap)
    elif best == 0:
        print("this board did not meet the bar at ANY voice count -- either")
        print("the bar is wrong for it or something else is eating the CPU")
    else:
        print("the compiled ceiling is %d but this board sustains %d."
              % (cap, best))
        print("above %d a patch will try to render and may drop buffers,"
              % best)
        print("where at a lower ceiling it would have thinned silently.")
        print("consider CFLAGS_EXTRA=-DCIRCUITPY_SYNTHIO_MAX_CHANNELS=%d"
              % best)
    print("")
    print("upper bound only: no I2S device was opened, and one instrument")
    print("was measured, not an arrangement. Derate for both.")


if __name__ == "__main__":
    main()
