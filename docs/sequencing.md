# Playing a part on the audio's clock

A Python timer cannot keep a groove. A garbage collection, a screen redraw or
a flash write lands as a late note, and a bar rendered twice is never the same
bar twice. This is how a part is written instead: decide **when**, in frames,
as far ahead as you like, and let the pump apply it at a block boundary.

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

## What it buys, measured

The drum machine's own bar on a TR-808 with a Karplus line over it, played
twice on the unix build — once through the queue, once from a wall-clock
Python loop — with about 190 collections over a 40 MB live heap going on
beside it, worst tick 33–50 ms:

| | worst spread within one drum | render |
|---|---|---|
| **scheduled** | **0 frames**, every run | one digest, six runs out of six |
| Python-timed | 768–1280 frames (16–27 ms) | a different render every run |

Zero. Not "within a block": every hit of a given drum landed at exactly the
same offset into its block, six runs running. That is also what makes a
sequenced render diffable, and therefore testable at all.

Four bars of a real pattern through `Sequencer`, with the app thrashing
between every tick: 187 events, 0 refused, 0 late, 0 dropped, worst apply
7 µs.

### On a board

The seam has been on one. On the **Waveshare ESP32-P4 panel**, the drum
machine ran its full pattern at 200 BPM with the screen redrawing: **0 late,
0 dropped, 0 refused**, with the worst gap between two `Sequencer.tick()`
calls at **54 ms against a 300 ms look-ahead**. The same bar driven from a
Python timer had a worst step error of 37 ms on a 75 ms step.

A bar of sixteenths on a grid, measured as error against the frame each hit
asked for:

| board | scheduled | the same bar, Python-timed |
|---|---|---|
| Waveshare ESP32-P4 | 16 of 16 hits, **4.4 ms mean / 11.6 ms worst** | 15 of 16 — one hit lost — 15.4 / 49.4 ms |
| LilyGO T-Embed S3 | 16 of 16, **2.6 ms mean / 5.0 ms worst**, identical with the screen busy and idle | 8 of 16, 22 ms mean |

**The full-bar re-entrancy guard below has not been exercised on a board.**
Its two files are on the P4, but the bar that raised the original error was
not replayed there, and the proof that the guard fires in exactly that window
uses `sys.settrace`, which is CPython only.

## The three traps

**A tick can land inside your own bar.** On a board the timer that calls
`tick()` arrives through `micropython.schedule`, between the interpreter's own
bytecodes — so a top-up can land in the middle of `start()` while it is still
laying the bar, and re-arm the same keyboard. What comes back instead of a
voice is the seam's own state: `_staged` put back to `()` and `_tokens` put
back to `None` by a second `scheduled()` block nobody wrote, arriving as an
`AttributeError` out of a press. It reads exactly like an exhausted voice
pool, and it is not one — at the drum machine's own queue capacity a full bar
refuses nothing and presses five of the engine's sixty-four voices.

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
nothing left that knows about it. Measured: a note-on scheduled a second ahead
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
two match and the spread is zero. That is the difference between the two rows
in the table above and a table with no story in it.

## What cannot be scheduled

**`acoustickit`, and only it.** A strike there is `ModalBank.set_mode()` on a
bank that is already running, plus a press on a second synthesizer to excite
it. The retune is a C state change with no frame on it and it is shared by
every hit of that voice, so a bar scheduled ahead would retune the bank to the
last hit before the first one sounded. It declares `schedulable = False`, it
still plays live, and `Sequencer` refuses it rather than playing its part
early — which is the failure nobody would hear as a failure. All 54 others
take a frame.

**A macro move.** `set_macro` reaches code that builds new node objects with
delay lines and filter state in them; that is not a value to store, and the
pump's apply half is stores only. A sequenced knob move stays a control-thread
call, made from Python whenever Python gets to it. It lands under the pump
lock within a block and the audio does not tear — what it does not get is a
frame number. For a filter sweep locked to the bar, the honest answer today is
a `synthio.LFO` or `Math` block, which the pull evaluates itself,
sample-accurately, with no queue involved.

**A kit change mid-bar.** `drumkits` is schedulable, but hits already in the
queue when the kit changes stay on the outgoing machine. They still sound, on
a mixer voice kept so its tail is not cut off — benign, and not what the
dropdown said.

## How faithful a scheduled hit is

