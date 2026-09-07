"""GraphicEQ Station C: every number in `docs/effects/GraphicEQ-evidence.md`.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/graphiceq_evidence.py

CPython only, with numpy, because the analysis is (`docs/effects-kit-spec.md`
section 1: the render is dual-runtime, the analysis is not). The other two
interpreters are reached through `tools/render_effect.py`, whose digests the
pack's section 3 carries -- and byte-identical renders are what lets a Tier 1
row measured here stand for all three.

Every Tier 2 trait is followed by a planted fault **of the same kind**: not a
different bug that happens to be red, but the specific thing the trait denies.
The clean run beside it is the control, because a battery with no control only
proves the checker always fails.
"""

import math
import os
import sys
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))
sys.path.insert(0, ROOT)

import audiobiquad                                          # noqa: E402
import audiocore                                            # noqa: E402
import audioeffects                                         # noqa: E402
import numpy as np                                          # noqa: E402
from kit_probes import ArraySource, render                  # noqa: E402
from tools import effect_measurements as kit                # noqa: E402

RATE = 48000
CHANNELS = 2
BANDS = 10
DETENT = 64

#: gain in dB -> the MIDI code for a +/-12 dB band macro.
def code(db):
    return int(round((db + 12.0) / 24.0 * 127.0))


def grid(low, high, per_octave):
    points, octaves = [], math.log(high / low, 2.0)
    for step in range(int(round(octaves * per_octave)) + 1):
        points.append(low * (2.0 ** (step / float(per_octave))))
    return points


def tone(hz, seconds, rate=RATE, channels=CHANNELS, peak=6000):
    frames = int(rate * seconds)
    data = array("h", bytes(2 * channels * frames))
    for index in range(frames):
        value = int(peak * math.sin(2.0 * math.pi * hz * index / rate))
        for channel in range(channels):
            data[index * channels + channel] = value
    return data


def noise(frames, peak=8000, seed=12345, channels=CHANNELS):
    data = array("h", bytes(2 * channels * frames))
    state = seed
    for index in range(frames):
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        value = int(peak * (2.0 * (state / 0x7FFFFFFF) - 1.0))
        for channel in range(channels):
            data[index * channels + channel] = value
    return data


def burst_then_silence(hz, on_s, total_s, rate=RATE, peak=20000,
                       channels=CHANNELS):
    """The silence is inside the sample. A probe that lets the source *end*
    reads exact zeros for every configuration, including the dirty ones."""
    frames = int(rate * total_s)
    on = int(rate * on_s)
    data = array("h", bytes(2 * channels * frames))
    for index in range(on):
        value = int(peak * math.sin(2.0 * math.pi * hz * index / rate))
        for channel in range(channels):
            data[index * channels + channel] = value
    return data, on


def click(offset, frames, rate=RATE, channels=CHANNELS, peak=20000):
    data = array("h", bytes(2 * channels * frames))
    for channel in range(channels):
        data[offset * channels + channel] = peak
    return data


_DRY = {}


def dry(hz, seconds, rate=RATE, channels=CHANNELS):
    key = (round(hz, 4), seconds, rate, channels)
    if key not in _DRY:
        data = tone(hz, seconds, rate, channels)
        _DRY[key] = render(ArraySource(data, rate=rate, channels=channels),
                           int(rate * seconds), rate=rate, channels=channels)
    return _DRY[key]


def build(data, rate=RATE, channels=CHANNELS, macros=(), patch=None,
          plant=None, **options):
    source = ArraySource(data, rate=rate, channels=channels)
    effect = audioeffects.create("GraphicEQ", source, rate, **options)
    if patch is not None:
        effect.program_change(patch)
    for index, value in macros:
        effect.set_macro(index, value)
    if plant is not None:
        plant(effect)
    return effect


def run(data, frames, rate=RATE, channels=CHANNELS, **kwargs):
    effect = build(data, rate=rate, channels=channels, **kwargs)
    try:
        audiocore.reset_buffer(effect.output)
        return render(effect.output, frames, rate=rate, channels=channels,
                      class_name="GraphicEQ",
                      latency_samples=effect.latency_samples)
    finally:
        effect.deinit()


def curve(points, seconds, label, rate=RATE, **kwargs):
    """{hz: Render} wet and dry, one steady tone at a time."""
    wet, ref = {}, {}
    for hz in points:
        if hz >= rate * 0.45:
            continue
        data = tone(hz, seconds, rate)
        wet[hz] = run(data, int(rate * seconds), rate=rate, **kwargs)
        ref[hz] = dry(hz, seconds, rate)
    sys.stderr.write("  swept %s (%d points)\n" % (label, len(wet)))
    return wet, ref


