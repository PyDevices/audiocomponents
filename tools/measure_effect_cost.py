"""What does ONE effect, or ONE audioif node, cost this board per block?

    mpftp put -d COM4 tools/measure_effect_cost.py /measure_effect_cost.py
    mpftp exec -d COM4 'import measure_effect_cost as m; m.main("node:audiofilters.Filter")'
    mpftp exec -d COM4 'import measure_effect_cost as m; m.main("effect:Compressor")'
    mpftp exec -d COM4 'import measure_effect_cost as m; m.main()'   # catalogue

`audioeffects` must be importable on the board. If the firmware does not
freeze it in, put the package on the filesystem first:

    mpftp mkdir -d COM4 /lib
    mpftp cp lib/audioeffects :/lib/audioeffects --verify

For a target slow enough that the run outlives `exec`'s quiet timeout, use
the write-to-file pattern instead - `main()` prints to stdout, so redirect it
by wrapping the call in a script that writes the lines to a board file and
`mpftp probe --capture` that file.

WHY THIS EXISTS
---------------
The effects program is about to add native nodes. Before anything is added,
somebody has to be able to say what the existing palette already costs on the
two boards in the room - otherwise "the new node is worth its bytes" is an
argument with no numbers on either side. This is that baseline, and it is
deliberately the same method as `measure_voice_headroom.py`: audio seconds
rendered over wall seconds spent rendering them, `time.ticks_us` on the
board, no output device anywhere near it.

WHAT IT MEASURES
----------------
ONE target per run, against a fixed probe source, in three numbers:

    blocks/s   256-frame stereo blocks the board renders per wall second
    rt         real-time factor: audio seconds produced / seconds spent
    ms/block   wall milliseconds one 256-frame block costs

256 frames is not an arbitrary unit here. Every fixed-size node in the
audioif palette - `audioecho.FeedbackDelay`, `audiodynamics.Dynamics`,
`audiomath.Multiply`, `audioconvolve.Convolver`, and the `audioroute`
splitter's chunk - works in exactly 256-frame blocks, so it is the palette's
own block. At 48 kHz one such block is 5.333 ms of audio: a target must beat
5.333 ms/block to keep up at all, and rt is that same fact as a ratio.

Every run also measures the probe source ALONE as a control, on a freshly
built chain, and prints the difference. That matters because the harness is
not free: `audiocore.get_buffer` copies each block into a fresh allocation,
and the source is a `Mixer` doing real per-sample work. The control is the
floor the target is standing on; `marginal` is what the target itself added.
Read the marginal column when comparing two nodes, and the rt column when
asking whether a chain fits in real time.

THE DIGEST
----------
One sha256 per run, over the first 128 blocks (683 ms) the target renders from
a chain built one instruction earlier - so it is the same 683 ms of material
every time, on every board. It is there so that a cost table is also a
statement about what was rendered: two boards reporting the same digest
rendered the same audio, and a digest that moves when only the cost was meant
to move is a finding.

The probe material itself is generated with integer arithmetic only, so the
INPUT is byte-identical on any chip. Run the `source` target to get that
input's own digest.

WHAT IT DOES NOT MEASURE
------------------------
Real audio output. Nothing here opens an I2S device, so none of this includes
the audiodev pump or the I2S ring - the seam where a stompbox's latency
actually lives. Treat every number as an upper bound on what the board can do
and a lower bound on what a chain will cost in an app.

It also measures one target at a time. A rack is not the sum of its nodes:
splitters, mixers and the extra buffer copies between them cost too, which is
why the racks are targets of their own rather than an arithmetic exercise.
"""

import gc
import time
from array import array

import audiocore
import audiomixer

SAMPLE_RATE = 48000
CHANNELS = 2

#: The palette's own block. See the module docstring.
BLOCK_FRAMES = 256
BYTES_PER_FRAME = CHANNELS * 2
BLOCK_BYTES = BLOCK_FRAMES * BYTES_PER_FRAME

#: Audio seconds one 256-frame block stands for. A target costing more wall
#: time than this per block cannot keep up.
BLOCK_SECONDS = float(BLOCK_FRAMES) / SAMPLE_RATE

