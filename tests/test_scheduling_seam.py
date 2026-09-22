"""The scheduling seam: `Keys`, `Instrument.scheduled()` and `.at()`.

An instrument's note-on is Python and always will be. What the pump applies
on its own thread is the last step -- `synth.press(note)` -- at a frame this
package chose in advance. Everything between those two sentences is `Keys`,
and until this file existed none of it was tested: the `note_info` defect was
found because three piano tests happened to read through the proxy, and both
drum-machine defects were found by hand on a board.

The queue here is `tests/support/fake_pump.Events`, which is
`audiopump_events.c` written out in Python -- same validation, same ordering,
same token rules, same apply window. Read its docstring for what that can and
cannot prove. Timing on a real pump, and allocation on its thread, are
measured on built interpreters by the spike's probes; what is proved here is
which events the seam writes, in what order, at which frames, carrying which
notes -- which is where all three of the defects above actually lived.

**The same seam against the real engine** is
`tests/parity/scheduling_seam_live.py` (audiocomponents#92), which asks the
other question: not which events were written, but what was heard. It reads
its answers off `audiopump.Tap` with the loop advanced by
`audiopump.service()`, has no event log on purpose, and needs a MicroPython
build carrying the pump -- so it is workspace-local, and this file is what
runs everywhere.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fake_pump                                            # noqa: E402

fake_pump.install()

import audiocore                                            # noqa: E402
import synthio                                              # noqa: E402

import audioinstruments                                     # noqa: E402
from audioinstruments import _support                       # noqa: E402

RATE = 48000
BLOCK = 256

#: The pump applies the events inside the block it is about to pull, so a
#: frame is heard at the top of the block containing it.
def block_of(frame):
    return (frame // BLOCK) * BLOCK


def drum():
    """A TR-808: two notes per hit, one permanent `Note` per circuit
    rewritten on every strike. The shape that needs the shadow copies."""
    return audioinstruments.create("tr808", RATE)


def presses(queue):
    """Every `Note` the queue has applied as a press, in order."""
    return [arg for _frame, op, _target, arg in queue.log
            if op == fake_pump.PRESS]


class AScheduledNoteSoundsAtItsFrame(unittest.TestCase):

    def test_nothing_is_pressed_before_the_frame_arrives(self):
        inst = drum()
        self.addCleanup(inst.deinit)
        synth = _support.node(inst.synth)
        queue = fake_pump.Events(capacity=64)

        with inst.scheduled(queue, 6000) as tokens:
            inst.note_on(36, 127)

        self.assertTrue(tokens, "scheduling wrote no events")
        self.assertNotIn(0, tokens, "the queue refused an event")
        self.assertEqual(len(synth.pressed), 0,
                         "the press reached the engine at schedule time")

        # Every block up to the one holding frame 6000.
        for start in range(0, block_of(6000), BLOCK):
            queue.apply(start, BLOCK)
        self.assertEqual(len(synth.pressed), 0, "pressed early")

        queue.apply(block_of(6000), BLOCK)
        self.assertEqual(len(synth.pressed), 2,
                         "the bass drum's two notes did not press at 6000")
        self.assertEqual(queue.late, 0)

    def test_at_schedules_one_call(self):
        inst = drum()
        self.addCleanup(inst.deinit)
        synth = _support.node(inst.synth)
        queue = fake_pump.Events(capacity=64)

        inst.at(queue, 12000).note_on(38, 100)
        self.assertEqual(len(synth.pressed), 0)
        queue.apply(block_of(12000), BLOCK)
        self.assertGreater(len(synth.pressed), 0)

    def test_a_scheduled_note_off_releases_it(self):
        inst = audioinstruments.create("karplus", RATE)
        self.addCleanup(inst.deinit)
        synth = _support.node(inst.synth)
        queue = fake_pump.Events(capacity=64)

        with inst.scheduled(queue, 6000):
            inst.note_on(60, 100)
        with inst.scheduled(queue, 18000):
            inst.note_off(60)

        queue.apply(block_of(6000), BLOCK)
        held = len(synth.pressed)
        self.assertGreater(held, 0, "the scheduled note-on did not press")
        queue.apply(block_of(18000), BLOCK)
        self.assertEqual(len(synth.pressed), 0,
                         "the scheduled note-off did not release the %d "
                         "notes the scheduled note-on pressed" % held)

    def test_the_events_are_written_in_time_order(self):
        """A note-off written before its note-on must find something to
        release: the instrument's own bookkeeping runs at schedule time."""
        inst = audioinstruments.create("karplus", RATE)
        self.addCleanup(inst.deinit)
        queue = fake_pump.Events(capacity=64)

        with inst.scheduled(queue, 6000):
            inst.note_on(60, 100)
        with inst.scheduled(queue, 18000):
            inst.note_off(60)

        frames = [event.frame for event in queue._events]
        self.assertEqual(frames, sorted(frames))
        ops = [event.op for event in queue._events]
        self.assertEqual(ops, sorted(ops, key=lambda op: op == fake_pump.RELEASE),
                         "a release was written before the press it undoes")
        self.assertIn(fake_pump.PRESS, ops)
        self.assertIn(fake_pump.RELEASE, ops)


