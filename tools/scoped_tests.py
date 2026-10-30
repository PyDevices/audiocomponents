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
    tools/scoped_tests.py --ci origin/main  # a pull request's tests, for CI
    tools/scoped_tests.py --ci <sha>        # a push's tests, from the commit
                                            # it moved main from

It prints the scope it chose and why before running, so a report can quote it.
Exit status is the suite's own. `--ci` runs nothing: it prints the test files
for pytest, or `full`, on stdout, and its reasons on stderr.

"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _find_root():
    """The checkout whose tests to run: the one the caller is standing in.

    A builder works in its own worktree and calls the main checkout's copy of
    this script, as the phase briefs tell it to. Resolving the root from this
    file's location then scanned the main checkout, where the builder's new
    test file does not exist -- Phase 4's Distortion builder got "no test
    file found" for a test it had just written, and other builders quoted
    a green run that never included their class. So the root is the nearest
    ancestor of the current directory that is an audiocomponents checkout,
    and only when there is none the checkout this file lives in.
    """
    here = os.getcwd()
    while True:
        if os.path.isfile(os.path.join(here, "lib", "audioeffects",
                                       "_component.py")) and \
                os.path.isdir(os.path.join(here, "tests")):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            return os.path.dirname(HERE)
        here = parent


ROOT = _find_root()
TESTS = os.path.join(ROOT, "tests")
LIB_EFFECTS = os.path.join(ROOT, "lib", "audioeffects")

#: Run these whenever anything under `lib/` moves: they are the shared promises
#: — the component API, the foundation, the portability tiers, the catalogue —
#: and a change to one effect can break them through `_component` or `__init__`.
CONTRACT = (
    "test_audio_component_api",
    "test_component_foundation",
    "test_portability_tier",
    "test_catalogue",
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
                "every effect; instruments skipped (audiodsp is pinned)")
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
            if stem in ("__init__", "_component"):
                picked.update(_effects_only(modules))
                why.append("%s is shared by every effect, so every effect "
                           "test runs (instruments stay off)"
                           % os.path.basename(path))
            else:
                hits = _test_for_effect(stem, modules)
                picked.update(hits or [])
                why.append("%s -> %s" % (stem, ", ".join(hits) or "no test"))
            picked.update(CONTRACT)
        elif path.startswith("lib/audioinstruments/") or "AUDIODSP_PIN" in path:
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


#: What CI always runs, whatever the change touched: the kit's tests, the
#: shared promises, and the two lifecycle matrices, which pick their own
#: classes and nodes from the same diff (LIFECYCLE_CHANGED_FROM).
CI_ALWAYS = KIT + ("test_kit",) + CONTRACT + (
    "test_lifecycle_matrix", "test_node_matrix")

#: Paths every test leans on. A change that touches one runs the whole
#: suite, because no mapping can say which tests it moved.
CI_SHARED = (
    ".github/",
    "tests/support/ulab/",
    "tests/conftest.py",
    "tools/effect_measurements",
    "tools/effect_probes/",
    "tools/scoped_tests.py",
    "lib/audioeffects/_",
    "lib/audioeffects/__init__.py",
    "lib/audioinstruments/_",
    "lib/audioinstruments/__init__.py",
    "AUDIODSP_PIN",
)

#: The roster tests that name every class, run when one class moves.
_ROSTERS = ("test_metadata_contract", "test_shared_circuit_overlap",
            "test_cpython_effects_library", "test_audio_component_api")

#: Paths no test reads, besides the ones the workflow already ignores.
_CI_SILENT = ("docs/", "LICENSE", "VERSION")

#: A docs page a test compares with the classes, so it is not silent.
_DOC_TESTS = {"docs/reference/effect-controls.md": "test_metadata_contract"}

#: A test that goes through every effect class, or every instrument, runs
#: when any one of them changes.
_EVERY_EFFECT = re.compile(r"audioeffects\.ALL\b|\bkit_options\b|\bGATED\b")
_EVERY_INSTRUMENT = re.compile(
    r"audioinstruments\.(ALL|MELODIC|DRUM_MACHINES)\b|"
    r"from audioinstruments import [^\n]*\b(ALL|MELODIC|DRUM_MACHINES)\b")


def _source(rel):
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8",
                  errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def _helpers():
    """{stem: path} for the python files under tests/ that are not tests:
    tests/support/*.py and the helpers beside the tests. Their names are
    unique, because the tests import them bare (tests/support is on
    sys.path), so a stem is all an import has to name."""
    out = {}
    for folder in ("tests", "tests/support"):
        for name in sorted(os.listdir(os.path.join(ROOT, folder))):
            if name.endswith(".py") and not (folder == "tests" and
                                             name.startswith("test_")):
                out.setdefault(name[:-3], "%s/%s" % (folder, name))
    return out


def _imported_names(rel):
    """Every name an import in `rel` mentions, dotted parts split, so that
    `import kit_common as kc`, `from support import kit` and `from kit_probes
    import x` all name the helper they load. Imports inside functions count."""
    import ast
    try:
        tree = ast.parse(_source(rel))
    except SyntaxError:
        return None
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.update(alias.name.split("."))
        elif isinstance(node, ast.ImportFrom):
            names.update((node.module or "").split("."))
            names.update(alias.name for alias in node.names)
    return names


