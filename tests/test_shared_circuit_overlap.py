"""A voice struck in its sibling's shadow must decay like the voice it is.

Several audioinstruments kits give two or more voices ONE permanent
synthio.Note and reconfigure it per hit - closed and open hi-hat, clap and
maracas, rimshot and cowbell. That is faithful to the hardware, where those
sounds really do come off one circuit and choke each other. It is also the one
place a target can get an envelope wrong without anything sounding broken.

audioif's CPython target used to bake the envelope definition into the state
object at press time, so a re-pressed note kept stepping the envelope it was
FIRST pressed with (fixed in d84470a, this repository's pinned floor). A closed
hat struck a beat after an open one rang for the OPEN hat's decay: 400 ms
instead of 53 ms on tr808, 747 ms instead of 64 ms on tr707. Nine of ten phrase
renders moved. It passed a listening pass anyway, because a hat ringing 400 ms
still sounds like a hat, and no test phrase ever put an open hat and a closed
one back to back.

That is the reason this file exists. A listening gate only catches what the
material exercises, and it catches absence far better than plausible
wrongness - so this gate does not depend on the material being right. It walks
every shared circuit every kit actually builds, plays both faces of it in both
orders, and holds the second hit to the decay that hit has on its own.

Discovery is dynamic in both directions: the kits come from
`audioinstruments.DRUM_MACHINES` and the circuits from
`tools.shared_circuits.differing`, which instruments `synthio.Synthesizer.press`
rather than reading each module. A kit added later, or a new shared circuit in
an existing kit, is covered without editing this file.
"""

import unittest

import audioinstruments

from tools.shared_circuits import (
    BUDGET_SECONDS, DECAY_FLOOR, SAMPLE_RATE, block_rms, budget_blocks,
    differing, frames_per_block, gap_blocks, solo_decay)


# The decay ruler, the gap rule and the render budget all live in
# tools/shared_circuits.py, imported above, because the `transitions`
# render mode has to probe the same moment this gate measures. If the
# two ever disagreed, a listener and this test could reach opposite
# conclusions about the same kit - which is the failure the whole
# effort exists to remove. The rationale for each value is recorded
# there; what follows is what this gate adds on top.
#
# Decay is the time for the block RMS to fall to a hundredth of the voice's own
# peak - 40 dB down. That is the depth the fault was originally characterised
# at, and it is where a drum voice's decay actually lives: at 20 dB down these
# hats have barely started to separate.

# The gap between the two hits is taken from the FIRST voice's own decay rather
# than fixed, and the choice is load-bearing at both ends.
#
# Too short and the two hits are one event - the second press lands inside the
# first's attack and what follows is a fused sound, not a transition.
#
# Too long and there is nothing left to inherit. The fault only bites while the
# first note's envelope state is still stepping; once that note has run out the
# next press builds a fresh state and gets its own envelope, bug or no bug.
# That is exactly why the original hand measurement, taken at a fixed 250 ms,
# reported tr909 as clean (74.6 ms alone against 70.0 ms after): the tr909 open
# hat is only 101 ms long, so at 250 ms the circuit had already finished and
# the closed hat was never in its shadow. Half of the first voice's own decay
# is inside every voice's life by construction, and it puts tr909 back in the
# gate - on the pre-fix floor its (42, 46) circuit now misses by 4 and 6 blocks
# in the two directions.
#
# Half is also well past the attack transient and leaves the first voice about
# 20 dB down, which is what keeps its residual under the second hit small (see
# `_after`). Across the ten kits the rule picks gaps of 16 ms to 373 ms: a flam
# at one end, a dotted eighth at 120 BPM at the other, all of them things a
# drummer plays.

# ...and never less than two blocks, so the two note_on calls cannot land in
# one pull and collapse into a single press.

# How far the second hit's decay may sit from its solo decay: three blocks
# (16.0 ms at 48 kHz), or a tenth of the solo decay, whichever is larger.
#
# Measured margin on today's floor. All 52 measurements the ten kits produce
# land within TWO blocks of the solo decay, and 50 of them within exactly one.
# The tightest margin is 3.0x, on the short hats where the three-block floor is
# the binding term - dmx 54 -> 37 is 32.0 ms alone against 37.3 ms after. The
# widest deviation, dmx 56 -> 39 at 400.0 ms alone against 410.7 ms after, sits
# at 3.75x.
#
# What it has to catch is far larger. On the pre-fix floor 49 of those same 52
# measurements breach this tolerance, across 9 of the 10 kits, by 1.27x to
# 11.75x on the rings-too-long side and 0.82x down to 0.09x on the other.
#
# The relative term binds for any voice past about 160 ms and nothing on
# today's floor comes near it. It is there so the gate does not become a 16 ms
# hair trigger on a future voice whose decay is measured in whole seconds.
TOLERANCE_BLOCKS = 3
TOLERANCE_FRACTION = 0.10