def magnitudes(wet, ref, settled=0.6):
    result = kit.response(wet, ref, settled_ratio=settled)
    return [(row["hz"], row["magnitude_db"]) for row in result["values"]["grid"]]


def at(points, hz):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return kit._interpolate_log(xs, ys, hz)


def peak_of(points):
    best = max(points, key=lambda p: p[1])
    return best[0], best[1]


def span_octaves(points, level):
    """Width in octaves of the region above `level`, around the peak."""
    hz_peak, _ = peak_of(points)
    below = [p for p in points if p[0] <= hz_peak]
    above = [p for p in points if p[0] >= hz_peak]
    low = kit._crossing([p[0] for p in below], [p[1] for p in below], level)
    high = kit._crossing([p[0] for p in above], [p[1] for p in above], level)
    if low is None or high is None:
        return None, low, high
    return math.log(high / low, 2.0), low, high


def band_width(points, gain_db):
    """Mid-gain bandwidth in octaves, and the first +1 dB crossing."""
    width, low, high = span_octaves(points, gain_db / 2.0)
    _, edge_low, _ = span_octaves(points, 1.0)
    return width, low, high, edge_low


def line(text=""):
    print(text)


# ---------------------------------------------------------------- Tier 2 ---

FULL = grid(20.0, 22000.0, 8)
MID = grid(125.0, 8000.0, 12)
LONG, SHORT = 0.5, 0.25


def trait_one():
    line("## T1  the top band is a shelf, the other nine are bells")
    shelf = magnitudes(*curve(FULL, LONG, "16k shelf +12",
                              macros=((9, 127),)))
    bell = magnitudes(*curve(FULL, LONG, "8k bell +12", macros=((8, 127),)))
    at16, at20 = at(shelf, 16000.0), at(shelf, 20000.0)
    bell_hz, bell_db = peak_of(bell)
    bell16 = at(bell, 16000.0)
    line("   shelf: %.2f dB at 16 kHz, %.2f dB at 20 kHz, drop %.2f dB "
         "(bar 1.50), level bar +9.00" % (at16, at20, at16 - at20))
    line("   8k bell: peak %.2f dB at %.0f Hz, %.2f dB at 16 kHz, "
         "down %.2f dB (bar 6.00)"
         % (bell_db, bell_hz, bell16, bell_db - bell16))
    ok = abs(at16 - at20) <= 1.5 and at20 >= 9.0 and (bell_db - bell16) >= 6.0
    line("   VERDICT %s" % ("demonstrated" if ok else "DISCONFIRMED"))

    line("   planted fault -- the top band built as a bell, not a shelf:")

    def as_bell(effect):
        effect._sections[9].deinit()
        node = audiobiquad.Biquad(mode=audiobiquad.PEAKING_EQ,
                                  frequency=16000.0, Q=1.4, gain_db=12.0,
                                  mix=1.0, sample_rate=effect.sample_rate,
                                  channel_count=effect.channel_count)
        node.play(effect._sections[8])
        effect._sections[9] = node
        effect._nodes[effect._nodes.index(effect._volume) - 1] = node
        effect._volume.play(node)

    faulted = magnitudes(*curve([12000.0, 16000.0, 20000.0], LONG,
                                "T1 fault", macros=((9, 127),), plant=as_bell))
    f16, f20 = at(faulted, 16000.0), at(faulted, 20000.0)
    line("   faulted: %.2f dB at 16 kHz, %.2f dB at 20 kHz, drop %.2f dB "
         "-> %s" % (f16, f20, f16 - f20,
                    "RED" if abs(f16 - f20) > 1.5 else "still green"))
    line()


