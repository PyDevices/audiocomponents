#!/usr/bin/env python3
"""Generate the measurement kit's probe material, once, on CPython.

    tools/effect_probes/make_probes.py [--dry-run] [--verify]
                                       [--only NAME ...] [--outdir DIR]

`docs/effects-kit-spec.md` section 3. A fixed set, generated here and never
recomputed on a board (the ESP32 ports are single-precision, so a probe
computed there would not be the probe the desktop measured against). One
manifest, `probes.json`, names each probe, its rate, its length, its level
and its FNV digest, so a stale probe cannot be mistaken for a fresh one:
`tools/render_effect.py` checks the digest of every probe it loads and
refuses one that has drifted.

Every probe exists at all three rates (48000 / 44100 / 22050) and at
channel_count 1 and 2, and **every probe is identical in both channels**.
That is not tidiness: STEREO's own clause requires it, or L-R is not silent
at width zero and a correct endpoint reads as broken.

    --dry-run   print the plan and what it will cost on disk, write nothing
    --verify    re-hash every file against probes.json and report drift
    --only      generate just these probe names (the manifest is merged)

Numbers, not adjectives: `--dry-run` prints the exact byte count, because
the full set as section 3 specifies it is not small and whether it belongs
in git is a decision for a person, not for this script.

stdlib only, deliberately: numpy's sin and math's sin need not round the
same way in the last LSB, and these files are committed data whose digests
have to be reproducible from the source that is checked in beside them.
"""

import json
import math
import os
import sys
from array import array

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from render_effect import checksum          # noqa: E402  the kit's one digest

RATES = (48000, 44100, 22050)
CHANNEL_COUNTS = (1, 2)
FULL_SCALE = 32767
REFERENCE = 32768.0                          # 0 dBFS reference for readouts

#: Where the probes land. `tools/probes_scratch/` in the spec's section 8 is
#: this repo's `tools/phase0_probes/` and `tools/spice/`; nothing named
#: `tools/probes/` is created, and neither of those is touched.
HERE = os.path.dirname(os.path.abspath(__file__))


# --- small helpers ---------------------------------------------------------

def amplitude_of(dbfs):
    """Peak int16 amplitude for a level in dBFS, as an exact integer.

    Levels are stated in dBFS and generated to land on exact int16 values:
    the returned integer *is* the probe's peak, and the manifest records
    the level it actually achieves rather than the one that was asked for.
    At -80 dBFS that is 3 LSB and the two differ by 0.7 dB, which a
    measurement reading the manifest can see and one reading the name
    cannot.
    """
    return int(round(REFERENCE * 10.0 ** (dbfs / 20.0)))


def dbfs_of(amplitude):
    if amplitude <= 0:
        return None
    return round(20.0 * math.log10(amplitude / REFERENCE), 3)


def period_frames(frequency, rate):
    """Frames in one exact period of `frequency` at `rate`.

    A sine of this many frames contains a whole number of cycles, so it
    lands on an exact FFT bin with no window (SPECTRUM's requirement) and
    can be looped without a discontinuity.
    """
    frequency_hz = int(round(frequency))
    divisor = math.gcd(frequency_hz, int(rate))
    return int(rate) // divisor if divisor else int(rate)


def whole_cycles(seconds, frequency, rate):
    """`seconds` of `frequency`, rounded up to a whole number of periods."""
    period = period_frames(frequency, rate)
    wanted = seconds * rate
    count = max(1, int(round(wanted / period)))
    return count * period


def silence(frames):
    return array("h", bytes(frames * 2))


def sine_into(values, frames, frequency, rate, amplitude, phase=0.0):
    step = 2.0 * math.pi * frequency / rate
    for index in range(frames):
        values.append(int(round(amplitude * math.sin(step * index + phase))))
    return values


def max_frequency(rate):
    """The highest tone a probe may contain at `rate`.

    0.45 x Nyquist-and-a-bit: 20 kHz does not exist at 22050 Hz, and a
    probe that pretends it does is an aliased probe, not a 20 kHz one.
    The manifest records what each file actually reached.
    """
    return min(20000.0, 0.45 * rate)


def rms_dbfs(values):
    total = 0
    for value in values:
        total += value * value
    if not len(values) or total == 0:
        return None
    return round(20.0 * math.log10(math.sqrt(total / len(values))
                                   / REFERENCE), 3)


