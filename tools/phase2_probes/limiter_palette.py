"""What an `audiodynamics.Dynamics` at the pin can and cannot do for `Limiter`.

Appendix G of `docs/effects/Limiter.md`. The seed's Appendices B and F probed
an older node; three of their palette claims are stale, and this file is how
that was found out rather than asserted. Every number the dossier's §§3-8 moved
comes from one run of this script.

    PYTHONPATH=lib .venv/bin/python tools/phase2_probes/limiter_palette.py

CPython with numpy, against the audioif build in `audiocomponents/.venv`. It
probes the *node*, never the class: the class's own evidence is
`docs/effects/Limiter-evidence.md`.
"""

import array
import math

import numpy as np

import audiocore
import audiodynamics
import audiomixer

RATE = 48000


def pcm(x, channels=2):
    """A float array in -1..1 as the int16 buffer a RawSample takes."""
    q = np.clip(np.round(np.asarray(x) * 32768.0), -32768, 32767)
    q = q.astype(np.int64)
    if channels == 2:
        q = np.repeat(q[:, None], 2, axis=1)
    return array.array("h", q.reshape(-1).tolist())


def source(buffer, rate=RATE, channels=2):
    return audiocore.RawSample(buffer, sample_rate=rate,
                               channel_count=channels)


def render(node, frames, channels=2):
    out = bytearray()
    audiocore.reset_buffer(node)
    want = frames * channels * 2
    while len(out) < want:
        result, block = audiocore.get_buffer(node)
        chunk = bytes(block)
        if not chunk:
            break
        out += chunk
        if result == audiocore.GET_BUFFER_ERROR:
            break
    data = np.frombuffer(bytes(out[:want]), dtype="<i2")
    return data.reshape(-1, channels)


def peak_db(x, full=32768.0):
    top = float(np.abs(np.asarray(x, dtype=np.float64)).max())
    return -200.0 if top <= 0 else 20.0 * math.log10(top / full)


def oversample(x, factor=4, taps_per_phase=24):
    """Blackman-windowed-sinc reconstruction: the waveform between samples."""
    x = np.asarray(x, dtype=np.float64)
    length = taps_per_phase * factor
    index = np.arange(-length, length + 1)
    kernel = np.sinc(index / float(factor)) * np.blackman(2 * length + 1)
    kernel = kernel / float(kernel[::factor].sum())
    stuffed = np.zeros(len(x) * factor)
    stuffed[::factor] = x
    out = np.convolve(stuffed, kernel, mode="same")
    return out[length:len(out) - length]


def thd_percent(y, rate, fundamental, harmonics=10):
    spectrum = np.abs(np.fft.rfft(np.asarray(y, dtype=np.float64)))
    width = rate / float(len(y))

    def magnitude(hz):
        index = int(round(hz / width))
        return float(spectrum[max(0, index - 1):index + 2].max())

    upper = math.sqrt(sum(magnitude(fundamental * n) ** 2
                          for n in range(2, harmonics + 1)))
    return 100.0 * upper / magnitude(fundamental)


def limiter(src, ceiling_db, *, lookahead_ms=0.0, release_ms=60.0,
            true_peak=0, knee_db=0.0, gain_db=0.0, catch=True, rate=RATE,
            channels=2, offset_db=0.0):
    """The class's own topology, built from node arguments only."""
    shape = audiodynamics.Dynamics(
        audiodynamics.DYN_COMPRESS, sample_rate=rate, channel_count=channels,
        threshold_db=ceiling_db - gain_db + offset_db, ratio=1e6,
        knee_db=knee_db, makeup_db=gain_db, attack_ms=0.0,
        release_ms=release_ms, lookahead_ms=lookahead_ms, true_peak=true_peak)
    shape.play(src)
    if not catch:
        return shape, [shape]
    trap = audiodynamics.Dynamics(
        audiodynamics.DYN_LIMIT, sample_rate=rate, channel_count=channels,
        threshold_db=ceiling_db + offset_db, attack_ms=0.0, release_ms=5.0,
        true_peak=true_peak)
    trap.play(shape)
    return trap, [shape, trap]


def burst(frames=48000, start=4800, length=48, level=1.0):
    x = np.zeros(frames)
    x[start:start + length] = level
    return x