#: Blocks the digest covers. Fixed on purpose: two boards must hash the same
#: material, so this number may never depend on how fast a board is.
#:
#: 128 blocks is 683 ms, and the length is load-bearing rather than arbitrary.
#: At 64 blocks (341 ms) the window ended BEFORE the first repeat of a
#: `DigitalDelay`, whose default time is 350 ms - and since the delay nodes
#: pass the dry through at unity, the effect hashed byte-identical to the bare
#: source. A digest that cannot tell a delay from a piece of wire is not a
#: check. Any default longer than this window has the same problem, so a
#: target whose digest equals the `source` row's is a result to go and explain,
#: not one to accept.
DIGEST_BLOCKS = 128

#: The timed pass keeps rendering until it has spent this long, so a fast
#: node is not measured over a window a single GC pause could dominate.
MIN_WALL_S = 1.5

#: ...and stops here regardless, so a heavy target still returns.
MAX_WALL_S = 12.0

#: Wall seconds one timed segment aims at. Segments exist so the run prints
#: something every fraction of a second: `mpftp run --follow` gives up on a
#: board that stays quiet for about ten.
SEGMENT_S = 0.35

#: Frames of probe material before it loops. 4096 is 85 ms, long enough that
#: the loop point is not a rhythm any effect can lock onto.
PROBE_FRAMES = 4096


def pcm(buffer_size=BLOCK_BYTES):
    """The keyword bundle every audioif node wants, at this tool's format."""
    return {
        "sample_rate": SAMPLE_RATE,
        "channel_count": CHANNELS,
        "bits_per_sample": 16,
        "samples_signed": True,
        "buffer_size": buffer_size,
    }


def _clip(value):
    if value > 32767:
        return 32767
    if value < -32768:
        return -32768
    return value


