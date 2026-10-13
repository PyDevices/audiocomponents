"""The constructor options the kit builds a class with.

Most classes are run at their defaults ({}). A class whose defaults are
trivial (the generic `Rack`'s default chain is empty, so it is a wire) is
given something real here, and every kit check builds it with these.
"""

KIT_OPTIONS = {
    # Filled with a real chain when the Rack's kit run is set up.
    "Rack": {"chain": ()},
}


def options_for(name):
    """A fresh dict of the options for class NAME `name`."""
    return dict(KIT_OPTIONS.get(name, {}))