def trait_two():
    line("## T2  proportional Q -- the bands narrow as the slider travels")
    rows = []
    for gain in (3.0, 6.0, 12.0):
        points = magnitudes(*curve(MID, SHORT, "1k band %+g dB" % gain,
                                   macros=((5, code(gain)),)))
        width, low, high, edge = band_width(points, gain)
        rows.append((gain, width, edge, at(points, 1000.0)))
        line("   %+5.1f dB: peak %.2f dB, mid-gain width %.3f oct "
             "(%.1f..%.1f Hz), first +1 dB crossing %.1f Hz"
             % (gain, rows[-1][3], width or -1, low or -1, high or -1,
                edge or -1))
    drift = abs(rows[2][2] - rows[0][2]) / rows[0][2] * 100.0
    ok = (rows[0][1] >= 1.5 and rows[2][1] <= 0.8 and drift < 10.0)
    line("   +3 dB width %.3f oct (bar >= 1.5); +12 dB width %.3f oct "
         "(bar <= 0.8); crossing moved %.2f %% (bar < 10)"
         % (rows[0][1], rows[2][1], drift))
    line("   VERDICT %s" % ("demonstrated" if ok else "DISCONFIRMED"))

    line("   planted fault -- Constant Q on, which is the trait's own limit:")
    faults = []
    for gain in (3.0, 12.0):
        points = magnitudes(*curve(MID, SHORT, "constant Q %+g dB" % gain,
                                   macros=((13, 127), (5, code(gain)))))
        width, _, _, _ = band_width(points, gain)
        faults.append(width)
        line("   %+5.1f dB constant Q: width %.3f oct" % (gain, width or -1))
    line("   widths %.3f and %.3f -> %s"
         % (faults[0], faults[1],
            "RED" if faults[0] < 1.5 else "still green"))
    line()


def trait_three():
    line("## T3  adjacent bands overshoot when summed")
    macros = ((4, code(6.0)), (5, code(6.0)), (6, code(6.0)))
    points = magnitudes(*curve(MID, SHORT, "500/1k/2k at +6", macros=macros))
    hz_peak, db_peak = peak_of(points)
    width, low, high = span_octaves(points, db_peak - 3.0)
    line("   combined peak %.2f dB at %.0f Hz (bar >= 9.00); "
         "-3 dB span %.3f oct (%.0f..%.0f Hz, bar > 2.00)"
         % (db_peak, hz_peak, width or -1, low or -1, high or -1))
    ok = db_peak >= 9.0 and (width or 0) > 2.0
    line("   VERDICT %s" % ("demonstrated" if ok else "DISCONFIRMED"))

    line("   planted fault -- Band Q at its narrowest, so the bands do not "
         "overlap:")
    faulted = magnitudes(*curve(MID, SHORT, "T3 fault",
                                macros=((13, 127), (12, 127)) + macros))
    hz_f, db_f = peak_of(faulted)
    width_f, _, _ = span_octaves(faulted, db_f - 3.0)
    line("   faulted peak %.2f dB, -3 dB span %.3f oct -> %s"
         % (db_f, width_f or -1,
            "RED" if db_f < 9.0 or (width_f or 0) <= 2.0 else "still green"))
    line()


def trait_four():
    line("## T4  a band at zero is out of the circuit")
    line("   The comparison is against the chain with that section taken "
         "out of it, not against the same chain twice: section k+1 is "
         "played from section k-1, so the reference really is eleven "
         "sections and not twelve.")
    data = noise(24000)
    rails = [(index, 127 if index % 2 else 0) for index in range(BANDS)]

    def without(band, rate):
        """Render the class's own chain with section `band` unlinked."""
        settings = [entry for entry in rails if entry[0] != band]
        effect = build(data, rate=rate, macros=settings + [(band, DETENT)])
        try:
            sections = effect._nodes
            position = sections.index(effect._sections[band])
            sections[position + 1].play(sections[position - 1])
            effect._output = effect._volume
            audiocore.reset_buffer(effect._output)
            return render(effect._output, 24000, rate=rate)
        finally:
            effect.deinit()

    verdict = True
    for rate in (48000, 44100):
        for band in (0, 1, 5, 9):
            settings = [entry for entry in rails if entry[0] != band]
            intact = run(data, 24000, rate=rate,
                         macros=settings + [(band, DETENT)])
            reference = without(band, rate)
            same = intact.digest == reference.digest
            verdict = verdict and same
            line("   %5d Hz band %d: detented %08x, eleven sections %08x "
                 "-> %s" % (rate, band, intact.digest, reference.digest,
                            "identical" if same else "DIFFER"))
    line("   VERDICT %s" % ("demonstrated" if verdict else "DISCONFIRMED"))

    line("   planted fault -- the detented band left unmuted (mix = 1). It "
         "has to be planted at the *bottom* of the bank: a flat section is "
         "already bit-transparent from 250 Hz up, so the same fault at "
         "1 kHz is invisible and the check would pass either way.")
    for band in (0, 5):
        def unmute(effect, which=band):
            effect._sections[which].mix = 1.0

        settings = [entry for entry in rails if entry[0] != band]
        faulted = run(data, 24000, macros=settings + [(band, DETENT)],
                      plant=unmute)
        control = run(data, 24000, macros=settings + [(band, DETENT)])
        line("     band %d: faulted %08x against %08x -> %s"
             % (band, faulted.digest, control.digest,
                "RED" if faulted.digest != control.digest
                else "still green"))
    line("   how far a flat-but-unmuted section drifts, per centre:")
    for band, hz in ((0, 31.25), (1, 62.5), (2, 125.0), (3, 250.0)):
        node = audiobiquad.Biquad(mode=audiobiquad.PEAKING_EQ, frequency=hz,
                                  Q=1.4, gain_db=0.0, sample_rate=RATE,
                                  channel_count=CHANNELS)
        node.play(ArraySource(data))
        audiocore.reset_buffer(node)
        wet = render(node, 24000)
        node.deinit()
        reference = render(ArraySource(data), 24000)
        worst = int(np.abs(wet.data.astype(np.int32)
                           - reference.data.astype(np.int32)).max())
        line("     band %d at %8.2f Hz: worst %d LSB" % (band, hz, worst))
    line()


