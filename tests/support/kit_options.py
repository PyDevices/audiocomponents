"""The constructor options the kit builds a class with.

Most classes are run at their defaults ({}). A class whose defaults are
trivial (the generic `Rack`'s default chain is empty, so it is a wire) is
given something real here, and every kit check builds it with these.
"""

KIT_OPTIONS = {
    # The Rack card's probe chain K: a nested rack, a delay line mid-chain,
    # latency in three children, finite tails and one tempo-synced child.
    "Rack": {"chain": (
        ("Fuzz", {}),
        ("Rack", {"chain": (("DigitalDelay", {"mix": 0.3, "feedback": 0.4}),
                            ("Vibrato", {}))}),
        ("ConvolutionReverb", {}))},
}

#: What the lifecycle matrix builds a class with, where the kit's options
#: would hide the class's own faults behind a child's: Rack's chain here has
#: no Vibrato or Fuzz (each is red on E1 P4 alone), keeping a nested rack
#: with a delay line mid-chain and ConvolutionReverb's latency.
LIFECYCLE_OPTIONS = {
    "Rack": {"chain": (
        ("Rack", {"chain": (("DigitalDelay", {"mix": 0.3, "feedback": 0.4}),)}),
        ("ConvolutionReverb", {}))},
}


def options_for(name):
    """A fresh dict of the options for class NAME `name`."""
    return dict(KIT_OPTIONS.get(name, {}))


def lifecycle_options_for(name):
    """A fresh dict of the lifecycle matrix's options for class NAME `name`
    (the kit's own where it has none of its own)."""
    return dict(LIFECYCLE_OPTIONS.get(name) or options_for(name))
