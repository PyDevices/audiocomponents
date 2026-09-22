"""The scheduling seam's claims, against the REAL pump instead of a stand-in.

    MICROPYPATH=<repo>:<repo>/lib <workspace>/cmods/bin/micropython \
        tests/parity/scheduling_seam_live.py [case ...] [--fault WHICH]

Cases: ``frame``, ``velocity``, ``silence``, ``wire``, ``kit``,
``kitlevels``, ``kitchoke`` (all by default).
Faults: ``early`` (frame), ``flat`` (velocity), ``held`` (silence),
``armed`` (wire), ``unstruck`` (kit), ``even`` (kitlevels), ``ringing``
(kitchoke). Each one must make this exit non-zero; a probe whose failing
mode is never run is not a gate.

Why it exists
-------------

`tests/test_scheduling_seam.py` proves which events the seam *writes* -
their order, their frames, the notes they carry - against
`tests/support/fake_pump.Events`, which is `audiopump_events.c` written out
in Python. That is the right instrument for those questions and it runs
anywhere. What it cannot answer is whether the real C applies them the way
the Python says it would (audiocomponents#92).

So this asks a different question of the same seam: **not which events were
written, but what was heard.** Every claim below is read off the audio the
pump actually produced, through `audiopump.Tap`, with the loop advanced by
`audiopump.service()` on this thread - the mode a build with no platform
driver runs in, and the one the CPython wheel gets. There is no event log
here on purpose: a log is the stand-in's affordance, and reading one would
put the Python back between the claim and the evidence.

Workspace-local by design, like the parity gates: it needs a MicroPython
build carrying audiodsp as a usermod, because `audiopump` exists only where
the pump does. CPython has no such module, which is exactly why the
stand-in exists.
"""

import sys

import audiopump
import audioinstruments

RATE = 48000
BLOCK_FRAMES = 256
BLOCK_BYTES = BLOCK_FRAMES * 2 * 2          # 16-bit stereo

#: Word offsets into `audiopump.STATUS_WORDS`, as `audiodsp/tests/pump`
#: reads them.
BLOCKS_AT = 0


def status():
    return bytearray(audiopump.STATUS_BYTES)


def blocks_pulled(block):
    import struct
    return struct.unpack_from("<Q", block, BLOCKS_AT * 8)[0]


def peaks(pcm, frames_per_window):
    """The loudest sample in each window of the captured audio."""
    view = memoryview(pcm)
    out = []
    step = frames_per_window * 4
    for start in range(0, len(view) - step + 1, step):
        top = 0
        chunk = view[start:start + step]
        for index in range(0, len(chunk), 2):
            value = chunk[index] | (chunk[index + 1] << 8)
            if value >= 32768:
                value -= 65536
            if value < 0:
                value = -value
            if value > top:
                top = value
        out.append(top)
    return out


def render(instrument, blocks, schedule=None, queue_capacity=256):
    """Pull `blocks` through the real pump and return what the tap heard.

    `schedule(queue, frame_of)` runs before the pull, with `frame_of(block)`
    turning a block index into the frame the pump will be at.
    """
    probe = audiopump.Tap(frames=blocks * BLOCK_FRAMES)
    audiopump.tap(probe)
    queue = audiopump.Events(capacity=queue_capacity)
    audiopump.events(queue)
    try:
        if schedule is not None:
            start = audiopump.now()
            schedule(queue, lambda block: start + block * BLOCK_FRAMES)
        block = status()
        audiopump.pull(instrument.output, blocks, block)
        heard = bytearray(blocks * BLOCK_BYTES)
        got = probe.readinto(heard)
    finally:
        audiopump.events(None)
        audiopump.tap(None)
        # `pull()` leaves the loop's frame counter where it stopped, and the
        # next `pull()` starts from zero again - so without this the second
        # render in a process schedules into a future that never arrives and
        # reads silence. Every case here is a fresh graph, so a shutdown
        # between them is the honest teardown as well as the working one.
        audiopump.shutdown()
    return bytes(heard[:got]), blocks_pulled(block)


def drum():
    """A TR-808: two notes per hit, one permanent `Note` per circuit
    rewritten on every strike - the shape the shadow copies exist for."""
    return audioinstruments.create("tr808", RATE)


def say(name, ok, detail):
    print("%-4s %-10s %s" % ("ok" if ok else "FAIL", name, detail))
    return ok


