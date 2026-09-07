"""Station A probes for the `TransientShaper` dossier (Phase 2).

Every number §4 and §8 of `docs/effects/TransientShaper.md` state comes from
one run of this file. It drives `audiodynamics.Dynamics(DYN_TRANSIENT)`
directly, not the class -- at Station A the class does not exist yet, and
the questions being settled are about the node's options.

    audiocomponents/.venv/bin/python \
        tools/phase2_probes/transientshaper_station_a.py

The gain trace is the measurement kit's GAINTRACE
(`tools/effect_measurements.py:1182`) over an in-process render, so the
readout is the one Station C will use, not a second implementation of it.
"""

import math
import os
import sys
import wave
from array import array

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import audiocore                                          # noqa: E402
import audiodynamics                                      # noqa: E402
import effect_measurements as kit                         # noqa: E402

RATE = 48000
PROBES = os.path.join(os.path.dirname(HERE), "effect_probes")

#: What the rebuilt class fixes on the node, settled by the runs below.
FIXED = dict(transient_dual=True, slow_hold_ms=150.0,
             sustain_fast_attack_ms=0.0, detector="rms", rms_ms=3.0)


def probe(name, rate=RATE, channels=2):
    path = "%s/%d/%dch/%s.wav" % (PROBES, rate, channels, name)
    with wave.open(path, "rb") as handle:
        frames = handle.getnframes()
        return handle.readframes(frames), frames


def decaying(db_per_s, seconds=1.0, hz=220.0, dbfs=-6.0, attack_ms=1.0,
             rate=RATE, channels=2):
    """An exponentially decaying tone -- T4's and T6's material."""
    count = int(rate * seconds)
    peak = (10 ** (dbfs / 20.0)) * 32767
    out = array("h", bytes(2 * count * channels))
    for index in range(count):
        seconds_in = index / rate
        envelope = 10.0 ** (-db_per_s * seconds_in / 20.0)
        rise = 1.0 if attack_ms <= 0 else min(
            1.0, seconds_in / (attack_ms / 1000.0))
        value = int(max(-32768, min(32767, round(
            peak * envelope * rise
            * math.sin(2 * math.pi * hz * seconds_in)))))
        for channel in range(channels):
            out[index * channels + channel] = value
    return bytes(memoryview(out).cast("B")), count


def burst(hz, on_ms=250.0, seconds=0.5, dbfs=-6.0, rate=RATE, channels=2):
    """A flat-topped tone burst -- T5's material."""
    count = int(rate * seconds)
    on = int(rate * on_ms / 1000.0)
    peak = (10 ** (dbfs / 20.0)) * 32767
    out = array("h", bytes(2 * count * channels))
    for index in range(on):
        value = int(max(-32768, min(32767, round(
            peak * math.sin(2 * math.pi * hz * index / rate)))))
        for channel in range(channels):
            out[index * channels + channel] = value
    return bytes(memoryview(out).cast("B")), count


def render(pcm, frames, rate=RATE, channels=2, **options):
    source = audiocore.RawSample(array("h", pcm), sample_rate=rate,
                                 channel_count=channels)
    node = audiodynamics.Dynamics(audiodynamics.DYN_TRANSIENT,
                                  sample_rate=rate, channel_count=channels,
                                  **options)
    node.play(source)
    out = bytearray()
    want = frames * channels * 2
    while len(out) < want:
        result, buffer = audiodynamics.get_buffer(node)
        block = bytes(buffer)
        if result == audiodynamics.GET_BUFFER_ERROR or not block:
            break
        out += block
    return bytes(out[:want])


def trace(pcm, frames, rate=RATE, channels=2, hop=1.0, floor=-90.0,
          **options):
    wet = render(pcm, frames, rate, channels, **options)
    result = kit.gaintrace(
        kit.Render.from_pcm(wet, rate, channels, label="wet"),
        kit.Render.from_pcm(pcm, rate, channels, label="dry"),
        hop_ms=hop, floor_db=floor)
    values = result["values"]
    return (np.array(values["trace_ms"]),
            np.array([np.nan if v is None else v
                      for v in values["trace_gr_db"]], dtype=float))