class EveryHitKeepsItsOwnVelocity(unittest.TestCase):
    """The drum-machine defect: a bar scheduled ahead of the audio.

    Every drum machine here owns one permanent `Note` per circuit and
    rewrites its amplitude on each strike. Live that is fine, because the
    press is on the next line. A bar ahead it is not: the second hit's Python
    has already overwritten the first hit's note before the first hit sounds.
    Measured on tr808 at the time: a downbeat came out at the quiet hit's
    level, peak 4638 against 25795 live.
    """

    def test_two_hits_scheduled_before_either_sounds_keep_their_levels(self):
        inst = drum()
        self.addCleanup(inst.deinit)
        queue = fake_pump.Events(capacity=64)

        with inst.scheduled(queue, 6000):
            inst.note_on(36, 127)          # loud
        with inst.scheduled(queue, 30000):
            inst.note_on(36, 20)           # quiet, a bar later

        queue.apply(block_of(6000), BLOCK)
        queue.apply(block_of(30000), BLOCK)

        loud = [note.amplitude for note in presses(queue)[:2]]
        quiet = [note.amplitude for note in presses(queue)[2:]]
        self.assertEqual(len(loud), 2)
        self.assertEqual(len(quiet), 2)
        for was, then in zip(loud, quiet):
            self.assertGreater(
                was, then * 2.0,
                "the downbeat sounded at the later hit's velocity -- the "
                "per-press Note copy is gone")

    def test_each_scheduled_press_carries_its_own_note(self):
        inst = drum()
        self.addCleanup(inst.deinit)
        queue = fake_pump.Events(capacity=64)

        with inst.scheduled(queue, 6000):
            inst.note_on(36, 127)
        with inst.scheduled(queue, 30000):
            inst.note_on(36, 20)

        pressed = [event.arg for event in queue._events
                   if event.op == fake_pump.PRESS]
        self.assertEqual(len(pressed), 4)
        self.assertEqual(len({id(note) for note in pressed}), 4,
                         "two scheduled presses share one Note object")

    def test_a_retrigger_chokes_the_outgoing_copy(self):
        """Pressing a drum synthio is already sounding takes its channel
        back. Two shadows cannot share one, so the outgoing copy is released
        at the same frame with a release of zero, ahead of the new press."""
        inst = drum()
        self.addCleanup(inst.deinit)
        queue = fake_pump.Events(capacity=64)

        with inst.scheduled(queue, 6000):
            inst.note_on(36, 127)
        with inst.scheduled(queue, 30000):
            inst.note_on(36, 100)

        second = [event for event in queue._events if event.frame == 30000]
        self.assertEqual(second[0].op, fake_pump.RELEASE,
                         "the retrigger did not choke the outgoing copy")
        self.assertEqual(second[0].arg.envelope.release_time, 0.0,
                         "the choked copy keeps its release and rings on")
        self.assertIn(fake_pump.PRESS, [event.op for event in second])