# --- the claims -------------------------------------------------------------

def frame(fault):
    """A scheduled press sounds at its frame, and not one block before it."""
    inst = drum()
    at_block = 0 if fault == "early" else 20

    def lay(queue, frame_of):
        with inst.scheduled(queue, frame_of(at_block)):
            inst.note_on(36, 127)

    pcm, _pulled = render(inst, 40, lay)
    inst.deinit()
    window = peaks(pcm, BLOCK_FRAMES)
    before = max(window[:20]) if len(window) >= 20 else 0
    after = max(window[20:]) if len(window) > 20 else 0
    return say("frame", before == 0 and after > 1000,
               "loudest sample before block 20: %d (want 0), after: %d "
               "(want a hit)" % (before, after))


def velocity(fault):
    """Two hits laid before either sounds keep their own levels.

    The shadow copy is taken at schedule time; a seam that handed the queue
    the live note instead would let the second press overwrite the first,
    and both hits would come out at the second one's velocity.
    """
    inst = drum()
    second = 127 if fault == "flat" else 32

    def lay(queue, frame_of):
        with inst.scheduled(queue, frame_of(4)):
            inst.note_on(36, 127)
        with inst.scheduled(queue, frame_of(24)):
            inst.note_on(36, second)

    pcm, _pulled = render(inst, 44, lay)
    inst.deinit()
    window = peaks(pcm, BLOCK_FRAMES)
    loud = max(window[4:20]) if len(window) > 20 else 0
    quiet = max(window[24:40]) if len(window) > 40 else 0
    return say("velocity", loud > 1000 and quiet > 0 and loud > quiet * 2,
               "hit at 127 peaks %d, hit at 32 peaks %d (want the first at "
               "least twice the second)" % (loud, quiet))


