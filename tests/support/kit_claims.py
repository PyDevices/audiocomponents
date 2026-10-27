"""The claims check: every sentence in a class's docstring that makes a
claim is tied to a test, and that test exists and passes.

**The convention.** The class's test module (by default
`tests/test_cpython_effects_<name>.py`, else `tests/test_<name>.py`) holds a
module-level `CLAIMS` table. Each row is `(sentence, test)`: the docstring
sentence word for word (whitespace aside), and the test that asserts it. `test` is a test
method's name (`"test_x"`, any TestCase in the module that defines it), a
`"Class.test_x"`, a tuple of those, or `"DECLARED:<NAME>,<event
prefix>,<property>[,<scope>...]"`, naming a row of the lifecycle matrix's
DECLARED table (a disclosure the matrix holds). A scoped row is named with
its scopes: `patches=1/2/d` for a patch tuple (`d` the defaults), and each
interpreter by name (`DECLARED:PitchShifter,E10-reset,P4,circuitpython`).

**The text.** What a player reads: the class's module docstring, then the
class docstring (a rebuilt module holds one class, and either may carry
the player's text). Markdown bold headings (`**Controls.**`) are not
sentences.

**What counts as a claim.** Mechanically, a sentence is a claim if it holds
a digit, a number word, or one of the bound and absolute words in
`CLAIM_WORDS` (always, never, exactly, every, no, at most, up to, within,
...). The rule errs on catching too much: a sentence it catches that
asserts nothing is reworded or struck, not argued with.

**Cells.** `table` (the module and its CLAIMS exist), `row<N>` per CLAIMS
row (the sentence is in the docstring, each named test exists by an AST
lookup and passes when run alone under unittest on CPython; a skipped test
has not passed), and `loose<N>` per claim-shaped docstring sentence that no
row covers.

CPython only: it reads the source and runs unittest.

    python tests/support/kit_claims.py SlapbackDelay [--no-run]
"""

import ast
import io
import os
import re
import sys
import unittest

if __name__ == "__main__":
    sys.path.insert(0, "lib")
    sys.path.insert(0, "tests/support")

import kit_common as kc

CHECK = "claims"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS = os.path.join(ROOT, "tests")

NUMBER_WORDS = (
    "zero one two three four five six seven eight nine ten eleven twelve "
    "twenty thirty forty fifty sixty hundred thousand million half halves "
    "twice double triple quarter third thirds").split()
CLAIM_WORDS = (
    "always never exactly every each all any no none nothing only cannot "
    "can't must guarantee guarantees guaranteed bound bounded bounds limit "
    "limits most least more less fewer than within under over above below "
    "beyond until same identical unchanged untouched equal equals "
    "maximum minimum max min").split()
