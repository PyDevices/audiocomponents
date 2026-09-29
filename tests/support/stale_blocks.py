"""The stale-block measurement, shared by the ten classes' tests
(audiocomponents#113).

A control that routes a class's graph around - Mix to 0 handing the source
straight back, Lookahead to 0, Band Limit off - leaves the graph behind it
un-pulled, holding whatever it held. `blip()` plays the move the way a
musician would: a 300 Hz tone at 20 000 LSB for 0.5 s with the macro at `a`,
the macro to `b` as the tone stops, 1 s of silence, the macro back to `a`,
0.5 s more silence. It returns the peak over the last 0.25 s before the move
back (the class's own ring: 0 means the move back is into silence) and the
peak after it, short of the last two blocks. Sound there is old audio
coming back out of silence.

`first_blip()` is the construction variant: built at its default (which is
wet, so a mixer voice primes itself with the first block of the source), Mix
to 0 before anything is pulled, the tone and the silence through the bypass,
then Mix up. What it returns is the peak after the move up.

`StaleRejoin` and `ClearOnlyRejoin` are the two planted faults every class
test shows red, applied to a class with `planted(cls, fault)`:

* `StaleRejoin` - the old behaviour: coming back off a bypass touches
  nothing.
* `ClearOnlyRejoin` - a wrong cure: the nodes are cleared but the class is
  told nothing happened, so it does not re-arm - the voices keep the blocks
  they had queued and a biased shaper's coupling pole is left uncharged.
"""

import math
import os
import sys
from array import array

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "lib"))

import audiocore                                            # noqa: E402
import audiofilters                                         # noqa: E402

#: `_component` reads VENDOR off the module a class is defined in, and the
#: planted classes `planted()` builds are defined here.
VENDOR = "PyDevices"

BLOCK = 256
RATES = (48000, 44100, 22050)


def _block_up(frames):
    return (frames + BLOCK - 1) // BLOCK * BLOCK


