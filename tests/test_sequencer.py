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


if __name__ == "__main__":
    unittest.main()
