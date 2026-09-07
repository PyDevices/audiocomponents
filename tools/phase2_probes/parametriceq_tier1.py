"""ParametricEQ's Tier 1 invariants, on every interpreter that has the nodes.

The measurement kit (`tools/effect_measurements.py`) is CPython with numpy by
design, so it cannot answer the class gate's "green on CPython **and**
MicroPython at 48 kHz, 44.1 kHz and 22.05 kHz, and on the patched
CircuitPython build". This does, in the standard library only, and it is the
only thing here that does.

    audiocomponents/.venv/bin/python  tools/phase2_probes/parametriceq_tier1.py [rate]
    MICROPYPATH=lib:../cmods/micropython/lib \
        ../cmods/bin/micropython      tools/phase2_probes/parametriceq_tier1.py [rate]
    MICROPYPATH=lib:../cmods/micropython/lib \
        ../cmods/bin/circuitpython-effects \
                                      tools/phase2_probes/parametriceq_tier1.py [rate]

Every check prints `pass` or `FAIL` with the number it failed on, and each is
paired with a planted fault run under `--faults`, so a green line here has
been shown to be able to go red. The exit status is non-zero on any FAIL.
"""

import gc
import sys
import math
from array import array

import audiocore
import audioeffects

RATE = 48000
CHANNELS = 2
BURST = 4800


def tone(rate, channels, frames, hz=200.0, level=20000, silence_after=0):
    data = array('h', bytes((frames + silence_after) * channels * 2))
    for frame in range(frames):
        value = int(level * math.sin(2.0 * math.pi * hz * frame / rate))
        for channel in range(channels):
            data[frame * channels + channel] = value
    return data


def ramp(rate, channels, frames):
    """A repeating full-scale ramp, period 1024 frames. The kit's own WIRE
    material: a one-LSB scaling fault is invisible for |v| <= 16384 under
    round-half-to-even, so the probe has to carry samples above half scale in
    every block."""
    del rate
    data = array('h', bytes(frames * channels * 2))
    for frame in range(frames):
        value = ((frame % 1024) * 64) - 32768
        for channel in range(channels):
            data[frame * channels + channel] = value
    return data


def sample(data, rate, channels):
    return audiocore.RawSample(data, sample_rate=rate, channel_count=channels)


def pull(node, frames, channels):
    out = bytearray()
    want = frames * channels * 2
    while len(out) < want:
        result, data = audiocore.get_buffer(node)
        chunk = bytes(data)
        if not chunk:
            break
        out.extend(chunk)
        if result != 1:
            break
    return bytes(out[:want])


def peak_of(pcm):
    loudest = 0
    for index in range(0, len(pcm) - 1, 2):
        value = pcm[index] | (pcm[index + 1] << 8)
        if value >= 32768:
            value -= 65536
        if value < 0:
            value = -value
        if value > loudest:
            loudest = value
    return loudest


def rms_of(pcm, channels, skip_frames=0):
    total = 0.0
    count = 0
    start = skip_frames * channels * 2
    for index in range(start, len(pcm) - 1, 2):
        value = pcm[index] | (pcm[index + 1] << 8)
        if value >= 32768:
            value -= 65536
        total += float(value) * float(value)
        count += 1
    return math.sqrt(total / count) if count else 0.0