def _importers(changed_helpers, modules):
    """The test modules that import any of `changed_helpers` (stems), directly
    or through other helpers. None when a file cannot be parsed."""
    helpers = _helpers()
    files = dict(("tests/%s.py" % m, m) for m in modules)
    files.update((path, None) for path in helpers.values())
    imports = {}
    for path in files:
        names = _imported_names(path)
        if names is None:
            return None
        imports[path] = names & set(helpers)
    reached = set(changed_helpers)
    grew = True
    while grew:
        grew = False
        for path, names in imports.items():
            stem = os.path.basename(path)[:-3]
            if files[path] is None and stem not in reached and \
                    names & reached:
                reached.add(stem)
                grew = True
    return sorted(m for path, m in files.items()
                  if m is not None and imports[path] & reached)


def _mentions(words, modules, pattern=None):
    """The test modules whose text names one of `words`, or matches
    `pattern`: a test that builds a class by its name reaches its module."""
    word = re.compile(r"\b(%s)\b" % "|".join(re.escape(w) for w in words))
    out = []
    for module in modules:
        text = _source("tests/%s.py" % module)
        if word.search(text) or (pattern and pattern.search(text)):
            out.append(module)
    return out


def _effect_classes(rel):
    import ast
    try:
        tree = ast.parse(_source(rel))
    except SyntaxError:
        return []
    return [n.name for n in tree.body
            if isinstance(n, ast.ClassDef) and not n.name.startswith("_")]


def _changed_since(base):
    """The files changed since `base`: a pull request's base branch, or the
    commit a push to main moved from."""
    done = subprocess.run(["git", "diff", "--name-only", base + "...HEAD"],
                          cwd=ROOT, capture_output=True, text=True)
    if done.returncode:
        raise SystemExit("git cannot diff from %s: %s"
                         % (base, done.stderr.strip()))
    return sorted(p for p in done.stdout.split("\n") if p.strip())


def choose_ci(changed, modules):
    """Return (test modules, or None for the whole suite; the reasons).

    Anything this cannot map to its own tests runs the whole suite: a
    narrower run that misses a break is worse than a slow one.
    """
    picked, why = set(m for m in CI_ALWAYS if m in modules), []
    helpers = []
    for path in changed:
        if path.startswith(CI_SHARED):
            return None, ["%s is shared, so the whole suite runs" % path]
        if path in _DOC_TESTS:
            if _DOC_TESTS[path] in modules:
                picked.add(_DOC_TESTS[path])
                why.append("%s is checked by %s" % (path, _DOC_TESTS[path]))
            continue
        if path.startswith(_CI_SILENT) or (
                path.endswith(".md") and not path.startswith(("lib/",
                                                              "tests/"))):
            continue
        name = os.path.basename(path)
        top = "/" not in path[6:]
        if path.startswith("tests/") and top and name.startswith("test_") \
                and name.endswith(".py"):
            if name[:-3] in modules:
                picked.add(name[:-3])
                why.append("%s edited" % name[:-3])
            continue
        if name.endswith(".py") and (
                (path.startswith("tests/") and top) or
                (path.startswith("tests/support/") and
                 "/" not in path[14:])):
            helpers.append(name[:-3])
            continue
        if path.startswith("lib/audioeffects/") and \
                "/" not in path[17:] and name.endswith(".py"):
            hits = _test_for_effect(name[:-3], modules)
            if hits and hits != ["test_cpython_effects_library"]:
                words = [name[:-3]] + _effect_classes(path)
                more = _mentions(words, modules, _EVERY_EFFECT)
                picked.update(hits)
                picked.update(more)
                # The rosters that name every class read this one too.
                picked.update(m for m in _ROSTERS if m in modules)
                why.append("%s -> %s, and %d tests that name it or go "
                           "through every effect"
                           % (name[:-3], ", ".join(hits),
                              len(set(more) - set(hits))))
                continue
        if path.startswith("lib/audioinstruments/") and \
                "/" not in path[21:] and name.endswith(".py"):
            hits = _mentions([name[:-3]], modules, _EVERY_INSTRUMENT)
            if hits:
                picked.update(hits)
                picked.update(m for m in INSTRUMENTS + _ROSTERS
                              if m in modules)
                why.append("%s -> %d tests that name it or go through "
                           "every instrument" % (name[:-3], len(hits)))
                continue
        return None, ["%s has no tests of its own, so the whole suite runs"
                      % path]
    if helpers:
        users = _importers(helpers, modules)
        if users is None:
            return None, ["a test file does not parse, so the whole suite "
                          "runs"]
        if not users:
            return None, ["%s is imported by no test, so the whole suite "
                          "runs" % ", ".join(helpers)]
        picked.update(users)
        why.append("%s -> the %d tests that import it"
                   % (", ".join(helpers), len(users)))
    return sorted(picked), why or ["only the tests every change runs"]


def ci(base):
    modules = _modules()
    chosen, why = choose_ci(_changed_since(base), modules)
    for line in why:
        print(line, file=sys.stderr)
    if chosen is None:
        print("full")
    else:
        print(" ".join("tests/%s.py" % m for m in chosen))
    return 0


def main(argv):
    if "--ci" in argv:
        return ci(argv[argv.index("--ci") + 1])
    listing = "--list" in argv
    argv = [a for a in argv if a != "--list"]
    scope = argv[1] if len(argv) > 1 else "auto"
    modules = _modules()
    chosen, why = choose(scope, modules)
    print("scope %s: %s" % (scope, why))
    print("root %s" % ROOT)
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
