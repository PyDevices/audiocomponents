"""A stand-in for ``audiopump`` on an interpreter that has no pump.

The scheduling seam -- `Keys`, `Instrument.scheduled()`, `Sequencer` -- is
pure Python, and everything it does it does through two calls on one object:
``q.at(frame, op, target, arg)`` and ``q.cancel(token)``. That object is a C
``audiopump.Events``, which exists only in a firmware carrying the pump. So
this is that object, in Python, written from ``audiopump_events.c``:

* ``at()`` validates first and stores second, sorts by frame with the same
  wrapping comparison, hands back a token counting from 1, and answers **0**
  rather than raising when the queue is full;
* ``cancel()`` is True only while the event is still pending;
* :meth:`Events.apply` is ``audiopump_events_apply``: every event inside
  ``[now, now + block)`` is applied in frame order, one press, release or
  release-all per event, and late ones are counted;
* ``stats()`` returns the same eight numbers in the same order.

**What a fake cannot catch.** Whether the real pump reaches those frames on
time, whether applying one allocates, and whether the C sorts the way this
does are not testable from here -- they are measured on a built interpreter
by ``docs/spikes/probes/events_timing.py``, ``events_bytes.py``,
``seq_timing.py`` and ``alloc_gate.py`` in the workspace anchor, and by
audiodsp's own ``tests/pump/`` probes in its clean-build workflow. What this
*does* catch is everything above the queue: which events the seam writes, in
what order, at which frames, carrying which notes. That is where all three
defects the spike found actually lived.
"""

import sys

PRESS = 1
RELEASE = 2
RELEASE_ALL = 3
PLAY = 4
STOP = 5
LEVEL = 6

#: ``audiopump.STATUS_WORDS`` -- the pump's status block, unused here but
#: part of the surface a caller may look for.
STATUS_WORDS = 32
STATUS_BYTES = STATUS_WORDS * 8

_MASK = 0xFFFFFFFF


def before(a, b):
    """``a`` is earlier than ``b`` on the 32-bit wrapping clock."""
    return ((a - b) & _MASK) >= 0x80000000


class _Event:
    __slots__ = ("frame", "op", "target", "arg", "token")

    def __init__(self, frame, op, target, arg, token):
        self.frame = frame
        self.op = op
        self.target = target
        self.arg = arg
        self.token = token


class Events:
    """``audiopump.Events``, in Python, with a clock a test drives."""

    def __init__(self, capacity=64):
        if not 1 <= capacity <= 4096:
            raise ValueError("capacity is 1..4096")
        self.capacity = capacity
        self._events = []
        self._token = 0
        self.scheduled = 0
        self.applied_count = 0
        self.late = 0
        self.cancelled = 0
        self.dropped = 0
        self.refused = 0
        #: Every event this queue has applied, in order:
        #: ``(frame, op, target, arg)``. The C keeps no such log; a test
        #: needs one to say *when* a note sounded.
        self.log = []

    # -- what audioinstruments calls ---------------------------------------

    def at(self, frame, op, target, arg=None, loop=False):
        frame &= _MASK
        self._validate(op, target, arg)
        if len(self._events) >= self.capacity:
            self.dropped += 1
            return 0
        self._token += 1
        if self._token == 0:
            self._token += 1
        event = _Event(frame, op, target, arg, self._token)
        index = len(self._events)
        while index > 0 and before(frame, self._events[index - 1].frame):
            index -= 1
        self._events.insert(index, event)
        self.scheduled += 1
        return event.token

    def cancel(self, token):
        for index, event in enumerate(self._events):
            if event.token == token:
                del self._events[index]
                self.cancelled += 1
                return True
        return False

    def clear(self):
        was = len(self._events)
        self._events = []
        self.cancelled += was
        return was

    def pending(self):
        return len(self._events)

    def stats(self):
        return (self.scheduled, self.applied_count, self.late, self.cancelled,
                self.dropped, self.refused, len(self._events), self.capacity)

    # -- what the pump's thread does ---------------------------------------

    def apply(self, now, block_frames=256):
        """``audiopump_events_apply``: the block ``[now, now + block)``."""
        end = (now + block_frames) & _MASK
        applied = 0
        while self._events and before(self._events[0].frame, end):
            event = self._events.pop(0)
            if before(event.frame, now):
                self.late += 1
            self.log.append((event.frame, event.op, event.target, event.arg))
            if event.op == PRESS:
                event.target.press(event.arg)
            elif event.op == RELEASE:
                event.target.release(event.arg)
            elif event.op == RELEASE_ALL:
                event.target.release_all()
            applied += 1
        self.applied_count += applied
        return applied

    # -- the half that raises ----------------------------------------------

    def _validate(self, op, target, arg):
        """``audiopump_events_validate``, for the three synth ops.

        It is here because the seam relies on it: `Keys` hands the queue a
        `synthio.Note` it has just copied, and a seam that handed over a
        *list* of notes -- which `press()` accepts and `at()` does not -- is
        a defect nothing else would see until a board ran it.
        """
        if op in (PRESS, RELEASE, RELEASE_ALL):
            if not hasattr(target, "press"):
                raise TypeError("press/release want a Synthesizer")
            if op == RELEASE_ALL:
                return
            if isinstance(arg, bool) or isinstance(arg, int):
                if not 0 <= arg <= 127:
                    raise ValueError("a MIDI note is 0..127")
                return
            if not hasattr(arg, "frequency"):
                raise TypeError("a scheduled note is a Note or a MIDI number"
                                " -- an iterable of them is several events")
            return
        raise ValueError("unknown op")


class _Clock:
    """``audiopump.now()`` -- frames pulled, which a test moves by hand."""

    def __init__(self):
        self.frame = 0

    def __call__(self):
        return self.frame & _MASK


now = _Clock()


def install():
    """Put this module on ``sys.modules`` as ``audiopump`` and reset it.

    `audioinstruments._support` caches ``(PRESS, RELEASE, RELEASE_ALL)`` the
    first time an instrument is scheduled, so the module has to be in place
    before that and has to stay the same object afterwards.
    """
    sys.modules.setdefault("audiopump", sys.modules[__name__])
    now.frame = 0
    return sys.modules["audiopump"]
