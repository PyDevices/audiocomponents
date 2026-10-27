# Sequence a part on the audio's clock

A Python timer cannot keep a groove. A garbage collection, a screen redraw or
a flash write lands as a late note, and a bar rendered twice is never the same
bar twice. Instead, decide **when**, in frames, as far ahead as you like, and
let the pump apply it at a block boundary. How close that gets is in
[How accurate a scheduled part is](../how-it-works/sequencing-accuracy.md).

```python
import audiopump, audioinstruments
from audioinstruments.sequencer import Sequencer

drums = audioinstruments.create("tr808", 48000)
bass = audioinstruments.create("tb303", 48000)

q = audiopump.Events(capacity=192)
audiopump.events(q)
audiopump.spawn(mixer, blocks, status)

seq = Sequencer(q, sample_rate=48000, bpm=120)
seq.track(drums, {0: (36, 42), 4: (38, 42), 8: (36, 42), 12: (38, 42)})
seq.track(bass,  {0: (33, 110, 3), 8: (40, 110, 3)})   # pitch, velocity, gate
seq.start()

while playing:
    seq.tick()          # from a timer, as often or as rarely as you like
    if wants_faster:
        seq.set_bpm(180)

seq.stop()
```

`tick()` tops the queue up a few steps ahead of the audio and returns. It may
be forty milliseconds late and the groove does not move, because the step's
frame was decided when it was scheduled. A step is a pitch, or
`(pitch, velocity)`, or `(pitch, velocity, gate)` where the gate is in steps
and schedules the note-off; a drum needs no gate, a held note does.

Writing a tempo change is `bpm = ` or `set_bpm()`: what has not sounded is
taken back by token and re-laid on the new grid, phase-locked to the next
step, so the tempo changes where the player asked for it. `Events.clear()` is
never called, because it would drop a live player's notes too.

## Schedule one instrument without a sequencer

`Sequencer` is a convenience over one primitive, and a part that is not a grid
uses the primitive directly:

```python
with inst.scheduled(q, audiopump.now() + 24000) as tokens:
    inst.note_on(36, 127)            # heard at that frame, not now
    inst.note_on(42, 100)

inst.at(q, frame).note_on(38, 90)    # the same thing, for one call
inst.schedulable                     # True for all 55 that ship here
```

Inside the block the instrument does **all** of its usual Python on the
calling thread — validating, tracking held keys, building notes and envelopes
— and only the final presses and releases go on the queue. `tokens` holds one
token per event in schedule order, and a `0` is an event a full queue refused
rather than an exception from nowhere.

`audiopump.now()` is frames the pump has **pulled**, which is what it compares
your frame against, so schedule at `now() + wanted` and subtract nothing. What
a listener has heard is that minus what the sink is holding: with a 4 × 128
ring the lead is the ring plus one block, 384–640 frames, stable to within a
block.

Two costs worth knowing before a bar gets long. Each scheduled press makes a
private copy of its note, at schedule time, on the interpreter thread — which
is what stops a bar of one voice playing every hit at the last hit's velocity
— and that copy is about 1.4 kB and three quarters of the seam's cost. And it
roughly **doubles the event count** for a repeatedly-struck kit, because each
retrigger schedules its own release: 595 events for 200 note-ons, not 300.
That is queue capacity. A sequencer that fills one gets a `0` token and a
`dropped` count, not an exception.

## Three traps

**A tick can land inside your own bar.** On a board the timer that calls
`tick()` arrives through `micropython.schedule`, between the interpreter's own
bytecodes — so a top-up can land in the middle of `start()` while it is still
laying the bar, and re-arm the same keyboard. What comes back instead of a
voice is the seam's own state: `_staged` put back to `()` and `_tokens` put
back to `None` by a second `scheduled()` block nobody wrote, arriving as an
`AttributeError` out of a press. It reads exactly like an exhausted voice
pool, and it is not one.

You do not have to do anything about it. `Keys.arm()` nests, and
`Sequencer.tick()` is refused while the sequencer is already writing and
counted in `Sequencer.reentered`. What it means for you is that **a tick is
allowed to do nothing**: if you drive `tick()` from an interrupt or a
scheduled callback, do not assume every call tops the queue up, and keep the
look-ahead wide enough that the next one is in time.

**Schedule the note-off with the note-on.** An instrument updates its own
bookkeeping at *schedule* time, so a live press of a key the queue is still
holding finds that key held, releases notes that have not been pressed yet
(a no-op), presses its own — and the queued press arrives afterwards with
nothing left that knows about it. A note-on scheduled a second ahead
with its note-off queued too leaves nothing stuck; the same note-on **alone**
left three notes sounding forever. `Sequencer` always schedules both. A
hand-written `with inst.scheduled(...)` need not, and nothing stops it. If a
live player and a part must share an instrument, give them different channels
or different `note_id`s.

**Match the instrument's block to the pump's.** The grid's granularity is not
the pump's block — it is the **coarsest block in the path from the queue's
target to the sink**, and for an instrument that is `synthio`'s 256 frames. A
press applied at the top of a pump block that falls in the middle of a
synthesizer block is not heard until the synthesizer's next one, so half the
hits land a whole extra block late. With a 1024-byte mixer buffer the pump's
block is 128 frames and the spread is 128 frames; with a 2048-byte buffer the
two match and the spread is zero. The two cases are the two
rows of the timing table in [How accurate a scheduled part
is](../how-it-works/sequencing-accuracy.md).

## What cannot be scheduled

**No instrument in this package.** All 55 take a frame, `acoustickit`
included: audiodsp's pump queue carries `STRIKE` and `CHOKE`, and the kit lays
its whole mode table on them.

`schedulable = False` is still part of the `Instrument` contract, for a
provider outside this package whose note-on reaches the audio outside a
press. `Sequencer` refuses one rather than playing its part live and early —
the failure nobody would hear as a failure.

**A macro move.** `set_macro` reaches code that builds new node objects with
delay lines and filter state in them; that is not a value to store, and the
pump's apply half is stores only. A sequenced knob move stays a control-thread
call, made from Python whenever Python gets to it. It lands under the pump
lock within a block and the audio does not tear — what it does not get is a
frame number. For a filter sweep locked to the bar, use
a `synthio.LFO` or `Math` block, which the pull evaluates itself,
sample-accurately, with no queue involved.

**A kit change mid-bar.** `drumkits` is schedulable, but hits already in the
queue when the kit changes stay on the outgoing machine. They still sound, on
a mixer voice kept so its tail is not cut off — benign, and not what the
dropdown said.