class TheKeyboardDoesNotStrandAVoice(unittest.TestCase):
    """What sounds for a scheduled note is the shadow copy, not the note the
    instrument hands back -- so anything that releases only the source leaves
    the copy pressed for ever. The drum machine's STOP button found this."""

    def test_all_notes_off_releases_a_scheduled_note(self):
        """The drum machine's STOP button is `all_notes_off()`, and it left
        one voice per drum held on the engine with a tail audible after the
        transport said stop."""
        for name, pitch in (("tr808", 36), ("karplus", 60)):
            with self.subTest(instrument=name):
                inst = audioinstruments.create(name, RATE)
                try:
                    synth = _support.node(inst.synth)
                    queue = fake_pump.Events(capacity=64)
                    with inst.scheduled(queue, 6000):
                        inst.note_on(pitch, 127)
                    queue.apply(block_of(6000), BLOCK)
                    self.assertGreater(len(synth.pressed), 0)

                    inst.all_notes_off()
                    self.assertEqual(
                        len(synth.pressed), 0,
                        "STOP left a scheduled voice held on the engine")
                    self.assertEqual(inst.synth.shadows, 0)
                finally:
                    inst.deinit()

    def test_a_live_press_of_a_scheduled_key_lets_the_copy_go(self):
        """A drum's scheduled hit has no note-off, so the copy is held until
        something lets it go. The player hitting the same pad is that."""
        inst = drum()
        self.addCleanup(inst.deinit)
        synth = _support.node(inst.synth)
        queue = fake_pump.Events(capacity=64)

        with inst.scheduled(queue, 6000):
            inst.note_on(36, 127)
        queue.apply(block_of(6000), BLOCK)
        self.assertEqual(len(synth.pressed), 2)

        inst.note_on(36, 90)               # the player hits the pad live
        self.assertEqual(
            len(synth.pressed), 2,
            "a live press on top of a scheduled one stranded a voice")
        self.assertEqual(inst.synth.shadows, 0)

    def test_a_key_with_a_scheduled_on_and_off_ends_up_silent(self):
        """The whole life of a held key: scheduled on, the player pressing
        it live in the middle, scheduled off, then the player letting go.
        Nothing may be left holding a channel at the end of that."""
        inst = audioinstruments.create("karplus", RATE)
        self.addCleanup(inst.deinit)
        synth = _support.node(inst.synth)
        queue = fake_pump.Events(capacity=64)

        with inst.scheduled(queue, 6000):
            inst.note_on(60, 100)
        with inst.scheduled(queue, 12000):
            inst.note_off(60)

        queue.apply(block_of(6000), BLOCK)
        inst.note_on(60, 90)
        queue.apply(block_of(12000), BLOCK)
        inst.note_off(60)

        self.assertEqual(queue.pending(), 0)
        self.assertEqual(inst.synth.shadows, 0)
        self.assertEqual(len(synth.pressed), 0,
                         "a voice is still held after every note-off")

    def test_pressed_answers_this_block_while_armed(self):
        """`press_voice` asks about a note it pressed one line earlier. While
        armed the honest answer is what this block staged, not what the
        engine is sounding -- otherwise the voice arbiter steals from keys
        that are still audibly held."""
        inst = drum()
        self.addCleanup(inst.deinit)
        queue = fake_pump.Events(capacity=64)
        keys = inst.synth

        with inst.scheduled(queue, 6000):
            inst.note_on(36, 127)
            self.assertTrue(keys.pressed, "the staged press is invisible")
        self.assertEqual(list(keys.pressed), [],
                         "disarming left the staged list behind")