def impulse(frames=48000, at=4800, level=1.0):
    x = np.zeros(frames)
    x[at] = level
    return x


def worst_phase_fs4(frames, sample_peak_db):
    n = np.arange(frames)
    amp = 10.0 ** (sample_peak_db / 20.0) / math.cos(math.pi / 4.0)
    return amp * np.cos(2.0 * math.pi * n / 4.0 + math.pi / 4.0)


def g1_catch_stage():
    print("G.1  the catch stage, reproduced on the pin "
          "(seed Appendix F.1)")
    print("     ceiling -12 dBFS, release 60 ms; sample peak of the output")
    print("     probe          lookahead   lone shape node    + catch stage")
    for name, make in (("1 ms burst", burst), ("1-sample impulse", impulse)):
        for look in (0.0, 0.5, 1.0, 2.0, 5.0, 10.0):
            row = []
            for catch in (False, True):
                node, built = limiter(source(pcm(make())), -12.0,
                                      lookahead_ms=look, catch=catch)
                row.append(peak_db(render(node, 48000)[:, 0]))
                for one in built:
                    one.deinit()
            print("     %-16s %6.2f ms   %8.2f dBFS      %8.2f dBFS"
                  % (name, look, row[0], row[1]))
    print()


def g2_true_peak():
    print("G.2  true_peak is a level, not a flag: the 4x detector N-L2 asked")
    print("     for is on the pin. Worst-phase f_s/4 tone, sample peak")
    print("     -0.50 dBFS, ceiling -6 dBFS, release 60 ms, catch stage on.")
    print("     true_peak  lookahead   sample peak    true peak   over ceiling")
    tone = worst_phase_fs4(48000, -0.5)
    for mode in (0, 1, 2):
        for look in (0.0, 1.5, 5.0):
            node, built = limiter(source(pcm(tone)), -6.0, lookahead_ms=look,
                                  true_peak=mode)
            out = render(node, 48000)[400:, 0] / 32768.0
            true = peak_db(oversample(out) * 32768.0)
            print("     %9d  %6.2f ms   %8.2f dBFS   %8.2f dBTP   %+6.2f dB"
                  % (mode, look, peak_db(out * 32768.0), true, true + 6.0))
            for one in built:
                one.deinit()
    print("     L1 allows +0.50 dB. Only true_peak=2 is inside it.")
    print()


def g3_lookahead_arithmetic():
    print("G.3  the node truncates the lookahead in float32, and a naive")
    print("     double-precision restatement disagrees with it.")
    print("     `lookahead_frames = (uint32_t)(ms * fs / 1000.0f)`, "
          "audioif_dynamics.c:127-128")
    naive = midpoint = tested = 0
    first = []
    for rate in (48000, 44100, 22050):
        cases = [i * 1000.0 / rate for i in range(1, 60)]
        cases += [(i + 1e-9) * 1000.0 / rate for i in range(1, 60)]
        cases += [0.017 * k * 1000.0 / rate * 3.7 for k in range(1, 61)]
        for ms in cases:
            want = int(ms * rate / 1000.0)
            if want == 0 or ms > 10.0:
                continue
            tested += 1
            for form, asked in (("naive", ms),
                                ("midpoint", (want + 0.5) * 1000.0 / rate)):
                x = np.zeros(6000)
                x[1000] = 0.5
                node = audiodynamics.Dynamics(
                    audiodynamics.DYN_LIMIT, sample_rate=rate,
                    channel_count=2, threshold_db=0.0, attack_ms=0.0,
                    release_ms=60.0, lookahead_ms=asked)
                node.play(source(pcm(x), rate=rate))
                got = int(np.argmax(np.abs(render(node, 6000, 2)[:, 0]))) - 1000
                node.deinit()
                if got != want:
                    if form == "naive":
                        naive += 1
                        if len(first) < 4:
                            first.append("     naive: %d Hz, %.9f ms -> "
                                         "wanted %d samples, got %d"
                                         % (rate, ms, want, got))
                    else:
                        midpoint += 1
    for line in first:
        print(line)
    print("     %d cases: naive form wrong %d times, "
          "bin-midpoint form wrong %d times."
          % (tested, naive, midpoint))
    print("     The class sets the node to the midpoint of the truncation "
          "bin and reports floor().")
    print()


