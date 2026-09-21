"""`audioinstruments.sequencer.Sequencer`, driven by a clock a test moves.

The sequencer's whole claim is that the groove does not depend on when
`tick()` is called. So every test here calls `tick()` from a loop that also
moves the clock and applies the queue -- a transport -- and then reads what
the queue *applied*, not what the sequencer meant to do.

The queue is `tests/support/fake_pump.Events`; its docstring says what a
Python queue cannot prove. Everything below is about which frames the
sequencer writes and which ones survive an edit, a tempo change or a stop,
and none of that is the C's business.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "support"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fake_pump                                            # noqa: E402

fake_pump.install()

import audioinstruments                                     # noqa: E402
from audioinstruments.sequencer import Sequencer            # noqa: E402

RATE = 48000
BLOCK = 256

#: One hit on every fourth sixteenth: the four-on-the-floor a transport
#: button plays, and the pattern the drum machine app ships with.
PATTERN = {0: (36,), 4: (38,), 8: (36,), 12: (38,)}


class Transport:
    """A clock, a queue, a drum machine and a sequencer, wound by hand.

    `run_to(step)` advances the clock one block at a time, applying the
    queue and ticking the sequencer, exactly as a board does -- except that
    nothing here is ever late, so a hit that goes missing went missing in
    the sequencer.
    """

    def __init__(self, test, bpm=120, ahead=8, capacity=256,
                 pattern=None, instrument="tr808"):
        self.clock = fake_pump.now
        self.clock.frame = 0
        self.queue = fake_pump.Events(capacity=capacity)
        self.instrument = audioinstruments.create(instrument, RATE)
        test.addCleanup(self.instrument.deinit)
        self.pattern = dict(PATTERN if pattern is None else pattern)
        self.seq = Sequencer(self.queue, sample_rate=RATE, bpm=bpm, steps=16,
                             ahead=ahead, now=self.clock)
        self.seq.track(self.instrument, self.pattern)

    def run_to(self, step, on_step=None, limit=40000):
        seen = set()
        blocks = 0
        while self.seq.position < step and blocks < limit:
            self.queue.apply(self.clock.frame, BLOCK)
            self.seq.tick()
            position = self.seq.position
            if on_step is not None and position not in seen:
                seen.add(position)
                on_step(position)
            self.clock.frame += BLOCK
            blocks += 1
        self.queue.apply(self.clock.frame, BLOCK)
        return blocks

    def hits(self):
        """The frames a note was pressed at, one entry per hit."""
        return sorted({frame for frame, op, _target, _arg
                       in self.queue.log if op == fake_pump.PRESS})

    def presses(self):
        return len([1 for _frame, op, _t, _a in self.queue.log
                    if op == fake_pump.PRESS])


class TheGridIsMadeOfFrames(unittest.TestCase):

    def test_a_pattern_lays_its_steps_at_the_tempo(self):
        rig = Transport(self)
        self.assertEqual(rig.seq.step_frames, RATE * 60 // (120 * 4))
        rig.seq.start()
        origin = rig.seq._origin

        rig.run_to(16)
        step = rig.seq.step_frames
        self.assertEqual(rig.hits()[:4],
                         [origin + index * step for index in (0, 4, 8, 12)])

    def test_the_frame_of_a_step_is_derived_not_accumulated(self):
        """A long run must not drift by rounding.

        A step's frame comes from its absolute index, so the error against
        exact arithmetic stays under one frame however far the bar has run.
        Adding `step_frames` on each time is out by 153 frames -- three
        milliseconds -- by step 1000 at this tempo, and keeps growing.
        """
        rig = Transport(self, bpm=127.3)
        rig.seq.start(at=0)
        exact = RATE * 60.0 / (int(127.3 * 4))
        for step in (1, 10, 1000, 100000):
            self.assertLess(abs(rig.seq.frame_of(step) - step * exact), 1.0,
                            "step %d has drifted" % step)

    def test_position_is_read_off_the_clock(self):
        rig = Transport(self)
        self.assertEqual(rig.seq.position, -1, "stopped, but reporting a step")
        rig.seq.start()
        self.assertEqual(rig.seq.position, -1,
                         "the origin is still in the future")
        rig.clock.frame = rig.seq._origin + rig.seq.step_frames * 5 + 10
        self.assertEqual(rig.seq.position, 5)


class ATempoChangeDoesNotPunchAHoleInTheBar(unittest.TestCase):
    """`set_bpm` cancels everything ahead of the audio and lays it again.

    The defect this is built around: it resumed from the earliest step still
    *holding tokens*, and a step with no cells on it holds none -- so every
    silent step inside the look-ahead was skipped. With a 300 ms window that
    is two sixteenths of nothing at the seam.
    """

    def test_every_hit_of_two_bars_sounds_once_across_a_tempo_change(self):
        steady = Transport(self)
        steady.seq.start()
        steady.run_to(32)
        steady.seq.stop()

        moved = Transport(self)
        moved.seq.start()
        moved.run_to(32, on_step=lambda step: step == 5
                     and moved.seq.set_bpm(150))
        moved.seq.stop()

        self.assertEqual(len(moved.hits()), len(steady.hits()),
                         "the tempo change lost %d of %d hits"
                         % (len(steady.hits()) - len(moved.hits()),
                            len(steady.hits())))
        self.assertEqual(moved.presses(), steady.presses())
        self.assertGreater(moved.seq.cancelled, 0,
                           "nothing was taken back, so nothing was re-laid")

    def test_the_steps_it_cancelled_are_laid_again(self):
        rig = Transport(self)
        rig.seq.start()
        rig.run_to(2)
        before = rig.seq._next

        rig.seq.set_bpm(150)
        self.assertLessEqual(
            rig.seq._next, before,
            "set_bpm resumed past the steps it had just cancelled")
        self.assertTrue(rig.queue.pending(), "the grid was not re-laid")

    def test_a_tempo_that_has_not_moved_cancels_nothing(self):
        rig = Transport(self)
        rig.seq.start()
        rig.run_to(2)
        self.assertEqual(rig.seq.set_bpm(120), 0)

    def test_the_steps_that_have_sounded_stay_where_they_were(self):
        rig = Transport(self)
        rig.seq.start()
        rig.run_to(5)
        sounded = rig.hits()
        rig.seq.set_bpm(90)
        rig.run_to(10)
        self.assertEqual(rig.hits()[:len(sounded)], sounded,
                         "a tempo change moved a hit that had already played")


class AnEditIsHeardOnThisPassOfTheStep(unittest.TestCase):
    """A step's cells are read up to `ahead` steps before it sounds. Without
    `relay()` a player who toggles a cell inside that window hears it a bar
    later, which reads as a bug in the button."""

    def test_relay_sees_a_cell_switched_on(self):
        rig = Transport(self, pattern={0: (36,)})
        rig.seq.start()
        rig.run_to(1)
        step = rig.seq.step_frames
        origin = rig.seq._origin

        rig.pattern[4] = (42,)              # the player lights a cell
        rig.seq.relay()
        rig.run_to(8)

        self.assertIn(origin + 4 * step, rig.hits(),
                      "the cell switched on inside the look-ahead was not "
                      "heard on this pass of the bar")

    def test_relay_does_not_double_a_step_that_has_sounded(self):
        rig = Transport(self)
        rig.seq.start()
        rig.run_to(6)
        sounded = rig.hits()
        rig.seq.relay()
        rig.run_to(7)
        self.assertEqual(rig.hits()[:len(sounded)], sounded)
        self.assertEqual(len(set(rig.hits())), len(rig.hits()),
                         "a step sounded twice")

    def test_retrack_takes_back_what_the_old_instrument_had(self):
        rig = Transport(self)
        rig.seq.start()
        rig.run_to(1)
        other = audioinstruments.create("tr909", RATE)
        self.addCleanup(other.deinit)

        was = rig.seq.retrack(other)
        self.assertIs(was, rig.instrument)
        self.assertIs(rig.seq.tracks[0][0], other)
        for event in rig.queue._events:
            self.assertIsNot(event.target,
                             rig.instrument.synth.node,
                             "a step still sounds on the instrument the "
                             "dropdown says is gone")


class TheTransportStopsCleanly(unittest.TestCase):

    def test_stop_takes_back_everything_that_has_not_sounded(self):
        rig = Transport(self)
        rig.seq.start()
        rig.run_to(3)
        self.assertTrue(rig.queue.pending())

        rig.seq.stop()
        self.assertEqual(rig.queue.pending(), 0,
                         "stop left notes on the queue")
        self.assertEqual(rig.seq.position, -1)

    def test_stop_releases_a_held_key(self):
        """A drum decays on its own envelope, but a held note does not: the
        copy standing in for it is what is sounding, and `stop()` has to
        reach that and not only the note the instrument hands back."""
        rig = Transport(self, instrument="karplus",
                        pattern={0: (60, 100, 8)})
        rig.seq.start()
        rig.run_to(3)
        self.assertGreater(len(rig.instrument.synth.node.pressed), 0,
                           "nothing was sounding to release")

        rig.seq.stop()
        self.assertEqual(len(rig.instrument.synth.node.pressed), 0,
                         "a key is still held after the transport stopped")
        self.assertEqual(rig.instrument.synth.shadows, 0)

    def test_start_again_picks_the_groove_up_where_it_was(self):
        """Changing kit restarts the pump, which resets its clock. Starting
        the bar at the downbeat instead of where the player was is a jump
        they did not ask for."""
        rig = Transport(self)
        rig.seq.start()
        rig.run_to(5)
        rig.seq.stop()

        rig.clock.frame = 0                     # the pump's clock went back
        rig.seq.start(step=5)
        self.assertEqual(rig.seq.frame_of(5),
                         rig.seq._origin + 5 * rig.seq.step_frames)
        self.assertTrue(rig.seq._live, "nothing was laid at all")
        self.assertGreaterEqual(
            rig.seq._live[0][0], 5,
            "restarting at step 5 re-played a step that had gone by")


class ATrackHasToBeSchedulable(unittest.TestCase):

    def test_an_unschedulable_instrument_is_refused_with_a_sentence(self):
        queue = fake_pump.Events(capacity=64)
        seq = Sequencer(queue, sample_rate=RATE, now=fake_pump.now)
        kit = audioinstruments.create("acoustickit", RATE)
        self.addCleanup(kit.deinit)
        with self.assertRaises(ValueError) as caught:
            seq.track(kit, dict(PATTERN))
        self.assertIn("cannot be scheduled", str(caught.exception))
        self.assertEqual(seq.tracks, [],
                         "the refused instrument was tracked anyway")

    def test_retrack_refuses_one_too(self):
        rig = Transport(self)
        kit = audioinstruments.create("acoustickit", RATE)
        self.addCleanup(kit.deinit)
        with self.assertRaises(ValueError):
            rig.seq.retrack(kit)


class AFullQueueIsCounted(unittest.TestCase):
    """A sequencer that fills the queue wants to know it dropped a note, not
    to lose its whole step to an exception."""

    def test_a_refused_event_is_a_zero_token_and_a_count(self):
        rig = Transport(self, capacity=2)
        rig.seq.start()
        rig.run_to(4)
        self.assertGreater(rig.seq.refused, 0,
                           "a queue of two took a whole bar")
        self.assertGreater(rig.queue.dropped, 0)


#: Every row on every step: the drum machine's four circuits, sixteen
#: sixteenths, no rest anywhere. It is the heaviest bar the shipped app can
#: be asked for, and the one the P4 raised on.
FULL_BAR = {step: (36, 38, 42, 46) for step in range(16)}

#: The same bar for a melodic instrument, with a four-step gate so each
#: chord is still sounding when the next three land on top of it.
FULL_CHORDS = {step: ((48, 100, 4), (55, 100, 4), (60, 100, 4),
                      (64, 100, 4)) for step in range(16)}


class ATickInsideAnotherOne(unittest.TestCase):
    """A tick that arrives while the sequencer is already laying a step.

    A tick is a timer callback. On a board a timer callback arrives through
    `micropython.schedule`, between the interpreter's own bytecodes, so it
    lands wherever it lands - including in the middle of `start()`, which
    with a full bar is a hundred-odd lines of scheduling, and including
    inside a `Keys.press` that the sequencer has armed and not yet
    disarmed. Found on the P4 on 2026-09-21 as two AttributeErrors out of
    an LVGL timer callback, at two different lines of
    `audioinstruments._support.press`, on a full bar that a sparse one
    never showed: `docs/spikes/live-audio-path-fullbar.md`.

    Nothing is exhausted when it happens - at the app's queue capacity of
    96 a full bar refuses nothing and presses at most five voices of the
    engine's sixty-four. What came back instead of a voice was the seam's
    own state, put back to `()` and `None` by the inner tick's exit.

    The interrupt is delivered from `Events.at()` because that is a call
    the armed region really makes; the line-by-line version, which is the
    only way to reach the other of the two lines, is in
    `test_scheduling_seam.ArmingNests`.
    """

    #: How many `at()` calls to use as interrupt points. The first bar of a
    #: full pattern is about forty; today's code raises inside the first
    #: dozen.
    POINTS = 24

    #: instrument, pattern, bpm, queue capacity. 96 is the drum machine
    #: app's own `QUEUE_CAPACITY`, which a full drum bar fits inside; the
    #: melodic bar is four-note chords with a four-step gate, which is eight
    #: events a step and does not. The last row is the app's queue cut to
    #: eight on purpose: past capacity the hit has to be dropped and counted,
    #: interrupted or not, and still never raise.
    CASES = (("tr808", FULL_BAR, 200, 96), ("tr909", FULL_BAR, 200, 96),
             ("juno106", FULL_CHORDS, 200, 256), ("tr808", FULL_BAR, 120, 96),
             ("tr808", FULL_BAR, 200, 8))

    class Ticking(fake_pump.Events):
        """`micropython.schedule`, as a queue that calls back once."""

        seq = None
        at_call = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.calls = 0
            self.fired = 0
            self._inside = False

        def at(self, frame, op, target, arg=None, loop=False):
            self.calls += 1
            if (self.at_call == self.calls and self.seq is not None
                    and not self._inside):
                self._inside = True
                try:
                    self.fired += 1
                    self.seq.tick()
                finally:
                    self._inside = False
            return super().at(frame, op, target, arg, loop)

    def bar(self, instrument, pattern, bpm, at_call=None, bars=2,
            capacity=96):
        """Two bars of ``pattern``, with one tick delivered at ``at_call``.

        Returns what the queue APPLIED, which is what a listener would
        hear: the frame, the op and the pitch of every event, in order.
        """
        clock = fake_pump.now
        clock.frame = 0
        queue = self.Ticking(capacity=capacity)
        inst = audioinstruments.create(instrument, RATE)
        self.addCleanup(inst.deinit)
        seq = Sequencer(queue, sample_rate=RATE, bpm=bpm, steps=16, ahead=4,
                        now=clock)
        seq.track(inst, dict(pattern))
        queue.seq = seq
        queue.at_call = at_call
        seq.start()
        for _ in range((seq.step_frames * 16 * bars) // BLOCK):
            queue.apply(clock.frame, BLOCK)
            clock.frame += BLOCK
            seq.tick()
        heard = [(frame, op, getattr(note, "frequency", note))
                 for frame, op, _target, note in queue.log]
        return heard, seq, queue

    def test_the_full_bar_survives_a_tick_landing_anywhere_in_it(self):
        for instrument, pattern, bpm, capacity in self.CASES:
            with self.subTest(instrument=instrument, bpm=bpm,
                              capacity=capacity):
                quiet, whole, _queue = self.bar(instrument, pattern, bpm,
                                                capacity=capacity)
                self.assertTrue(quiet, "the bar played nothing at all")
                fired = 0
                for at_call in range(1, self.POINTS + 1):
                    heard, seq, queue = self.bar(instrument, pattern, bpm,
                                                 at_call=at_call,
                                                 capacity=capacity)
                    fired += queue.fired
                    self.assertEqual(
                        heard, quiet,
                        "a tick delivered at at() call %d changed the bar"
                        % at_call)
                    self.assertEqual(
                        seq.refused, whole.refused,
                        "the interrupt changed what the queue turned away")
                    self.assertEqual(
                        seq.reentered, queue.fired,
                        "a re-entrant tick was run instead of counted")
                self.assertEqual(fired, self.POINTS,
                                 "the interrupt did not land every time")

    def test_past_capacity_the_hit_is_dropped_and_counted_not_raised(self):
        """The queue cut to eight: the bar thins, nothing throws.

        This is the degradation a timer callback can live with. It is also
        what the P4's failure was mistaken for - at the app's own capacity
        of 96 a full drum bar refuses nothing at all and presses five of
        the engine's sixty-four voices, so nothing was exhausted there.
        """
        _quiet, whole, queue = self.bar("tr808", FULL_BAR, 200, capacity=8)
        self.assertGreater(whole.refused, 0, "a queue of eight took the bar")
        self.assertEqual(whole.refused, queue.dropped,
                         "the sequencer and the queue disagree on refusals")
        _roomy, wide, queue = self.bar("tr808", FULL_BAR, 200, capacity=96)
        self.assertEqual(wide.refused, 0,
                         "the app's own capacity refused a full drum bar")
        self.assertEqual(queue.dropped, 0)

    def test_a_refused_tick_is_counted_and_the_next_one_catches_up(self):
        """The refusal has to be visible, and it has to be free.

        `reentered` climbing is the app's sign that its timer is firing
        faster than a bar can be laid; what it must never mean is a hole,
        because the look-ahead is hundreds of milliseconds deep and the
        next tick lays whatever this one did not.
        """
        quiet, _whole, _q = self.bar("tr808", FULL_BAR, 200)
        heard, seq, queue = self.bar("tr808", FULL_BAR, 200, at_call=6)
        self.assertEqual(queue.fired, 1, "the interrupt did not land")
        self.assertEqual(seq.reentered, 1, "the refused tick was not counted")
        self.assertEqual(heard, quiet, "the bar is not the same bar")
        self.assertEqual(seq.scheduled,
                         len([1 for _f, op, _n in heard
                              if op in (fake_pump.PRESS, fake_pump.RELEASE)])
                         + queue.pending(),
                         "a step was laid twice or not at all")


if __name__ == "__main__":
    unittest.main()