# Long enough for every voice in the ten kits to fall 40 dB (the slowest, the
# tr707 open hat, takes 747 ms) with room for a kit that rings much longer,
# and short enough that a stuck voice fails rather than hangs. Nothing is
# rendered to this length unless it needs to be; the scans below stop early.





def _milliseconds(blocks):
    return blocks * frames_per_block() * 1000.0 / SAMPLE_RATE




def _after(name, first, second, gap, floor):
    """Decay in blocks of `second`, struck `gap` blocks after `first`.

    Contamination - the first voice still ringing under the second - is the
    whole difficulty here, and it splits into a dangerous half and a benign
    one.

    The dangerous half is the threshold. Measured against "40 dB below the
    loudest block after the onset", a decay reads whatever is loudest, and the
    first voice can still be louder than the second: on tr808 the 75 tail is
    3.3x the 37 peak at the moment 37 is struck. Taking the threshold from the
    mix would silently rescale the measurement by how loud the FIRST voice
    happened to be. So `floor` is an absolute level supplied by the caller from
    the second voice's own solo render - the same level its solo decay was
    measured against, which is what makes the two numbers the same question
    asked twice.

    The benign half is left in place deliberately. Whatever the first voice
    still puts out only adds energy, so it can only hold the envelope above the
    floor LONGER, never shorter: the result is an upper bound on the second
    voice's true decay.

    That bound is weaker than it first looks and the comment here used to
    overstate it. An upper bound rules out one direction only - a voice cut
    SHORT cannot be hidden by residual, so no undershoot can pass unseen. It
    does not rule out the other: a voice ringing slightly too long could in
    principle be read as residual and land inside tolerance. What makes that
    acceptable is the size, not the logic. Striking the second voice at the same block with no first hit at
    all reproduces the solo decay exactly, for all 52 measurements - so the
    entire deviation this gate sees on a healthy floor, one block and 5.3 ms,
    is that residual, against a 16.0 ms tolerance floor.

    Also worth stating plainly: the three-block tolerance floor is 16.0 ms,
    which on the shortest voices here is a coarse detection floor - dmx pitch
    37 decays in 32.0 ms alone, so anything from 16 to 48 ms passes. That is a
    deliberate trade against the one block of measurement noise, and it is far
    below the 1.27x-11.75x breaches this gate exists to catch, but a fault
    smaller than about a third of a short voice's decay will not be seen.

    Subtracting the first voice's solo render in the energy domain was tried
    and is wrong: most of that render is the SHARED note, which the second
    press takes over, so subtracting it removes energy the mix never contained.
    Four pairs collapsed to a one-block decay under it. Over-subtraction
    shortens the measurement, which is the one direction a gate must not err
    in.
    """
    limit = gap + budget_blocks()
    for index, level in enumerate(
            block_rms(name, {0: first, gap: second}, limit)):
        if index >= gap and level <= floor:
            return index - gap
    return None


