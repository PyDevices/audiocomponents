"""Discover which pitches of an instrument share a synthio.Note.

Several `audioinstruments` kits give two or more voices one permanent circuit -
closed and open hi-hat, clap and maracas, a rimshot and a cowbell - and
reconfigure it per hit. That is a faithful model of the hardware, where the two
sounds really do come off one circuit and choke each other.

It also means the two voices only stay correct if each hit's parameters are
fully applied. A circuit whose pitches assign DIFFERENT envelopes is the case
worth testing: audioif d84470a fixed a CPython target that kept stepping the
envelope a note was first pressed with, and before it a closed hat struck after
an open one rang for the open hat's full decay in eight of ten kits.

Discovery is by instrumenting `synthio.Synthesizer.press` rather than by reading
each module, because the kits do not share a spelling - some carry a
`PITCH_CIRCUIT` map, others branch on `pitch in (...)`. Recording the actual
presses is the only way that generalizes, and it is what a new kit will be
measured by without anyone maintaining a list.
"""

import math

import audiocore
import synthio

import audioinstruments


class Circuit:
    """One synthio.Note driven by more than one pitch."""

    def __init__(self, pitches, envelopes):
        #: sorted pitches that press this Note
        self.pitches = pitches
        #: pitch -> the envelope tuple it assigns (None if the note has none)
        self.envelopes = envelopes

    @property
    def differing(self):
        """True if the pitches assign different envelopes to this Note.

        Only these can express the fault; a circuit whose faces share one
        envelope has nothing to inherit.
        """
        return len(set(self.envelopes.values())) > 1

    def pairs(self):
        """(a, b) pitch pairs that assign different envelopes, a < b."""
        out = []
        for i, a in enumerate(self.pitches):
            for b in self.pitches[i + 1:]:
                if self.envelopes[a] != self.envelopes[b]:
                    out.append((a, b))
        return out

    def __repr__(self):
        return "<Circuit pitches=%s differing=%s>" % (self.pitches, self.differing)


def discover(name, sample_rate=48000, channel_count=2):
    """Return the shared Circuits of instrument ``name``.

    Triggers every pitch in the module's NOTE_MAP once and records which Note
    objects each press touched. Restores ``Synthesizer.press`` on the way out,
    including on error.
    """
    module = __import__("audioinstruments." + name, None, None, ["NOTE_MAP"])
    real_press = synthio.Synthesizer.press
    record = []

    def spy(self, notes):
        seq = notes if isinstance(notes, (list, tuple)) else (notes,)
        for note in seq:
            if isinstance(note, synthio.Note):
                envelope = note.envelope
                record.append((id(note),
                               tuple(envelope) if envelope is not None else None))
        return real_press(self, notes)

    synthio.Synthesizer.press = spy
    try:
        instrument = audioinstruments.create(
            name, sample_rate=sample_rate, channel_count=channel_count)
        owner = {}
        for pitch, _label in module.NOTE_MAP:
            del record[:]
            instrument.note_on(pitch, 100)
            for note_id, envelope in record:
                owner.setdefault(note_id, {}).setdefault(pitch, envelope)
        instrument.deinit()
    finally:
        synthio.Synthesizer.press = real_press

    return [Circuit(sorted(by_pitch), by_pitch)
            for by_pitch in owner.values() if len(by_pitch) > 1]


def differing(name, **kwargs):
    """Just the circuits whose pitches assign different envelopes."""
    return [c for c in discover(name, **kwargs) if c.differing]


# ---------------------------------------------------------------------------
# The decay ruler, and the gap rule built on it.
#
# Both the overlap gate (tests/test_shared_circuit_overlap.py) and the
# `transitions` render mode need to know how long a voice rings and how long
# after its sibling to strike it. They must agree: material that probes a
# different moment than the gate measures would let a listener and the test
# disagree about the same kit, which is the exact failure this whole effort
# exists to remove. So the definition lives here once.
# ---------------------------------------------------------------------------

SAMPLE_RATE = 48000

#: A voice has "decayed" when its block RMS falls to a hundredth of its own
#: peak - 40 dB down, and effectively gone under anything else in a pattern.
DECAY_FLOOR = 100.0

#: Strike the second voice half its sibling's decay in - deep enough to still
#: be in its shadow (which is the only time the fault can express) and past the
#: attack transient, with the sibling about 20 dB down so it does not swamp the
#: measurement. Never less than two blocks, or the two presses land in one pull
#: and fuse into a single hit.
GAP_FRACTION = 0.5
MIN_GAP_BLOCKS = 2

#: Long enough for the slowest voice in the ten kits (the tr707 open hat, 747
#: ms) to fall 40 dB, with room to spare; short enough that a stuck voice fails
#: rather than hangs. Scans stop early, so this is a ceiling, not a cost.
BUDGET_SECONDS = 4.0

_FRAMES_PER_BLOCK = None


def frames_per_block(sample_rate=SAMPLE_RATE):
    """Frames in one pull - the resolution every block count here is quoted at.

    Probed rather than assumed: the pull size is audioif's to choose.
    """
    global _FRAMES_PER_BLOCK
    if _FRAMES_PER_BLOCK is None:
        instrument = audioinstruments.create(
            audioinstruments.DRUM_MACHINES[0], sample_rate=sample_rate,
            channel_count=2)
        _FRAMES_PER_BLOCK = len(
            bytes(audiocore.get_buffer(instrument.output)[1])) // 4
        instrument.deinit()
    return _FRAMES_PER_BLOCK


def budget_blocks(sample_rate=SAMPLE_RATE):
    return int(BUDGET_SECONDS * sample_rate / frames_per_block(sample_rate))


def block_rms(name, hits, limit, sample_rate=SAMPLE_RATE):
    """Yield block RMS of kit `name` while `hits` (block -> pitch) play.

    A generator on purpose: callers stop at a threshold crossing, and on a
    broken floor that crossing can be ten times further out than on a healthy
    one. Rendering a fixed length would pay the worst case every time.
    """
    instrument = audioinstruments.create(
        name, sample_rate=sample_rate, channel_count=2)
    try:
        for block in range(limit):
            if block in hits:
                instrument.note_on(hits[block], 100)
            data = memoryview(
                bytes(audiocore.get_buffer(instrument.output)[1])).cast("h")
            energy = 0
            for value in data:
                energy += value * value
            yield math.sqrt(energy / len(data)) / 32768.0
    finally:
        instrument.deinit()


def solo_decay(name, pitch, sample_rate=SAMPLE_RATE):
    """(peak, decay in blocks) for `pitch` struck by itself on a fresh kit.

    The peak is a running maximum and the scan stops at the first crossing,
    which for a percussive one-shot is the answer a whole-render maximum gives.
    """
    peak = 0.0
    for index, level in enumerate(
            block_rms(name, {0: pitch}, budget_blocks(sample_rate),
                      sample_rate)):
        if level > peak:
            peak = level
        elif peak and level <= peak / DECAY_FLOOR:
            return peak, index
    return peak, None


def gap_blocks(lead_decay_blocks):
    """How long after the first voice to strike the second."""
    if lead_decay_blocks is None:
        return MIN_GAP_BLOCKS
    return max(MIN_GAP_BLOCKS, int(round(lead_decay_blocks * GAP_FRACTION)))