def main():
    print("Station A probes -- TransientShaper, %d Hz, stereo, 16-bit"
          % RATE)
    print("audiodynamics.Dynamics(DYN_TRANSIENT) driven directly; "
          "gain trace = kit GAINTRACE over an in-process render")

    print("\nQ1 -- are the two sections two circuits, or one switch? "
          "(dossier section 8 Q1, section 5 N-TRAN-1, T2)")
    hit, frames = probe("hit_levels_-6")
    single = dict(FIXED)
    single["transient_dual"] = False
    for label, options in (("transient_dual=True ", FIXED),
                           ("transient_dual=False", single)):
        both = trace(hit, frames, attack_gain_db=12.0, sustain_gain_db=-12.0,
                     **options)[1]
        only_a = trace(hit, frames, attack_gain_db=12.0, sustain_gain_db=0.0,
                       **options)[1]
        only_s = trace(hit, frames, attack_gain_db=0.0, sustain_gain_db=-12.0,
                       **options)[1]
        count = min(len(both), len(only_a), len(only_s))
        both, only_a, only_s = both[:count], only_a[:count], only_s[:count]
        live = ~(np.isnan(both) | np.isnan(only_a) | np.isnan(only_s))
        # T2 clause (a): both sections acting at the SAME hop.
        together = live & (only_a > 0.5) & (only_s < -0.5)
        # T2 clause (b): each control's effect unmoved by the other's setting.
        drift = np.abs(both - (only_a + only_s))[live]
        print("  %s hops with attack boost AND sustain cut at once: "
              "%3d of %3d" % (label, int(together.sum()), int(live.sum())))
        print("  %s each section's effect, alone vs in company: max "
              "%.3f dB (T2 allows 0.500)" % (" " * len(label), drift.max()))
    print("  the superposition figure alone cannot tell the two apart -- a "
          "gain computer that\n  SELECTS one section by the sign of one "
          "difference decomposes exactly too. The\n  hop count is the "
          "discriminator, and 0 of them is T2's planted fault.")

    print("\nsection 4 -- sustain_fast_attack_ms beside an instantaneous "
          "peak-hold")
    note, note_frames = decaying(10.0)
    for fast_ms in (1.0, 0.0):
        options = dict(FIXED)
        options["sustain_fast_attack_ms"] = fast_ms
        times, gains = trace(note, note_frames, attack_gain_db=0.0,
                             sustain_gain_db=-12.0, **options)
        window = (times <= 200.0) & ~np.isnan(gains)
        depth = -gains[window]
        drop = (np.maximum.accumulate(depth) - depth).max()
        # What it costs the attack section when both controls are set.
        paired = trace(hit, frames, attack_gain_db=12.0,
                       sustain_gain_db=-12.0, **options)[1]
        print("  sustain_fast_attack_ms=%.1f: T4 monotone drop over 0-200 ms "
              "%7.3f dB; attack peak with Sustain -12 also set %+7.3f dB"
              % (fast_ms, drop, np.nanmax(paired)))

    print("\nsection 4 -- the detector, on a 1 kHz burst at Attack +12 "
          "(T5's steady clause)")
    tone, tone_frames = burst(1000.0)
    for label, override in (("peak", {"detector": "peak"}),
                            ("rms 3 ms", {})):
        options = dict(FIXED)
        options.update(override)
        times, gains = trace(tone, tone_frames, hop=0.1, attack_gain_db=12.0,
                             sustain_gain_db=0.0, **options)
        first = (times <= 5.0) & ~np.isnan(gains)
        steady = int(np.searchsorted(times, 150.0))
        print("  detector %-8s peak over 0-5 ms %+7.3f dB; steady at 150 ms "
              "%+7.3f dB" % (label, gains[first].max(), gains[steady]))

    print("\nQ2 -- do the time constants follow the material? "
          "(dossier section 8 Q2, T6)")
    for attack_ms in (0.5, 2.0, 8.0):
        material, count = decaying(6.0, seconds=0.5, hz=2000.0,
                                   attack_ms=attack_ms)
        times, gains = trace(material, count, hop=0.05, attack_gain_db=12.0,
                             sustain_gain_db=0.0, **FIXED)
        window = (times <= 60.0) & ~np.isnan(gains)
        span, values = times[window], gains[window]
        top = values.max()
        low = int(np.argmax(values >= 0.1 * top))
        high = int(np.argmax(values >= 0.9 * top))
        print("  material 10-90%% %5.2f ms -> gain-trace 10-90%% %6.3f ms "
              "(peak %+6.3f dB)"
              % (attack_ms * 0.8, span[high] - span[low], top))

    print("\nsection 6 -- what patch 0's quantization costs")
    for label, span, default in (("Attack", (-15.0, 15.0), 0.0),
                                 ("Sustain", (-24.0, 24.0), 0.0),
                                 ("Output", (-22.0, 6.0), 0.0),
                                 ("Attack Speed", (0.2, 5.0, "log"), 1.0),
                                 ("Sustain Hold", (0.0, 500.0), 150.0)):
        grid = kit_macro_of(span, default)
        back = macro_value(span, grid / 127.0)
        print("  %-13s default %8.3f -> MIDI %3d -> %8.3f  (delta %+.3f)"
              % (label, default, grid, back, back - default))


def macro_value(span, position):
    low, high = span[0], span[1]
    if len(span) > 2:
        return low * ((high / low) ** position)
    return low + (high - low) * position


def kit_macro_of(span, value):
    low, high = span[0], span[1]
    if len(span) > 2:
        position = math.log(value / low) / math.log(high / low)
    else:
        position = (value - low) / (high - low)
    return int(round(min(1.0, max(0.0, position)) * 127))


if __name__ == "__main__":
    main()
