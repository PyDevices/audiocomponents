#!/usr/bin/env python3
"""Run the tests that this change can break, and no more.

The full suite renders audio; it passed five minutes during Phase 2 and grows
with every rebuilt class. Most agents do not need it: a fixer working on one
effect needs that effect's tests and the contract tests, and nothing else. Only
an integrator or an auditor needs everything.

    tools/scoped_tests.py                 # decide from what git says changed
    tools/scoped_tests.py --list          # say what it would run, run nothing
    tools/scoped_tests.py class:DeEsser   # one effect, plus the contract
    tools/scoped_tests.py effects         # every effect, no instruments
    tools/scoped_tests.py contract        # the shared promises only
    tools/scoped_tests.py full            # everything, for a gate

It prints the scope it chose and why before running, so a report can quote it.
Exit status is the suite's own.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TESTS = os.path.join(ROOT, "tests")
LIB_EFFECTS = os.path.join(ROOT, "lib", "audioeffects")

#: Run these whenever anything under `lib/` moves: they are the shared promises
#: — the component API, the foundation, the portability tiers, the registry —
#: and a change to one effect can break them through `_component` or `__init__`.
CONTRACT = (
    "test_audio_component_api",
    "test_component_foundation",
    "test_portability_tier",
    "test_rebuilt_registry",
)

#: The measurement kit's own tests. A change to the kit invalidates every
#: number an evidence pack quotes, so they run whenever it moves.
KIT = tuple(sorted(
    m[:-3] for m in os.listdir(TESTS)
    if m.startswith("test_effect_kit") and m.endswith(".py")
)) if os.path.isdir(TESTS) else ()

INSTRUMENTS = ("test_cpython_instruments", "test_cpython_piano_polyphony")

#: Roster files that name every Phase 2 class. A content search that lands
#: here has not found that class's own tests.
_NOT_OWN = set(CONTRACT) | set(KIT) | set(INSTRUMENTS) | {
    "test_metadata_contract",
    "test_shared_circuit_overlap",
    "test_rig_comparator",
    "test_cpython_effects_library",
}


def _modules():
    return sorted(m[:-3] for m in os.listdir(TESTS)
                  if m.startswith("test_") and m.endswith(".py"))


def _changed():
    """Every path this working tree has touched: staged, unstaged, untracked."""
    out = set()
    for cmd in (["git", "diff", "--name-only", "HEAD"],
                ["git", "diff", "--name-only", "--cached"],
                ["git", "ls-files", "--others", "--exclude-standard"]):
        try:
            done = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        except OSError:
            continue
        out.update(p for p in done.stdout.split("\n") if p.strip())
    return sorted(out)


def _normalise_class(name):
    """`DeEsser`, `deesser`, `multibandcompressor` -> a module stem."""
    text = name.strip().replace("-", "_")
    if not text:
        return ""
    if "_" in text or text.islower() or text.isupper():
        return text.lower()
    pieces = []
    for char in text:
        if char.isupper() and pieces:
            pieces.append("_")
        pieces.append(char.lower())
    return "".join(pieces).replace("__", "_")


def _test_for_effect(stem, modules):
    """`multibandcompressor` -> `test_cpython_effects_multiband`, by search.

    The test file is not always named after the module (Phase 2 shortened a
    few, and `NoiseGate` lives at `test_noisegate.py`), so fall back to a
    prefix of `test_cpython_effects_*` and then whichever own-test file
    mentions the stem. Classes with a home module but no trait file
    (`LadderFilter`) resolve to the catalogue contract.
    """
    stem = _normalise_class(stem).replace("_", "")
    if not stem:
        return []
    exact = "test_cpython_effects_" + stem
    if exact in modules:
        return [exact]
    short = "test_" + stem
    if short in modules:
        return [short]

    prefixed = []
    for module in modules:
        marker = "test_cpython_effects_"
        if not module.startswith(marker):
            continue
        suffix = module[len(marker):].replace("_", "")
        if suffix and stem.startswith(suffix) and len(suffix) >= 4:
            prefixed.append((len(suffix), module))
    if prefixed:
        prefixed.sort(reverse=True)
        longest = prefixed[0][0]
        return [module for length, module in prefixed if length == longest]

    hits = []
    for module in modules:
        if module in _NOT_OWN:
            continue
        try:
            with open(os.path.join(TESTS, module + ".py"), encoding="utf-8",
                      errors="replace") as handle:
                head = handle.read(4000)
        except OSError:
            continue
        if re.search(r"\b%s\b" % re.escape(stem), head, re.I):
            hits.append(module)
    if hits:
        return hits
    home = os.path.join(LIB_EFFECTS, stem + ".py")
    if os.path.isfile(home) and "test_cpython_effects_library" in modules:
        return ["test_cpython_effects_library"]
    return []


def _effects_only(modules):
    return [m for m in modules if m not in INSTRUMENTS]


def choose(scope, modules):
    """Return (test modules, one line saying why)."""
    if scope == "full":
        return modules, "full suite: a gate, an integration, or a release"
    if scope == "effects":
        return (_effects_only(modules),
                "every effect; instruments skipped (audioif is pinned)")
    if scope == "contract":
        return list(CONTRACT), "the shared promises only"
    if scope.startswith("class:"):
        name = scope.split(":", 1)[1].strip()
        found = _test_for_effect(name, modules)
        if not found:
            print("no test file found for %r" % name, file=sys.stderr)
            return [], "nothing matched"
        seen = []
        for module in list(found) + list(CONTRACT):
            if module not in seen:
                seen.append(module)
        return seen, "%s plus the contract" % ", ".join(found)

    # auto
    changed = _changed()
    if not changed:
        return list(CONTRACT), "nothing changed; the contract as a smoke check"
    picked, why = set(), []
    for path in changed:
        if path.startswith("tests/"):
            stem = os.path.basename(path)[:-3]
            if stem in modules:
                picked.add(stem)
                why.append("%s edited" % stem)
        elif path.startswith("lib/audioeffects/"):
            stem = os.path.basename(path)[:-3].lower()
            if stem in ("__init__", "_core", "_component"):
                picked.update(_effects_only(modules))
                why.append("%s is shared by every effect, so every effect "
                           "test runs (instruments stay off)"
                           % os.path.basename(path))
            else:
                hits = _test_for_effect(stem, modules)
                picked.update(hits or [])
                why.append("%s -> %s" % (stem, ", ".join(hits) or "no test"))
            picked.update(CONTRACT)
        elif path.startswith("lib/audioinstruments/") or "AUDIOIF_PIN" in path:
            picked.update(INSTRUMENTS)
            why.append("instruments, because %s moved" % path)
        elif path.startswith("tools/effect_measurements") or \
                path.startswith("tests/support/"):
            picked.update(KIT)
            picked.update(CONTRACT)
            why.append("the kit moved, so every number it prints is suspect")
    if not picked:
        return [], "only documents or probes changed; no test can see it"
    return sorted(picked), "; ".join(why[:4])


def main(argv):
    listing = "--list" in argv
    argv = [a for a in argv if a != "--list"]
    scope = argv[1] if len(argv) > 1 else "auto"
    modules = _modules()
    chosen, why = choose(scope, modules)
    print("scope %s: %s" % (scope, why))
    print("running %d of %d test files" % (len(chosen), len(modules)))
    for module in chosen:
        print("  %s" % module)
    if listing or not chosen:
        return 0
    cmd = [sys.executable, "-m", "unittest"] + ["tests.%s" % m for m in chosen]
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", os.path.join(ROOT, "lib"))
    return subprocess.call(cmd, cwd=ROOT, env=env)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