def spans(rate):
    """Where the tone stops, where the move back lands, and where reading
    ends, in frames."""
    tone = _block_up(rate // 2)
    back = tone + _block_up(rate)
    end = back + _block_up(rate // 2)
    return tone, back, end


def source(rate, channels):
    """The tone, then silence, delivered a block at a time and never
    again: `render_effect.py`'s bit-transparent adapter. A bare RawSample
    hands its whole buffer to a class whose Mix 0 is the source itself, and
    starts again when it runs out."""
    tone, _back, end = spans(rate)
    values = array("h", bytes(2 * channels * end))
    step = 2.0 * math.pi * 300.0 / rate
    for frame in range(tone):
        value = int(20000 * math.sin(step * frame))
        for channel in range(channels):
            values[frame * channels + channel] = value
    sample = audiocore.RawSample(values, sample_rate=rate,
                                 channel_count=channels)
    wrap = audiofilters.Filter(filter=None, mix=1,
                               buffer_size=BLOCK * channels * 2,
                               sample_rate=rate, bits_per_sample=16,
                               samples_signed=True, channel_count=channels)
    wrap.play(sample, loop=False)
    return wrap


def _render(effect, frames, channels, moves):
    out = array("h")
    pending = list(moves)
    while len(out) < frames * channels:
        done = len(out) // channels
        while pending and done >= pending[0][0]:
            _frame, index, value = pending.pop(0)
            effect.set_macro(index, value)
        data = bytes(audiocore.get_buffer(effect.output)[1])
        if not data:
            data = bytes(2 * BLOCK * channels)
        out.extend(array("h", data))
    return out


def _peak(values, lo, hi):
    top = 0
    for value in values[lo:hi]:
        if value < 0:
            value = -value
        if value > top:
            top = value
    return top


def _build(cls, rate, channels, patch, options):
    effect = cls(source(rate, channels), sample_rate=rate, **options)
    if patch is not None:
        effect.program_change(patch)
    return effect


def blip(cls, index, a, b, rate=48000, channels=2, patch=None, **options):
    """(before, after): the peak before the move back and after it."""
    tone, back, end = spans(rate)
    effect = _build(cls, rate, channels, patch, options)
    effect.set_macro(index, a)
    out = _render(effect, end, channels,
                  [(tone, index, b), (back, index, a)])
    effect.deinit()
    ch = channels
    return (_peak(out, (back - rate // 4) * ch, back * ch),
            _peak(out, back * ch, (end - 2 * BLOCK) * ch))


def twin(cls, index, a, rate=48000, channels=2, patch=None, **options):
    """The peak an instance that never moves plays over the window `blip`
    reads after the move back: the class's own floor there. A few settings
    never reach silence whatever the move (an off-centre Bias's wander),
    and a blip is only old audio where this is lower."""
    _tone, back, end = spans(rate)
    effect = _build(cls, rate, channels, patch, options)
    effect.set_macro(index, a)
    out = _render(effect, end, channels, [])
    effect.deinit()
    return _peak(out, back * channels, (end - 2 * BLOCK) * channels)


def in_step(cls, index, a, b, rate=48000, channels=2, patch=None,
            **options):
    """The largest difference between a moved instance and one that never
    moved over the second half of a second tone played after the move back:
    0 (or a few LSB of settling) when the graph came back in step, and
    thousands when one leg came back a block out of line."""
    tone, back, end = spans(rate)
    again = end + _block_up(rate // 4)

    def material():
        values = array("h", bytes(2 * channels * again))
        step = 2.0 * math.pi * 300.0 / rate
        for lo, hi in ((0, tone), (end, again)):
            for frame in range(lo, hi):
                value = int(20000 * math.sin(step * (frame - lo)))
                for channel in range(channels):
                    values[frame * channels + channel] = value
        sample = audiocore.RawSample(values, sample_rate=rate,
                                     channel_count=channels)
        wrap = audiofilters.Filter(
            filter=None, mix=1, buffer_size=BLOCK * channels * 2,
            sample_rate=rate, bits_per_sample=16, samples_signed=True,
            channel_count=channels)
        wrap.play(sample, loop=False)
        return wrap

    outs = []
    for moves in ([(tone, index, b), (back, index, a)], []):
        effect = cls(material(), sample_rate=rate, **options)
        if patch is not None:
            effect.program_change(patch)
        effect.set_macro(index, a)
        outs.append(_render(effect, again, channels, moves))
        effect.deinit()
    moved, still = outs
    half = end + (again - end) // 2
    gap = 0
    for position in range(half * channels, again * channels):
        step = moved[position] - still[position]
        if step < 0:
            step = -step
        if step > gap:
            gap = step
    return gap


def first_blip(cls, index, rate=48000, channels=2, patch=None, **options):
    """The peak after Mix comes up on an instance that went to 0 before its
    first pull."""
    _tone, back, end = spans(rate)
    effect = _build(cls, rate, channels, patch, options)
    effect.set_macro(index, 0)
    out = _render(effect, end, channels, [(back, index, 127)])
    effect.deinit()
    ch = channels
    return _peak(out, back * ch, (end - 2 * BLOCK) * ch)


class StaleRejoin:
    """Planted: the old behaviour. A bypass left behind is taken back
    untouched, so what the graph held plays."""

    def _rejoin(self, keep=()):
        self._stranded = False
        return False


class ClearOnlyRejoin:
    """Planted, a wrong cure: the nodes are cleared, but the class is not
    told, so it does not re-arm them the way its constructor does."""

    def _rejoin(self, keep=()):
        if self._stranded:
            self._stranded = False
            self._clear_nodes(keep)
        return False


def planted(cls, fault):
    """`cls` with `fault` mixed in, under the same provider name."""
    return type(cls.__name__ + fault.__name__, (fault, cls),
                {"NAME": cls.NAME})