def g4_release_and_thd():
    print("G.4  L7 lives on the Release default. 60 Hz sine at 0 dBFS into a")
    print("     -12 dBFS ceiling; THD h2..h10 over 0.5 s of steady state.")
    print("     release    lone shape   + catch    catch + 1.5 ms lookahead")
    frames = 48000
    n = np.arange(frames)
    tone = 0.999 * np.sin(2.0 * math.pi * 60.0 * n / RATE)
    for release in (1.0, 10.0, 30.0, 60.0, 100.0, 150.0, 200.0, 300.0):
        row = []
        for look, catch in ((0.0, False), (0.0, True), (1.5, True)):
            node, built = limiter(source(pcm(tone)), -12.0,
                                  lookahead_ms=look, release_ms=release,
                                  catch=catch)
            out = render(node, frames)[24000:, 0]
            row.append(thd_percent(out, RATE, 60.0))
            for one in built:
                one.deinit()
        print("     %6.1f ms  %8.2f %%  %8.2f %%   %8.2f %%"
              % (release, row[0], row[1], row[2]))
    print("     L7's bar is 1 %. 100 ms reads 1.05 %; the patch uses 149 ms.")
    print()
    print("     True Peak on, Lookahead 0: click delay, 48 kHz")
    x = np.zeros(6000)
    x[1000] = 0.5
    node, built = limiter(source(pcm(x)), 0.0, true_peak=2)
    got = int(np.argmax(np.abs(render(node, 6000)[:, 0]))) - 1000
    print("       %d samples - the 4x detector's group delay never reaches "
          "the audio path." % got)
    for one in built:
        one.deinit()
    print()


def g5_knee():
    print("G.5  DYN_LIMIT ignores knee_db; DYN_COMPRESS at ratio 1e6 is the")
    print("     brickwall. 1 kHz sine, threshold -12 dBFS, steady state.")
    frames = 12000
    n = np.arange(frames)

    def curve(mode, ratio, knee, levels):
        out = []
        for level_db in levels:
            tone = 10.0 ** (level_db / 20.0) * np.sin(
                2.0 * math.pi * 1000.0 * n / RATE)
            node = audiodynamics.Dynamics(
                mode, sample_rate=RATE, channel_count=2, threshold_db=-12.0,
                ratio=ratio, knee_db=knee, attack_ms=0.0, release_ms=150.0)
            node.play(source(pcm(tone)))
            out.append(peak_db(render(node, frames)[6000:, 0]))
            node.deinit()
        return out

    levels = [-13.0, -12.0, -6.0, -0.1]
    print("     in dBFS        %s" % "  ".join("%8.1f" % v for v in levels))
    for label, mode, ratio, knee in (
            ("LIMIT knee 0 ", audiodynamics.DYN_LIMIT, 4.0, 0.0),
            ("LIMIT knee 12", audiodynamics.DYN_LIMIT, 4.0, 12.0),
            ("COMP 1e6 kn 0", audiodynamics.DYN_COMPRESS, 1e6, 0.0),
            ("COMP 1e6 kn12", audiodynamics.DYN_COMPRESS, 1e6, 12.0)):
        row = curve(mode, ratio, knee, levels)
        print("     %s  %s" % (label, "  ".join("%8.3f" % v for v in row)))
    print("     The two LIMIT rows are identical: knee_db is not in that gain")
    print("     computer at all (audioif_dynamics.c:368-370).")
    print()


def g6_hold():
    print("G.6  hold_ms exists on the module and does nothing here.")
    print("     `gate_machine = hold_frames != 0 && mode == DYN_GATE`, "
          "audioif_dynamics.c:452-453")
    frames = 48000
    x = burst(frames)
    for hold in (0.0, 20.0):
        node, built = limiter(source(pcm(x)), -12.0, lookahead_ms=5.0,
                              catch=False)
        built[0].set(hold_ms=hold)
        print("     hold_ms=%5.1f on DYN_COMPRESS, 5 ms lookahead -> "
              "peak %8.2f dBFS" % (hold, peak_db(render(node, frames)[:, 0])))
        for one in built:
            one.deinit()
    print()


