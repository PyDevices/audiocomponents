# audiocomponents

audiocomponents is the part of OmniPython that makes sound: 55 instruments
(synthesizers, electromechanical keyboards and drum machines) and 45 effects,
pure Python on audiodsp's audio nodes, the same on MicroPython-compatible
boards, CircuitPython-compatible boards and a desktop.

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pydevices-audioinstruments pydevices-audioeffects
```

```python
import mip
mip.install("audioinstruments", index="https://PyDevices.github.io/mip")
mip.install("audioeffects", index="https://PyDevices.github.io/mip")
```

The first is for a desktop. The second is for a board whose firmware carries
audiodsp; [Install](docs/get-started/install.md) has the rest.

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

```text
25600 frames, 0.53 seconds
```

That plays middle C on a Minimoog through a tape delay and writes it to
`minimoog_delay.wav`. On a board, hand `echo.output` to `audio_out.play()`
instead.

[Docs](https://github.com/PyDevices/audiocomponents/blob/main/docs/index.md) · [Examples](https://pydevices.github.io/gallery/gallery/) · [Roadmap](ROADMAP.md)

OmniPython is made by [PyDevices](https://pydevices.com).