class TheProxyForwardsTheSynthesizer(unittest.TestCase):
    """`instrument.synth` is public. What `Keys` will not answer, nothing
    can, which is how `note_info` went missing."""

    def test_the_state_and_the_pure_queries_come_through(self):
        inst = drum()
        self.addCleanup(inst.deinit)
        keys = inst.synth
        for name in ("note_info", "max_polyphony", "bits_per_sample",
                     "samples_signed", "envelope", "waveform", "sample_rate",
                     "channel_count", "blocks", "pressed"):
            self.assertTrue(hasattr(keys, name), "Keys cannot answer " + name)

    def test_the_three_that_change_what_sounds_are_refused(self):
        """`change`, `release_then_press` and `release_all_then_press` must
        not forward: while armed they would bypass the queue and the shadow
        copies. Nothing in the package calls them."""
        inst = drum()
        self.addCleanup(inst.deinit)
        for name in ("change", "release_then_press", "release_all_then_press"):
            self.assertFalse(hasattr(inst.synth, name),
                             name + " forwards past the scheduling seam")


class _Counting:
    """A synthesizer stand-in that can, or cannot, count refused presses.

    `synthio.Synthesizer.refused` arrived in audiodsp#137 and this
    repository's `AUDIODSP_PIN` is older, so the engine CI runs against
    cannot answer. Testing the reading against whatever engine happens to be
    installed would mean this file proves one thing today and the other
    thing after the pin moves, and says nothing either way -- so the subject
    is a stand-in with the property and one without it.
    """

    sample_rate = RATE
    channel_count = 2
    blocks = ()
    pressed = ()

    def __init__(self, refused=None):
        if refused is not None:
            self.refused = refused

    def press(self, note):
        pass

    def release(self, note):
        pass

    def release_all(self):
        pass

    def deinit(self):
        pass


class ARefusedNoteIsCounted(unittest.TestCase):
    """audiocomponents#96: a press the engine had no channel for.

    Stealing cannot be decided at schedule time -- the occupancy at a future
    frame is unknowable and every number available to guess with lies -- so
    the library refuses, which is what it always did. What it did not do was
    say so. Measured on the real pump at the 64-voice ceiling, two bars at
    200 BPM: `tr808` and a four-note `juno106` lose nothing, an eight-note
    `juno106` loses **488** notes and `solina` loses 1796, and before this
    nothing on either side of the seam could see one of them.
    """

    def instrument(self, *counts):
        """An `Instrument` over one keyboard per entry in ``counts``.

        `Instrument` adopts every `Keys` built since the last one, through
        `_support._PENDING`. Reaching into it is what building a two-keyboard
        instrument by hand costs, and this file is that module's test.
        """
        del _support._PENDING[:]
        keyboards = [_support.Keys(_Counting(count)) for count in counts]
        _support._PENDING.extend(keyboards)
        inst = _support.Instrument(keyboards[0], lambda *a: None, {}, ())
        self.addCleanup(inst.deinit)
        return inst

    def test_an_engine_that_cannot_count_says_None_rather_than_zero(self):
        """0 would read as "your bar is fine" about a bar that lost 488."""
        self.assertIsNone(self.instrument(None).refused)

    def test_the_count_comes_off_the_engine(self):
        self.assertEqual(488, self.instrument(488).refused)

    def test_it_is_summed_over_every_keyboard_the_instrument_plays(self):
        """`acoustickit` has two synthesizers and is one instrument."""
        self.assertEqual(19, self.instrument(12, 7).refused)

    def test_one_keyboard_that_cannot_say_makes_the_whole_answer_unknown(self):
        """A partial total would read as a small number, not an unknown one,
        and a small number here is the answer an app is hoping for."""
        self.assertIsNone(self.instrument(12, None).refused)

    def test_a_keyboard_forwards_what_its_node_says(self):
        self.assertEqual(3, _support.Keys(_Counting(3)).refused)
        self.assertIsNone(_support.Keys(_Counting()).refused)


