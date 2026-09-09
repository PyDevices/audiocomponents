"""Forty-five effect classes built out of audioif's audio nodes.

Every class wires itself from an audio source - a synthesizer, an
instrument's `output`, a host input, or a previous effect's `output` - and
exposes its chain tail as `output`. See README.md for the catalogue.

    import audioeffects
    comp = audioeffects.create("Compressor", source, 48000,
                               threshold_db=-20, ratio=3)
    audio_out.play(comp.output)

The package factory receives the source and sample rate explicitly. Direct
class construction remains supported for local code after `configure()`.

Some classes also carry patches - named settings on the 0-127 MIDI grid, the
way an instrument does. See README.md, "A note on patches".
"""

from . import _component
from . import _core
from . import rebuilt as _rebuilt
from ._core import channel_count, configure, sample_rate

from .compressor import Compressor
from .limiter import Limiter
from .expander import Expander
from .noisegate import NoiseGate
from .deesser import DeEsser
from .transientshaper import TransientShaper
from .multibandcompressor import MultibandCompressor
from .parametriceq import ParametricEQ
from .graphiceq import GraphicEQ
from .lowpass import LowPass
from .highpass import HighPass
from .bandpass import BandPass
from .notch import Notch
from .ladderfilter import LadderFilter
from .combfilter import CombFilter
from .dynamiceq import DynamicEQ
from .reverb import Reverb, ConvolutionReverb
from .delay import (DigitalDelay, SlapbackDelay, TapeDelay, AnalogDelay,
                    PingPongDelay, MultiTapDelay)
from .chorus import Chorus
from .phaser import Phaser
from .tremolo import Tremolo
from .autopan import AutoPan
from .vibrato import Vibrato
from .modulation import Flanger, RingMod
from .drive import (Overdrive, Distortion, Fuzz, Saturation, Bitcrusher,
                    Exciter, CabinetSim)
from .pitch import PitchShifter, Harmonizer, Octaver, StereoWidener
from .rack import Rack, ShimmerHall, AirSpace


#: The package's whole surface, grouped as the modules above are. Every
#: name here is re-exported; nothing else in a submodule is public.
__all__ = [
    "configure", "sample_rate", "channel_count", "create", "ALL",
    # dynamics
    "Compressor", "Limiter", "Expander", "NoiseGate", "DeEsser",
    "TransientShaper", "MultibandCompressor",
    # eq and filters
    "ParametricEQ", "GraphicEQ", "LowPass", "HighPass", "BandPass",
    "Notch", "LadderFilter", "CombFilter", "DynamicEQ",
    # reverb
    "Reverb", "ConvolutionReverb",
    # delay
    "DigitalDelay", "SlapbackDelay", "TapeDelay", "AnalogDelay",
    "PingPongDelay", "MultiTapDelay",
    # modulation
    "Chorus", "Flanger", "Phaser", "Tremolo", "AutoPan", "Vibrato",
    "RingMod",
    # drive
    "Overdrive", "Distortion", "Fuzz", "Saturation", "Bitcrusher", "Exciter",
    "CabinetSim",
    # pitch and stereo
    "PitchShifter", "Harmonizer", "Octaver", "StereoWidener",
    # racks
    "Rack", "ShimmerHall", "AirSpace",
]


def _is_provider(candidate):
    """Whether `candidate` is one of this package's public effect classes.

    Two bases, on purpose: `_core.Effect` for the families this program has
    not rebuilt yet, `_component.Component` for the ones it has. The test is
    structural rather than a base-class list a consumer must know about --
    the contract is structural too (`docs/audio-component-api.md`).
    """
    return (isinstance(candidate, type)
            and candidate is not _core.Effect
            and candidate is not _component.Component
            and issubclass(candidate, (_core.Effect, _component.Component))
            and getattr(candidate, "NAME", None) is not None)


def _adopt(namespace, names):
    """Let an **adopted** rebuilt class stand in for the class it replaces,
    by NAME.

    This is the registry rule of the effects roadmap (§3): a rebuilt class
    lands as its own file under `rebuilt/`, named after its `NAME`, and
    replaces the old class here without either module being edited. When no
    such file exists the old class stands. `ALL` and `create()` therefore
    keep their meaning at every phase boundary, whichever half of the
    library a given name is served by.

    Phase 2's sixteen and Phase 3's five THROUGH classes (AutoPan, Chorus,
    Phaser, Tremolo, Vibrato) have come home as one file per effect beside
    this module, so they are imported above rather than substituted. The
    machinery stays for Flanger, RingMod and the phases still to come:
    `rebuilt.load()` answers `None` for a parked name (or a name with no
    file), and `rebuilt.module_class()` is how a tool or a class's own
    tests reach a rebuild that has not come home yet.
    """
    for exported in names:
        current = namespace.get(exported)
        if not _is_provider(current):
            continue
        replacement = _rebuilt.load(current.NAME)
        if replacement is not None:
            namespace[exported] = replacement
    return namespace


_adopt(globals(), __all__)


def create(name, source, sample_rate, transport=None, **options):
    """Construct the public effect named ``name``.

    This is the effect-side counterpart to ``audioinstruments.create``. The
    selected class's ``create`` method owns the actual construction, so a
    consumer does not need to know which module contains it.
    """
    for exported in __all__:
        cls = globals().get(exported)
        if _is_provider(cls) and cls.NAME == name:
            return cls.create(source, sample_rate, transport=transport,
                              **options)
    raise ImportError("audioeffects has no %s" % name)


# Stable provider names, not implementation module names. This is computed
# from the already-imported public classes and never constructs an effect.
ALL = tuple(sorted(
    globals()[name].NAME
    for name in __all__
    if _is_provider(globals().get(name))
))