def peak_dbfs(values):
    peak = 0
    for value in values:
        magnitude = -value if value < 0 else value
        if magnitude > peak:
            peak = magnitude
    return dbfs_of(peak), peak


# --- the probes ------------------------------------------------------------
#
# Each entry is (name, seconds-estimate, builder, facts). The builder takes
# a rate and returns (array('h') of one channel, extra manifest facts). The
# seconds estimate is only for --dry-run's arithmetic.

SINE_FREQUENCIES = ((100, "100"), (440, "440"), (1000, "1k"), (5000, "5k"))
SINE_LEVELS = (-6, -14, -26, -40, -60)
SINE_SECONDS = 1.5      # 1.5 s is 33075 frames at 22050 Hz, so a 32768-point
                        # transform fits at the lowest rate as well as the
                        # highest. A 65536-point one does not, and SPECTRUM
                        # exports its transform length for exactly that reason.

CREST_FREQUENCY = 1000  # The crest-factor rows (Compressor V3, Expander and
CREST_SECONDS = 1.0     # DeEsser XF, NoiseGate G6) vary crest at a level, not
                        # frequency, so the square and train pairs are
                        # generated at 1 kHz only. --only square_<f>_... is
                        # not enough to add another; edit CREST_FREQUENCY and
                        # regenerate, and say so in the manifest diff.


def build_impulse(rate):
    frames = int(round(3.0 * rate))
    values = silence(frames)
    values[0] = FULL_SCALE
    return values, {"offset_frames": 0, "amplitude": FULL_SCALE,
                    "seconds": frames / float(rate)}


def build_click_stereo(rate):
    frames = int(round(3.0 * rate))
    offset = int(round(0.05 * rate))
    values = silence(frames)
    values[offset] = FULL_SCALE
    return values, {"offset_frames": offset, "offset_seconds": 0.05,
                    "amplitude": FULL_SCALE, "seconds": frames / float(rate)}


def build_click_train(rate):
    frames = int(round(1.0 * rate))
    spacing = int(round(0.020 * rate))
    values = silence(frames)
    count = 0
    index = 0
    while index < frames:
        values[index] = FULL_SCALE
        count += 1
        index += spacing
    return values, {"spacing_frames": spacing, "spacing_seconds": 0.020,
                    "clicks": count, "amplitude": FULL_SCALE,
                    "seconds": frames / float(rate)}


def make_sine(frequency, level):
    def build(rate):
        amplitude = amplitude_of(level)
        frames = whole_cycles(SINE_SECONDS, frequency, rate)
        values = sine_into(array("h"), frames, frequency, rate, amplitude)
        return values, {
            "frequency_hz": frequency,
            "level_dbfs": level,
            "amplitude": amplitude,
            "achieved_peak_dbfs": dbfs_of(amplitude),
            "period_frames": period_frames(frequency, rate),
            "cycles": int(round(frames * frequency / float(rate))),
            "seconds": frames / float(rate),
        }
    return build


def build_sweep_log(rate):
    seconds = 4.0
    frames = int(round(seconds * rate))
    low, high = 20.0, max_frequency(rate)
    amplitude = amplitude_of(-40)
    ratio = math.log(high / low)
    values = array("h")
    fade = int(round(0.010 * rate))
    for index in range(frames):
        t = index / float(rate)
        phase = 2.0 * math.pi * low * seconds / ratio * (
            math.exp(t * ratio / seconds) - 1.0)
        gain = 1.0
        if index < fade:
            gain = 0.5 - 0.5 * math.cos(math.pi * index / fade)
        elif index > frames - fade:
            gain = 0.5 - 0.5 * math.cos(math.pi * (frames - index) / fade)
        values.append(int(round(amplitude * gain * math.sin(phase))))
    return values, {"f_low_hz": low, "f_high_hz": high, "level_dbfs": -40,
                    "amplitude": amplitude, "fade_frames": fade,
                    "seconds": seconds,
                    "sweep_octaves_per_second":
                        round(math.log(high / low, 2) / seconds, 4)}