def _tri(frame, period, amp):
    """One triangle cycle of `period` frames, peak `amp`, integer only."""
    span = 4 * amp
    position = ((frame * span) // period) % span
    if position <= amp:
        return position
    if position <= 3 * amp:
        return 2 * amp - position
    return position - span


def probe_pcm():
    """Deterministic stereo probe material - integers all the way down.

    No `math.sin` anywhere, and no float arithmetic, because the point of the
    digest is that the two boards start from byte-identical input: a libm
    difference between a RISC-V and an Xtensa build would otherwise show up
    downstream as a digest difference and be read as an effects bug.

    The material is two detuned triangles plus a little noise under a
    repeating decay, which gives an effect all four things it needs to show
    its cost honestly: harmonics for a filter to remove, transients for a
    compressor's envelope to chase, a level that moves so a gate opens and
    closes, and different content per channel so a stereo effect is not
    quietly measured in mono.
    """
    data = array("h")
    seed = 0x1234ABCD
    for frame in range(PROBE_FRAMES):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        noise = ((seed >> 13) & 2047) - 1024
        envelope = 255 - (((frame & 1023) * 255) >> 10)
        left = ((_tri(frame, 436, 9000) + _tri(frame, 291, 4200) + noise)
                * envelope) >> 8
        right = ((_tri(frame, 291, 8200) + _tri(frame, 655, 4600) - noise)
                 * envelope) >> 8
        data.append(_clip(left))
        data.append(_clip(right))
    return data


class Probe:
    """The source every target is measured behind.

    A looping `RawSample` through a one-voice `Mixer`, because the effects
    library's classes call `play(source)` without `loop=True` - they are
    written to sit behind an endless source (a synthesizer, an instrument),
    and a bare RawSample reports DONE after one buffer. The Mixer is the
    cheapest endless source in the palette.

    `buffer_size` is twice the block size deliberately: a Mixer is
    double-buffered, so it hands back half of what it was given. 2048 in is
    the 1024-byte, 256-frame block out that everything else here works in.
    """

    def __init__(self):
        self.sample = audiocore.RawSample(
            probe_pcm(), sample_rate=SAMPLE_RATE, channel_count=CHANNELS)
        self.mixer = audiomixer.Mixer(voice_count=1,
                                      **pcm(2 * BLOCK_BYTES))
        self.mixer.voice[0].level = 1.0
        self.mixer.play(self.sample, voice=0, loop=True)
        self.output = self.mixer


# --- targets ---------------------------------------------------------------
#
# A builder takes the probe and returns (output, extras, keep):
#   output  the node to pull for timing and for the digest
#   extras  further nodes to pull once per block (a second splitter tap has
#           to be consumed or it is not being measured at all)
#   keep    everything that must outlive the builder so the GC leaves the
#           chain alone mid-measurement
#
# Node arguments are the ones the effects library actually passes. This is a
# baseline for THIS palette as THESE effects use it, not a synthetic
# benchmark: a Filter with no filter or a Convolver with no impulse would
# measure a code path nothing ships.


def _source(probe):
    return probe.output, (), ()


def _feedback_delay(probe):
    import audioecho
    node = audioecho.FeedbackDelay(sample_rate=SAMPLE_RATE,
                                   channel_count=CHANNELS, max_delay_ms=250)
    node.set(delay_ms=180.0, feedback=0.45, mix=0.5)
    node.play(probe.output)
    return node, (), (node,)


def _dynamics(probe):
    import audiodynamics
    node = audiodynamics.Dynamics(audiodynamics.DYN_COMPRESS,
                                  sample_rate=SAMPLE_RATE,
                                  channel_count=CHANNELS)
    node.set(threshold_db=-20.0, ratio=4.0, attack_ms=5.0, release_ms=120.0,
             knee_db=6.0, makeup_db=0.0)
    node.play(probe.output)
    return node, (), (node,)


def _multiply(probe):
    import audiomath
    carrier = array("h")
    # A whole number of cycles of a triangle: Multiply loops its modulator,
    # and a partial cycle would step the phase once per table.
    length = 218                       # 48000 / 218 is about 220 Hz
    for frame in range(length):
        value = _tri(frame, length, 32000)
        carrier.append(value)
        carrier.append(value)
    table = audiocore.RawSample(carrier, sample_rate=SAMPLE_RATE,
                                channel_count=CHANNELS)
    node = audiomath.Multiply(sample_rate=SAMPLE_RATE,
                              channel_count=CHANNELS)
    node.play(probe.output)
    node.modulate(table)
    node.set(mix=1.0)
    return node, (), (node, table)


def _splitter(probe):
    """A two-tap splitter with ONE tap consumed - what a parallel branch
    costs before the branch itself does anything."""
    import audioroute
    split = audioroute.Splitter(probe.output, taps=2)
    return split.tap(0), (), (split,)


def _splitter_two_taps(probe):
    """The same splitter with BOTH taps consumed per block. The difference
    from the row above is what a second reader of the same signal costs."""
    import audioroute
    split = audioroute.Splitter(probe.output, taps=2)
    second = split.tap(1)
    return split.tap(0), (second,), (split, second)


def _convolver(taps):
    def build(probe):
        import audioconvolve
        node = audioconvolve.Convolver(max_taps=taps, ir_channels=CHANNELS,
                                       sample_rate=SAMPLE_RATE,
                                       channel_count=CHANNELS)
        node.play(probe.output)
        # A synthesized impulse rather than a measured one: convolution cost
        # is set by the tap count, not by what is in the taps.
        node.synthesize(decay=float(taps) / SAMPLE_RATE, damping_hz=6000.0,
                        predelay_ms=0.0, diffusion_ms=0.0, seed=1)
        node.set(mix=0.5)
        return node, (), (node,)
    return build


def _filter(probe):
    import audiofilters
    import synthio
    node = audiofilters.Filter(
        filter=synthio.Biquad(synthio.FilterMode.LOW_PASS, 1200.0, Q=0.707),
        mix=1.0, **pcm())
    node.play(probe.output)
    return node, (), (node,)


def _filter_modulated(probe):
    """The same Filter, but with its cutoff behind a `synthio.Math` block -
    which is how every `_SingleFilter` subclass in `audioeffects` builds one,
    so that `set_frequency` can move it later. The difference between this row
    and the plain Filter above is what a *sweepable* cutoff costs."""
    import audiofilters
    import synthio
    frequency = synthio.Math(synthio.MathOperation.SUM, 1200.0, 0.0, 0.0)
    node = audiofilters.Filter(
        filter=synthio.Biquad(synthio.FilterMode.LOW_PASS, frequency,
                              Q=0.707),
        mix=1.0, **pcm())
    node.play(probe.output)
    return node, (), (node, frequency)


def _phaser(probe):
    import audiofilters
    node = audiofilters.Phaser(frequency=800.0, feedback=0.6, mix=1.0,
                               stages=6, **pcm())
    node.play(probe.output)
    return node, (), (node,)


def _distortion(probe):
    import audiofilters
    node = audiofilters.Distortion(mode=audiofilters.DistortionMode.OVERDRIVE,
                                   soft_clip=True, pre_gain=12.0,
                                   post_gain=-6.0, mix=1.0, **pcm())
    node.play(probe.output)
    return node, (), (node,)


def _chorus(probe):
    import audiodelays
    node = audiodelays.Chorus(max_delay_ms=50, delay_ms=20.0, voices=3,
                              mix=0.5, **pcm())
    node.play(probe.output)
    return node, (), (node,)


def _echo(probe):
    import audiodelays
    node = audiodelays.Echo(max_delay_ms=300, delay_ms=180.0, decay=0.45,
                            mix=0.5, freq_shift=False, **pcm())
    node.play(probe.output)
    return node, (), (node,)


def _multitap(probe):
    import audiodelays
    node = audiodelays.MultiTapDelay(max_delay_ms=500, delay_ms=400.0,
                                     decay=0.0, mix=0.5,
                                     taps=(0.25, 0.5, 0.75, 1.0), **pcm())
    node.play(probe.output)
    return node, (), (node,)


def _pitch_shift(probe):
    import audiodelays
    node = audiodelays.PitchShift(semitones=7.0, mix=1.0, window=2048,
                                  **pcm())
    node.play(probe.output)
    return node, (), (node,)


def _freeverb(probe):
    import audiofreeverb
    node = audiofreeverb.Freeverb(roomsize=0.88, damp=0.35, mix=0.3, **pcm())
    node.play(probe.output)
    return node, (), (node,)


def _mixer(probe):
    """A second Mixer stage - what one more mixing point costs. Every
    parallel effect in the library ends in one of these."""
    node = audiomixer.Mixer(voice_count=2, **pcm(2 * BLOCK_BYTES))
    node.voice[0].play(probe.output)
    node.voice[0].level = 1.0
    node.voice[1].level = 0.0
    return node, (), (node,)


#: The audioif palette as the effects library uses it. Keys are the import
#: path of the node, with a suffix where one node is worth measuring at more
#: than one size.
NODES = {
    "audioecho.FeedbackDelay": _feedback_delay,
    "audiodynamics.Dynamics": _dynamics,
    "audiomath.Multiply": _multiply,
    "audioroute.Splitter": _splitter,
    "audioroute.Splitter+tap": _splitter_two_taps,
    "audioconvolve.Convolver@1024": _convolver(1024),
    "audioconvolve.Convolver@48000": _convolver(48000),
    "audiofilters.Filter": _filter,
    "audiofilters.Filter@math": _filter_modulated,
    "audiofilters.Phaser": _phaser,
    "audiofilters.Distortion": _distortion,
    "audiodelays.Chorus": _chorus,
    "audiodelays.Echo": _echo,
    "audiodelays.MultiTapDelay": _multitap,
    "audiodelays.PitchShift": _pitch_shift,
    "audiofreeverb.Freeverb": _freeverb,
    "audiomixer.Mixer": _mixer,
}


def _effect(name):
    def build(probe):
        import audioeffects
        audioeffects.configure(SAMPLE_RATE, CHANNELS)
        effect = audioeffects.create(name, probe.output, SAMPLE_RATE)
        return effect.output, (), (effect,)
    return build


def resolve(target):
    """`target` -> a builder, or raise with something readable.

    Accepts `source`, `node:<key>`, `effect:<Name>`, and a bare name, which
    is treated as a node key if one matches and an effect otherwise. The
    prefixes exist so a typo in an effect name fails as a missing effect
    rather than being silently measured as something else.
    """
    if target == "source":
        return _source
    if target.startswith("node:"):
        key = target[5:]
        if key not in NODES:
            raise ValueError("no such node: %s" % key)
        return NODES[key]
    if target.startswith("effect:"):
        return _effect(target[7:])
    if target in NODES:
        return NODES[target]
    return _effect(target)


# --- measurement -----------------------------------------------------------


def _seconds_since(start):
    return time.ticks_diff(time.ticks_us(), start) / 1000000.0


def _warm(output, extras, want_digest, blocks=DIGEST_BLOCKS):
    """Render `blocks` blocks from a chain that has just been built.

    Hashes them when asked, and times them roughly - roughly because the
    hashing is in the loop, so this pass sizes the timed pass's segments and
    is never itself reported as a cost.
    """
    hasher = None
    if want_digest:
        import hashlib
        hasher = hashlib.sha256()
    wanted = blocks * BLOCK_FRAMES
    frames = 0
    pulls = 0
    gc.collect()
    start = time.ticks_us()
    while frames < wanted:
        for extra in extras:
            audiocore.get_buffer(extra)
        result, buffer = audiocore.get_buffer(output)
        if buffer is None:
            raise RuntimeError(
                "get_buffer returned no data (result %s) after %d pulls"
                % (result, pulls))
        if hasher is not None:
            hasher.update(bytes(buffer))
        got = len(buffer) // BYTES_PER_FRAME
        frames += got
        pulls += 1
        if got == 0 and pulls > 64:
            raise RuntimeError("output produced no frames in %d pulls" % pulls)
        if pulls > blocks * 16 + 64:
            raise RuntimeError("output never reached %d frames" % wanted)
    spent = _seconds_since(start)
    digest = ""
    if hasher is not None:
        import binascii
        digest = binascii.hexlify(hasher.digest()).decode()[:16]
    return digest, spent, frames, pulls


def _timed(output, extras):
    """The measurement. Nothing in the inner loop but the pulls.

    The chain arrives warm from `_warm`, which is the honest state to measure
    in: delay lines are full, LFOs are running, and a compressor's envelope
    has settled. A cold first block costs something different and is not what
    an effect does for the rest of its life.
    """
    per_segment = 16
    frames = 0
    pulls = 0
    spent = 0.0
    gc.collect()
    while True:
        start = time.ticks_us()
        for _ in range(per_segment):
            for extra in extras:
                audiocore.get_buffer(extra)
            _result, buffer = audiocore.get_buffer(output)
            frames += len(buffer) // BYTES_PER_FRAME
        segment = _seconds_since(start)
        spent += segment
        pulls += per_segment
        print(".", end="")
        if spent >= MIN_WALL_S or spent >= MAX_WALL_S:
            break
        # Size the next segment from what the last one actually cost, so a
        # fast node stops printing a dot every millisecond and a slow one
        # still prints one before the host's quiet timeout.
        per_pull = segment / per_segment
        if per_pull > 0:
            want = int(SEGMENT_S / per_pull)
            per_segment = max(1, min(8192, want))
    print("")
    return spent, frames, pulls


def prime(build):
    """Build the chain once, render a little, and throw it all away.

    Not optional, and not tidiness. `audioeffects` is 100 KB of Python that a
    board with no frozen copy compiles on first import, and on a fresh VM that
    compile - plus the first touch of those pages through the flash cache, plus
    the GC settling around the result - lands squarely in the middle of the run
    that follows it.

    Measured without this step, `effect:LowPass` returned 1.966, 1.133 and
    0.356 ms/block on three consecutive fresh-VM runs of the identical script:
    a 5.5x spread, on audio that never changed (the digest was the same all
    three times). The node rows never showed it, because a node imports nothing
    from the filesystem - so the artefact would have landed only on the effect
    rows, and looked exactly like effects being expensive.
    """
    probe = Probe()
    output, extras, keep = build(probe)
    _warm(output, extras, False, blocks=DIGEST_BLOCKS // 4)
    del keep, probe, output, extras
    gc.collect()


def _rates(spent, frames):
    if spent <= 0:
        return 0.0, 0.0, 0.0
    audio_seconds = frames / float(SAMPLE_RATE)
    blocks = frames / float(BLOCK_FRAMES)
    return blocks / spent, audio_seconds / spent, spent * 1000.0 / blocks


def run(build, want_digest):
    """Build a fresh chain, warm it, time it. Returns everything measured.

    The RAM figure is taken across `build` alone, with the probe already
    standing, so it is the target's own footprint and not the harness's.
    `gc.mem_alloc` rather than `gc.mem_free`: on a board with SPIRAM the free
    figure moves for reasons that have nothing to do with this allocation.
    """
    probe = Probe()
    gc.collect()
    before = gc.mem_alloc()
    output, extras, keep = build(probe)
    gc.collect()
    after = gc.mem_alloc()
    digest, _warm_s, _warm_frames, _warm_pulls = _warm(output, extras,
                                                       want_digest)
    spent, frames, pulls = _timed(output, extras)
    blocks_per_s, rt, ms_per_block = _rates(spent, frames)
    del keep, probe, output, extras
    gc.collect()
    return {
        "digest": digest,
        "seconds": spent,
        "frames": frames,
        "pulls": pulls,
        "blocks_per_s": blocks_per_s,
        "rt": rt,
        "ms_per_block": ms_per_block,
        "bytes": after - before,
    }


# --- report ----------------------------------------------------------------


def identity():
    """The board this ran on, in the two forms that identify a firmware."""
    import os
    import sys
    name = os.uname()
    build = getattr(sys.implementation, "_build", "?")
    return ("%s %s / %s / %s"
            % (name.sysname, name.release, name.version, build))


def catalogue():
    print("targets, one per run:")
    print("  source")
    for key in sorted(NODES):
        print("  node:%s" % key)
    try:
        import audioeffects
        for name in audioeffects.ALL:
            print("  effect:%s" % name)
    except ImportError as exc:
        print("  effect:<name> - audioeffects is not importable here: %s"
              % exc)


def main(target=None):
    if target is None:
        catalogue()
        return None

    print("== effect cost ==")
    print("target: %s" % target)
    print("board:  %s" % identity())
    print("format: %d Hz, %d ch, %d-frame blocks (%d bytes, %.3f ms audio)"
          % (SAMPLE_RATE, CHANNELS, BLOCK_FRAMES, BLOCK_BYTES,
             BLOCK_SECONDS * 1000.0))

    build = resolve(target)

    prime(build)
    print("control (probe source alone) ", end="")
    control = run(_source, False)
    print("target  (%s) " % target, end="")
    measured = run(build, True)

    print("")
    print("%-36s %10s %9s %10s %10s"
          % ("", "blocks/s", "rt", "ms/block", "RAM bytes"))
    print("%-36s %10.1f %9.2f %10.3f %10d"
          % ("source (control)", control["blocks_per_s"], control["rt"],
             control["ms_per_block"], control["bytes"]))
    print("%-36s %10.1f %9.2f %10.3f %10d"
          % (target, measured["blocks_per_s"], measured["rt"],
             measured["ms_per_block"], measured["bytes"]))
    marginal = measured["ms_per_block"] - control["ms_per_block"]
    print("%-36s %10s %9s %10.3f"
          % ("marginal (target - control)", "", "", marginal))
    print("")
    print("budget: %.3f ms/block is real time; this target uses %.0f%% of it"
          % (BLOCK_SECONDS * 1000.0,
             100.0 * measured["ms_per_block"] / (BLOCK_SECONDS * 1000.0)))
    print("digest (%d blocks): %s" % (DIGEST_BLOCKS, measured["digest"]))
    print("timed:  %d frames in %.3f s over %d pulls"
          % (measured["frames"], measured["seconds"], measured["pulls"]))

    # One tab-separated line so a runner can build a table without parsing
    # the prose above.
    print("ROW\t%s\t%.1f\t%.2f\t%.3f\t%.3f\t%.3f\t%d\t%s"
          % (target, measured["blocks_per_s"], measured["rt"],
             measured["ms_per_block"], control["ms_per_block"], marginal,
             measured["bytes"], measured["digest"]))
    return measured


if __name__ == "__main__":
    main()