def silence(fault):
    """`all_notes_off()` reaches a note that is only scheduled.

    The drum machine's STOP button is this call. It used to release the
    source note and leave the shadow copy pressed on the engine for ever,
    which is a tail audible after the transport says stop.
    """
    inst = drum()

    def lay(queue, frame_of):
        with inst.scheduled(queue, frame_of(4)):
            inst.note_on(46, 127)           # the open hat: a long voice
        if fault != "held":
            with inst.scheduled(queue, frame_of(8)):
                inst.all_notes_off()

    pcm, _pulled = render(inst, 48, lay)
    inst.deinit()
    window = peaks(pcm, BLOCK_FRAMES)
    struck = max(window[4:8]) if len(window) > 8 else 0
    tail = max(window[24:]) if len(window) > 24 else 0
    return say("silence", struck > 1000 and tail < struck // 20,
               "the hit peaks %d, the tail 20 blocks after the stop peaks %d "
               "(want under %d)" % (struck, tail, struck // 20))


def wire(fault):
    """Playing live through the keyboard is the same audio as playing live.

    `Keys` is a pass-through when nothing has armed it. The fault arms it,
    which sends the press to the queue at a frame instead - so the live
    render goes silent and the two no longer match.
    """
    first = drum()

    def live(queue, _frame_of):
        first.note_on(36, 127)

    plain, _pulled = render(first, 32, live)
    first.deinit()

    second = drum()

    def maybe_armed(queue, frame_of):
        if fault == "armed":
            with second.scheduled(queue, frame_of(16)):
                second.note_on(36, 127)
        else:
            second.note_on(36, 127)

    other, _pulled = render(second, 32, maybe_armed)
    second.deinit()
    return say("wire", plain == other and max(peaks(plain, BLOCK_FRAMES)) > 1000,
               "%d bytes either way, identical: %s"
               % (len(plain), plain == other))


# --- the modal kit, whose strike is not a press -----------------------------
#
# `acoustickit` is the one instrument here whose hit reaches the audio outside
# a press: a strike is `Bank.set_mode()` on a running node and the energy goes
# in on that line. audiodsp#138 gave the pump `STRIKE` and `CHOKE` with frames
# on them and audiocomponents#94 made the kit emit them, so these three ask
# the same questions of a retune that the four above ask of a press.
#
# Every case strikes a TOM, and that is the measurement, not a taste in drums.
# Only `kick`, `snare` and `sidestick` carry layer notes played straight into
# the mixer; a tom is the bank and nothing else, and the excitation burst is
# not in the mixer at all. So a tom makes a sound if and only if a `STRIKE`
# reached the bank, and a case that passed with the strike missing could not
# happen quietly.


def kit():
    return audioinstruments.create("acoustickit", RATE)


def kit_frame(fault):
    """A kit's strike carries a frame: the bank is retuned by the pump."""
    inst = kit()
    at_block = 0 if fault == "unstruck" else 20

    def lay(queue, frame_of):
        with inst.scheduled(queue, frame_of(at_block)):
            inst.note_on(45, 127)               # Low Tom: bank-only

    pcm, _pulled = render(inst, 40, lay)
    inst.deinit()
    window = peaks(pcm, BLOCK_FRAMES)
    before = max(window[:20]) if len(window) >= 20 else 0
    after = max(window[20:]) if len(window) > 20 else 0
    return say("kit", before == 0 and after > 1000,
               "loudest sample before block 20: %d (want 0), after: %d "
               "(want a hit)" % (before, after))


def kit_levels(fault):
    """Two strikes laid before either sounds keep their own levels.

    This is the case that a frame-stamped `STRIKE` is *for*, and the one a
    retune at schedule time cannot pass: both sweeps would have run on this
    thread before the first stick arrived, so the downbeat would sound with
    the second hit's gains. Measured by declining `strike_bank` and leaving
    everything else scheduled - the old behaviour exactly - the loud hit came
    out at 666 and the soft one at 808, the bar inside out and both of them
    ten times down from 6981 and 2072.
    """
    inst = kit()
    second = 127 if fault == "even" else 32

    def lay(queue, frame_of):
        with inst.scheduled(queue, frame_of(4)):
            inst.note_on(45, 127)
        with inst.scheduled(queue, frame_of(24)):
            inst.note_on(45, second)

    pcm, _pulled = render(inst, 44, lay)
    inst.deinit()
    window = peaks(pcm, BLOCK_FRAMES)
    loud = max(window[4:20]) if len(window) > 20 else 0
    quiet = max(window[24:40]) if len(window) > 40 else 0
    return say("kitlevels", loud > 1000 and quiet > 0 and loud > quiet * 2,
               "tom at 127 peaks %d, tom at 32 peaks %d (want the first at "
               "least twice the second)" % (loud, quiet))


def kit_choke(fault):
    """A closing hi-hat silences the open one, at the closing hat's frame.

    Live this is `Bank.clear()`. Scheduled it is `audiopump.CHOKE`, laid at
    the same frame as the strike that follows it and before it, because
    events at one frame apply in schedule order.
    """
    inst = kit()

    def lay(queue, frame_of):
        with inst.scheduled(queue, frame_of(2)):
            inst.note_on(46, 127)               # Open Hi-Hat: a long voice
        if fault != "ringing":
            with inst.scheduled(queue, frame_of(16)):
                inst.note_on(42, 20)            # Closed Hi-Hat, soft

    pcm, _pulled = render(inst, 40, lay)
    inst.deinit()
    window = peaks(pcm, BLOCK_FRAMES)
    struck = max(window[2:16]) if len(window) > 16 else 0
    tail = max(window[24:]) if len(window) > 24 else 0
    return say("kitchoke", struck > 1000 and tail < struck // 20,
               "the open hat peaks %d, the tail 8 blocks after the closing "
               "hat peaks %d (want under %d)" % (struck, tail, struck // 20))


CASES = (("frame", frame), ("velocity", velocity),
         ("silence", silence), ("wire", wire),
         ("kit", kit_frame), ("kitlevels", kit_levels),
         ("kitchoke", kit_choke))


def main():
    wanted = []
    fault = None
    args = sys.argv[1:]
    index = 0
    while index < len(args):
        if args[index] == "--fault":
            index += 1
            fault = args[index]
        else:
            wanted.append(args[index])
        index += 1
    ok = True
    for name, case in CASES:
        if wanted and name not in wanted:
            continue
        ok = case(fault) and ok
    if fault is not None:
        # A fault run must go red. Inverted here so the caller can run it
        # the same way as a clean one and read the exit code.
        print("fault %r: %s" % (fault, "seen" if not ok else "NOT SEEN"))
        raise SystemExit(0 if not ok else 1)
    raise SystemExit(0 if ok else 1)


main()