def build_tones_step(rate):
    """1/6-octave stepped tones, 30 Hz to the rate's ceiling, 0.25 s each.

    The first draft's 1/12-octave 50 Hz-10 kHz could not serve
    MultibandCompressor's SUM (1/6-octave, 30 Hz-20 kHz) or DeEsser's SPLIT
    at all. Every step holds a whole number of cycles so it starts and ends
    at zero, and the step table is exported: RESPONSE reads one steady tone
    at a time and needs to know where each one is.
    """
    hold = 0.25
    ceiling = max_frequency(rate)
    amplitude = amplitude_of(-20)
    values = array("h")
    steps = []
    index = 0
    while True:
        frequency = 30.0 * (2.0 ** (index / 6.0))
        if frequency > ceiling:
            break
        exact = int(round(frequency))
        frames = whole_cycles(hold, exact, rate)
        start = len(values)
        sine_into(values, frames, exact, rate, amplitude)
        steps.append({"index": index, "frequency_hz": exact,
                      "start_frame": start, "frames": frames})
        index += 1
    return values, {"steps": steps, "step_count": len(steps),
                    "hold_seconds_floor": hold, "level_dbfs": -20,
                    "amplitude": amplitude, "f_low_hz": 30.0,
                    "f_high_hz": ceiling, "fraction_of_octave": 6,
                    "seconds": len(values) / float(rate)}


def build_staircase(rate):
    """1 kHz sine, 1 dB steps, -80 -> -10 dBFS, 0.2 s per step."""
    hold = 0.2
    values = array("h")
    steps = []
    for level in range(-80, -9):
        amplitude = amplitude_of(level)
        frames = whole_cycles(hold, 1000, rate)
        start = len(values)
        sine_into(values, frames, 1000, rate, amplitude)
        steps.append({"level_dbfs": level, "amplitude": amplitude,
                      "achieved_peak_dbfs": dbfs_of(amplitude),
                      "start_frame": start, "frames": frames})
    return values, {"steps": steps, "step_count": len(steps),
                    "frequency_hz": 1000, "hold_seconds": hold,
                    "low_dbfs": -80, "high_dbfs": -10,
                    "seconds": len(values) / float(rate)}


def build_burst_silence(rate):
    amplitude = amplitude_of(-6)
    burst = whole_cycles(0.200, 1000, rate)
    tail = int(round(3.0 * rate))
    values = sine_into(array("h"), burst, 1000, rate, amplitude)
    values.extend(silence(tail))
    return values, {"burst_frames": burst, "burst_seconds": 0.200,
                    "tail_frames": tail, "tail_seconds": 3.0,
                    "frequency_hz": 1000, "level_dbfs": -6,
                    "amplitude": amplitude,
                    "edges": "hard, no fade - the step is the excitation",
                    "seconds": (burst + tail) / float(rate)}


def build_dc_step(rate):
    """+-0.5 FS held 5 s, removed while the source still supplies frames.

    The audioif#23 shape: a node that holds +1 LSB of DC after the offset is
    taken away has no last non-zero sample, and TAIL reads the residual both
    while the step is present and after it is gone.
    """
    level = FULL_SCALE // 2
    plan = [(0.5, 0), (5.0, level), (2.0, 0), (5.0, -level), (2.0, 0)]
    values = array("h")
    marks = []
    for seconds, value in plan:
        frames = int(round(seconds * rate))
        marks.append({"start_frame": len(values), "frames": frames,
                      "value": value})
        if value:
            values.extend(array("h", [value]) * frames)
        else:
            values.extend(silence(frames))
    return values, {"segments": marks, "amplitude": level,
                    "level_fs": 0.5, "hold_seconds": 5.0,
                    "seconds": len(values) / float(rate)}


def build_alt_fs(rate):
    frames = int(round(0.5 * rate))
    values = array("h")
    for index in range(frames):
        values.append(FULL_SCALE if index % 2 == 0 else -FULL_SCALE)
    return values, {"frequency_hz": rate / 2.0, "amplitude": FULL_SCALE,
                    "seconds": frames / float(rate),
                    "note": "+-32767 rather than +-32768: an asymmetric "
                            "full scale would show up as a DC term in "
                            "RESIDUAL's mean"}


