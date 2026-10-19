"""Forty-five effect classes built out of audiodsp's audio nodes.

Every class wires itself from an audio source - a synthesizer, an
instrument's `output`, a host input, or a previous effect's `output` - and
exposes its chain tail as `output`. See README.md for the catalogue.

    import audioeffects
    comp = audioeffects.create("Compressor", source, 48000,
                               threshold_db=-20, ratio=3)
    audio_out.play(comp.output)

The package factory receives the source and sample rate explicitly. Direct
class construction is supported for local code too, and reads the format
off the source it is handed.

Some classes also carry patches - named settings on the 0-127 MIDI grid, the
way an instrument does. See README.md, "A note on patches".
"""

from . import _component


#: What `configure()` last set. No class reads it: every effect takes its
#: format from the source it is built around. It stays so the
#: `configure(48000)` idiom in existing code keeps working.
_FORMAT = [48000, 2]


def configure(rate, channel_count=2):
    """Record a default format. Kept for code that calls it; an effect's
    format always comes from its source, so this changes no effect."""
    _FORMAT[0] = int(rate)
    _FORMAT[1] = int(channel_count)


def sample_rate():
    """The rate `configure()` last recorded (48000 until it is called)."""
    return _FORMAT[0]


def channel_count():
    """The channel count `configure()` last recorded (2 until it is called)."""
    return _FORMAT[1]


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
from .reverb import Reverb
from .convolutionreverb import ConvolutionReverb
from .digitaldelay import DigitalDelay
from .slapbackdelay import SlapbackDelay
from .tapedelay import TapeDelay
from .analogdelay import AnalogDelay
from .pingpongdelay import PingPongDelay
from .multitapdelay import MultiTapDelay
from .chorus import Chorus
from .phaser import Phaser
from .tremolo import Tremolo
from .autopan import AutoPan
from .vibrato import Vibrato
from .ringmod import RingMod
from .flanger import Flanger
from .overdrive import Overdrive
from .distortion import Distortion
from .bitcrusher import Bitcrusher
from .cabinetsim import CabinetSim
from .fuzz import Fuzz
from .saturation import Saturation
from .exciter import Exciter
from .pitchshifter import PitchShifter
from .harmonizer import Harmonizer
from .octaver import Octaver
from .stereowidener import StereoWidener
from .rack import Rack
from .shimmerhall import ShimmerHall
from .airspace import AirSpace


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

    Every class the package ships is a `_component.Component` subclass that
    carries a `NAME`; the base itself is not a provider.
    """
    return (isinstance(candidate, type)
            and candidate is not _component.Component
            and issubclass(candidate, _component.Component)
            and getattr(candidate, "NAME", None) is not None)


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
