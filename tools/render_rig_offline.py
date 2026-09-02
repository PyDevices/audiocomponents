#!/usr/bin/env python3
"""Render a rig's gestures directly through this repo's own
`audioinstruments.create()` - no REAPER, no plug-in, no IPC - as the
offline reference `compare_rig.py` checks the plug-in bounce against.

    tools/render_rig_offline.py <instrument> [out.wav]

Uses the SAME gesture module (`rig_instruments/<name>.py`) and the SAME
`measure_peak` helper `generate_rig.py` uses, so the level-match boost in
rhodes' gesture 2c is the identical number on both paths - it is computed
once per path, from the same instrument code, not shared as a literal.

Events land on block boundaries (the instrument's own pull size), matching
`audioinstruments`'s existing `tools/render_component.py`: this instrument
never reads its `sample_position` argument (see rhodes.py's handle_event),
so block-boundary delivery is the actual granularity of a note here, not
an approximation of finer timing.
"""
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO_DIR = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(REPO_DIR / "lib"))

from generate_rig import load_gesture_module  # noqa: E402

import audiocore  # noqa: E402
import audioinstruments  # noqa: E402


def wav_header(data_len, sample_rate, channels):
    byte_rate = sample_rate * channels * 2
    return (b"RIFF" + (36 + data_len).to_bytes(4, "little")
            + b"WAVEfmt " + (16).to_bytes(4, "little")
            + (1).to_bytes(2, "little") + channels.to_bytes(2, "little")
            + sample_rate.to_bytes(4, "little") + byte_rate.to_bytes(4, "little")
            + (channels * 2).to_bytes(2, "little") + (16).to_bytes(2, "little")
            + b"data" + data_len.to_bytes(4, "little"))


def measure_peak_factory(instrument, sr):
    def measure_peak(chord, velocity, seconds=2.0):
        inst = audioinstruments.create(instrument, sample_rate=sr,
                                       channel_count=2)
        for pitch in chord:
            inst.note_on(pitch, velocity)
        peak = 0.0
        frames = 0
        total = int(seconds * sr)
        while frames < total:
            _r, buf = audiocore.get_buffer(inst.output)
            chunk = bytes(buf)
            for i in range(0, len(chunk), 2):
                s = int.from_bytes(chunk[i:i + 2], "little", signed=True)
                v = abs(s) / 32768.0
                if v > peak:
                    peak = v
            frames += len(chunk) // 4
        inst.deinit()
        return peak
    return measure_peak


def apply_vol_boosts(pcm, sr, channels, boosts):
    """Multiply the same fader-boost windows the .RPP's track volume
    envelope carries (see generate_rig.py's vol_points), so a segment the
    rig deliberately turns up is turned up in the offline comparison too -
    the boost is a mixing decision this rig makes on the plug-in's output,
    not something the instrument itself does, and both paths must agree
    on it to be comparable."""
    if not boosts:
        return pcm
    frame_bytes = 2 * channels
    n_frames = len(pcm) // frame_bytes
    out = bytearray(pcm)
    for start, end, gain in boosts:
        s0 = max(0, int(start * sr))
        s1 = min(n_frames, int(end * sr))
        for frame in range(s0, s1):
            off = frame * frame_bytes
            for ch in range(channels):
                idx = off + ch * 2
                v = int.from_bytes(out[idx:idx + 2], "little", signed=True)
                v = max(-32768, min(32767, int(round(v * gain))))
                out[idx:idx + 2] = int(v).to_bytes(2, "little", signed=True)
    return bytes(out)


def render(instrument, spec, sr, path):
    inst = audioinstruments.create(instrument, sample_rate=sr,
                                   channel_count=2)
    result, buf = audiocore.get_buffer(inst.output)
    fpb = len(bytes(buf)) // 4
    inst.reset()

    def at(t):
        return int(t * sr / fpb)

    events = []
    for start, dur, pitch, vel in spec["notes"]:
        events.append((at(start), lambda p=pitch, v=vel: inst.note_on(p, v)))
        events.append((at(start + dur), lambda p=pitch: inst.note_on(p, 0)))
    base = spec["_base_macros"]
    for index, points in spec["macro_env"].items():
        for t, v in sorted(points, key=lambda p: p[0]):
            value = base.get(index, 0.5) if v is None else v
            events.append((at(t), lambda i=index, x=value:
                          inst.set_macro(i, x * 127.0)))

    total = int(spec["total_seconds"] * sr)
    pending = sorted(events, key=lambda e: e[0])
    block = 0
    frames_done = 0
    pcm = bytearray()
    while frames_done < total:
        while pending and pending[0][0] <= block:
            pending.pop(0)[1]()
        _r, buf = audiocore.get_buffer(inst.output)
        chunk = bytes(buf)
        pcm += chunk
        frames_done += fpb
        block += 1
    inst.deinit()

    pcm = apply_vol_boosts(bytes(pcm), sr, 2, spec.get("vol_boosts", []))
    with open(path, "wb") as f:
        f.write(wav_header(len(pcm), sr, 2))
        f.write(pcm)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: render_rig_offline.py <instrument> [out.wav]")
    instrument = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else (
        REPO_DIR / "build" / "rig" / ("%s_offline.wav" % instrument))
    out.parent.mkdir(parents=True, exist_ok=True)
    sr = 48000

    from generate_rig import literal_metadata, patch0_macros
    meta = literal_metadata(REPO_DIR / "lib" / "audioinstruments" /
                            (instrument + ".py"))
    base_macros = patch0_macros(meta)

    module = load_gesture_module(instrument)
    spec = module.build(measure_peak_factory(instrument, sr))
    spec["_base_macros"] = base_macros

    render(instrument, spec, sr, out)
    print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