def build_ramp_fs(rate):
    """A repeating full-scale ramp, period 1024 frames.

    WIRE's planted fault - the dry path scaled by 32767/32768 - is invisible
    for every |v| <= 16384 under round-half-to-even, so the material has to
    carry samples above half scale *everywhere*, not only at the ends of one
    long monotonic ramp. 1024 frames is short enough that every block of
    every render contains them.
    """
    period = 1024
    frames = int(round(0.5 * rate / period)) * period
    values = array("h")
    for index in range(frames):
        position = index % period
        values.append(-32768 + (position * 65535) // (period - 1))
    return values, {"period_frames": period, "amplitude": FULL_SCALE,
                    "seconds": frames / float(rate)}


def build_noise_det(rate):
    """Deterministic PRNG, fixed seed, RMS -20 dBFS.

    A 32-bit xorshift written out here rather than `random`: the algorithm
    and the seed are in the manifest, so the sequence is reproducible from
    the description and not only from the file.
    """
    frames = int(round(4.0 * rate))
    state = 0x2545F491
    target = 10.0 ** (-20 / 20.0) * REFERENCE
    scale = target * math.sqrt(3.0)          # uniform: RMS = peak / sqrt(3)
    values = array("h")
    for _ in range(frames):
        state ^= (state << 13) & 0xffffffff
        state ^= state >> 17
        state ^= (state << 5) & 0xffffffff
        uniform = (state / 4294967296.0) * 2.0 - 1.0
        sample = int(round(scale * uniform))
        if sample > FULL_SCALE:
            sample = FULL_SCALE
        elif sample < -FULL_SCALE:
            sample = -FULL_SCALE
        values.append(sample)
    return values, {"prng": "xorshift32", "seed": "0x2545F491",
                    "target_rms_dbfs": -20, "seconds": frames / float(rate)}


def make_square(level, matching):
    def build(rate):
        sine_peak = amplitude_of(level)
        if matching == "peak":
            amplitude = sine_peak
        else:                                # square RMS == its amplitude
            amplitude = int(round(sine_peak / math.sqrt(2.0)))
        if amplitude > FULL_SCALE:
            return None, {"omitted": "matched-%s amplitude %d exceeds full "
                                     "scale" % (matching, amplitude)}
        frames = whole_cycles(CREST_SECONDS, CREST_FREQUENCY, rate)
        period = period_frames(CREST_FREQUENCY, rate)
        values = array("h")
        for index in range(frames):
            values.append(amplitude if (index % period) < period / 2
                          else -amplitude)
        return values, {"frequency_hz": CREST_FREQUENCY, "level_dbfs": level,
                        "matched": matching, "amplitude": amplitude,
                        "pairs_with": "sine_1k_%d" % level,
                        "crest_factor_db": 0.0,
                        "seconds": frames / float(rate)}
    return build


def make_train10(level, matching):
    """A 10 %-duty bipolar train: 5 % at +A, 45 % zero, 5 % at -A, 45 % zero.

    RMS is A x sqrt(0.1), so a matched-RMS train at -6 dBFS would need
    36722 LSB and cannot exist in int16. It is omitted rather than clipped,
    and the manifest says so: a silently clipped crest probe is a crest
    probe that no longer has the crest factor its name claims.
    """
    def build(rate):
        sine_peak = amplitude_of(level)
        if matching == "peak":
            amplitude = sine_peak
        else:
            amplitude = int(round(sine_peak / math.sqrt(2.0)
                                  / math.sqrt(0.1)))
        if amplitude > FULL_SCALE:
            return None, {"omitted": "matched-%s amplitude %d exceeds full "
                                     "scale" % (matching, amplitude)}
        frames = whole_cycles(CREST_SECONDS, CREST_FREQUENCY, rate)
        period = period_frames(CREST_FREQUENCY, rate)
        values = array("h")
        for index in range(frames):
            phase = (index % period) / float(period)
            if phase < 0.05:
                values.append(amplitude)
            elif 0.5 <= phase < 0.55:
                values.append(-amplitude)
            else:
                values.append(0)
        crest = 20.0 * math.log10(1.0 / math.sqrt(0.1))
        return values, {"frequency_hz": CREST_FREQUENCY, "level_dbfs": level,
                        "matched": matching, "amplitude": amplitude,
                        "duty": 0.10, "pairs_with": "sine_1k_%d" % level,
                        "crest_factor_db": round(crest, 3),
                        "seconds": frames / float(rate)}
    return build


def make_sibilant(level):
    """200 Hz + 6 kHz at a fixed amplitude ratio - DeEsser's LEVEL."""
    ratio_db = -12.0
    def build(rate):
        peak = amplitude_of(level)
        low_gain = 1.0
        high_gain = 10.0 ** (ratio_db / 20.0)
        scale = peak / (low_gain + high_gain)
        frames = whole_cycles(1.5, 200, rate)
        values = array("h")
        low_step = 2.0 * math.pi * 200 / rate
        high_step = 2.0 * math.pi * 6000 / rate
        for index in range(frames):
            values.append(int(round(
                scale * low_gain * math.sin(low_step * index)
                + scale * high_gain * math.sin(high_step * index))))
        return values, {"low_hz": 200, "high_hz": 6000,
                        "ratio_db": ratio_db, "level_dbfs": level,
                        "seconds": frames / float(rate)}
    return build


def build_tone_fs4(rate):
    """A tone at exactly f_s/4 with pi/4 phase - S1's worst case.

    Sampled at pi/4, every sample sits at +-0.7071 of the true peak, so the
    sample peak reads 3.01 dB below what the reconstructed waveform reaches.
    Limiter L1 says in its own disconfirmation clause that a probe set with
    no such tone reads green on a limiter with no true-peak detection at
    all: the level below is chosen so the SAMPLE peak lands on -6.00 dBFS,
    which is the seed's own measured pair (Limiter.md:557-558) and the value
    that lets the faulted TRUEPEAK certify a -6 dBFS ceiling as met while
    3 dB escapes.
    """
    if rate == 22050:
        return None, {"omitted": "section 3 names tone_fs4 at 48 kHz and "
                                 "44.1 kHz only"}
    sample_peak = amplitude_of(-6)
    amplitude = int(round(sample_peak * math.sqrt(2.0)))
    frames = whole_cycles(1.0, rate // 4, rate)
    values = sine_into(array("h"), frames, rate // 4, rate, amplitude,
                       math.pi / 4.0)
    achieved, peak = peak_dbfs(values)
    return values, {"frequency_hz": rate / 4.0, "phase_radians": math.pi / 4,
                    "amplitude": amplitude, "sample_peak": peak,
                    "sample_peak_dbfs": achieved,
                    "true_peak_dbfs": dbfs_of(amplitude),
                    "seconds": frames / float(rate)}


def make_step_over(over_db):
    """A 1 kHz tone stepping from silence to `over_db` over a threshold.

    Compressor V2's three published attack points are stated in dB over
    threshold, not in dBFS, so the probe has to name the threshold it is
    relative to. -40 dBFS is the reference: at +30 the tone is -10 dBFS and
    still has 10 dB of headroom, which a reference of -20 would not.
    """
    reference = -40.0
    def build(rate):
        level = reference + over_db
        amplitude = amplitude_of(level)
        lead = int(round(0.5 * rate))
        tone = whole_cycles(2.0, 1000, rate)
        values = silence(lead)
        sine_into(values, tone, 1000, rate, amplitude)
        return values, {"threshold_ref_dbfs": reference,
                        "over_db": over_db, "level_dbfs": level,
                        "amplitude": amplitude, "lead_frames": lead,
                        "tone_frames": tone, "frequency_hz": 1000,
                        "seconds": len(values) / float(rate)}
    return build


def build_burst_train(rate):
    """Ten 10 ms bursts at 200 ms spacing - Compressor M3's program
    dependence. The GR depth each one reaches is the class's to report; what
    the probe fixes is the level, the length and the spacing."""
    amplitude = amplitude_of(-6)
    spacing = int(round(0.200 * rate))
    burst = int(round(0.010 * rate))
    frames = 10 * spacing + int(round(0.2 * rate))
    values = silence(frames)
    step = 2.0 * math.pi * 1000 / rate
    starts = []
    for index in range(10):
        start = index * spacing
        starts.append(start)
        for offset in range(burst):
            values[start + offset] = int(round(
                amplitude * math.sin(step * offset)))
    return values, {"bursts": 10, "burst_frames": burst,
                    "burst_seconds": 0.010, "spacing_frames": spacing,
                    "spacing_seconds": 0.200, "starts": starts,
                    "frequency_hz": 1000, "level_dbfs": -6,
                    "amplitude": amplitude, "seconds": frames / float(rate)}


# --- probes rendered from audioinstruments ---------------------------------

def _render_instrument(name, rate, notes, seconds):
    """One instrument, one gesture, mono, as an array('h').

    Rendered at channel_count 1 so the probe is identical in both channels
    when it is written as stereo - STEREO's clause again. CPython only, and
    that is fine: the probe set is generated once, here.
    """
    import audiocore
    import audioinstruments
    instrument = audioinstruments.create(name, sample_rate=rate,
                                         channel_count=1)
    for pitch, velocity in notes:
        instrument.note_on(pitch, velocity)
    values = array("h")
    wanted = int(round(seconds * rate))
    while len(values) < wanted:
        _result, buffer = audiocore.get_buffer(instrument.output)
        data = bytes(buffer)
        if not data:
            break
        import struct
        values.extend(struct.unpack("<%dh" % (len(data) // 2), data))
    instrument.deinit()
    return values[:wanted]


def build_chord(rate):
    """One held instrument chord - DIGEST's and COST's material.

    A polysynth pad rather than a tone: DIGEST wants material that moves
    every part of a class, and COST's honest caveat is that a class idling
    below threshold costs what a wire costs.
    """
    values = _render_instrument("juno106", rate,
                                ((48, 100), (55, 100), (60, 100), (64, 100)),
                                3.0)
    achieved, peak = peak_dbfs(values)
    return values, {"instrument": "juno106", "notes": [48, 55, 60, 64],
                    "velocity": 100, "peak_dbfs": achieved,
                    "rms_dbfs": rms_dbfs(values),
                    "seconds": len(values) / float(rate)}


def make_hit_level(level):
    """One percussive hit, scaled to a stated peak.

    Section 3 says "one recorded percussive hit". The recorded captures in
    `.reference-captures/` are reference material this program analyses and
    never redistributes, so a probe cut from one could not be committed
    beside the code that reads it. This is `audioinstruments`' own tr808
    snare instead - our material, at the same job - and the deviation is
    recorded here rather than left for a reader to discover from the bytes.
    """
    def build(rate):
        values = _render_instrument("tr808", rate, ((38, 127),), 1.0)
        _achieved, peak = peak_dbfs(values)
        if not peak:
            return None, {"omitted": "tr808 note 38 rendered silence"}
        target = amplitude_of(level)
        scaled = array("h")
        for value in values:
            scaled.append(max(-FULL_SCALE,
                              min(FULL_SCALE,
                                  int(round(value * target / peak)))))
        achieved, _peak = peak_dbfs(scaled)
        return scaled, {"instrument": "tr808", "note": 38, "velocity": 127,
                        "level_dbfs": level, "achieved_peak_dbfs": achieved,
                        "source": "rendered, not recorded - see "
                                  "make_hit_level's docstring",
                        "seconds": len(scaled) / float(rate)}
    return build


# --- the catalogue ---------------------------------------------------------

def catalogue():
    entries = [
        ("impulse", 3.0, build_impulse,
         "one full-scale sample, then silence",
         ["CLICK", "TAPS", "DECAY", "RESPONSE"]),
        ("click_stereo", 3.0, build_click_stereo,
         "the same, identical in both channels, at a known offset",
         ["CLICK", "TAPS", "STEREO"]),
        ("click_train", 1.0, build_click_train,
         "full-scale clicks at 20 ms spacing",
         ["TAPS"]),
    ]
    for frequency, label in SINE_FREQUENCIES:
        for level in SINE_LEVELS:
            entries.append(("sine_%s_%d" % (label, level), SINE_SECONDS,
                            make_sine(frequency, level),
                            "steady sine, %d Hz at %d dBFS"
                            % (frequency, level),
                            ["SPECTRUM", "CURVE", "ENVELOPE", "IFREQ"]))
    entries += [
        ("sweep_log", 4.0, build_sweep_log,
         "20 Hz to the rate's ceiling, log, 4 s, -40 dBFS",
         ["RESPONSE", "RESIDUAL"]),
        ("tones_step", 14.3, build_tones_step,
         "1/6-octave stepped tones, 30 Hz to the rate's ceiling",
         ["RESPONSE", "SUM", "SPLIT", "XOVER", "ISO"]),
        ("staircase", 14.2, build_staircase,
         "1 kHz sine, 1 dB steps, -80 to -10 dBFS",
         ["CURVE"]),
        ("burst_silence", 3.2, build_burst_silence,
         "200 ms burst then 3 s silence",
         ["TAIL", "GAINTRACE", "DECAY"]),
        ("dc_step", 14.5, build_dc_step,
         "+-0.5 FS held 5 s, then removed while frames keep coming",
         ["TAIL"]),
        ("alt_fs", 0.5, build_alt_fs,
         "+-FS alternating (Nyquist)",
         ["TAIL", "RESIDUAL"]),
        ("ramp_fs", 0.5, build_ramp_fs,
         "repeating full-scale ramp",
         ["WIRE"]),
        ("noise_det", 4.0, build_noise_det,
         "deterministic PRNG, fixed seed",
         ["RESPONSE", "RESIDUAL", "STEREO", "LEVEL"]),
        ("chord", 3.0, build_chord,
         "one held instrument chord from audioinstruments",
         ["DIGEST", "COST"]),
    ]
    for level in (-6, -20, -40, -60, -80):
        entries.append(("hit_levels_%d" % level, 1.0, make_hit_level(level),
                        "one percussive hit at %d dBFS" % level,
                        ["GAINTRACE", "TRUEPEAK"]))
    for level in SINE_LEVELS:
        for matching in ("rms", "peak"):
            entries.append(("square_1k_%d_%s" % (level, matching),
                            CREST_SECONDS, make_square(level, matching),
                            "square at 1 kHz, matched-%s with sine_1k_%d"
                            % (matching, level),
                            ["CURVE", "GAINTRACE"]))
            entries.append(("train10_1k_%d_%s" % (level, matching),
                            CREST_SECONDS, make_train10(level, matching),
                            "10 %% duty bipolar train at 1 kHz, matched-%s "
                            "with sine_1k_%d" % (matching, level),
                            ["CURVE", "GAINTRACE"]))
    for level in (-6, -20, -40, -55):
        entries.append(("sibilant_%d" % level, 1.5, make_sibilant(level),
                        "200 Hz + 6 kHz at a fixed ratio, %d dBFS" % level,
                        ["GAINTRACE", "RESPONSE"]))
    entries.append(("tone_fs4", 1.0, build_tone_fs4,
                    "f_s/4 at pi/4 phase - the worst case for a sample-peak "
                    "reading", ["TRUEPEAK"]))
    for over in (10, 20, 30):
        entries.append(("step_over_%d" % over, 2.5, make_step_over(over),
                        "1 kHz stepping to %d dB over the stated threshold"
                        % over, ["GAINTRACE"]))
    entries.append(("burst_train", 2.2, build_burst_train,
                    "ten 10 ms bursts at 200 ms spacing", ["GAINTRACE"]))
    return entries


# --- writing ---------------------------------------------------------------

def wav_bytes(mono, rate, channels):
    """PCM for one channel count, from one mono array.

    The stereo file is the mono one in both channels - byte slicing rather
    than a Python loop, because the full set is fifteen million samples and
    an append per sample doubles the run.
    """
    payload = mono.tobytes()
    if channels == 2:
        stereo = bytearray(len(payload) * 2)
        stereo[0::4] = payload[0::2]
        stereo[1::4] = payload[1::2]
        stereo[2::4] = payload[0::2]
        stereo[3::4] = payload[1::2]
        payload = bytes(stereo)
    header = (b"RIFF" + (36 + len(payload)).to_bytes(4, "little")
              + b"WAVEfmt " + (16).to_bytes(4, "little")
              + (1).to_bytes(2, "little") + channels.to_bytes(2, "little")
              + rate.to_bytes(4, "little")
              + (rate * channels * 2).to_bytes(4, "little")
              + (channels * 2).to_bytes(2, "little")
              + (16).to_bytes(2, "little")
              + b"data" + len(payload).to_bytes(4, "little"))
    return header + payload, payload


def main(argv):
    dry_run = "--dry-run" in argv
    verify = "--verify" in argv
    outdir = HERE
    only = []
    index = 0
    while index < len(argv):
        if argv[index] == "--only":
            only.append(argv[index + 1]); index += 2
        elif argv[index] == "--outdir":
            outdir = argv[index + 1]; index += 2
        else:
            index += 1

    entries = catalogue()
    if only:
        entries = [entry for entry in entries if entry[0] in only]
        if not entries:
            raise SystemExit("no probe matches %s" % ", ".join(only))

    if dry_run:
        total = 0
        files = 0
        print("%-24s %8s  %s" % ("probe", "seconds", "what it is"))
        for name, seconds, _builder, description, _feeds in entries:
            cost = 0
            for rate in RATES:
                frames = int(round(seconds * rate))
                for channels in CHANNEL_COUNTS:
                    cost += 44 + frames * channels * 2
                    files += 1
            total += cost
            print("%-24s %8.2f  %-52s %6.1f MB"
                  % (name, seconds, description[:52], cost / 1048576.0))
        print("\n%d probe names, %d files, %.1f MB estimated"
              % (len(entries), files, total / 1048576.0))
        print("(the estimate ignores whole-cycle rounding and the probes "
              "that are omitted at a rate)")
        return 0

    manifest_path = os.path.join(outdir, "probes.json")
    manifest = {"generator": "tools/effect_probes/make_probes.py",
                "spec": "docs/effects-kit-spec.md section 3",
                "rates": list(RATES),
                "channel_counts": list(CHANNEL_COUNTS),
                "channels_identical": True,
                "digest": "FNV-1a over the PCM bytes, header excluded "
                          "(render_effect.checksum)",
                "probes": {}}
    if os.path.exists(manifest_path):
        with open(manifest_path) as handle:
            manifest = json.load(handle)
        manifest.setdefault("probes", {})

    if verify:
        bad = 0
        checked = 0
        for name, probe in sorted(manifest["probes"].items()):
            for key, entry in sorted(probe.get("files", {}).items()):
                path = os.path.join(outdir, entry["path"])
                checked += 1
                if not os.path.exists(path):
                    print("MISSING %s %s" % (name, key)); bad += 1
                    continue
                with open(path, "rb") as handle:
                    handle.seek(44)
                    value = checksum(handle.read())
                if "%08x" % value != entry["fnv1a"]:
                    print("DRIFTED %s %s: file %08x, manifest %s"
                          % (name, key, value, entry["fnv1a"]))
                    bad += 1
        print("verified %d files, %d bad" % (checked, bad))
        return 1 if bad else 0

    written = 0
    total_bytes = 0
    for name, _seconds, builder, description, feeds in entries:
        probe = {"description": description, "feeds": feeds, "files": {}}
        omitted = {}
        for rate in RATES:
            mono, facts = builder(rate)
            if mono is None:
                omitted["%d" % rate] = facts.get("omitted", "omitted")
                continue
            for channels in CHANNEL_COUNTS:
                directory = os.path.join(outdir, "%d" % rate,
                                         "%dch" % channels)
                if not os.path.isdir(directory):
                    os.makedirs(directory)
                blob, payload = wav_bytes(mono, rate, channels)
                path = os.path.join(directory, name + ".wav")
                with open(path, "wb") as handle:
                    handle.write(blob)
                achieved, peak = peak_dbfs(mono)
                entry = {
                    "path": "%d/%dch/%s.wav" % (rate, channels, name),
                    "frames": len(mono),
                    "seconds": round(len(mono) / float(rate), 6),
                    "peak_dbfs": achieved,
                    "peak_lsb": peak,
                    "rms_dbfs": rms_dbfs(mono),
                    "bytes": len(blob),
                    "fnv1a": "%08x" % checksum(payload),
                }
                # Every fact the builder returned is rate-dependent -
                # a step table is frame-indexed, and tones_step's own
                # ceiling moves with the rate - so the facts live in the
                # per-file entry and never at the probe level, where the
                # last rate generated would silently overwrite the rest.
                for key, value in facts.items():
                    if key != "seconds":
                        entry[key] = value
                probe["files"]["%d/%d" % (rate, channels)] = entry
                written += 1
                total_bytes += len(blob)
        if omitted:
            probe["omitted"] = omitted
        manifest["probes"][name] = probe
        print("%-26s %s"
              % (name, " ".join(sorted(probe["files"]))[:100]
                 or "OMITTED " + str(omitted)))

    with open(manifest_path, "w") as handle:
        json.dump(manifest, handle, indent=1, sort_keys=True)
    print("\n%d probe names, %d files, %.1f MB, manifest %s"
          % (len(entries), written, total_bytes / 1048576.0, manifest_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
