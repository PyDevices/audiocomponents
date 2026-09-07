"""Station C's cross-interpreter analysis for `TransientShaper`.

Reads the renders `transientshaper_interpreters.sh` took on CPython,
MicroPython and the patched CircuitPython, and does two things with them:
the Tier 1 invariants that can be read off a finished render (WIRE, TAIL,
LEVEL, CLICK), per interpreter and per rate; and the DIGEST comparison the
class gate asks for. The analysis is CPython's, as the kit spec's section 1
requires - nothing here runs on a board.

    audiocomponents/.venv/bin/python \
        tools/phase2_probes/transientshaper_across.py <renderdir>
"""

import json
import os
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "lib"))

import effect_measurements as kit                         # noqa: E402

INTERPRETERS = ("cpython", "micropython", "circuitpython-effects")
RATES = (48000, 44100, 22050)
PROBES = os.path.join(ROOT, "tools", "effect_probes")


def source_pcm(name, rate, channels=2):
    path = "%s/%d/%dch/%s.wav" % (PROBES, rate, channels, name)
    with wave.open(path, "rb") as handle:
        return handle.readframes(handle.getnframes())


def load(directory, stem, rate, interpreter):
    base = "%s/%s" % (directory, stem)
    with wave.open(base + ".wav", "rb") as handle:
        pcm = handle.readframes(handle.getnframes())
    with open(base + ".json") as handle:
        meta = json.load(handle)
    return kit.Render.from_pcm(pcm, rate, meta["channel_count"],
                               block=meta["block_frames"],
                               interpreter=interpreter,
                               label=meta["probe"]), meta


def stem(probe, rate, macros=""):
    return "TransientShaper__%s__%d__2ch__blk256%s" % (probe, rate, macros)


def main(argv):
    directory = argv[0] if argv else os.path.join(ROOT, "..", "ts-renders")
    print("Cross-interpreter leg -- TransientShaper, renders from %s"
          % directory)

    print("\nTier 1 off the rendered bytes, per interpreter and rate")
    for rate in RATES:
        for interpreter in INTERPRETERS:
            here = os.path.join(directory, interpreter)
            row = []

            render, meta = load(here, stem("ramp_fs", rate), rate,
                                interpreter)
            result = kit.wire(render, kit.Render.from_pcm(
                source_pcm("ramp_fs", rate), rate, 2),
                latency_samples=meta["latency_samples"])
            row.append("WIRE %s (%d differ)"
                       % ("pass" if result["passed"] else "FAIL",
                          result["values"]["differing_samples"]))

            render, meta = load(here, stem("burst_silence", rate,
                                           "__m0-114.3__m1-31.75"),
                                rate, interpreter)
            result = kit.tail(render, burst_end_frame=int(rate * 0.2),
                              declared_tail_samples=meta["tail_samples"])
            row.append("TAIL %s (residual %d LSB)"
                       % ("pass" if result["passed"] else "FAIL",
                          result["values"]["residual_lsb"]))

            render, meta = load(here, stem("noise_det", rate), rate,
                                interpreter)
            result = kit.level(render, kit.Render.from_pcm(
                source_pcm("noise_det", rate), rate, 2))
            row.append("LEVEL %s (%s dB)"
                       % ("pass" if result["passed"] else "FAIL",
                          result["values"]["rms_db"][0]))

            render, meta = load(here, stem("click_stereo", rate), rate,
                                interpreter)
            result = kit.click(render, kit.Render.from_pcm(
                source_pcm("click_stereo", rate), rate, 2),
                meta["latency_samples"])
            row.append("CLICK %s (%s samples)"
                       % ("pass" if result["passed"] else "FAIL",
                          result["values"]["measured_latency_samples"][0]))
            print("  %6d Hz  %-22s %s" % (rate, interpreter, "  ".join(row)))

    print("\nDIGEST -- FNV-1a over the PCM bytes, block 256")
    print("  %-16s %-7s %-10s %-10s %-10s %s"
          % ("probe", "rate", "cpython", "micropython", "cpy-effects",
             "agree"))
    print("  the first three rows are the class at its defaults, which is a "
          "wire; the last three\n  are the shaper working (patch 1 Snap, "
          "and Attack +12 with Sustain -12).")
    for probe, macros in (("chord", ""), ("noise_det", ""),
                          ("sweep_log", ""),
                          ("chord", "__p1"), ("noise_det", "__p1"),
                          ("burst_silence", "__m0-114.3__m1-31.75")):
        for rate in RATES:
            digests = []
            for interpreter in INTERPRETERS:
                render, meta = load(os.path.join(directory, interpreter),
                                    stem(probe, rate, macros), rate,
                                    interpreter)
                digests.append(meta["digest_fnv1a"])
                if meta["silent"]:
                    digests[-1] += " SILENT"
            agree = "yes" if len(set(digests)) == 1 else "NO"
            print("  %-16s %-7d %-10s %-10s %-10s %s"
                  % (probe + macros.replace("__", " "), rate, digests[0],
                     digests[1], digests[2], agree))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
