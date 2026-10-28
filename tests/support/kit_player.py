"""The player's text against its `CLAIMS` table, and the two readings every
class's table leans on: latency and the modules it needs.

A test file passes its own `globals()` as `owners`, so a row naming
`TheBypassIsAWire.test_...` is checked against the test classes that file
actually defines.
"""

import array
import re
import sys

import audiocore


def _flat(text):
    return " ".join(text.split())


def claim_problems(doc, claims, owners):
    """What is wrong between a docstring and `claims`: a sentence missing, a
    named test that does not exist, a figure outside every claim."""
    doc = _flat(doc)
    problems = []
    rest = doc
    for sentence, tests in claims:
        if sentence not in doc:
            problems.append("missing: %s" % sentence)
        rest = rest.replace(sentence, " ")
        for name in tests:
            owner, _, test = name.partition(".")
            if not hasattr(owners.get(owner), test):
                problems.append("no test %s" % name)
    for match in re.finditer(r"\S*\d\S*", rest):
        problems.append("figure outside a claim: %s" % match.group())
    return problems


def check_claims(case, doc, claims, owners, sentence):
    """The table holds, and the checker can fail: a figure outside a claim,
    `sentence` dropped from the docstring, a row naming a missing test."""
    doc = _flat(doc)
    case.assertIn(sentence, doc)
    case.assertEqual(claim_problems(doc, claims, owners), [])
    case.assertTrue(claim_problems(doc + " It reads 12 ms.", claims, owners))
    case.assertTrue(claim_problems(doc.replace(sentence, ""), claims, owners))
    case.assertTrue(claim_problems(
        doc, claims + (("Latency", ("Nobody.test_nothing",)),), owners))


def impulse(rate, channels=2, frames=256):
    values = array.array("h", bytes(2 * channels * frames))
    for channel in range(channels):
        values[channel] = 16000
    return audiocore.RawSample(values, sample_rate=rate,
                               channel_count=channels)


def first_frame(effect):
    """The first output frame's samples."""
    data = audiocore.get_buffer(effect.output)[1]
    data = memoryview(bytes(data)).cast("h")
    return list(data[:effect.channel_count])


def latency_problems(cls, rate, delayed=False, patches=None):
    """Every patch whose impulse does not show in the first output frame,
    or whose reported latency is not zero. `delayed` plants the fault: the
    impulse is moved one frame late, which a zero-latency reading must
    catch. `patches` narrows the walk where a patch's first output sample
    rounds to zero for a reason other than delay."""
    problems = []
    for patch in sorted(cls.PATCHES) if patches is None else patches:
        source = impulse(rate)
        if delayed:
            values = array.array("h", bytes(2 * 2 * 256))
            values[2] = values[3] = 16000
            source = audiocore.RawSample(values, sample_rate=rate,
                                         channel_count=2)
        effect = cls.create(source, rate, patch=patch)
        try:
            if effect.latency_samples != 0:
                problems.append("p%d reports %d" % (patch,
                                                    effect.latency_samples))
            if not any(first_frame(effect)):
                problems.append("p%d is silent on the impulse's frame" % patch)
        finally:
            effect.deinit()
    return problems


def missing_module_problems(cls, rate):
    """Each module in `REQUIRES` that construction does not refuse to do
    without."""
    problems = []
    for name in cls.REQUIRES:
        saved = sys.modules.get(name)
        sys.modules[name] = None
        try:
            cls.create(impulse(rate), rate)
            problems.append("built without %s" % name)
        except ImportError:
            pass
        finally:
            if saved is None:
                del sys.modules[name]
            else:
                sys.modules[name] = saved
    return problems
