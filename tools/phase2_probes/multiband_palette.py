"""What the palette actually offers `MultibandCompressor`, re-run at Station
A rather than carried from the seed.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/multiband_palette.py

The seed's section 4 and section 5 were written on 2026-09-06 against the
palette as it stood, and three of their claims did not survive this run. Each
one below is measured, not argued, and the dossier's Appendix P quotes these
numbers.
"""

import math
import sys
from array import array

import audiocore
import audiobiquad
import audiodynamics
import audiofilters
import audiomixer
import audioroute
import synthio

from audioeffects.rebuilt.multibandcompressor import (
    MultibandCompressor)

VENDOR = "PyDevices"

RATE = 48000
CHANNELS = 2
Q = 0.7071067811865475


def raw(values, rate=RATE, channels=CHANNELS):
    array_of = array("h")
    for value in values:
        for _ in range(channels):
            array_of.append(value)
    return audiocore.RawSample(array_of, sample_rate=rate,
                               channel_count=channels)


def pull(node, frames, channels=CHANNELS):
    out = array("h")
    while len(out) < frames * channels:
        _result, buffer = audiocore.get_buffer(node)
        data = bytes(buffer)
        if not data:
            break
        values = array("h")
        values.frombytes(data)
        out.extend(values)
    return out[:frames * channels]


def guard(source, rate=RATE, channels=CHANNELS, block=256):
    node = audiofilters.Filter(filter=None, mix=1,
                               buffer_size=block * channels * 2,
                               sample_rate=rate, channel_count=channels,
                               bits_per_sample=16, samples_signed=True)
    node.play(source, loop=False)
    return node


def sine(hz, seconds, amplitude=8000, rate=RATE):
    frames = int(seconds * rate)
    step = 2.0 * math.pi * hz / rate
    return [int(round(amplitude * math.sin(step * index)))
            for index in range(frames)]


def rms(values, start=0, stride=CHANNELS):
    total = 0.0
    count = 0
    for index in range(start, len(values), stride):
        total += float(values[index]) ** 2
        count += 1
    return math.sqrt(total / count) if count else 0.0


def last_non_zero(values):
    for index in range(len(values) - 1, -1, -1):
        if values[index]:
            return index
    return -1


def peak(values):
    top = 0
    for value in values:
        if abs(value) > top:
            top = abs(value)
    return top


# --- P1 --------------------------------------------------------------------

