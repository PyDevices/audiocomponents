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

An editor changes three more things while the bar is playing, and each has a
call: `relay()` after a pattern edit (the step is read again at the frame it
already had, so the edit is heard on the next pass of that step rather than
a bar later), `retrack()` for a change of instrument, and `position`, which
is the step the audio is in -- derived from the clock, so a late repaint
still lights the right cell. `start(step=)` picks the groove up where it was
after something reset the pump's clock.

The queue is this sequencer's. `cancel()` takes back one event by token and
is what a tempo change uses; `Events.clear()` would drop a live player's
notes too, and this never calls it.

`tick()` is **refused while the sequencer is already writing to the queue**,
and counted in `reentered`. On a board a timer callback arrives between the
interpreter's own bytecodes, so it can land inside `start()` or inside
another tick; re-entering there laid the same step twice and disarmed the
keyboard underneath a press that was still using it. See
`docs/spikes/live-audio-path-fullbar.md` in the workspace anchor.
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
        #: True while this sequencer is writing to the queue. A `tick()` that
        #: arrives inside that window is refused and counted rather than run.
        #: See `tick`.
        self._busy = False
        #: How many ticks arrived while the sequencer was already scheduling.
        #: Not an error: the next tick tops the queue up, and `ahead` is
        #: hundreds of milliseconds deep. A number that climbs fast means the
        #: timer is firing faster than a bar can be laid.
        self.reentered = 0

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

    @property
    def position(self):
        """Which step the audio is in now, or -1 when nothing is playing.

        Counted from ``start()``, so ``position % steps`` is the cell a
        playhead should light. It is read off the same clock the notes are
        stamped with, which is the point: a Python timer painting the
        indicator can be forty milliseconds late without the light landing
        on the wrong step, because the step is derived and not counted.

        What ``now()`` reports is frames PULLED, so this runs the sink's
        depth -- a block or two on a board -- ahead of what is audible. For
        a light that is the right way round to be wrong.
        """
        if not self._running:
            return -1
        delta = (self._now() - self._origin) & 0xFFFFFFFF
        if delta >= 0x80000000:      # the origin is still in the future
            return -1
        return int(delta // self.step_frames)

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

    def retrack(self, instrument, index=0, pattern=None):
        """Put ``instrument`` on track ``index`` in place of what was there.

        For a player changing kit mid-bar. The steps already on the queue
        belong to the instrument that is leaving, so they are taken back
        here rather than left to sound on a machine the dropdown says is
        gone; :meth:`relay` lays them again on the new one.
        """
        if not instrument.schedulable:
            raise ValueError("%r cannot be scheduled" % instrument)
        old, old_pattern = self.tracks[index]
        self.tracks[index] = (instrument,
                              old_pattern if pattern is None else pattern)
        self.relay()
        return old

    # -- transport ---------------------------------------------------------

    def start(self, at=None, step=0):
        """Start playing, ``step`` steps into the pattern.

        ``step=0`` is the top of the bar and is what a transport button
        wants. A non-zero one is for picking the groove up where it was
        after something interrupted the audio -- changing kit restarts the
        pump, which resets its clock to zero, and restarting the bar at the
        downbeat instead of where the player was is a jump they did not ask
        for.
        """
        self._busy = True
        try:
            step = int(step)
            origin = self._now() + (self._lead or self.step_frames) \
                if at is None else at
            self._origin = origin - (step * self.sample_rate * 60
                                     // int(self._bpm * self.steps_per_beat))
            self._next = step
            self._live = []
            self._running = True
            self._top_up()
        finally:
            self._busy = False
        return self

    def stop(self):
        """Stop, and take back every step that has not sounded."""
        self._busy = True
        try:
            self._running = False
            self.cancelled += self._cancel_pending()
            for instrument, _pattern in self.tracks:
                instrument.all_notes_off()
        finally:
            self._busy = False

    def tick(self):
        """Top the queue up. Cheap, idempotent, and safe to call late.

        **Refused while this sequencer is already writing to the queue.**
        A tick is a timer callback, and on a board a timer callback arrives
        through `micropython.schedule`, between the interpreter's own
        bytecodes - so it can land inside `start()`, `relay()`, a tempo
        change, or another tick, all of which are laying steps on this same
        queue through this same instrument. Re-entering there laid `_next`
        twice, once from each call, and left the armed keyboard underneath
        disarmed by the inner call's exit while the outer press was still
        using it (docs/spikes/live-audio-path-fullbar.md). A refused tick
        costs nothing: the look-ahead is hundreds of milliseconds and the
        next tick tops up what this one did not.
        """
        if self._busy:
            self.reentered += 1
            return 0
        self._busy = True
        try:
            return self._top_up()
        finally:
            self._busy = False

    def _top_up(self):
        """`tick()` without the re-entrancy guard, for callers holding it."""
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

    def relay(self):
        """Read the pattern again for every step that has not sounded yet.

        A step's cells are read when the step is scheduled, which is up to
        ``ahead`` steps before it sounds. Without this, a player who toggles
        a step inside that window hears the edit a whole bar later -- long
        enough that it reads as a bug in the button. Call it after any edit
        to a pattern this sequencer is playing.

        Nothing moves: a step is re-laid at the frame it already had, so the
        groove is the same bar with different cells in it. Only steps whose
        every event came back off the queue are laid again, because a step
        that has already been applied would sound twice.
        """
        if not self._running:
            return 0
        self._busy = True
        try:
            taken, resume = self._take_back()
            self._next = resume
            self._top_up()
        finally:
            self._busy = False
        return taken

    def _take_back(self):
        """Cancel what has not sounded; say how much, and where to resume.

        Shared by `relay` and `set_bpm`, which want exactly the same two
        things out of the queue and used to disagree about the second.
        """
        now = self._now()
        cancel = self.queue.cancel
        taken = 0
        spent = {}
        for step, tokens in self._live:
            alive = True
            for token in tokens:
                if token and cancel(token):
                    taken += 1
                else:
                    # Applied already, or never taken: this step has sounded,
                    # or partly sounded, and re-laying it would double it.
                    alive = False
            spent[step] = not alive
        self._live = []
        self.cancelled += taken
        # Then walk back over the steps already scheduled, to the earliest
        # one that has not sounded. **Not driven off `_live`**: a step with
        # no cells on it never got there, and the cell a player has just
        # switched ON is exactly such a step. Reading `_live` alone left the
        # new hit waiting for the next bar, which is the whole failure
        # `relay` exists to prevent; and it left a tempo change SKIPPING
        # every step it had cancelled, which is a hole in the bar as wide as
        # the look-ahead.
        resume = self._next
        step = self._next - 1
        while step >= 0:
            if spent.get(step) or _before(self.frame_of(step), now):
                break
            resume = step
            step -= 1
        return taken, resume

    def set_bpm(self, bpm):
        """Change tempo, keeping the phase of the next step that has not
        sounded. Everything ahead of the audio is cancelled and re-laid."""
        bpm = float(bpm)
        if bpm == self._bpm or bpm <= 0.0:
            self._bpm = bpm if bpm > 0.0 else self._bpm
            return 0
        if not self._running:
            taken = self._cancel_pending()
            self.cancelled += taken
            self._bpm = bpm
            return taken
        # The earliest step that has not sounded, not the earliest step still
        # holding tokens: a step with no cells on it never held any, and
        # resuming past it skipped every silent step inside the look-ahead.
        # With a 300 ms window that was two sixteenths of nothing at the
        # seam, which is a hole in the bar and not a tempo change.
        self._busy = True
        try:
            taken, resume = self._take_back()
            self._bpm = bpm
            # The next unsounded step starts one step in front of the audio,
            # on the new grid. Re-anchoring on the ORIGIN instead would move
            # every step that already played, which is a different bar.
            self._origin = (self._now() + (self._lead or self.step_frames)
                            - (resume * self.sample_rate * 60
                               // int(bpm * self.steps_per_beat)))
            self._next = resume
            self._top_up()
        finally:
            self._busy = False
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
