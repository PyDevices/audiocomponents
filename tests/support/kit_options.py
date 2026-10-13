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


def options_for(name):
    """A fresh dict of the options for class NAME `name`."""
    return dict(KIT_OPTIONS.get(name, {}))
