"""What does ONE effect, or ONE audiodsp node, cost this board per block?

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
audiodsp palette - `audioecho.FeedbackDelay`, `audiodynamics.Dynamics`,
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
    """The keyword bundle every audiodsp node wants, at this tool's format."""
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


def _splitter_four_taps(probe):
    """A four-tap splitter with ALL four taps consumed per block. DeEsser
    and MultibandCompressor both instantiate this graph; the 1-tap and
    2-tap rows do not cover it."""
    import audioroute
    split = audioroute.Splitter(probe.output, taps=4)
    extras = (split.tap(1), split.tap(2), split.tap(3))
    return split.tap(0), extras, (split,) + extras


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


#: RingMod's default carrier at 48 kHz stereo: frequency=220, TARGET_FRAMES=2048
#: → cycles=9, length=1964 frames. Tremolo's default Rate 5 Hz is 9600 frames
#: (fs/rate). dtype array("h"), stereo interleaved, RawSample single_buffer
#: (the whole table every get_buffer, which is how it loops).
RINGMOD_CARRIER_FRAMES = 1964
TREMOLO_LFO_FRAMES = 9600


def _extra_rawsample(frames):
    """A second looping RawSample pulled every block, no processing node.

    The probe source is already one pull. The builder adds only a table
    returned as an extra so the timed loop pulls it once per block.
    Marginal over the control is the extra source pull; Multiply is not
    in this graph.
    """
    def build(probe):
        values = array("h")
        for frame in range(frames):
            value = _tri(frame, frames, 32000)
            values.append(value)
            values.append(value)
        extra = audiocore.RawSample(
            values, sample_rate=SAMPLE_RATE, channel_count=CHANNELS)
        return probe.output, (extra,), (extra,)
    return build


# --- the Phase 1 nodes -----------------------------------------------------
#
# Eight additions landed in the firmware of 2026-09-07. Their settings below
# are chosen so a row is comparable to the row it argues against, not so it
# flatters: the `audiobiquad` rows use the same frequency, Q, stages and
# feedback as the `audiofilters` rows above them, and the two "@options" rows
# repeat their base row's settings exactly and add only the new paths.


