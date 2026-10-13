"""pytest's view of the suite, for CI's parallel run (pytest-xdist).

The tests are plain unittest and `python -m unittest discover -s tests`
ignores this file. It changes only the order pytest hands the tests out in,
never which tests run.

The slowest class goes first. The lifecycle matrix runs the whole matrix on
CPython in its setUpClass, longer than any other worker's share of the rest;
started last, it would finish long after every other worker had gone idle.
With `--dist loadscope` each class stays on one worker, so its setUpClass
runs once.
"""

#: Files whose tests start first, slowest first.
SLOW_FIRST = ("test_lifecycle_matrix.py",)


def pytest_collection_modifyitems(config, items):
    def rank(item):
        name = item.path.name
        return SLOW_FIRST.index(name) if name in SLOW_FIRST else len(SLOW_FIRST)

    items.sort(key=rank)