class DiscoveryIsAliveTest(unittest.TestCase):
    """Guard the guard: prove discovery still finds anything at all.

    Every kit case below skips when a kit has no differing circuit, which is
    correct for sp1200 and would be correct for a kit that stopped sharing.
    But if the press instrumentation in tools/shared_circuits ever stopped
    working - a synthio change, a rename - EVERY kit would skip and the suite
    would report OK with zero measurements taken. Verified: stubbing
    `differing` to return [] turns the run into "10 tests, OK (skipped=10)",
    green and empty.

    So assert the floor directly. These counts are the discovered population
    on today's code; they are a tripwire, not a specification, and a kit that
    legitimately gains or loses a shared circuit should move them deliberately.
    """

    def test_discovery_still_finds_shared_circuits(self):
        found = {name: len(differing(name))
                 for name in audioinstruments.DRUM_MACHINES}
        sharing = {n: c for n, c in found.items() if c}
        self.assertGreaterEqual(
            len(sharing), 9,
            "only %d of %d kits report a shared circuit with differing "
            "envelopes (expected 9; sp1200 is the one that shares none). "
            "Discovery itself is probably broken, which would make every "
            "kit case below skip and this suite pass while measuring "
            "nothing. Found: %s" % (len(sharing), len(found), found))
        self.assertEqual(
            found.get("sp1200"), 0,
            "sp1200 has always been the one kit that shares no circuit; if "
            "it now reports %r either it changed or discovery is misfiring"
            % (found.get("sp1200"),))

    def test_every_discovered_circuit_yields_a_pair(self):
        """A differing circuit that produces no pair would be measured by
        nothing, and would vanish from the gate without failing it."""
        for name in audioinstruments.DRUM_MACHINES:
            for circuit in differing(name):
                with self.subTest(kit=name, pitches=circuit.pitches):
                    self.assertTrue(
                        circuit.pairs(),
                        "%s: circuit %s reports differing envelopes but "
                        "yields no pitch pair to measure"
                        % (name, circuit.pitches))


class SharedCircuitOverlapTest(unittest.TestCase):
    """Every shared circuit, both faces, both orders."""

    def check_kit(self, name):
        circuits = differing(name, sample_rate=SAMPLE_RATE, channel_count=2)
        if not circuits:
            self.skipTest("%s builds no shared circuit whose pitches assign "
                          "different envelopes" % name)
        labels = dict(audioinstruments.load(name).NOTE_MAP)
        solo = {}
        for circuit in circuits:
            for a, b in circuit.pairs():
                # Both orders: the fault is symmetric, and the two directions
                # fail differently. On the pre-fix floor 25 of the 49 breaches
                # are a voice ringing too long and 24 are a voice cut short -
                # an open hat struck after a closed one dying as a closed hat.
                # A one-sided assertion would have missed half the evidence.
                for first, second in ((a, b), (b, a)):
                    with self.subTest(kit=name, first=first, second=second):
                        self.check_pair(name, labels, solo, first, second)

    def check_pair(self, name, labels, solo, first, second):
        for pitch in (first, second):
            if pitch not in solo:
                # Cached: 26 pairs x 2 directions share 46 solo renders.
                solo[pitch] = solo_decay(name, pitch)
        _, lead_decay = solo[first]
        peak, alone = solo[second]

        def named(pitch):
            return "%d %s" % (pitch, labels.get(pitch, "?"))

        for pitch, decay in ((first, lead_decay), (second, alone)):
            self.assertIsNotNone(
                decay, "%s: %s never falls 40 dB within %.1f s struck alone, "
                       "so there is no decay to compare against - raise "
                       "BUDGET_SECONDS if that is genuinely its sound"
                       % (name, named(pitch), BUDGET_SECONDS))

        gap = gap_blocks(lead_decay)
        measured = _after(name, first, second, gap, peak / DECAY_FLOOR)
        if measured is None:
            self.fail(
                "%s: %s struck %.1f ms after %s never falls 40 dB within "
                "%.1f s, against %.1f ms struck alone - it is still sounding "
                "%s's envelope" % (name, named(second), _milliseconds(gap),
                                   named(first), BUDGET_SECONDS,
                                   _milliseconds(alone), named(first)))

        tolerance = max(TOLERANCE_BLOCKS, TOLERANCE_FRACTION * alone)
        self.assertLessEqual(
            abs(measured - alone), tolerance,
            "%s: %s decays in %.1f ms struck %.1f ms after %s, but %.1f ms "
            "struck alone (tolerance %.1f ms) - the second hit is not getting "
            "its own envelope"
            % (name, named(second), _milliseconds(measured),
               _milliseconds(gap), named(first), _milliseconds(alone),
               _milliseconds(tolerance)))


def _kit_case(name):
    def check(self):
        self.check_kit(name)
    check.__name__ = "test_" + name
    check.__doc__ = ("%s reconfigures every shared circuit on every hit"
                     % name)
    return check


# One case per kit rather than one case for all ten, so a kit with nothing to
# test (sp1200 shares no circuit that assigns differing envelopes) reports as
# a skip against its own name instead of disappearing into a loop.
for _kit in audioinstruments.DRUM_MACHINES:
    setattr(SharedCircuitOverlapTest, "test_" + _kit, _kit_case(_kit))
del _kit


if __name__ == "__main__":
    unittest.main()