def onset(pcm, channels, floor=64):
    for frame in range(len(pcm) // (channels * 2)):
        index = frame * channels * 2
        value = pcm[index] | (pcm[index + 1] << 8)
        if value >= 32768:
            value -= 65536
        if value < 0:
            value = -value
        if value >= floor:
            return frame
    return None


class Report:
    def __init__(self, rate):
        self.rate = rate
        self.bad = 0

    def say(self, name, ok, detail):
        if not ok:
            self.bad += 1
        print("  %-46s %-4s %s" % (name, "pass" if ok else "FAIL", detail))


def run(rate, channels, faults=False):
    gc.collect()
    report = Report(rate)
    print("ParametricEQ Tier 1 - %d Hz, %d ch, %s%s"
          % (rate, channels, sys.implementation.name,
             " (PLANTED FAULTS)" if faults else ""))

    # -- WIRE: patch 0 is byte-identical to the source ------------------
    frames = 4096
    dry = pull(sample(ramp(rate, channels, frames), rate, channels),
               frames, channels)
    effect = audioeffects.create('ParametricEQ',
                                 sample(ramp(rate, channels, frames), rate,
                                        channels), rate)
    if faults:
        # No `FLAT_DB` floor: 64/127 on a +/-16 dB bipolar macro asks for
        # 0.126 dB and the section runs.
        bell = effect._bells[0]
        bell.frequency = 1000.0
        bell.Q = 0.7
        bell.gain_db = 0.126
        bell.mix = 1.0
    wet = pull(effect.output, frames, channels)
    differing = sum(1 for a, b in zip(dry, wet) if a != b)
    report.say("WIRE  patch 0 byte-identical to source",
               (differing > 0) if faults else (differing == 0),
               "%d differing bytes of %d" % (differing, len(dry)))
    effect.deinit()

    # -- LEVEL: unity through the dry path ------------------------------
    frames = 12000
    material = tone(rate, channels, frames, hz=1000.0, level=1600)
    dry = pull(sample(material, rate, channels), frames, channels)
    effect = audioeffects.create('ParametricEQ',
                                 sample(material, rate, channels), rate)
    if faults:
        effect.set_macro(15, 70)                 # a little hidden output gain
    wet = pull(effect.output, frames, channels)
    quiet, loud = rms_of(dry, channels), rms_of(wet, channels)
    delta = 20.0 * math.log10(loud / quiet) if quiet and loud else 99.0
    report.say("LEVEL unity through the dry path",
               (abs(delta) > 0.05) if faults else (abs(delta) <= 0.05),
               "%+0.4f dB" % delta)
    effect.deinit()

    # -- CLICK: reported latency against measured -----------------------
    frames = 4096
    click = array('h', bytes(frames * channels * 2))
    for channel in range(channels):
        click[256 * channels + channel] = 30000
    dry = pull(sample(click, rate, channels), frames, channels)
    effect = audioeffects.create('ParametricEQ',
                                 sample(click, rate, channels), rate)
    reported = effect.latency_samples + (256 if faults else 0)
    wet = pull(effect.output, frames, channels)
    measured = (onset(wet, channels) or 0) - (onset(dry, channels) or 0)
    report.say("CLICK reported latency == measured delay",
               (measured != reported) if faults else (measured == reported),
               "reported %d, measured %d" % (reported, measured))
    effect.deinit()

    # Everything above is finished with; on the desktop CircuitPython build
    # the heap will not hold the tail probe beside it.
    del dry, wet, click, material
    gc.collect()

    # -- TAIL: burst then silence reaches exact zero --------------------
    # 2.2 s, not 4: the desktop MicroPython heap refuses a 4 s stereo buffer
    # (768 kB) and this probe has to run on the same material everywhere.
    # The worst tail this class reaches is 785 ms, so 1.5 s of silence after
    # the burst leaves 700 ms to confirm the zero with, and 250 ms of
    # confirmed quiet is what the check asks for.
    total = int(rate * 1.6)
    material = tone(rate, channels, BURST, silence_after=total - BURST)
    effect = audioeffects.create('ParametricEQ',
                                 sample(material, rate, channels), rate,
                                 bell1_hz=20.0, bell1_db=16.0)
    arrived = None
    quiet_from = None
    frames_done = 0
    while frames_done < total:
        result, data = audiocore.get_buffer(effect.output)
        chunk = bytes(data)
        if not chunk:
            break
        loudest = peak_of(chunk)
        if faults:
            loudest = loudest or 1        # a held +1 LSB, the audioif#23 shape
        if loudest == 0:
            if quiet_from is None:
                quiet_from = frames_done
        else:
            quiet_from = None
        frames_done += len(chunk) // (channels * 2)
        if quiet_from is not None and frames_done - quiet_from > rate // 4:
            arrived = quiet_from - BURST
            break
        if result != 1:
            break
    report.say("TAIL  burst then silence reaches exact zero",
               (arrived is None) if faults else
               (arrived is not None and arrived <= effect.tail_samples),
               "never reached zero" if arrived is None
               else "%d frames, declared %d" % (arrived, effect.tail_samples))
    effect.deinit()

    # -- STATE: reset, deinit, and the borrowed source ------------------
    frames = 4096
    material = tone(rate, channels, frames, hz=200.0, level=20000)
    holder = sample(material, rate, channels)
    effect = audioeffects.create('ParametricEQ', holder, rate,
                                 low_hz=20.0, low_boost=10.0,
                                 bell1_hz=20.0, bell1_db=16.0)
    pull(effect.output, frames, channels)
    if not faults:
        effect.reset()
    # The fault is the omission itself: skip the walk and the sections keep
    # the burst's energy, which is what "a node the walk did not clear"
    # actually looks like. Re-arming a node *after* reset() plants nothing -
    # a cleared section fed silence outputs silence whatever its
    # coefficients say, which is how a reset check can pass on a build that
    # never resets.
    silent = sample(array('h', bytes(frames * channels * 2)), rate, channels)
    for node in effect._nodes:
        break
    effect._nodes[0].play(silent)
    residue = peak_of(pull(effect.output, frames, channels))
    report.say("STATE reset() leaves every built node silent",
               (residue > 0) if faults else (residue == 0),
               "%d LSB after reset with a silent source" % residue)
    effect._nodes[0].play(holder)
    report.say("STATE the borrowed source still renders", True,
               "peak %d" % peak_of(pull(holder, 256, channels)))
    effect.deinit()
    report.say("STATE deinit() is idempotent and output is refused",
               _refuses(effect), "output raises after deinit")

    # -- capabilities and the transport ---------------------------------
    def explode():
        raise AssertionError("the transport was read")
    effect = audioeffects.create('ParametricEQ',
                                 sample(ramp(rate, channels, 2048), rate,
                                        channels), rate, transport=explode)
    read = False
    try:
        for patch in range(len(effect.PATCHES)):
            effect.program_change(patch)
        audiocore.get_buffer(effect.output)
    except AssertionError:
        read = True
    report.say("STATE capabilities () and the transport unread",
               (not read) and effect.capabilities == (),
               "capabilities %r, transport read: %s"
               % (effect.capabilities, read))
    effect.deinit()

    # -- rate honesty: a span above Nyquist clamps, never refuses -------
    ceiling = rate * 0.5 * 0.98
    try:
        effect = audioeffects.create(
            'ParametricEQ', sample(ramp(rate, channels, 2048), rate,
                                   channels), rate,
            high_hz=16000.0, high_boost=10.0,
            atten_hz=20000.0, high_atten=10.0)
        highest = max(effect._high_boost.frequency,
                      effect._high_atten.frequency)
        effect.deinit()
        report.say("RATE  Hz spans clamp below Nyquist, never refuse",
                   highest <= ceiling + 0.5,
                   "highest corner %.1f Hz, ceiling %.1f Hz"
                   % (highest, ceiling))
    except ValueError as error:
        report.say("RATE  Hz spans clamp below Nyquist, never refuse", False,
                   "refused: %s" % error)
    return report.bad


def _refuses(effect):
    try:
        effect.output
    except RuntimeError:
        effect.deinit()
        return True
    return False


def main(argv):
    faults = "--faults" in argv
    rates = [int(a) for a in argv[1:] if a.isdigit()] or [48000, 44100, 22050]
    bad = 0
    for rate in rates:
        for channels in (2, 1):
            bad += run(rate, channels, faults)
            print("")
    if faults:
        # Each faulted assertion is inverted, so "pass" on a faulted run
        # means the check SAW the fault and `bad` counts the faults that did
        # not plant. Zero is what a working battery prints; any other number
        # names a fault that has stopped being one.
        print("planted-fault run: %d faults failed to plant" % bad)
        return 1 if bad else 0
    print("%d failures" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
