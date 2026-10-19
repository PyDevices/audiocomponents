"""The paperwork check: the class has a CHANGELOG line, and every source
citation in its module resolves against the audiodsp pin.

**CHANGELOG.** CHANGELOG.md names a class at the start of a bullet:
``- **`DigitalDelay` (rebuilt, Phase 5; ...):**``. The `changelog` cell is
red when no line starts with ``- **`<NAME>`**``.

**Citations.** Every `<file>.c:NN`, `.h:NN`, `.py:NN` or `<path>:NN-MM`
in the class's module (docstrings and comments alike), and every bare
`` `:NN` `` after one, which cites the file named last. A citation that
names a file in audiodsp at the commit in AUDIODSP_PIN (by path, or by
file name when it gives no directory) must name lines inside that file
there; one that names a file of this repository is read against the
working tree. A file found in neither is red. Line numbers inside the
file are all this can know: a citation whose lines moved under it still
resolves.

**The surface.** The class's `MACRO_LABELS` and `MACRO_MODES` against the
surface table of its class card: `<NAME>.md` in the cards directory
(`KIT_CARDS`, or a `docs/effects-internal/dossiers` directory in a parent
of this repository), read as text. The table is the first in section 3
whose header has `#`, `Label` and `Mode` columns; a label is compared
without its backticks and a mode by its first word (`UNIPOLAR, log` is
UNIPOLAR; a macro `MACRO_MODES` leaves out is UNIPOLAR). One
`surface-m<i>` cell per macro either side has; a mismatch names both. With
no card, or no such table on it, the `surface` cell prints `na(...)`.

The pinned audiodsp is read from a checkout, never changed: `KIT_AUDIODSP`
or an `audiodsp` directory beside this repository (or beside a parent of
it). Without one, or without the pinned commit in it, each audiodsp
citation prints `na(...)` saying which.

CPython only: it reads git.

    python tests/support/kit_paperwork.py DigitalDelay
"""

import os
import re
import subprocess
import sys

if __name__ == "__main__":
    sys.path.insert(0, "lib")
    sys.path.insert(0, "tests/support")

import kit_common as kc

CHECK = "paperwork"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

CITE = re.compile(
    r"(?<![\w/.-])((?:[\w-]+/)*[\w.-]+\.(?:c|h|py)):(\d+)(?:-(\d+))?")
MORE = re.compile(r"(?:(?<=[\s(,`])|^):(\d+)(?:-(\d+))?\b")


def pin_commit(root=ROOT):
    """The commit AUDIODSP_PIN names (its last non-comment line's second
    word), or None."""
    path = os.path.join(root, "AUDIODSP_PIN")
    if not os.path.isfile(path):
        return None
    commit = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                words = line.split()
                commit = words[1] if len(words) > 1 else words[0]
    return commit


def find_checkout(root=ROOT):
    env = os.environ.get("KIT_AUDIODSP")
    if env:
        return env if os.path.isdir(env) else None
    here = root
    for _up in range(6):
        here = os.path.dirname(here)
        candidate = os.path.join(here, "audiodsp")
        if os.path.exists(os.path.join(candidate, ".git")):
            return candidate
    return None


class Pin:
    """The audiodsp tree at one commit, read with git."""

    def __init__(self, checkout, commit):
        self.checkout = checkout
        self.commit = commit
        self.why = None
        self.files = None
        self._lines = {}
        if checkout is None:
            self.why = "no audiodsp checkout"
        elif commit is None:
            self.why = "no AUDIODSP_PIN"
        else:
            done = subprocess.run(
                ["git", "-C", checkout, "ls-tree", "-r", "--name-only",
                 commit], capture_output=True, text=True)
            if done.returncode != 0:
                self.why = "pin %s is not in %s" % (commit[:10], checkout)
            else:
                self.files = done.stdout.split()

    def match(self, path):
        if self.files is None:
            return []
        if path.startswith("audiodsp/"):
            # A citation may name the repository too: audiodsp/src/x.c.
            path = path[len("audiodsp/"):]
        if "/" in path:
            return [f for f in self.files
                    if f == path or f.endswith("/" + path)]
        return [f for f in self.files if f.rsplit("/", 1)[-1] == path]

    def lines(self, path):
        if path not in self._lines:
            done = subprocess.run(
                ["git", "-C", self.checkout, "show",
                 "%s:%s" % (self.commit, path)], capture_output=True)
            self._lines[path] = done.stdout.count(b"\n") \
                if done.returncode == 0 else 0
        return self._lines[path]


def local_match(path, root=ROOT):
    if "/" in path and os.path.isfile(os.path.join(root, path)):
        return [os.path.join(root, path)]
    base = path.rsplit("/", 1)[-1]
    out = []
    for top in ("lib", "tools", "tests"):
        for here, _dirs, files in os.walk(os.path.join(root, top)):
            if base in files:
                full = os.path.join(here, base)
                if full.endswith(path):
                    out.append(full)
    return sorted(out)


def _count(path):
    with open(path, "rb") as f:
        return f.read().count(b"\n")


def citations(text):
    """[(file, first line, last line)] in the order they appear; a bare
    `:NN` cites the file named last."""
    found = []
    for m in CITE.finditer(text):
        found.append((m.start(), m.group(1), int(m.group(2)),
                      int(m.group(3) or m.group(2))))
    for m in MORE.finditer(text):
        before = [c for c in found if c[0] < m.start() and c[1] is not None]
        if not before:
            continue
        last = max(before, key=lambda c: c[0])
        found.append((m.start(), last[1], int(m.group(1)),
                      int(m.group(2) or m.group(1))))
    found.sort()
    return [(f, a, b) for _pos, f, a, b in found]


