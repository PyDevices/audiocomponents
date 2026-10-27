# How accurate a scheduled part is

What [sequencing a part on the audio's clock](../guides/sequence-a-part.md) buys, what it costs, and where it falls short.

## Timing

Play the TR-808's own bar with a Karplus line over it twice on the unix build:
once through the queue, once from a wall-clock Python loop, with 185 to 260
garbage collections over a live heap of about 40 MB running beside it and a
worst tick of 27 to 47 ms.

| | worst spread within one drum | render |
|---|---|---|
| **scheduled** | **0 frames**, every run | one digest, six runs out of six |
| Python-timed | 256-1231 frames (5.3-25.7 ms) | a different render every run |

Not "within a block": every hit of a given drum lands at exactly the same
offset into its block. That also makes a sequenced render diffable, and so
testable.

Four bars of a real pattern through `Sequencer`, with the app thrashing
between every tick: 192 events, 0 refused, 0 late, 0 dropped, worst apply
6 µs.

### On a board

On an ESP32-P4 panel the drum machine ran its full pattern at 200 BPM with the
screen redrawing: 0 late, 0 dropped, 0 refused, with the worst gap between two
`Sequencer.tick()` calls at 54 to 60 ms against a 300 ms look-ahead. The same
bar driven from a Python timer had a worst step error of 42 to 179 ms on a
75 ms step, different on every run.

A bar of sixteenths on a grid, as error against the frame each hit asked for:

| board | scheduled | the same bar, Python-timed |
|---|---|---|
| ESP32-P4 | 16 of 16 hits, **4.4 ms mean / 11.6 ms worst** | 12 to 15 of 16 over four runs; 15.5-23.9 ms mean, 28.9-60.7 ms worst |
| ESP32-S3 | 16 of 16, **2.6 ms mean / 5.0 ms worst**, the same with the screen busy and idle | 8 of 16, 22 ms mean |

The re-entrancy guard described under "A tick can land inside your own bar" in
the guide has no board run. Its test uses `sys.settrace`, which is CPython
only.

## How faithful a scheduled hit is

Every instrument is byte-identical scheduled and live for a figure that
strikes each voice once. Strike a voice **twice** with both hits in the queue
at once and ten of the 55 differ, because a retrigger on this engine
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

The way round it is the look-ahead window: the defect only exists while two
hits of one voice sit in the queue together, so topping up one step at a time
removes it, at the cost of the lateness the queue exists to avoid.

There is no fix on this side of the seam. The shadow copy is what two hits of
one voice in one queue need, and a live retrigger is exact because it presses
the *same* object and lets the engine hand the channel back with the envelope
where it already is. Pressing the same shadow twice is exact only where the
second hit's parameters are unchanged; elsewhere it rewrites a note under the
hit that is still sounding, which is a worse defect for a smaller one.
Making the choke frame-exact is tracked in
[#95](https://github.com/PyDevices/audiocomponents/issues/95).

## Limits

- No test here runs a real pump. The gates drive
  `tests/support/fake_pump.py`, the engine's event queue written out in Python
  with the same validation, ordering, token rules and apply window. It catches
  everything above the queue — which events the seam writes, in what order, at
  which frames, carrying which notes — and the defects found so far lived there.
  It cannot catch whether the C sorts the way the Python does,
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
