# Your first program

This program plays a note on a Minimoog through a tape delay and writes what it
hears to a WAV file. It needs no speaker, so it runs the same on a desktop
and in a script on a build machine.

```python
import wave
import audiocore
import audioeffects
import audioinstruments

RATE = 48000
synth = audioinstruments.create("minimoog", sample_rate=RATE)
echo = audioeffects.create("TapeDelay", synth.output, sample_rate=RATE)
synth.note_on(60)
pcm = bytearray()
for _ in range(100):
    _, block = audiocore.get_buffer(echo.output)
    pcm += bytes(block)
with wave.open("minimoog_delay.wav", "wb") as wav:
    wav.setnchannels(2)
    wav.setsampwidth(2)
    wav.setframerate(RATE)
    wav.writeframes(bytes(pcm))
print(len(pcm) // 4, "frames,", round(len(pcm) / 4 / RATE, 2), "seconds")
```

It prints:

```text
25600 frames, 0.53 seconds
```

and `minimoog_delay.wav` holds a middle C with the delay on it.

## What each line does

`audioinstruments.create("minimoog", sample_rate=RATE)` builds an instrument by
its catalogue name. `audioinstruments.ALL` lists every name `create()` takes.

`audioeffects.create("TapeDelay", synth.output, sample_rate=RATE)` builds an
effect around a source. The source is the instrument's `output`, and the effect
has an `output` of its own, so effects chain: hand one effect's `output` to the
next. `audioeffects.ALL` lists the effects.

`synth.note_on(60)` presses middle C (MIDI note 60) at full velocity. Notes,
velocity, channels and controllers are all in MIDI units; the full list is in
[the runtime API](../reference/component-api.md#midi-and-control-methods).

`audiocore.get_buffer(echo.output)` pulls one block of audio from the end of
the chain. A host does this for you: on a board, hand `echo.output` to
`audio_out.play()` instead of looping yourself. Each block here is 256
frames of 16-bit stereo, so 100 of them make 25,600 frames.

## Next

Put more effects in the chain with [Chain effects](../guides/chain-effects.md),
or play a part in time with
[Sequence a part](../guides/sequence-a-part.md).

To hear something right away, run one of the two complete examples. Each
writes a WAV file you can open in any audio player:
[audioinstruments_simpletest.py](https://github.com/PyDevices/audiocomponents/blob/main/examples/audioinstruments_simpletest.py)
plays a tune on a Rhodes electric piano, and
[audioeffects_simpletest.py](https://github.com/PyDevices/audiocomponents/blob/main/examples/audioeffects_simpletest.py)
runs plucked notes through a tape echo and a hall.