def p1():
    print("P1  the tail. The seed's section 4 maps the crossover onto")
    print("    `audiofilters.Filter` carrying a `synthio.Biquad` cascade.")
    print("    Tier 1's first invariant is that a decaying tail reaches")
    print("    exact zero (audioif#23), so this is the claim to test first.")
    probe = [0] * 256 + [20000] * 256 + [0] * (RATE * 3)
    for corner in (100.0, 40.0):
        for kind in ("audiobiquad", "audiofilters"):
            source = guard(raw(probe))
            if kind == "audiobiquad":
                node = source
                for _ in range(2):
                    section = audiobiquad.Biquad(
                        mode=audiobiquad.LOW_PASS, frequency=corner, Q=Q,
                        sample_rate=RATE, channel_count=CHANNELS)
                    section.play(node)
                    node = section
            else:
                node = audiofilters.Filter(
                    filter=[synthio.Biquad(synthio.FilterMode.LOW_PASS,
                                           frequency=corner, Q=Q),
                            synthio.Biquad(synthio.FilterMode.LOW_PASS,
                                           frequency=corner, Q=Q)],
                    mix=1.0, buffer_size=2048, sample_rate=RATE,
                    channel_count=CHANNELS, bits_per_sample=16,
                    samples_signed=True)
                node.play(source, loop=False)
            out = pull(node, len(probe))
            last = last_non_zero(out)
            held = peak(out[-2000:])
            print("      LOW_PASS %5.0f Hz x2, %-12s last non-zero frame "
                  "%7d of %d, held %d LSB"
                  % (corner, kind, last // CHANNELS, len(probe), held))
    print("      -> the ported cascade holds DC for ever; the float one")
    print("         arrives. The rebuild uses `audiobiquad`.")


# --- P2 --------------------------------------------------------------------

def p2():
    print()
    print("P2  the all-pass. Section 5 says the palette has none, read off")
    print("    `synthio.FilterMode`. It has one, in `audiobiquad` - but not")
    print("    the one the three-way correction needs.")
    print("      audiobiquad.MODES: %s"
          % (tuple(audiobiquad.MODES),))
    print("      audiobiquad.AllPass(stages=..., frequency=..., "
          "feedback=..., mix=...)")
    print("      MAX_STAGES %d" % audiobiquad.MAX_STAGES)
    print("      -> a cascade of FIRST-order sections. The correction the")
    print("         textbook three-way wants is a SECOND-order all-pass at")
    print("         Q = 0.7071 (it is what LP4 + HP4 sums to), and no")
    print("         palette node produces one. Section 8.1's answer stands;")
    print("         its reason does not.")


# --- P3 --------------------------------------------------------------------

def p3():
    print()
    print("P3  the detector. Section 5 says the palette's detectors are")
    print("    peak, so S2's Fig. 7 RMS detectors are out of reach.")
    probe = sine(220.0, 0.4, 9000)
    #: Two pairs, because the two detectors answer different questions and
    #: a probe that fixes the wrong quantity reads as if one of them were
    #: broken. Equal AMPLITUDE is the peak detector's fixed point; equal
    #: RMS is the RMS detector's.
    same_peak = [9000 if (index // 109) % 2 == 0 else -9000
                 for index in range(len(probe))]
    same_rms = [int(round(value / math.sqrt(2.0))) for value in same_peak]
    for detector in ("peak", "rms"):
        for square, pair in ((same_peak, "equal amplitude"),
                             (same_rms, "equal RMS")):
            _detector_pair(detector, probe, square, pair)
    print("      -> `detector=\"rms\"` is on the pin, and at equal RMS it")
    print("         gives a sine and a square the same gain where the peak")
    print("         detector does not. That is S2's Fig. 7. The rebuild")
    print("         uses it.")


def _detector_pair(detector, probe, square, pair):
    gains = []
    for material, name in ((probe, "sine"), (square, "square")):
        node = audiodynamics.Dynamics(
            audiodynamics.DYN_COMPRESS, sample_rate=RATE,
            channel_count=CHANNELS, detector=detector,
            threshold_db=-40.0, ratio=4.0, attack_ms=1.0,
            release_ms=100.0)
        node.play(guard(raw(material)))
        out = pull(node, len(material))
        start = int(0.25 * RATE) * CHANNELS
        reference = rms(material, start // CHANNELS, 1)
        gains.append((name, 20.0 * math.log10(
            rms(out, start) / reference) if reference else 0.0))
    spread = abs(gains[0][1] - gains[1][1])
    print("      detector=%-5s %-16s sine %+.2f dB, square %+.2f dB, "
          "spread %.2f dB" % (detector, pair, gains[0][1], gains[1][1],
                              spread))


# --- P4 --------------------------------------------------------------------

def p4():
    print()
    print("P4  the guard, and the ladder (the seed's V-M3, re-run).")
    for frames in (256, 8192, 16384, 20000, 32768):
        probe = [0] * 64 + [20000] + [0] * (frames - 65)
        line = []
        for use_guard in (False, True):
            source = raw(probe)
            head = guard(source) if use_guard else source
            split = audioroute.Splitter(head, taps=4)
            out = pull(split.tap(0), min(frames, 4096))
            line.append(sum(1 for value in out if value))
        print("      %6d-frame source: no guard %d non-zero, guarded %d"
              % (frames, line[0], line[1]))


# --- P5 --------------------------------------------------------------------

def p5():
    print()
    print("P5  `audiomixer`'s reset is not only a clear: it resets each")
    print("    voice's source and then PULLS A CHUNK through it. A class")
    print("    that resets its Mixer before the nodes upstream of it lands")
    print("    their ring-down in the voice buffer, where the rest of the")
    print("    walk cannot reach it.")
    probe = [0] * 480 + sine(80.0, 0.04, 26000) + [0] * int(0.2 * RATE)
    end = 480 + int(0.04 * RATE)
    for order in ("mixer first (tail-first, the natural order)",
                  "mixer last"):
        source = guard(raw(probe))
        split = audioroute.Splitter(source, taps=2)
        node = split.tap(1)
        sections = []
        for _ in range(2):
            section = audiobiquad.Biquad(mode=audiobiquad.LOW_PASS,
                                         frequency=200.0, Q=Q,
                                         sample_rate=RATE,
                                         channel_count=CHANNELS)
            section.play(node)
            sections.append(section)
            node = section
        mixer = audiomixer.Mixer(voice_count=2, sample_rate=RATE,
                                 channel_count=CHANNELS,
                                 bits_per_sample=16, samples_signed=True)
        mixer.voice[0].level = 0.0
        mixer.play(split.tap(0), voice=0, loop=True)
        mixer.voice[1].level = 1.0
        mixer.play(node, voice=1, loop=True)
        primed = peak(pull(mixer, end + 64))
        walk = ([mixer] + sections[::-1] + [source]) if "first" in order \
            else (sections[::-1] + [source] + [mixer])
        for item in walk:
            audiocore.reset_buffer(item)
        print("      %-44s primed %6d, after reset %6d"
              % (order, primed, peak(pull(mixer, 1024))))
    _p5_on_the_class(probe, end)


class _MixerResetTailFirst(MultibandCompressor):
    """The class with the Mixer moved back to the end of the walk.

    That is where owning it in build order - tail-first, as every other node
    here is owned - would have put it, so this subclass is the ordering
    decision undone and nothing else.
    """

    def _build(self, **options):
        MultibandCompressor._build(self, **options)
        index = self._nodes.index(self._mixer)
        for walk in (self._nodes, self._resets, self._deinits):
            walk.append(walk.pop(index))


def _p5_on_the_class(probe, end):
    """The same ordering question on the real class, and per band.

    Each band's figure is taken on its own instance, with the solo set
    **before** the first pull after the reset: read it after a pull and the
    residual is already gone, which reads as a clean reset and is not one.
    """
    print("      the same, on the class itself:")
    for cls, label in ((MultibandCompressor, "the class (Mixer reset last)"),
                       (_MixerResetTailFirst, "Mixer reset first")):
        effect = cls(raw(probe), sample_rate=RATE, mix=1.0)
        primed = peak(pull(effect.output, end + 64))
        effect.reset()
        total = peak(pull(effect.output, 1024))
        effect.deinit()
        per_band = []
        for band in range(3):
            solo = cls(raw(probe), sample_rate=RATE, mix=1.0)
            pull(solo.output, end + 64)
            solo.reset()
            for voice in range(solo.bands + 1):
                solo._mixer.voice[voice].level = (
                    1.0 if voice == band + 1 else 0.0)
            per_band.append(peak(pull(solo.output, 256)))
            solo.deinit()
        print("        %-30s primed %6d, after reset %6d  (per band %s)"
              % (label, primed, total,
                 ", ".join(str(value) for value in per_band)))


# --- P6 --------------------------------------------------------------------

def three_way(f_low, f_high, tones):
    results = []
    for hz in tones:
        probe = sine(hz, 0.35, 8000)
        source = guard(raw(probe))
        split = audioroute.Splitter(source, taps=4)
        mixer = audiomixer.Mixer(voice_count=4, sample_rate=RATE,
                                 channel_count=CHANNELS,
                                 bits_per_sample=16, samples_signed=True)
        mixer.voice[0].level = 0.0
        mixer.play(split.tap(0), voice=0, loop=True)
        plans = ((audiobiquad.LOW_PASS, f_low), (audiobiquad.LOW_PASS,
                                                 f_low)), \
            ((audiobiquad.HIGH_PASS, f_low), (audiobiquad.HIGH_PASS, f_low),
             (audiobiquad.LOW_PASS, f_high), (audiobiquad.LOW_PASS,
                                              f_high)), \
            ((audiobiquad.HIGH_PASS, f_high), (audiobiquad.HIGH_PASS,
                                               f_high))
        for band, plan in enumerate(plans):
            node = split.tap(band + 1)
            for mode, corner in plan:
                section = audiobiquad.Biquad(mode=mode, frequency=corner,
                                             Q=Q, sample_rate=RATE,
                                             channel_count=CHANNELS)
                section.play(node)
                node = section
            detector = audiodynamics.Dynamics(
                audiodynamics.DYN_COMPRESS, sample_rate=RATE,
                channel_count=CHANNELS, ratio=1.0, threshold_db=0.0)
            detector.play(node)
            mixer.voice[band + 1].level = 1.0
            mixer.play(detector, voice=band + 1, loop=True)
        out = pull(mixer, len(probe))
        start = int(0.20 * RATE) * CHANNELS
        reference = rms(probe, start // CHANNELS, 1)
        measured = rms(out, start)
        results.append((hz, 20.0 * math.log10(measured / reference)
                        if reference and measured else -99.0))
    return results


def p6():
    print()
    print("P6  the three-way sum on `audiobiquad`, every band at unity.")
    tones = [30, 50, 80, 100, 141, 200, 283, 400, 500, 700, 1000, 1414,
             2000, 2828, 4000, 6000, 8000, 12000, 16000, 20000]
    results = three_way(200.0, 2000.0, tones)
    print("      200/2000 Hz: " + "  ".join("%d:%+.3f" % row
                                            for row in results[:6]) + " ...")
    print("      max %+.3f  min %+.3f dB"
          % (max(value for _hz, value in results),
             min(value for _hz, value in results)))
    print("      the ratio table (worst deviation over the same tones):")
    for f_high, label in ((400.0, "2:1"), (800.0, "4:1"), (1600.0, "8:1")):
        rows = three_way(200.0, f_high, tones)
        print("        200/%-5d %s  max %+.3f  min %+.3f dB"
              % (f_high, label, max(v for _h, v in rows),
                 min(v for _h, v in rows)))


def main():
    print("MultibandCompressor palette verification, CPython, audioif pin")
    print("=" * 72)
    p1()
    p2()
    p3()
    p4()
    p5()
    p6()
    return 0


if __name__ == "__main__":
    sys.exit(main())