def cite_verdict(path, first, last, pin, root=ROOT):
    if last < first:
        return "RED(range runs backwards)"
    hits = pin.match(path)
    if hits:
        fits = [h for h in hits if last <= pin.lines(h)]
        if not fits:
            return "RED(%s has %d lines at the pin)" % (
                hits[0], max(pin.lines(h) for h in hits))
        return "ok"
    local = local_match(path, root)
    if local:
        if any(last <= _count(p) for p in local):
            return "ok"
        return "RED(%s has %d lines)" % (os.path.relpath(local[0], root),
                                         _count(local[0]))
    if pin.files is None:
        return "na(%s)" % pin.why
    return "RED(no %s at the pin or in this repository)" % path


def find_cards(root=ROOT):
    env = os.environ.get("KIT_CARDS")
    if env:
        return env if os.path.isdir(env) else None
    here = root
    for _up in range(6):
        here = os.path.dirname(here)
        candidate = os.path.join(here, "docs", "effects-internal",
                                 "dossiers")
        if os.path.isdir(candidate):
            return candidate
    return None


def _row(line):
    line = line.strip().replace("\\|", "/")
    return [c.strip() for c in line.strip("|").split("|")]


def card_surface(text):
    """[(index, label, mode)] from the card's surface table, or None."""
    inside = False
    header = None
    rows = []
    for line in text.splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = line[3:].lstrip().startswith("3")
            continue
        if not inside:
            continue
        if not line.lstrip().startswith("|"):
            if header is not None and rows:
                break
            continue
        cells = _row(line)
        if header is None:
            if "#" in cells and "Label" in cells and "Mode" in cells:
                header = cells
            continue
        if not "".join(cells).strip("-: "):
            continue
        words = cells[header.index("Mode")].replace(",", " ").split()
        mode = words[0].upper() if words else ""
        number = cells[header.index("#")].replace("\u2013", "-")
        label = cells[header.index("Label")].replace("`", "").strip()
        if "-" in number:
            # A range row: "1-3 | `Voice 1` ... `Voice 3`" names one macro
            # per index, the label's trailing number counting with it.
            try:
                first, last = (int(n) for n in number.split("-", 1))
            except ValueError:
                continue
            stem = label.split("\u2026")[0].split("...")[0].strip()
            base = stem.rstrip("0123456789").rstrip()
            start = stem[len(base):].strip()
            for step, index in enumerate(range(first, last + 1)):
                name = ("%s %d" % (base, int(start) + step) if start
                        else base)
                rows.append((index, name, mode))
            continue
        try:
            index = int(number)
        except ValueError:
            continue
        rows.append((index, label.strip(), mode))
    return rows if header is not None else None


def surface_cells(cells, cls, cards):
    """The surface cells for `cls` against its card in `cards`."""
    if cards is None:
        cells.cell("surface", "na(no class cards)")
        return
    path = os.path.join(cards, "%s.md" % cls.NAME)
    if not os.path.isfile(path):
        cells.cell("surface", "na(no card for %s)" % cls.NAME)
        return
    with open(path, encoding="utf-8") as f:
        rows = card_surface(f.read())
    if rows is None:
        cells.cell("surface", "na(no surface table in section 3)")
        return
    card = dict((index, (label, mode)) for index, label, mode in rows)
    labels = cls.MACRO_LABELS
    ours = dict((i, (labels[i], cls.MACRO_MODES.get(i, "UNIPOLAR")))
                for i in range(len(labels)))
    for i in sorted(set(card) | set(ours)):
        a = ours.get(i)
        b = card.get(i)
        if a == b:
            cells.cell("surface-m%d" % i, "ok")
            continue
        cells.cell("surface-m%d" % i, "RED(class %s, card %s)" % (
            "%r %s" % a if a else "none", "%r %s" % b if b else "none"))


def has_changelog_line(name, changelog_text):
    head = "- **`%s`" % name
    for line in changelog_text.splitlines():
        if line.startswith(head):
            return True
    return False


def check(name, text, changelog_text, pin, emit=print, root=ROOT, cls=None,
          cards=None):
    """The paperwork cells for class `name` whose module source is `text`
    (and, given `cls`, its surface against its card in `cards`). Returns
    the red count."""
    cells = kc.Cells(name, CHECK, emit)
    if cls is not None:
        surface_cells(cells, cls, cards)
    cells.cell("changelog", "ok" if has_changelog_line(name, changelog_text)
               else "RED(no CHANGELOG line starts - **`%s`)" % name)
    seen = {}
    for path, first, last in citations(text):
        key = "cite:%s:%d" % (path, first)
        if last != first:
            key += "-%d" % last
        if key in seen:
            continue
        seen[key] = True
        cells.cell(key, cite_verdict(path, first, last, pin, root))
    return cells.summary()


def run(cls, emit=print, name=None, **_):
    module = sys.modules[cls.__module__]
    with open(module.__file__, encoding="utf-8") as f:
        text = f.read()
    with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as f:
        changelog = f.read()
    pin = Pin(find_checkout(), pin_commit())
    return check(name or cls.NAME, text, changelog, pin, emit, cls=cls,
                 cards=find_cards())


if __name__ == "__main__":
    import kit
    kit.main(sys.argv[1:], only=(CHECK,))
