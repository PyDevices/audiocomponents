"""The five open questions the `DynamicEQ` seed left, answered from runs.

Station A of the class build. Every number printed here is quoted in
`docs/effects/DynamicEQ.md` section 8 and in the evidence pack.

    PYTHONPATH=<worktree>/lib audiocomponents/.venv/bin/python \\
        tools/phase2_probes/dynamiceq_opens.py
"""

import math
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0])

import dynamiceq_support as S           # noqa: E402


def open_one_low_band_residual():
    """D1: does a low band inherit the family's held DC?"""
    print("D1  held DC after silence, low bands (audiobiquad, float state)")
    print("    burst 200 ms then 3 s of silence; last non-zero frame and")
    print("    the residual in the final 4800 frames")
    for centre in (60.0, 80.0, 120.0, 400.0, 3000.0):
        data = S.burst(centre, S.amp(-3.0), 9600, 158400, lead=4800)
        effect, _ = S.build(data=data, frequency=centre, q=2.0,
                            threshold_db=-60.0, ratio=8.0)
        out = S.render(effect, 158400)
        tail = out[-4800 * S.CHANNELS:]
        last = 0
        for index in range(len(out) // S.CHANNELS):
            if out[index * S.CHANNELS] or out[index * S.CHANNELS + 1]:
                last = index
        residual = max([abs(v) for v in tail]) if tail else 0
        print("    %7.1f Hz  last non-zero frame %6d   residual %d LSB"
              % (centre, last, residual))


def open_two_lean_build():
    """D2: is a lean *patch* even possible, and what would a lean build be?"""
    print()
    print("D2  what a lean escape valve could be")
    import audiobiquad
    import audiodynamics
    cell = audiodynamics.Dynamics(audiodynamics.DYN_COMPRESS,
                                  sample_rate=S.RATE, channel_count=2)
    section = audiobiquad.Biquad(mode=audiobiquad.PEAKING_EQ,
                                 sample_rate=S.RATE, channel_count=2)
    print("    Dynamics exposes gain_reduction_db(): %s"
          % hasattr(cell, 'gain_reduction_db'))
    print("    ... as a synthio BlockInput anything can read: %s"
          % hasattr(cell, '_evaluate'))
    print("    Biquad.gain_db accepts a BlockInput: %s"
          % (hasattr(section, 'gain_db')))
    print("    so the moving-bell build needs Python between the two, per")
    print("    block, and nothing in the pull model calls Python per block.")
    print("    A lean PATCH is impossible either way: every node in the")
    print("    graph runs every block whatever the macros say.")


def open_four_range_is_mix():
    """D4: Range on the Mixer, or on the ratio? Neither - it is Mix."""
    print()
    print("D4  Mix is the Range control: composite at f0 against")
    print("    20*log10((1-m) + m*g1), g1 the composite at m = 1")
    frames = 48000
    data = S.sine(3000.0, S.amp(-10.0), frames)
    dry = S.rms(data, 24000)
    full, _ = S.build(data=data, mix=1.0)
    g1_db = S.gain_db(S.rms(S.render(full, frames), 24000), dry)
    g1 = 10.0 ** (g1_db / 20.0)
    print("    g1 = %+0.3f dB" % g1_db)
    for mix in (0.0, 0.25, 0.5, 0.75, 0.9, 1.0):
        effect, _ = S.build(data=S.sine(3000.0, S.amp(-10.0), frames),
                            mix=mix)
        got = S.gain_db(S.rms(S.render(effect, frames), 24000), dry)
        predicted = 20.0 * math.log10((1.0 - mix) + mix * g1)
        limit = (float('inf') if mix >= 1.0
                 else -20.0 * math.log10(1.0 - mix))
        print("    mix %4.2f -> %+8.3f dB (closed form %+8.3f, d %+0.3f)"
              "   range %s dB"
              % (mix, got, predicted, got - predicted,
                 ("inf" if limit == float('inf') else "%0.1f" % limit)))
    print("    out of band (375 Hz, two octaves down) as mix sweeps:")
    dry375 = S.rms(S.sine(375.0, S.amp(-10.0), frames), 24000)
    for mix in (0.0, 0.5, 1.0):
        effect, _ = S.build(data=S.sine(375.0, S.amp(-10.0), frames),
                            mix=mix)
        got = S.gain_db(S.rms(S.render(effect, frames), 24000), dry375)
        print("      mix %4.2f -> %+0.4f dB" % (mix, got))


def open_five_width_display():
    """D5: what should the Width macro display?"""
    print()
    print("D5  half-depth width of the composite bell against f0/Q,")
    print("    over the ratio-and-overshoot plane (closed form from S1 and")
    print("    the node's gain law; f0 = 3000 Hz, Q = 2, f0/Q = 1500 Hz)")
    centre, q, threshold = 3000.0, 2.0, -30.0
    print("    ratio  over    depth      half-depth width   ratio to f0/Q")
    for ratio in (2.0, 4.0, 8.0, 20.0):
        for over in (6.0, 20.0, 40.0):
            level = threshold + over
            depth = _band_gain(0.0, level, threshold, ratio)
            width = _half_depth_width(centre, q, level, threshold, ratio,
                                      depth)
            if width is None:
                print("    %5.1f  %5.1f  %8.3f    (never reaches half)"
                      % (ratio, over, depth))
                continue
            print("    %5.1f  %5.1f  %8.3f dB %9.1f Hz %13.2f"
                  % (ratio, over, depth, width, width / (centre / q)))


def _band_gain(response_db, level_db, threshold_db, ratio):
    return S.compressor_law(level_db + response_db - threshold_db, ratio)


def _composite_db(hz, centre, q, level_db, threshold_db, ratio):
    """|H_notch + 10^(g/20) H_bp| in dB, with g the law at L + |H_bp|."""
    notch = S.biquad_response('notch', hz, centre, q)
    band = S.biquad_response('band', hz, centre, q)
    gain = _band_gain(band, level_db, threshold_db, ratio)
    # Both sections share a denominator, so the sum is a ratio of the two
    # numerators against it and the phases are the numerators' own.
    w0 = 2.0 * math.pi * centre / S.RATE
    alpha = math.sin(w0) / (2.0 * q)
    cos0 = math.cos(w0)
    a = (1.0 + alpha, -2.0 * cos0, 1.0 - alpha)
    scale = 10.0 ** (gain / 20.0)
    b = (1.0 + scale * alpha, -2.0 * cos0, 1.0 - scale * alpha)
    del notch, band
    w = 2.0 * math.pi * hz / S.RATE
    return S._polar(b, a, w)


def _half_depth_width(centre, q, level_db, threshold_db, ratio, depth_db):
    target = depth_db * 0.5
    edges = []
    for direction in (-1, 1):
        low, high = centre, centre * (2.0 ** (4.0 * direction))
        if _composite_db(high, centre, q, level_db, threshold_db,
                         ratio) > target:
            for _ in range(60):
                mid = math.sqrt(low * high)
                if _composite_db(mid, centre, q, level_db, threshold_db,
                                 ratio) < target:
                    low = mid
                else:
                    high = mid
            edges.append(math.sqrt(low * high))
        else:
            return None
    return abs(edges[1] - edges[0])


def tail_constant():
    print()
    print("tail_samples: measured ring-down of the split, in periods of")
    print("    Q / f0, from a full-scale DC burst to the last non-zero frame")
    for centre in (60.0, 400.0, 3000.0, 12000.0):
        for q in (0.5, 2.0, 12.0):
            total = 240000
            data = S.dc(30000, 2400, total, lead=2400)
            effect, _ = S.build(data=data, frequency=centre, q=q,
                                threshold_db=0.0, ratio=1.0)
            out = S.render(effect, total)
            last = 0
            for index in range(len(out) // S.CHANNELS):
                if out[index * S.CHANNELS] or out[index * S.CHANNELS + 1]:
                    last = index
            samples = last - (2400 + 2400)
            periods = samples * centre / (q * S.RATE)
            print("    f0 %6.0f Hz  Q %5.1f  ring %7d samples  %6.2f"
                  " periods of Q/f0  (declared %d)"
                  % (centre, q, samples, periods, effect.tail_samples))


if __name__ == '__main__':
    open_one_low_band_residual()
    open_two_lean_build()
    open_four_range_is_mix()
    open_five_width_display()
    tail_constant()