class AnInstrumentCanStillRefuseToBeScheduled(unittest.TestCase):
    """`schedulable=False` is part of the `Instrument` contract. Nothing
    shipped uses it any more, and the subject here is a stand-in that does.

    `acoustickit` was the one, because a strike there is `Bank.set_mode()` on
    a running node rather than a press. audiodsp#138 gave the pump a
    frame-stamped `STRIKE` and `CHOKE` and audiocomponents#94 made the kit
    emit them, so the kit carries a frame now like everything else.

    These two tests used to name the kit, and that is worth not repeating:
    a refusal tested against whichever shipped instrument happens not to
    have been fixed yet goes quietly vacuous on the day it is fixed, and a
    passing suite is what you get either way. The flag is for a provider
    whose note-on reaches the audio outside a press -- which is a thing
    outside this package can still be -- so the subject declares it.
    """

    def unschedulable(self):
        synth = _support.synthesizer(RATE, 2)
        inst = _support.Instrument(synth, lambda *a: None, {}, (),
                                   schedulable=False)
        self.addCleanup(inst.deinit)
        return inst

    def test_it_says_no(self):
        self.assertFalse(self.unschedulable().schedulable)

    def test_it_refuses_with_a_sentence(self):
        inst = self.unschedulable()
        queue = fake_pump.Events(capacity=8)
        with self.assertRaises(RuntimeError) as caught:
            inst.at(queue, 6000).note_on(38, 100)
        self.assertIn("cannot be scheduled", str(caught.exception))
        with self.assertRaises(RuntimeError):
            with inst.scheduled(queue, 6000):
                pass
        self.assertEqual(queue.pending(), 0,
                         "a refused instrument still wrote to the queue")

    def test_every_instrument_this_package_ships_can_be_scheduled(self):
        """All 55 of them, the kit included -- which is audiocomponents#94.

        The whole list rather than a handful: the claim worth holding is
        that nothing here plays a bar live and early, and a sample of five
        cannot say that.
        """
        refused = []
        for name in audioinstruments.ALL:
            inst = audioinstruments.create(name, RATE)
            try:
                if not inst.schedulable:
                    refused.append(name)
            finally:
                inst.deinit()
        self.assertEqual([], refused,
                         "these ship unschedulable: " + ", ".join(refused))


class PlayingLiveThroughTheKeyboardIsAWire(unittest.TestCase):
    """Armed, `Keys` is the seam. Live, it must be nothing at all.

    Five instruments across the families, each rendered twice: once as the
    package builds it, and once with `_support.synthesizer` handing back a
    bare `synthio.Synthesizer` -- which is the same instrument with no
    keyboard in front of it. The bytes have to match.
    """

    CASES = (
        ("tr808", (36, 42)),        # drum machine, permanent notes
        ("karplus", (60, 64)),      # physical model
        ("dx7", (60,)),             # FM
        ("rhodes", (60,)),          # electromechanical
        ("minimoog", (48,)),        # subtractive
    )

    BLOCKS = 24

    def render(self, name, notes, bare):
        if bare:
            real = _support.synthesizer

            def plain(sample_rate, channel_count):
                return synthio.Synthesizer(sample_rate=sample_rate,
                                           channel_count=channel_count)

            _support.synthesizer = plain
        try:
            inst = audioinstruments.create(name, RATE)
        finally:
            if bare:
                _support.synthesizer = real
                del _support._PENDING[:]
        try:
            out = bytearray()
            for index in range(self.BLOCKS):
                if index == 2:
                    for pitch in notes:
                        inst.note_on(pitch, 100)
                if index == 12:
                    for pitch in notes:
                        inst.note_off(pitch)
                _result, buffer = audiocore.get_buffer(inst.output)
                out += bytes(buffer)
            return bytes(out)
        finally:
            inst.deinit()

    def test_the_render_is_byte_identical_either_way(self):
        for name, notes in self.CASES:
            with self.subTest(instrument=name):
                through = self.render(name, notes, bare=False)
                without = self.render(name, notes, bare=True)
                self.assertTrue(through, "rendered nothing")
                self.assertEqual(through, without,
                                 name + " does not sound the same through "
                                 "Keys as it does without one")