Every instrument is byte-identical scheduled and live for a figure that
strikes each voice once. Strike a voice **twice** with both hits in the queue
at once and ten of the 55 differ, because a retrigger on this hardware
*chokes*: pressing a note `synthio` is already sounding takes its channel
back, and two copies of a note cannot share a channel. The choke is rebuilt
out of the release instead, and that recovers most of it but not all:

| | difference from the live render |
|---|---|
| `tr808`, `tr606`, `drumkits` | −18.7, −14.0, −11.6 dB |
| `dmx`, `simmons_sdsv`, `sp1200`, `acoustickit` | −6.6 to −9.1 dB |
| `arp2600`, `ms20`, `prophet_vs` | −34.1 to −41.8 dB |
| the other 45 | byte-identical |

Musically: a voice struck twice while both hits are in the queue rings under
its own retrigger instead of being cut dead by it. It is loudest where the
voice has a long tail — an 808 kick at a 213 ms spacing — and inaudible on the
melodic three, which are a tail under a new note rather than a lost choke.

The way round it today is the look-ahead window: the defect only exists while
two hits of one voice sit in the queue together, so topping up one step at a
time removes it, at the cost of the lateness it was bought to avoid.

[audiocomponents#95](https://github.com/PyDevices/audiocomponents/issues/95)
carries a controlled re-measurement at the current pin — nulled against the
live render, with a single strike as the control — and the proposal for
making the choke frame-exact. The short of it: there is no fix on this side
of the seam. The shadow copy is what two hits of one voice in one queue
need, and a live retrigger is exact because it presses the *same* object and
lets the engine hand the channel back with the envelope where it already is.
Pressing the same shadow twice was tried and is exact only where the second
hit's parameters are unchanged; elsewhere it rewrites a note under the hit
that is still sounding, which is a worse defect for a smaller one.

## One instrument, no sequencer

`Sequencer` is a convenience over one primitive, and a part that is not a grid
uses the primitive directly:

```python
with inst.scheduled(q, audiopump.now() + 24000) as tokens:
    inst.note_on(36, 127)            # heard at that frame, not now
    inst.note_on(42, 100)

inst.at(q, frame).note_on(38, 90)    # the same thing, for one call
inst.schedulable                     # False for acoustickit, and only it
```

Inside the block the instrument does **all** of its usual Python on the
calling thread — validating, tracking held keys, building notes and envelopes
— and only the final presses and releases go on the queue. `tokens` holds one
token per event in schedule order, and a `0` is an event a full queue refused
rather than an exception from nowhere.

`audiopump.now()` is frames the pump has **pulled**, which is what it compares
your frame against, so schedule at `now() + wanted` and subtract nothing. What
a listener has heard is that minus what the sink is holding: on the T-Embed S3
the lead is the ring plus one block — 384–640 frames at a 4 × 128 ring, stable
to within a block.

Two costs worth knowing before a bar gets long. Each scheduled press makes a
private copy of its note, at schedule time, on the interpreter thread — which
is what stops a bar of one voice playing every hit at the last hit's velocity
— and that copy is about 1.4 kB and three quarters of the seam's cost. And it
roughly **doubles the event count** for a repeatedly-struck kit, because each
retrigger schedules its own release: 595 events for 200 note-ons, not 300.
That is queue capacity. A sequencer that fills one gets a `0` token and a
`dropped` count, not an exception.

## What is not built

- The full-bar re-entrancy guard has not been exercised on a board. Its two
  files are on the Waveshare ESP32-P4; the bar that raised the original error
  was not replayed there, and the proof that the guard fires in exactly that
  window uses `sys.settrace`, which is CPython only.
- Nothing in this repository's CI runs a real pump. The gates here drive
  `tests/support/fake_pump.py`, the engine's event queue written out in Python
  with the same validation, ordering, token rules and apply window. It catches
  everything above the queue — which events the seam writes, in what order, at
  which frames, carrying which notes — and all three defects the spike found
  lived there. It cannot catch whether the C sorts the way the Python does,
  whether applying an event allocates, or whether the pump reaches the frame
  on time.
- Voice stealing does not apply to scheduled notes: the arbiter asks the
  engine whether a press was taken, and a scheduled press has not happened
  yet. Past capacity a scheduled chord loses notes silently.
- No tempo map. `set_bpm` cancels and re-lays, which is better than clearing
  and rescheduling, but it is not events in beats.
- `Sequencer` has no swing, no per-step velocity ramp and no pattern chaining,
  and schedules nothing but notes.
- Two threads scheduling into one queue is undefended. `at()`, `cancel()` and
  `clear()` are safe against the *pump*, not against each other.