def trait_five():
    line("## T5  all ten together are smooth but hot")
    macros = tuple((index, code(6.0)) for index in range(BANDS))
    points = magnitudes(*curve(FULL, LONG, "all ten at +6", macros=macros))
    band = [p for p in points if 60.0 <= p[0] <= 8000.0]
    ripple = max(p[1] for p in band) - min(p[1] for p in band)
    mean = sum(p[1] for p in band) / len(band)
    line("   60 Hz - 8 kHz: ripple %.3f dB peak-to-peak (bar < 2.00), "
         "mean %.2f dB (bar > 9.00), %d points"
         % (ripple, mean, len(band)))
    ok = ripple < 2.0 and mean > 9.0
    line("   VERDICT %s" % ("demonstrated" if ok else "DISCONFIRMED"))

    line("   planted fault -- Constant Q at the narrowest, so the bands no "
         "longer fill between their centres:")
    faulted = magnitudes(*curve(FULL, LONG, "T5 fault",
                                macros=((13, 127), (12, 127)) + macros))
    band_f = [p for p in faulted if 60.0 <= p[0] <= 8000.0]
    ripple_f = max(p[1] for p in band_f) - min(p[1] for p in band_f)
    mean_f = sum(p[1] for p in band_f) / len(band_f)
    line("   faulted ripple %.3f dB, mean %.2f dB -> %s"
         % (ripple_f, mean_f,
            "RED" if ripple_f >= 2.0 or mean_f <= 9.0 else "still green"))
    line()


def anchor_sweep():
    """T2, T3 and T5 at a second `Band Q`, because they pull against it.

    T2 wants the +12 dB band narrow; T3 and T5 want the bands wide enough to
    overlap and add at +6 dB. `Q` scales with the anchor, so one number cannot
    be moved in both directions -- this leg reports all three traits at
    `Band Q` 1.5 beside the default 2.0 so the reader can see the trade
    rather than take it on faith.
    """
    line("## The Band Q trade -- T2, T3 and T5 at anchor 1.5")
    anchor = _component_macro_code(1.5)
    for gain in (3.0, 12.0):
        points = magnitudes(*curve(MID, SHORT, "anchor 1.5, 1k %+g dB" % gain,
                                   macros=((12, anchor), (5, code(gain)))))
        width, low, high, edge = band_width(points, gain)
        line("   T2 at %+5.1f dB: width %.3f oct (%.1f..%.1f Hz)"
             % (gain, width or -1, low or -1, high or -1))
    three = ((4, code(6.0)), (5, code(6.0)), (6, code(6.0)))
    points = magnitudes(*curve(MID, SHORT, "anchor 1.5, 500/1k/2k",
                               macros=((12, anchor),) + three))
    hz_peak, db_peak = peak_of(points)
    width, low, high = span_octaves(points, db_peak - 3.0)
    line("   T3: peak %.2f dB at %.0f Hz, -3 dB span %.3f oct"
         % (db_peak, hz_peak, width or -1))
    ten = tuple((index, code(6.0)) for index in range(BANDS))
    points = magnitudes(*curve(FULL, LONG, "anchor 1.5, all ten",
                               macros=((12, anchor),) + ten))
    band = [p for p in points if 60.0 <= p[0] <= 8000.0]
    line("   T5: ripple %.3f dB, mean %.2f dB"
         % (max(p[1] for p in band) - min(p[1] for p in band),
            sum(p[1] for p in band) / len(band)))
    line()


