"""A step sequencer that keeps time in frames instead of in Python.

    from audioinstruments.sequencer import Sequencer

    seq = Sequencer(queue, sample_rate=48000, bpm=120)
    seq.track(drums, {0: (36, 42), 4: (38, 42), 8: (36, 42), 12: (38, 42)})
    seq.track(bass, {0: (33, 100, 4), 8: (40, 100, 4)})   # pitch, vel, gate
    seq.start()
    while playing:
        seq.tick()          # from a timer, as often or as rarely as you like
    seq.stop()

`tick()` tops the queue up to `ahead` steps in front of the audio and returns.
It may be called every millisecond or once a bar; it may be forty milliseconds
late because a garbage collection ran; the groove does not move, because the
step's frame was decided when it was scheduled and the pump applies it. That
is the whole difference from a `_on_step_timer` that fires the note itself.

What a step holds is a pitch, or `(pitch, velocity)`, or
`(pitch, velocity, gate)` where the gate is in steps and schedules the
note-off. A drum needs no gate; a held note does.

`bpm` may be written at any time. What has not sounded yet is cancelled and
re-laid on the new grid, phase-locked to the next step rather than to the
bar, so the tempo changes where the player asked for it.

The queue is this sequencer's. `cancel()` takes back one event by token and
is what a tempo change uses; `Events.clear()` would drop a live player's
notes too, and this never calls it.
"""


class Sequencer:

    def __init__(self, queue, sample_rate=48000, bpm=120.0,
                 steps_per_beat=4, steps=16, ahead=8, now=None, lead=None):
        self.queue = queue
        self.sample_rate = int(sample_rate)
        self.steps_per_beat = int(steps_per_beat)
        self.steps = int(steps)
        self.ahead = int(ahead)
        self.tracks = []
        self.scheduled = 0
        self.refused = 0
        self.cancelled = 0
        if now is None:
            import audiopump
            now = audiopump.now
        self._now = now
        # How far in front of the audio a re-laid grid starts. One step by
        # default: enough that the next step is still in the future when a
        # tempo change is applied halfway through a tick.
        self._lead = lead
        self._bpm = float(bpm)
        self._origin = 0
        self._next = 0
        self._live = []            # (step, [token, ...]) not yet sounded
        self._running = False

    # -- the grid ----------------------------------------------------------

    @property
    def bpm(self):
        return self._bpm

    @bpm.setter
    def bpm(self, value):
        self.set_bpm(value)

    @property
    def step_frames(self):
        """Frames per step. One integer, and every step's frame is derived
        from its absolute index rather than added on, so a long run cannot
        drift by accumulated rounding."""
        return int(self.sample_rate * 60.0 / (self._bpm * self.steps_per_beat))

    def frame_of(self, step):
        return self._origin + (step * self.sample_rate * 60
                               // int(self._bpm * self.steps_per_beat))

    # -- tracks ------------------------------------------------------------

    def track(self, instrument, pattern):
        """Add ``instrument`` playing ``pattern``: {step: cells}.

        A cell is a pitch, `(pitch, velocity)` or `(pitch, velocity, gate)`.
        The instrument must be schedulable; `Instrument.schedulable` says so
        and this raises if it is not, rather than playing the part live and
        early, which is the failure nobody would hear as a failure.
        """
        if not instrument.schedulable:
            raise ValueError("%r cannot be scheduled" % instrument)
        self.tracks.append((instrument, pattern))
        return self

    # -- transport ---------------------------------------------------------

    def start(self, at=None):
        self._origin = self._now() + (self._lead or self.step_frames) \
            if at is None else at
        self._next = 0
        self._live = []
        self._running = True
        self.tick()
        return self

    def stop(self):
        """Stop, and take back every step that has not sounded."""
        self._running = False
        self.cancelled += self._cancel_pending()
        for instrument, _pattern in self.tracks:
            instrument.all_notes_off()

    def tick(self):
        """Top the queue up. Cheap, idempotent, and safe to call late."""
        if not self._running:
            return 0
        now = self._now()
        horizon = now + self.ahead * self.step_frames
        added = 0
        while _before(self.frame_of(self._next), horizon):
            self._schedule(self._next)
            self._next += 1
            added += 1
        # Forget the steps that have sounded; what is left is what a tempo
        # change can still take back.
        self._live = [row for row in self._live
                      if not _before(self.frame_of(row[0]), now)]
        return added

    def set_bpm(self, bpm):
        """Change tempo, keeping the phase of the next step that has not
        sounded. Everything ahead of the audio is cancelled and re-laid."""
        bpm = float(bpm)
        if bpm == self._bpm or bpm <= 0.0:
            self._bpm = bpm if bpm > 0.0 else self._bpm
            return 0
        taken = self._cancel_pending()
        self.cancelled += taken
        if self._running:
            resume = self._first_pending()
            self._bpm = bpm
            # The next unsounded step starts one step in front of the audio,
            # on the new grid. Re-anchoring on the ORIGIN instead would move
            # every step that already played, which is a different bar.
            self._origin = (self._now() + (self._lead or self.step_frames)
                            - (resume * self.sample_rate * 60
                               // int(bpm * self.steps_per_beat)))
            self._next = resume
            self.tick()
        else:
            self._bpm = bpm
        return taken

    # -- inside ------------------------------------------------------------

    def _schedule(self, step):
        frame = self.frame_of(step)
        cell_index = step % self.steps
        tokens = []
        for instrument, pattern in self.tracks:
            cells = pattern.get(cell_index)
            if not cells:
                continue
            for cell in cells:
                pitch, velocity, gate = _cell(cell)
                with instrument.scheduled(self.queue, frame, tokens):
                    instrument.note_on(pitch, velocity)
                if gate:
                    off = self.frame_of(step + gate)
                    with instrument.scheduled(self.queue, off, tokens):
                        instrument.note_off(pitch)
        self.scheduled += len(tokens)
        self.refused += tokens.count(0)
        if tokens:
            self._live.append((step, tokens))

    def _first_pending(self):
        return self._live[0][0] if self._live else self._next

    def _cancel_pending(self):
        taken = 0
        cancel = self.queue.cancel
        for _step, tokens in self._live:
            for token in tokens:
                if token and cancel(token):
                    taken += 1
        self._live = []
        return taken


def _cell(cell):
    """(pitch, velocity, gate) from a pitch, a pair or a triple."""
    if isinstance(cell, int):
        return cell, 127, 0
    if len(cell) == 2:
        return cell[0], cell[1], 0
    return cell[0], cell[1], cell[2]


def _before(a, b):
    """``a`` is earlier than ``b`` on the pump's 32-bit wrapping clock.

    The same comparison audiopump_events.c makes: a difference read as
    signed, so the clock's wrap every 24.9 hours is not a bar in the wrong
    place."""
    return ((a - b) & 0xFFFFFFFF) >= 0x80000000