class ArmingNests(unittest.TestCase):
    """A second `scheduled()` inside the first must give the keyboard BACK.

    On a board the second one is not written by anybody: the app's step
    timer arrives through `micropython.schedule`, between the interpreter's
    own bytecodes, and a timer that tops a sequencer up opens a scheduled
    block of its own wherever it lands - including inside `Keys.press`,
    after it has read `self._q` into a local and before it has touched the
    list that read promised.

    Found on the P4 on 2026-09-21 with every row of the drum machine on
    every step, as two AttributeErrors out of an LVGL timer callback at two
    different lines of `press` - `'tuple' object has no attribute 'append'`
    where the staging list had been put back to `()`, and `'NoneType'
    object has no attribute 'append'` where the token list had been put
    back to `None`. Both are this one class's doing, and both are here.
    """

    def test_the_inner_block_hands_the_outer_one_back(self):
        inst = drum()
        self.addCleanup(inst.deinit)
        keys = inst.synth
        queue = fake_pump.Events(capacity=64)

        with inst.scheduled(queue, 6000) as outer:
            self.assertIsNotNone(keys._q, "the outer block did not arm")
            with inst.scheduled(queue, 12000) as inner:
                inst.note_on(38, 100)
            self.assertTrue(inner, "the inner block scheduled nothing")
            # The outer block is still the one holding the keyboard.
            self.assertIs(keys._tokens, outer,
                          "the inner block took the outer one's token list")
            self.assertIsInstance(keys._staged, list,
                                  "the inner block left the staging list a "
                                  "tuple, which is line 604's AttributeError")
            self.assertEqual(keys._frame, 6000,
                             "the outer block's frame did not come back")
            inst.note_on(36, 127)

        self.assertTrue(outer, "the outer block scheduled nothing after the "
                               "inner one")
        self.assertIsNone(keys._q, "the keyboard is still armed")
        self.assertEqual(keys._staged, (), "the keyboard is still staging")
        self.assertFalse(keys._outer, "the arm stack was not emptied")

    def test_a_press_interrupted_between_its_own_lines_still_schedules(self):
        """The 604 window, reached the way a board reaches it.

        `Keys.press` reads `self._q` and then appends to `self._staged`.
        Nothing calls out between those two lines, so the only way in is a
        callback the interpreter delivers between bytecodes. `sys.settrace`
        stands in for `micropython.schedule`; what it delivers is a whole
        scheduled block, which is what the sequencer's tick opens.
        """
        settrace = getattr(sys, "settrace", None)
        code = getattr(_support.Keys.press, "__code__", None)
        if settrace is None or code is None or not hasattr(code, "co_lines"):
            self.skipTest("this interpreter cannot be interrupted by line")
        try:
            with open(_support.__file__) as handle:
                source = handle.read().splitlines()
        except (OSError, AttributeError):          # frozen, or no __file__
            self.skipTest("_support.py is not readable here")
        inst = drum()
        self.addCleanup(inst.deinit)
        other = audioinstruments.create("tr909", RATE)
        self.addCleanup(other.deinit)
        queue = fake_pump.Events(capacity=64)

        target = None
        for line in sorted({ln for _s, _e, ln in code.co_lines() if ln}):
            if "_staged.append" in source[line - 1]:
                target = line
                break
        self.assertIsNotNone(target, "no staging line in Keys.press")

        state = {"fired": False}

        def interrupt(frame, event, _arg):
            if event == "line" and frame.f_lineno == target \
                    and not state["fired"]:
                state["fired"] = True
                with other.scheduled(queue, 24000):
                    other.note_on(42, 90)
            return interrupt

        def tracer(frame, _event, _arg):
            return interrupt if frame.f_code is code else None

        settrace(tracer)
        try:
            with inst.scheduled(queue, 6000) as tokens:
                inst.note_on(36, 127)
        finally:
            settrace(None)

        self.assertTrue(state["fired"], "the interrupt never landed")
        self.assertTrue(tokens, "the interrupted press scheduled nothing")
        self.assertNotIn(0, tokens, "the queue refused an event")


if __name__ == "__main__":
    unittest.main()