def _component_macro_code(value):
    from audioeffects import _component
    return _component.macro_of(
        audioeffects.GraphicEQ._MACRO_RANGES[12], value)


# ---------------------------------------------------------------- Tier 1 ---

def tier_one():
    line("## Tier 1 invariants")
    for rate in (48000, 44100, 22050):
        for channels in (2, 1):
            data = noise(int(rate * 0.5), channels=channels)
            reference = render(ArraySource(data, rate=rate,
                                           channels=channels),
                               int(rate * 0.5), rate=rate, channels=channels)
            wet = run(data, int(rate * 0.5), rate=rate, channels=channels)
            result = kit.wire(wet, reference)
            line("   WIRE  %5d Hz %dch  patch 0: %d of %d samples differ  %s"
                 % (rate, channels, result["values"]["differing_samples"],
                    result["values"]["compared_samples"],
                    "pass" if result["passed"] else "FAIL"))

    line("   WIRE planted fault -- the dry path scaled by 32767/32768:")
    data = noise(24000)
    reference = render(ArraySource(data), 24000)
    scaled = array("h", (int(v * 32767 // 32768) for v in
                         array("h", data.tobytes())))
    faulted = render(ArraySource(scaled), 24000)
    result = kit.wire(faulted, reference)
    line("     %d of %d samples differ -> %s"
         % (result["values"]["differing_samples"],
            result["values"]["compared_samples"],
            "RED" if not result["passed"] else "still green"))

    for rate in (48000, 44100, 22050):
        for channels in (2, 1):
            data, on = burst_then_silence(200.0, 0.1, 1.6, rate=rate,
                                          channels=channels)
            macros = tuple((index, code(6.0)) for index in range(BANDS))
            wet = run(data, int(rate * 1.6), rate=rate, channels=channels,
                      macros=macros)
            effect = build(data, rate=rate, channels=channels)
            declared = effect.tail_samples
            effect.deinit()
            result = kit.tail(wet, burst_end_frame=on,
                              declared_tail_samples=declared)
            line("   TAIL  %5d Hz %dch  all +6: tail %s frames, residual "
                 "%d LSB, declared %d  %s"
                 % (rate, channels, result["values"]["tail_samples"],
                    result["values"]["residual_lsb"], declared,
                    "pass" if result["passed"] else "FAIL"))

    line("   TAIL positive control -- the same probe on the ported bank:")
    import audiofilters
    import synthio
    data, on = burst_then_silence(200.0, 0.1, 1.6)
    sections = [synthio.Biquad(synthio.FilterMode.PEAKING_EQ,
                               31.25 * 2 ** n, Q=1.4,
                               A=10.0 ** (6.0 / 40.0)) for n in range(BANDS)]
    node = audiofilters.Filter(filter=tuple(sections), mix=1.0,
                               sample_rate=RATE, channel_count=CHANNELS,
                               bits_per_sample=16, samples_signed=True,
                               buffer_size=2048)
    node.play(ArraySource(data))
    audiocore.reset_buffer(node)
    ported = render(node, int(RATE * 1.6))
    node.deinit()
    result = kit.tail(ported, burst_end_frame=on)
    line("     residual %d LSB -> %s"
         % (result["values"]["residual_lsb"],
            "RED" if not result["passed"] else "still green"))

    for rate in (48000, 44100):
        data = click(4096, int(rate * 0.3), rate=rate)
        reference = render(ArraySource(data, rate=rate), int(rate * 0.3),
                           rate=rate)
        wet = run(data, int(rate * 0.3), rate=rate,
                  macros=((5, code(6.0)),))
        result = kit.click(wet, reference, 0, subsample=False)
        fine = kit.click(wet, reference, 0, subsample=True)
        line("   CLICK %5d Hz: reported 0, measured %s integer / %s "
             "sub-sample  %s"
             % (rate, result["values"]["measured_latency_samples"],
                fine["values"]["measured_latency_samples"],
                "pass" if result["passed"] else "FAIL"))

    line("   CLICK planted fault -- latency reported 256 short:")
    result = kit.click(wet, reference, 256, subsample=False)
    line("     %s -> %s" % (result["red"] or "no complaint",
                            "RED" if not result["passed"] else "still green"))

    # The level sections are HIGH_SHELFs at 5 Hz, so they take a third of a
    # second to charge from a cold start. LEVEL is the *settled* gain, and
    # skipping less than that measures the charge instead: the first run of
    # this file read 3.5 dB of error on a 0.5 s tone with no skip, which is
    # the transient and not the gain. The settling is measured on its own,
    # below, rather than hidden in the skip.
    for rate in (48000, 44100, 22050):
        for macro, want in ((10, 12.0), (11, -12.0)):
            worst, rows = 0.0, []
            for hz in (100.0, 1000.0, 8000.0):
                if hz >= rate * 0.45:
                    continue
                # The same peak as `dry()` uses, or the comparison measures
                # the probe level instead of the macro: the first run of this
                # file drove 4000 against a 6000 reference and read every
                # level 3.52 dB low, which is 20*log10(4000/6000).
                data = tone(hz, 1.2, rate)
                reference = dry(hz, 1.2, rate)
                wet = run(data, int(rate * 1.2), rate=rate,
                          macros=((macro, code(want)),))
                result = kit.level(wet, reference, tolerance_db=99.0,
                                   skip_frames=int(rate * 0.6))
                got = result["values"]["rms_db"][0]
                rows.append("%.0f Hz %+.3f" % (hz, got))
                worst = max(worst, abs(got - want))
            line("   LEVEL %5d Hz macro %d at %+g dB: %s -- worst error "
                 "%.3f dB %s" % (rate, macro, want, ", ".join(rows), worst,
                                 "pass" if worst < 0.2 else "FAIL"))

    line("   LEVEL settling -- how long the 5 Hz level shelf takes to reach "
         "its stated gain from a cold start, 1 kHz:")
    data = tone(1000.0, 1.2, RATE)
    reference = dry(1000.0, 1.2, RATE)
    wet = run(data, int(RATE * 1.2), macros=((10, code(12.0)),))
    window = 2400
    settled = None
    for start in range(0, int(RATE * 1.0), window):
        got = kit.rms_db(wet.float[start:start + window, 0]) \
            - kit.rms_db(reference.float[start:start + window, 0])
        if abs(got - 12.0) < 0.2 and settled is None:
            settled = start
    line("     within 0.2 dB of +12.00 from frame %s (%.0f ms)"
         % (settled, 1000.0 * (settled or 0) / RATE))
    line()


def state_leg():
    line("## STATE -- reset, deinit, capabilities, allocation")
    data = noise(24000)
    probe = ArraySource(data)
    silent = ArraySource(array("h", bytes(2 * CHANNELS * 24000)))
    effect = audioeffects.create("GraphicEQ", probe, RATE)
    effect.program_change(5)

    def pull(blocks):
        return render(effect.output, blocks * 256)

    def swap(source):
        effect._gain.play(source)

    try:
        # `kit.enumerate_nodes` walks *public* attributes, and the
        # construction module's whole point is that a class enumerates its
        # own nodes with `_own()`. `_nodes` is that list, in build order, and
        # it is the one `reset()` and `deinit()` actually walk -- so it is
        # handed over rather than guessed at.
        named = [("section[%d]" % index, node)
                 for index, node in enumerate(effect._nodes)]
        result = kit.state(effect, pull=pull, swap=swap, probe_source=probe,
                           silent_source=silent, blocks=32, nodes=named)
        for key in sorted(result["values"]):
            line("   %-28s %s" % (key, result["values"][key]))
        line("   %s" % ("pass" if result["passed"]
                        else "FAIL: " + "; ".join(result["red"])))
    finally:
        if not effect._deinited:
            effect.deinit()
    line()


def digests():
    line("## Cross-interpreter digests (this interpreter)")
    for probe, macros in (("noise", tuple((i, code(6.0))
                                          for i in range(BANDS))),
                          ("patch0", ()),
                          ("patch5", ())):
        for rate in (48000, 44100, 22050):
            data = noise(int(rate * 0.5))
            kwargs = {"macros": macros}
            if probe == "patch5":
                kwargs = {"patch": 5}
            result = run(data, int(rate * 0.5), rate=rate, **kwargs)
            line("   %-7s %5d Hz  fnv %08x" % (probe, rate, result.digest))
    line()


if __name__ == "__main__":
    line("# GraphicEQ Station C -- raw run")
    line()
    tier_one()
    state_leg()
    trait_one()
    trait_two()
    trait_three()
    trait_four()
    trait_five()
    anchor_sweep()
    digests()