def g7_mixer_level():
    print("G7  audiomixer cannot be the Gain stage: voice level is clamped")
    print("    to 0..1 (audioif/src/cpython/audiomixer.py:143).")
    frames = 12000
    n = np.arange(frames)
    tone = 0.1 * np.sin(2.0 * math.pi * 1000.0 * n / RATE)
    mixer = audiomixer.Mixer(voice_count=1, sample_rate=RATE, channel_count=2,
                             bits_per_sample=16, samples_signed=True,
                             buffer_size=2048)
    mixer.voice[0].level = 4.0
    mixer.voice[0].play(source(pcm(tone)))
    out = render(mixer, frames)[2000:, 0]
    print("    level set to %.1f, reads back %.1f; in %.2f dBFS -> out "
          "%.2f dBFS" % (4.0, mixer.voice[0].level, peak_db(tone * 32768.0),
                         peak_db(out)))
    mixer.deinit()
    print()


def g8_wire_endpoint():
    print("G.8  the wire endpoint, and the detector epsilon that spoils it.")
    print("     `gain_to_db(state->envelope + 1e-6f)`, audioif_dynamics.c:749")
    frames = 8192
    n = np.arange(frames)
    ramp = ((n % 1024) / 1024.0) * 2.0 - 1.0
    ramp[::37] = 0.99997
    buffer = pcm(ramp)
    reference = np.frombuffer(bytes(memoryview(buffer).cast("B")),
                              dtype="<i2")
    for offset in (0.0, 0.00005, 0.0002, 0.001):
        node, built = limiter(source(buffer), 0.0, offset_db=offset)
        out = render(node, frames).reshape(-1).astype(np.int64)
        differ = int(np.count_nonzero(out != reference[:len(out)]))
        print("     threshold offset %+9.5f dB -> %5d of %d samples differ"
              % (offset, differ, len(out)))
        for one in built:
            one.deinit()
    print("     and the offset does not move the ceiling:")
    for offset in (0.0, 0.0002):
        for ceiling in (-24.0, -12.0, -1.0):
            tone = 0.999 * np.sin(2.0 * math.pi * 1000.0 * n / RATE)
            node, built = limiter(source(pcm(tone)), ceiling,
                                  release_ms=150.0, offset_db=offset)
            print("     offset %+8.5f dB, ceiling %+7.2f dB -> out peak "
                  "%9.4f dBFS" % (offset, ceiling,
                                  peak_db(render(node, frames)[4000:, 0])))
            for one in built:
                one.deinit()
    print()


def g9_internal_clamp():
    print("G.9  gain into a high ceiling clips inside the shape node, and the")
    print("     catch stage still lands the ceiling exactly.")
    print("     ceiling -0.3 dBFS, 1 ms burst 12 dB under it")
    frames = 48000
    x = burst(frames, level=10.0 ** (-12.0 / 20.0))
    for gain, look in ((0.0, 0.0), (12.0, 0.0), (12.0, 3.0), (12.0, 10.0)):
        shape_only, built_a = limiter(source(pcm(x)), -0.3, gain_db=gain,
                                      lookahead_ms=look, catch=False)
        first = render(shape_only, frames)
        clipped = int(np.count_nonzero(np.abs(first) >= 32767))
        whole, built_b = limiter(source(pcm(x)), -0.3, gain_db=gain,
                                 lookahead_ms=look)
        final = render(whole, frames)
        print("     gain %4.1f dB, lookahead %4.1f ms -> shape node %8.3f "
              "dBFS (%d samples clipped), final %8.3f dBFS"
              % (gain, look, peak_db(first[:, 0]), clipped,
                 peak_db(final[:, 0])))
        for one in built_a + built_b:
            one.deinit()
    print()


def main():
    print("Limiter palette probes, audioif at the pin, CPython")
    print("=" * 72)
    print()
    g1_catch_stage()
    g2_true_peak()
    g3_lookahead_arithmetic()
    g4_release_and_thd()
    g5_knee()
    g6_hold()
    g7_mixer_level()
    g8_wire_endpoint()
    g9_internal_clamp()


if __name__ == "__main__":
    main()
