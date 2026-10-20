"""The effects kit: nine mechanical checks on one class, no model in the loop.

    python tests/support/kit.py DigitalDelay [--only tail,plants,...]
        [--quick] [--plants-module NAME] [--claims-module NAME] [--no-run]

Prints one line per cell, `name|check|key|V:verdict[|h:digest]`, a
SUMMARY line per check, and DONE. On MicroPython and CircuitPython
(`MICROPYPATH=lib:tests/support`) it runs the six render checks and
nogb; the claims and paperwork checks read source and git, and run on
CPython only.
`KIT.md` beside this file says what each check measures and its bars.
"""

import sys

if __name__ == "__main__":
    sys.path.insert(0, "lib")
    sys.path.insert(0, "tests/support")
    sys.path.insert(0, "tests")

import kit_common as kc

CHECKS = ("paperwork", "claims", "args", "plants", "ceiling", "tail",
          "nogb", "fresh", "levels")
STATIC = ("paperwork", "claims")


def run_check(check, cls, emit=print, quick=False, plants_module=None,
              claims_module=None, execute=True, name=None):
    import kit_options
    options = kit_options.options_for(cls.NAME)
    if check == "tail":
        import kit_tail
        return kit_tail.run(cls, emit, quick=quick, name=name,
                            options=options)
    if check == "plants":
        import kit_plants
        return kit_plants.run(cls, emit, module=plants_module, name=name,
                              options=options)
    if check == "args":
        import kit_args
        return kit_args.run(cls, emit, quick=quick, name=name,
                            options=options)
    if check == "ceiling":
        import kit_ceiling
        return kit_ceiling.run(cls, emit, quick=quick, name=name,
                               options=options)
    if check == "nogb":
        import kit_nogb
        # nogb runs the lifecycle events, so it takes the lifecycle's
        # options (a chain without children whose own defects would read
        # as the class's).
        return kit_nogb.run(cls, emit, quick=quick, name=name,
                            options=kit_options.lifecycle_options_for(
                                cls.NAME))
    if check == "fresh":
        import kit_fresh
        return kit_fresh.run(cls, emit, quick=quick, name=name,
                             options=options)
    if check == "levels":
        import kit_levels
        return kit_levels.run(cls, emit, quick=quick, name=name,
                              options=options)
    if check == "claims":
        import kit_claims
        return kit_claims.run(cls, emit, module=claims_module,
                              execute=execute, name=name)
    if check == "paperwork":
        import kit_paperwork
        return kit_paperwork.run(cls, emit, name=name)
    raise ValueError(check)


def main(argv, only=None, emit=print):
    names = []
    quick = False
    execute = True
    plants_module = claims_module = None
    joined = []
    for arg in argv:
        if joined and joined[-1] in ("--only", "--plants-module",
                                     "--claims-module"):
            joined[-1] += "=" + arg
        else:
            joined.append(arg)
    for arg in joined:
        if arg.startswith("--only="):
            only = tuple(arg.split("=", 1)[1].split(","))
        elif arg == "--quick":
            quick = True
        elif arg == "--no-run":
            execute = False
        elif arg.startswith("--plants-module="):
            plants_module = arg.split("=", 1)[1]
        elif arg.startswith("--claims-module="):
            claims_module = arg.split("=", 1)[1]
        else:
            names.append(arg)
    only = only or CHECKS
    for name in names:
        cls = kc.resolve(name)
        if cls is None:
            emit("MISSING|%s" % name)
            continue
        for check in CHECKS:
            if check not in only:
                continue
            if check in STATIC and not kc.CPYTHON:
                emit("SKIP|%s|%s|CPython only" % (name, check))
                continue
            run_check(check, cls, emit, quick, plants_module, claims_module,
                      execute)
    emit("DONE")


if __name__ == "__main__":
    main(sys.argv[1:])