def q15_curve(points=1024):
    """An odd cubic soft-clip curve as int16 Q15, integer arithmetic only.

    `audioshaper.Waveshaper` takes its curve as data, and cost does not
    depend on what is in the table - only on how long it is. What the
    integer arithmetic buys is the same thing it buys in `probe_pcm`: the
    two boards shape against a byte-identical table, so a digest difference
    is the node's and never the libm's.

    y = 1.5x - 0.5x^3 over -1..+1, which reaches exactly +-1 at the rails.
    """
    curve = array("h")
    last = points - 1
    for index in range(points):
        x = (index * 65535) // last - 32767          # Q15, -32767..+32768
        cube = (x * x // 32768) * x // 32768
        value = (3 * x - cube) // 2
        curve.append(_clip(value))
    return curve


def _waveshaper(factor):
    def build(probe):
        import audioshaper
        curve = q15_curve()
        node = audioshaper.Waveshaper(sample_rate=SAMPLE_RATE,
                                      channel_count=CHANNELS,
                                      oversample=factor, curve=curve,
                                      pre_gain=8.0, bias=0.0,
                                      post_gain=0.5, mix=1.0)
        node.play(probe.output)
        return node, (), (node, curve)
    return build


def _biquad(probe):
    """The same low-pass the `audiofilters.Filter` row measures, on the
    float kernel instead of the Q12 one."""
    import audiobiquad
    node = audiobiquad.Biquad(mode=audiobiquad.LOW_PASS, frequency=1200.0,
                              Q=0.707, mix=1.0, sample_rate=SAMPLE_RATE,
                              channel_count=CHANNELS)
    node.play(probe.output)
    return node, (), (node,)


def _modal(modes, ringing=True):
    """A resonator bank of `modes` modes, all of them sounding.

    `ringing` is the whole point of having two of these rows. A bank skips a
    mode whose state has reached exact zero, so a bank of silent modes costs
    one compare each and a bank that is actually ringing costs the recursion -
    and a drum kit holds far more modes resident than it is sounding at once.
    Measuring only the quiet case would flatter it by the ratio of the two.
    """
    def build(probe):
        import audiomodal
        node = audiomodal.Bank(modes=modes, sample_rate=SAMPLE_RATE,
                               channel_count=CHANNELS)
        for index in range(modes):
            # Spread across the band, all with decays long enough that none of
            # them finishes inside the measurement.
            frequency = 60.0 + index * (6000.0 / max(modes - 1, 1))
            node.set_mode(index, frequency, 8.0, 1.0 if ringing else 0.0)
        node.play(probe.output)
        return node, (), (node,)
    return build


def _allpass(probe):
    """The same six stages, frequency and feedback as the
    `audiofilters.Phaser` row - the comparison audiodsp#36 is about."""
    import audiobiquad
    node = audiobiquad.AllPass(stages=6, frequency=800.0, feedback=0.6,
                               mix=1.0, sample_rate=SAMPLE_RATE,
                               channel_count=CHANNELS)
    node.play(probe.output)
    return node, (), (node,)


def _ladder(oversample):
    def build(probe):
        import audioladder
        node = audioladder.Ladder(sample_rate=SAMPLE_RATE,
                                  channel_count=CHANNELS,
                                  cutoff_hz=1200.0, resonance=3.5,
                                  drive=1.0, poles=4, passband_comp=0.5,
                                  oversample=oversample, mix=1.0)
        node.play(probe.output)
        return node, (), (node,)
    return build


def _tank(probe):
    """Dattorro's default network - the tables the node ships - with the
    modulation running, since a static tank is not what the class wants."""
    import audioverb
    node = audioverb.Tank(sample_rate=SAMPLE_RATE, channel_count=CHANNELS,
                          max_predelay_ms=200.0, decay=0.7, diffusion=0.75,
                          damping_hz=5000.0, bandwidth_hz=9000.0,
                          low_cut_hz=0.0, predelay_ms=20.0,
                          mod_depth_ms=0.5, mod_rate_hz=1.0, drive=0.0,
                          width=1.0, tone_db=0.0, mix=0.3)
    node.play(probe.output)
    return node, (), (node,)


def _suboctave(probe):
    import audiomath
    node = audiomath.SubOctave(probe.output, order=1, mix=1.0,
                               threshold=0.01, hold_ms=1.0,
                               sample_rate=SAMPLE_RATE,
                               channel_count=CHANNELS)
    return node, (), (node,)


def _midside(probe):
    import audioroute
    node = audioroute.MidSide(probe.output, width=1.5,
                              sample_rate=SAMPLE_RATE,
                              channel_count=CHANNELS)
    return node, (), (node,)


def _feedback_delay_options(probe):
    """The `audioecho.FeedbackDelay` row's settings, with all four of the
    2026-09-07 options switched on. The difference between the two rows is
    what the new paths cost, measured rather than reasoned about."""
    import audioecho
    shape = array("h")
    points = 256
    for index in range(points):                 # one period of a triangle
        shape.append(_tri(index, points, 32767))
    node = audioecho.FeedbackDelay(sample_rate=SAMPLE_RATE,
                                   channel_count=CHANNELS, max_delay_ms=250)
    node.set(delay_ms=180.0, feedback=0.45, mix=0.5,
             wow_hz=1.5, wow_depth_ms=2.0, wow_shape=shape,
             delay_slew=0.5, wow_am_depth=0.25,
             loop_semitones=12.0, loop_window_ms=25.0)
    node.play(probe.output)
    return node, (), (node, shape)


# --- the rate path the drive family prices from ----------------------------
#
# Phase 4 added these. `Bitcrusher` holds two `audiospeed.SpeedChanger` nodes
# in series and the palette table had no row for either, so its dossier budget
# says "plus two unpriced SpeedChanger nodes" - an argument with no number in
# it. The settings are the class's own (`bitcrusher.py`
# `STAND_RATE_HZ` 26040.0): at 48 kHz the down leg runs at
# 48000/26040 = 1.8433 and the up leg at its reciprocal.

#: `Bitcrusher.STAND_RATE_HZ`. Kept here rather than imported so a node row
#: costs nothing from `audioeffects`.
STAND_RATE_HZ = 26040.0


def _speed_changer(rate):
    def build(probe):
        import audiospeed
        node = audiospeed.SpeedChanger(probe.output, rate=rate)
        return node, (), (node,)
    return build


def _sample_hold(probe):
    """`audioshaper.SampleHold` at Bitcrusher's default hold: 48000/26040
    reduces to 400/217. Since audiodsp e3b95e7 (audiodsp#97) the class holds
    with this one node instead of a SpeedChanger pair, so this row is what
    its budget is priced from; the pair's two rows stay for the record."""
    import audioshaper
    node = audioshaper.SampleHold(probe.output, 48000, int(STAND_RATE_HZ))
    return node, (), (node,)


def _resampler(probe):
    """`Resampler` at the only ratio this harness can reach: 1.0.

    The ratio is not the caller's to set - it is bound by whatever plays the
    node, from the source's rate over the destination's
    (`audiospeed/Resampler.c:11-26`), and nothing here is a destination. Every
    rate in this file is 48 kHz, so even a bound one would be 1.0. The row is
    therefore the node's per-block machinery at identity ratio, and it is a
    floor for a resampling one, not a measurement of it.
    """
    import audiospeed
    node = audiospeed.Resampler(probe.output)
    return node, (), (node,)


def _dynamics_options(probe):
    """The `audiodynamics.Dynamics` row's settings with the expensive half
    of the new options on: the RMS detector, the feedback tap, the 4x
    true-peak reconstruction and a two-pole side-chain band."""
    import audiodynamics
    node = audiodynamics.Dynamics(audiodynamics.DYN_COMPRESS,
                                  sample_rate=SAMPLE_RATE,
                                  channel_count=CHANNELS)
    node.set(threshold_db=-20.0, ratio=4.0, attack_ms=5.0, release_ms=120.0,
             knee_db=6.0, makeup_db=0.0,
             detector="rms", rms_ms=10.0, feedback_detector=True,
             true_peak=2, sidechain_hz=120.0, sidechain_lp_hz=2500.0,
             sidechain_poles=2)
    node.play(probe.output)
    return node, (), (node,)


# --- the same nodes, at the settings the drive classes ship ----------------
#
# Added 2026-09-17 by the board-digest cause pass. Every node row above is
# measured at the settings ITS phase cared about, and a digest is only a
# statement about the settings it was rendered at: a class whose digest
# splits between two boards cannot be attributed to a node row taken at a
# different curve, frequency or level. These rows repeat six nodes at the
# settings `overdrive.py` and `exciter.py` construct them
# with, so a per-node answer is about the arithmetic the class runs.

#: `Overdrive._refresh()`'s `pre_gain` at patch 0 - `(r2/R1)/UMAX` with
#: `r2 = (12*9**(64/127) - 1) * R1` - written here as a literal so every leg
#: feeds the node the SAME number. The class computes it in Python floats,
#: which are double on CPython and on the unix build and single on a board;
#: that difference belongs to the class row and would otherwise be measured
#: here as if it were the node's.
OD_PRE_GAIN = 11.7709228

#: `Overdrive`'s blend mixer at patch 0: Mix 127 and Level 100 give
#: `voice[0].level = 0.0` and `voice[1].level = mix * level = 100/127`.
OD_BLEND_LEVEL = 0.7874015748031497


#: The same drive row with a `pre_gain` every leg holds to the bit.
#:
#: `OD_PRE_GAIN` above is a decimal that is not exactly representable, and a
#: board rounds it ONCE, in single (`mp_float_t`), where a desktop rounds it
#: in double and the node rounds that to single - so the two legs feed the
#: node `413c55b4` and `413c55b3`, one ULP apart, and the row that was
#: written to be identical on every leg is not. 11.75 is `413c0000` exactly,
#: on any interpreter. The row exists to separate "the node computes
#: differently on a board" from "the node was handed a different number".
OD_PRE_GAIN_EXACT = 11.75


def _waveshaper_drive(factor, pre_gain=None):
    """The waveshaper with a real drive curve instead of the synthetic one.

    The `@x1`..`@x8` rows above shape against `q15_curve()`, an odd cubic
    generated with integer arithmetic. `Overdrive`'s shipped `CURVE` is a
    diode table: asymmetric in the large, far steeper near zero, and it
    puts the oversampled path's half-band filters on entirely different
    numbers. These are the only node rows that import `audioeffects`, and
    the import is for the table only - the class is not built.
    """
    def build(probe):
        import audioshaper
        from audioeffects.overdrive import CURVE
        node = audioshaper.Waveshaper(sample_rate=SAMPLE_RATE,
                                      channel_count=CHANNELS,
                                      oversample=factor, curve=CURVE,
                                      mix=1.0,
                                      pre_gain=(OD_PRE_GAIN
                                                if pre_gain is None
                                                else pre_gain),
                                      post_gain=1.0, bias=0.0,
                                      hysteresis=0.0)
        node.play(probe.output)
        return node, (), (node, CURVE)
    return build



def _waveshaper_bitcrusher(probe):
    """The shaper at `Bitcrusher`'s own table: 8193 points, 16 KB.

    Every `@x*` and `@drive*` row above shapes through a 1024- or
    1025-point curve, and this file's own note says the cost "does not
    depend on what is in the table - only on how long it is". `Bitcrusher`
    runs eight times that length, set by the 12-bit span, and its pack
    (§12.4) names this row as the one the board owes: a 16 KB table and a
    2 KB table are not the same memory story on an S3. Settings are the
    class's own - unity everywhere, no oversampling.
    """
    import audioshaper
    from audioeffects.bitcrusher import CURVE
    node = audioshaper.Waveshaper(sample_rate=SAMPLE_RATE,
                                  channel_count=CHANNELS,
                                  oversample=1, curve=CURVE, mix=1.0,
                                  pre_gain=1.0, post_gain=1.0, bias=0.0,
                                  hysteresis=0.0)
    node.play(probe.output)
    return node, (), (node, CURVE)


def _biquad_at(mode, frequency, q, gain_db=None):
    """One `audiobiquad.Biquad` at a named mode, frequency and Q.

    `mode` is the attribute name rather than the constant, because the
    module is imported inside the builder like every other node here.
    """
    def build(probe):
        import audiobiquad
        extra = {} if gain_db is None else {"gain_db": gain_db}
        node = audiobiquad.Biquad(mode=getattr(audiobiquad, mode),
                                  frequency=frequency, Q=q, mix=1.0,
                                  sample_rate=SAMPLE_RATE,
                                  channel_count=CHANNELS, **extra)
        node.play(probe.output)
        return node, (), (node,)
    return build


def _midside_unity(probe):
    """`audioroute.MidSide` at width 1.0 - the identity width.

    `Overdrive` opens and closes on one of these, at width 1.0, where the
    node is arithmetically a wire. Whether it is a wire in the samples is
    the question the row exists to answer.
    """
    import audioroute
    node = audioroute.MidSide(probe.output, width=1.0,
                              sample_rate=SAMPLE_RATE,
                              channel_count=CHANNELS)
    return node, (), (node,)


def _mixer_at(levels, voice):
    """A two-voice `Mixer` with the probe on `voice`, at `levels`.

    The `audiomixer.Mixer` row above is 1.0 / 0.0 with the probe on voice 0,
    which is a voice at unity and a voice that is off: the one case where
    the scale is exact on any interpreter. `Overdrive` runs two of these
    stages, and only the first is at unity - its blend is 0.0 / 100/127,
    a fractional level, which is where audiodsp#84 lives.
    """
    def build(probe):
        node = audiomixer.Mixer(voice_count=2, **pcm(2 * BLOCK_BYTES))
        node.voice[voice].play(probe.output)
        for index, level in enumerate(levels):
            node.voice[index].level = level
        return node, (), (node,)
    return build


def _splitter_taps(taps):
    """An `n`-tap splitter with EVERY tap consumed per block.

    The `+tap` and `+4` rows above are the two counts Phase 1 and Phase 2
    needed. Phase 4's mixer rows want a 3-tap one to sit beside
    `audiomixer.Mixer@3active`, because a three-voice mixer fed from a
    splitter costs the splitter as well and the two have to be separable.
    """
    def build(probe):
        import audioroute
        split = audioroute.Splitter(probe.output, taps=taps)
        extras = tuple(split.tap(index) for index in range(1, taps))
        return split.tap(0), extras, (split,) + extras
    return build


def _mixer_active(voices):
    """A `Mixer` with `voices` voices ALL PLAYING, at level 1.0.

    The `audiomixer.Mixer` row above plays one voice and leaves the other
    at level 0.0 with no source, so it prices a mixing point with one
    reader. Every Phase 4 class sums two - a dry tap and a wet tap off the
    same `Splitter` - and `Overdrive` and `Distortion` run two such stages.
    Whether a second and a third active voice cost what the first did is a
    board question, and this is the row that answers it.

    The sources are splitter taps rather than independent `RawSample`s on
    purpose: that is the graph the classes build, and it keeps the extra
    source pull out of the figure. The comparison point is therefore
    `audioroute.Splitter+tap` (2) or `audioroute.Splitter+3` (3), not the
    bare control - subtract that row to get the mixer's own increment.
    """
    def build(probe):
        import audioroute
        split = audioroute.Splitter(probe.output, taps=voices)
        node = audiomixer.Mixer(voice_count=voices, **pcm(2 * BLOCK_BYTES))
        taps = []
        for index in range(voices):
            tap = split.tap(index)
            taps.append(tap)
            node.voice[index].play(tap)
            node.voice[index].level = 1.0
        return node, (), (node, split) + tuple(taps)
    return build


def _dynamics_transient(probe):
    """`audiodynamics.Dynamics` as `Exciter` constructs it: the transient
    shaper with both gains at 0 dB, which is what its patch 0 (Character
    off) leaves it at. The detector runs; the gain it applies is unity."""
    import audiodynamics
    node = audiodynamics.Dynamics(audiodynamics.DYN_TRANSIENT,
                                  sample_rate=SAMPLE_RATE,
                                  channel_count=CHANNELS,
                                  attack_gain_db=0.0, sustain_gain_db=0.0)
    node.play(probe.output)
    return node, (), (node,)


#: The audiodsp palette as the effects library uses it. Keys are the import
#: path of the node, with a suffix where one node is worth measuring at more
#: than one size.
NODES = {
    "audioecho.FeedbackDelay": _feedback_delay,
    "audiodynamics.Dynamics": _dynamics,
    "audiomath.Multiply": _multiply,
    "audioroute.Splitter": _splitter,
    "audioroute.Splitter+tap": _splitter_two_taps,
    "audioroute.Splitter+4": _splitter_four_taps,
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
    "audiocore.RawSample+extra": _extra_rawsample(RINGMOD_CARRIER_FRAMES),
    "audiocore.RawSample+extra@256": _extra_rawsample(BLOCK_FRAMES),
    "audiocore.RawSample+extra@9600": _extra_rawsample(TREMOLO_LFO_FRAMES),
    # The Phase 1 nodes, firmware of 2026-09-07.
    "audiobiquad.Biquad": _biquad,
    "audiomodal.Bank@8": _modal(8),
    "audiomodal.Bank@16": _modal(16),
    "audiomodal.Bank@32": _modal(32),
    "audiomodal.Bank@64": _modal(64),
    "audiomodal.Bank@64quiet": _modal(64, ringing=False),
    "audiobiquad.AllPass": _allpass,
    "audioladder.Ladder": _ladder(1),
    "audioladder.Ladder@os2": _ladder(2),
    "audioverb.Tank": _tank,
    "audiomath.SubOctave": _suboctave,
    "audioroute.MidSide": _midside,
    "audioshaper.Waveshaper@x1": _waveshaper(1),
    "audioshaper.Waveshaper@x2": _waveshaper(2),
    "audioshaper.Waveshaper@x4": _waveshaper(4),
    "audioshaper.Waveshaper@x8": _waveshaper(8),
    "audioecho.FeedbackDelay@options": _feedback_delay_options,
    "audiodynamics.Dynamics@options": _dynamics_options,
    # The rate path, Phase 4. Both legs of Bitcrusher's pair, at its rates.
    "audiospeed.SpeedChanger": _speed_changer(48000.0 / STAND_RATE_HZ),
    "audiospeed.SpeedChanger@up": _speed_changer(STAND_RATE_HZ / 48000.0),
    "audioshaper.SampleHold": _sample_hold,
    "audiospeed.Resampler": _resampler,
    # The drive classes' own settings, Phase 4's digest-cause pass.
    "audioshaper.Waveshaper@drive1": _waveshaper_drive(1),
    "audioshaper.Waveshaper@drive2": _waveshaper_drive(2),
    "audioshaper.Waveshaper@drive4": _waveshaper_drive(4),
    "audioshaper.Waveshaper@drive8": _waveshaper_drive(8),
    "audioshaper.Waveshaper@drive4exact": _waveshaper_drive(
        4, pre_gain=OD_PRE_GAIN_EXACT),
    "audioshaper.Waveshaper@drive1exact": _waveshaper_drive(
        1, pre_gain=OD_PRE_GAIN_EXACT),
    # Phase 4's palette: a 3-tap splitter, and the mixer with two and three
    # voices actually playing.
    "audioshaper.Waveshaper@bits12": _waveshaper_bitcrusher,
    "audioroute.Splitter+3": _splitter_taps(3),
    "audiomixer.Mixer@2active": _mixer_active(2),
    "audiomixer.Mixer@3active": _mixer_active(3),
    "audiobiquad.Biquad@hp720": _biquad_at("HIGH_PASS", 720.0, 0.15),
    "audiobiquad.Biquad@lp6000": _biquad_at("LOW_PASS", 6000.0, 0.15),
    "audiobiquad.Biquad@shelf3000": _biquad_at("HIGH_SHELF", 3000.0, 0.5,
                                               gain_db=6.0),
    # The four filters `Overdrive` runs at patch 0 and the one `Exciter`
    # does, at the values their `_refresh()` computes rather than the ones
    # their constructors take - read off the built classes and written here
    # as literals, so every leg configures the node from the same decimal.
    "audiobiquad.Biquad@od-hp": _biquad_at("HIGH_PASS", 723.9403965759934,
                                           0.25),
    "audiobiquad.Biquad@od-c4": _biquad_at("LOW_PASS", 21029.49403593439,
                                           0.4968844520277081),
    "audiobiquad.Biquad@od-lp": _biquad_at("LOW_PASS", 6960.3072719046795,
                                           0.27210198787316137),
    "audiobiquad.Biquad@od-shelf": _biquad_at("LOW_SHELF", 80.0, 0.5,
                                              gain_db=0.0031496062992125706),
    "audiobiquad.Biquad@ex-hp": _biquad_at("HIGH_PASS", 4026.4555023450857,
                                           0.7071),
    "audioroute.MidSide@1": _midside_unity,
    "audiomixer.Mixer@unity": _mixer_at((1.0, 1.0), 0),
    "audiomixer.Mixer@blend": _mixer_at((0.0, OD_BLEND_LEVEL), 1),
    "audiodynamics.Dynamics@transient": _dynamics_transient,
}


def _split_patch(name):
    """`<Name>` or `<Name>@<patch>` -> (name, patch or None).

    A cost figure at construction defaults is not a class's cost unless the
    defaults are the state the cost is about: four of Phase 2's sixteen
    board figures were the bare probe's, because the runner applies no
    patch (`docs/effects-phase2-pattern-revision.md` section 1.4).
    """
    if "@" not in name:
        return name, None
    name, _, tail = name.partition("@")
    return name, int(tail)


def _effect(name):
    """`Name`, `Name@rebuilt`, `Name#<patch>`, and `Name@<patch>`.

    `rebuilt:` prefix (see `_rebuilt`) and `@rebuilt` / `#<patch>` suffixes
    are the two branch forms for the same two facts: a parked class is not
    what `create()` returns, and a default-bypass class is not a cost.
    """
    patch = None
    rebuilt = False
    if "#" in name:
        name, _, tail = name.partition("#")
        patch = int(tail)
    if name.endswith("@rebuilt"):
        rebuilt = True
        name = name[:-len("@rebuilt")]
    if not rebuilt and patch is None:
        name, patch = _split_patch(name)

    def build(probe):
        import audioeffects
        audioeffects.configure(SAMPLE_RATE, CHANNELS)
        if rebuilt:
            from audioeffects import rebuilt as _rebuilt_mod
            cls = _rebuilt_mod.module_class(name)
            if cls is None:
                raise ValueError("no rebuilt module for %s" % name)
            effect = cls.create(probe.output, SAMPLE_RATE)
        else:
            effect = audioeffects.create(name, probe.output, SAMPLE_RATE)
        if patch is not None:
            effect.program_change(patch)
        return effect.output, (), (effect,)
    return build


def _rebuilt(name):
    """The **rebuilt** class of that name, whether or not it is adopted.

    `audioeffects.create()` reads the registry, and a Phase 2 class that is
    parked rather than adopted (`rebuilt.ADOPTED`) resolves there to the old
    family class - so `effect:Compressor` measures the class the rebuild
    replaces. `rebuilt:Compressor` names the rebuilt one, and
    `rebuilt:Compressor@3` puts it on patch 3.

    `rebuilt:Fuzz@os2` is the third form, and it is a construction option
    rather than a patch: the two Phase 4 classes that have a lean position at
    all reach it with `oversample=2` at `create()`, not with a
    `program_change` (`fuzz.py`, `saturation.py`; the other
    five say "no lean patch" in their own docstrings). Without it a lean cost
    is unmeasurable through this tool, which is how Phase 2 ended with no lean
    row anywhere.

    `rebuilt:Fuzz@ch-cascade@4` is the fourth form and it exists for the same
    reason. `Fuzz`'s second character is a CONSTRUCTOR option too, not a
    macro, so `rebuilt:Fuzz@4` - the patch whose name is "Cascade scoop
    centred" - builds the germanium graph and applies cascade's macro
    positions to it. Its pack prices cascade at two `Waveshaper` nodes
    against germanium's one, and without this form the board would measure
    the cheap graph and report it as the expensive one. The suffixes may be
    combined in any order: `@ch-cascade@os2@4`.
    """
    options = {}
    while True:
        if "@os" in name:
            head, _, tail = name.rpartition("@os")
            digits = tail.split("@")[0]
            if digits.isdigit():
                options["oversample"] = int(digits)
                name = head + tail[len(digits):]
                continue
        if "@ch-" in name:
            head, _, tail = name.rpartition("@ch-")
            value = tail.split("@")[0]
            options["character"] = value
            name = head + tail[len(value):]
            continue
        break
    name, patch = _split_patch(name)

    def build(probe):
        from audioeffects import rebuilt
        cls = rebuilt.module_class(name)
        if cls is None:
            raise ValueError("no rebuilt module for %s" % name)
        effect = cls.create(probe.output, SAMPLE_RATE, **options)
        if patch is not None:
            effect.program_change(patch)
        return effect.output, (), (effect,)
    return build


def resolve(target):
    """`target` -> a builder, or raise with something readable.

    Accepts `source`, `node:<key>`, `effect:<Name>`, `rebuilt:<Name>`, and a
    bare name, which is treated as a node key if one matches and an effect
    otherwise. An effect or rebuilt target may carry `@<patch>` or
    `#<patch>`; `effect:<Name>@rebuilt` is the expander-branch form of
    `rebuilt:<Name>`. The
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
    if target.startswith("rebuilt:"):
        return _rebuilt(target[8:])
    if target in NODES:
        return NODES[target]
    return _effect(target)


# --- measurement -----------------------------------------------------------


# MicroPython is the target; CPython is here only so the *same* builders can
# render the same 683 ms on the desktop and produce a digest to hold a board's
# against. The timing works either way, but a desktop ms/block is not a board
# number and no table quotes it.
try:
    time.ticks_us
    _HOST = False

    def _ticks_us():
        return time.ticks_us()

    def _ticks_delta_us(start):
        return time.ticks_diff(time.ticks_us(), start)
except AttributeError:
    _HOST = True

    def _ticks_us():
        return time.perf_counter_ns() // 1000

    def _ticks_delta_us(start):
        return time.perf_counter_ns() // 1000 - start


def _mem_alloc():
    try:
        return gc.mem_alloc()
    except AttributeError:
        return 0


def _seconds_since(start):
    return _ticks_delta_us(start) / 1000000.0


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
    start = _ticks_us()
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
        start = _ticks_us()
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
    before = _mem_alloc()
    output, extras, keep = build(probe)
    gc.collect()
    after = _mem_alloc()
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
    """The board this ran on, in the two forms that identify a firmware.

    `os.uname` is not everywhere: the unix MicroPython build does not carry
    it, so the one leg that this file exists to hold a board against used to
    lose the whole run to an `AttributeError` here. Fall back to
    `sys.implementation`, which every interpreter in this workspace has.
    """
    import os
    import sys
    build = getattr(sys.implementation, "_build", "?")
    uname = getattr(os, "uname", None)
    if uname is None:
        return ("%s %s / %s / %s"
                % (sys.implementation.name,
                   ".".join(str(part) for part in sys.implementation.version),
                   getattr(sys.implementation, "_machine", sys.platform),
                   build))
    name = uname()
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


def digests(*targets):
    """The digest of each target, several targets in ONE VM, no timing.

    `main()` is the method for a cost: one target per run, a fresh VM, a
    control beside it, and a table row that is a price. This is the other
    half of the same file and it is deliberately not that. When the question
    is which legs rendered the same bytes - a cause pass, not a cost pass -
    the timed passes are 90% of the wall clock and none of the answer, and
    four legs times a dozen nodes at three minutes apiece is a day.

    What it does NOT change is the digest: the chain is built fresh, from
    the same `Probe`, and hashed over the same first `DIGEST_BLOCKS` blocks
    by the same `_warm`. It costs no `prime()` because nothing here is a
    number that a first import could land in the middle of. A digest from
    this function and a digest from `main()` are the same 683 ms, and a
    run that quotes one against the other should say so.

    Each line is printed in two halves - the target before the render, the
    digest after it - so a host following the run sees a target start rather
    than a board going quiet, and a target that never returns leaves its own
    name on the last, unfinished line. A target that raises finishes its line
    with the error and the sweep carries on, because a missing node on one leg
    is a finding rather than a reason to lose the eleven that worked.
    """
    print("board:  %s" % identity())
    for target in targets:
        print("DIGEST\t%s\t" % target, end="")
        try:
            build = resolve(target)
            probe = Probe()
            output, extras, keep = build(probe)
            digest, _spent, _frames, _pulls = _warm(output, extras, True)
            del keep, probe, output, extras
            gc.collect()
        except Exception as exc:                       # noqa: BLE001
            print("ERROR %s: %s" % (type(exc).__name__, exc))
            continue
        print(digest)
    print("DIGESTS DONE")


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
    # The bare probe's own digest, rendered here rather than remembered, so
    # a target that handed the probe back says so on its own row. The runner
    # already refuses a silent render; a BYPASS is the other way a figure can
    # be a graph idling rather than a class working.
    if target != "source" and not target.startswith("node:"):
        probe = Probe()
        output, extras, keep = _source(probe)
        bare, _s, _f, _p = _warm(output, extras, True)
        del keep, probe, output, extras
        gc.collect()
        if bare == measured["digest"]:
            print("BYPASS: identical to the bare probe's digest (%s) - this "
                  "target handed the probe back and the figure above is a "
                  "graph idling, not this class working" % bare)
            raise RuntimeError(
                "BYPASS: %s rendered the bare probe's own digest (%s), so this "
                "run measures a graph idling and not the class. Name a patch "
                "that processes - `%s@<patch>` - and run it again."
                % (target, measured["digest"], target.partition("@")[0]))
        else:
            print("not a bypass: the bare probe's digest is %s" % bare)
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