_WORDS = re.compile(r"[A-Za-z']+")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z`*(\"'])")
_ABBREV = ("e.g.", "i.e.", "etc.", "vs.", "cf.")
_HEADING = re.compile(r"\*\*[^*]+\*\*")


def flat(text):
    return " ".join((text or "").split())


def is_claim(sentence):
    """Whether the sentence makes a claim, by the mechanical rule."""
    if any(c.isdigit() for c in sentence):
        return True
    for word in _WORDS.findall(sentence.lower()):
        if word in NUMBER_WORDS or word in CLAIM_WORDS:
            return True
    lowered = sentence.lower()
    return "up to" in lowered or "at most" in lowered or \
        "at least" in lowered


def sentences(text):
    """The flattened text cut into sentences, keeping e.g./i.e. inside."""
    out = []
    for piece in _SENTENCE_END.split(flat(text)):
        if out and out[-1].endswith(_ABBREV):
            out[-1] += " " + piece
        else:
            out.append(piece)
    return [s for s in out if s.strip()]


def test_index(path):
    """{method name: [TestCase class names]} by an AST read of `path`."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), path)
    index = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                        and item.name.startswith("test"):
                    index.setdefault(item.name, []).append(node.name)
    return index


def targets(test):
    if isinstance(test, (tuple, list)):
        return list(test)
    return [test]


def resolve(target, index):
    """Test ids ("Class.test_x") for one target, or None if none exists."""
    if "." in target:
        cls, meth = target.split(".", 1)
        return [target] if cls in index.get(meth, ()) else None
    owners = index.get(target)
    if not owners:
        return None
    return ["%s.%s" % (owner, target) for owner in owners]


def _canonical(name, prefix, prop, patches, impls):
    if patches is not None:
        patches = tuple(sorted(patches, key=lambda p: -1 if p is None
                               else p))
    if impls is not None:
        impls = tuple(sorted(impls))
    return (name, prefix, prop, patches, impls)


def parse_declared(target):
    """The canonical row a `DECLARED:` target names, or None. After NAME,
    prefix and property, a `patches=1/2/d` part scopes it to patches (`d`
    the defaults), and any other part names an interpreter."""
    parts = target.split(":", 1)[1].split(",")
    if len(parts) < 3:
        return None
    patches = impls = None
    for part in parts[3:]:
        if part.startswith("patches="):
            patches = []
            for p in part[8:].split("/"):
                if p == "d":
                    patches.append(None)
                elif p.isdigit():
                    patches.append(int(p))
                else:
                    return None
        else:
            impls = (impls or []) + [part]
    return _canonical(parts[0], parts[1], parts[2], patches, impls)


def declared_exists(target):
    import lifecycle
    want = parse_declared(target)
    if want is None:
        return False
    for key in lifecycle.DECLARED:
        patches, impls = lifecycle.declared_scope(key)
        if _canonical(key[0], key[1], key[2], patches, impls) == want:
            return True
    return False


def run_tests(module, ids):
    """{test id: None if it passed, else why not}."""
    out = {}
    for tid in ids:
        suite = unittest.defaultTestLoader.loadTestsFromName(tid, module)
        result = unittest.TextTestResult(io.StringIO(), False, 0)
        suite.run(result)
        if result.failures or result.errors:
            out[tid] = "fails"
        elif result.skipped:
            out[tid] = "skipped"
        elif result.testsRun == 0:
            out[tid] = "did not run"
        else:
            out[tid] = None
    return out


def check(name, doc, module, path, emit=print, execute=True):
    """The claims cells for a class with docstring `doc`, whose test module
    is the imported `module` at `path`. Returns the red count."""
    cells = kc.Cells(name, CHECK, emit)
    claims = getattr(module, "CLAIMS", None) if module is not None else None
    if not doc:
        cells.cell("table", "RED(no docstring)")
        return cells.summary()
    if claims is None:
        cells.cell("table", "RED(no CLAIMS table in %s)"
                   % os.path.basename(path or "the test module"))
        rows = ()
    else:
        cells.cell("table", "ok")
        rows = claims
    text = flat(doc)
    index = test_index(path) if path else {}
    ids = []
    plans = []
    for sentence, test in rows:
        sentence = flat(sentence)
        reds = []
        mine = []
        if sentence not in text:
            reds.append("not in the docstring")
        for target in targets(test):
            if target.startswith("DECLARED:"):
                if not declared_exists(target):
                    reds.append("no lifecycle row %s" % target[9:])
                continue
            found = resolve(target, index)
            if found is None:
                reds.append("no test %s" % target)
            else:
                mine.extend(found)
        ids.extend(t for t in mine if t not in ids)
        plans.append((sentence, reds, mine))
    results = run_tests(module, ids) if execute and ids else {}
    rest = text
    for n, (sentence, reds, mine) in enumerate(plans):
        for tid in mine:
            if results.get(tid):
                reds.append("%s %s" % (tid, results[tid]))
        rest = rest.replace(sentence, " ")
        verdict = "RED(%s: %s)" % ("; ".join(reds), sentence[:60]) if reds \
            else "ok"
        cells.cell("row%d" % n, verdict)
    n = 0
    for sentence in sentences(rest):
        sentence = flat(_HEADING.sub(" ", sentence))
        if sentence and is_claim(sentence):
            cells.cell("loose%d" % n, "RED(claim with no CLAIMS row: %s)"
                       % sentence[:80])
            n += 1
    return cells.summary()


#: Classes whose test file is not named after the class.
_TEST_MODULES = {"MultibandCompressor": "test_cpython_effects_multiband"}


def module_for(cls, name=None):
    """(imported test module or None, its path). With no `name`, the
    class's own `test_<name>.py` is read when there is no
    `test_cpython_effects_<name>.py`, as `NoiseGate`'s is."""
    if name is None:
        name = _TEST_MODULES.get(
            cls.NAME, "test_cpython_effects_%s" % cls.NAME.lower())
        short = "test_%s" % cls.NAME.lower()
        if (not os.path.isfile(os.path.join(TESTS, name + ".py"))
                and os.path.isfile(os.path.join(TESTS, short + ".py"))):
            name = short
    path = os.path.join(TESTS, name + ".py")
    if TESTS not in sys.path:
        sys.path.insert(0, TESTS)
    if not os.path.isfile(path):
        return None, None
    return __import__(name), path


def run(cls, emit=print, module=None, execute=True, name=None, **_):
    try:
        mod, path = module_for(cls, module)
    except Exception as exc:                              # noqa: BLE001
        cells = kc.Cells(name or cls.NAME, CHECK, emit)
        cells.cell("table", "RED(the test module does not import: %s)"
                   % type(exc).__name__)
        return cells.summary()
    return check(name or cls.NAME, player_text(cls), mod, path, emit,
                 execute)


def player_text(cls):
    module = sys.modules.get(cls.__module__)
    parts = [getattr(module, "__doc__", None), cls.__doc__]
    return " ".join(flat(p) for p in parts if p)


if __name__ == "__main__":
    import kit
    kit.main(sys.argv[1:], only=(CHECK,))
