# Install

audiocomponents is two packages, `audioinstruments` and `audioeffects`. Both
need [audiodsp](https://github.com/PyDevices/audiodsp), the part of OmniPython
that supplies the audio nodes and the CircuitPython-compatible `synthio` and
`audiocore` layer underneath.

## On a desktop

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pydevices-audioinstruments pydevices-audioeffects
```

pip pulls in `pydevices-audiodsp` for you. The distributions are
`pydevices-audioinstruments` and `pydevices-audioeffects`; the import names
are `audioinstruments` and `audioeffects`. Python 3.11 or newer.

Check it:

```bash
python -c "import audioinstruments, audioeffects; print(len(audioinstruments.ALL), 'instruments,', len(audioeffects.ALL), 'effects')"
```

```text
55 instruments, 45 effects
```

## On a MicroPython-compatible board

```python
import mip
mip.install("audioinstruments", index="https://PyDevices.github.io/mip")
mip.install("audioeffects", index="https://PyDevices.github.io/mip")
```

The firmware has to carry audiodsp's native modules, because the components
build their graphs from them. `mip` copies only the Python.

## On a CircuitPython-compatible board

The instruments need `synthio`, which CircuitPython ships. Most effects need
audiodsp's extra nodes (`audiodynamics`, `audiobiquad`, `audioecho`,
`audioverb` and others), which a stock CircuitPython build does not have. Each
effect class names the ones it needs in `REQUIRES`, for example
`Reverb.REQUIRES == ("audioverb",)`.

## A specific release

The sound of a component can change between releases
([Sound stability](../how-it-works/sound-stability.md)). To keep a composition
the way it sounds today, pin the version:

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pydevices-audioinstruments==0.4.1 pydevices-audioeffects==0.4.1
```
