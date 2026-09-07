"""One module per rebuilt effect class, named after the class's `NAME` in
lower case: `rebuilt/compressor.py` holds `Compressor`.

**Nothing in this file lists the classes.** A rebuild adds exactly one file
and edits nothing else -- not this module, not the family module it
supersedes, not `audioeffects/__init__.py` -- so the sixteen classes of a
family phase can be rebuilt in parallel with no shared file to conflict
over. The package resolves a provider name by trying to import
`rebuilt/<name>.py`; when that file is absent the old class in the family
module stands, unchanged, and `audioeffects.ALL` and `audioeffects.create()`
keep their meaning either way (roadmap §3).

A rebuilt module declares `VENDOR` at module level and holds exactly one
`_component.Component` subclass, whose `NAME` is the provider name the file
is named after. Anything else in the file is private helpers.

Resolution is by name, never by a list this file keeps. Where the package
has a directory -- every interpreter in this workspace, and a board's VFS --
one `os.listdir` at first use says which names have a file, and the misses
cost nothing after that. Where it does not -- a package frozen into firmware
-- every name falls back to an import attempt, which is correct but slower:
measured 2026-09-07, 46 misses cost +5.7 ms on `cmods/bin/micropython` and
+20.6 ms on `cmods/bin/circuitpython-effects`, once, at import.
"""

import sys

from .. import _component

_PACKAGE = __name__

#: Names already looked for and not found. A miss is far more common than a
#: hit until Phase 6, and repeating the failed import on every `create()`
#: would put a filesystem walk on the construction path.
_MISSING = set()

#: The module basenames this directory holds, or `None` when there is no
#: directory to list. Read through `_present()`, which fills it once.
_PRESENT = None
_LISTED = False


def _present():
    """The set of module basenames here, or `None` if they cannot be
    listed. `None` is not "none present": it means fall back to trying the
    import, which is what a frozen package needs."""
    global _PRESENT, _LISTED
    if _LISTED:
        return _PRESENT
    _LISTED = True
    here = globals().get("__file__")
    if here:
        try:
            import os
            _PRESENT = set(
                entry[:-3] for entry in os.listdir(here.rsplit("/", 1)[0])
                if entry.endswith(".py") and not entry.startswith("_"))
        except (ImportError, OSError):
            _PRESENT = None
    return _PRESENT


def load(name):
    """The rebuilt class registered under the provider `name`, or `None`.

    `None` means "no file, so the old class stands" -- the ordinary answer
    for a class this program has not reached yet. A file that exists but
    holds no matching class is an error, not a miss: that is a typo in a
    filename or a `NAME`, and silently falling back to the old class would
    hide a rebuild that never took effect.
    """
    basename = name.lower()
    present = _present()
    if present is not None and basename not in present:
        return None
    module_name = _PACKAGE + "." + basename
    if module_name in _MISSING:
        return None
    try:
        __import__(module_name)
    except ImportError:
        _MISSING.add(module_name)
        return None
    module = sys.modules.get(module_name)
    if module is None:                      # pragma: no cover - interpreter
        _MISSING.add(module_name)           # that does not register dotted
        return None                         # submodule names
    for attribute in dir(module):
        candidate = getattr(module, attribute)
        if (isinstance(candidate, type)
                and candidate is not _component.Component
                and issubclass(candidate, _component.Component)
                and getattr(candidate, "NAME", None) == name):
            return candidate
    raise ImportError("%s holds no Component whose NAME is %r"
                      % (module_name, name))


def known():
    """Every provider name with a rebuilt module here, by importing each
    one. Tooling and tests; `load()` is the runtime path."""
    present = _present()
    if present is None:
        raise OSError("%s cannot be listed on this interpreter" % _PACKAGE)
    names = []
    for basename in sorted(present):
        module_name = _PACKAGE + "." + basename
        __import__(module_name)
        module = sys.modules[module_name]
        for attribute in dir(module):
            candidate = getattr(module, attribute)
            if (isinstance(candidate, type)
                    and candidate is not _component.Component
                    and issubclass(candidate, _component.Component)
                    and getattr(candidate, "NAME", None) is not None):
                names.append(candidate.NAME)
    return tuple(names)
