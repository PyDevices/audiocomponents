"""pytest's view of the suite, for CI's parallel run (pytest-xdist).

The tests are plain unittest and `python -m unittest discover -s tests`
ignores this file. It changes only the order pytest hands the tests out in,
never which tests run.

The slowest files go first. The lifecycle matrix runs the whole matrix on
CPython in its setUpClass, the node matrix runs its nodes one after another
in its own (NodeFlanger alone takes minutes), and a few reverb and tape delay classes take
minutes each; started last, any of them would finish long after every other
worker had gone idle. With `--dist loadscope` each class stays on one worker,
so a setUpClass runs once.
"""

#: Files whose tests start first, slowest first.
SLOW_FIRST = ("test_lifecycle_matrix.py", "test_node_matrix.py",
              "test_cpython_effects_reverb.py",
              "test_cpython_effects_tapedelay.py")


def pytest_collection_modifyitems(config, items):
    def rank(item):
        name = item.path.name
        return SLOW_FIRST.index(name) if name in SLOW_FIRST else len(SLOW_FIRST)

    items.sort(key=rank)
