"""Render an audioinstruments component's one-shots, kit hit, or demo phrase.

    python tools/render_component.py <name> <outdir> [oneshots|kit|phrase] [sr]

Deliberately dual-runtime: runs under CPython and the workspace MicroPython
(MICROPYPATH=<repo>:<repo>/lib), so Station B's cross-interpreter check and
Station C's evidence renders come from the same code. stdlib-free of numpy,
argparse, pathlib, and wave on purpose.

- oneshots: one WAV per NOTE_MAP entry, fresh instrument each, 2.0 s.
- kit: every NOTE_MAP note struck at t=0 in map order on ONE instrument
  (the voice-stealing probe: if the pool exhausts, the first-struck voices
  vanish from the mix), 2.0 s.
- phrase: a fixed two-bar groove at 120 BPM for A/B listening.

Events land on block boundaries (the pull size), which is what makes the
render identical across interpreters.
"""
import sys
import audiocore
import audioinstruments


def wav_header(data_len, sample_rate, channels):
    byte_rate = sample_rate * channels * 2
    return (b"RIFF" + (36 + data_len).to_bytes(4, "little")
            + b"WAVEfmt " + (16).to_bytes(4, "little")
            + (1).to_bytes(2, "little") + channels.to_bytes(2, "little")
            + sample_rate.to_bytes(4, "little") + byte_rate.to_bytes(4, "little")
            + (channels * 2).to_bytes(2, "little") + (16).to_bytes(2, "little")
            + b"data" + data_len.to_bytes(4, "little"))


def render(instrument, seconds, sample_rate, events, path):
    """Pull blocks for `seconds`, delivering (block_index, fn) events.

    Streams straight to `path` and hashes incrementally - a whole render
    held in RAM is a MemoryError on MicroPython. Returns the hex digest
    of the PCM (header excluded).
    """
    import hashlib
    import binascii
    pending = sorted(events, key=lambda e: e[0])
    block = 0
    frames_done = 0
    total = int(seconds * sample_rate)
    frames_per_block = None
    hasher = hashlib.sha256()
    f = open(path, "wb")
    f.write(b"\x00" * 44)  # placeholder; header rewritten when size is known
    data_len = 0
    while frames_done < total:
        while pending and pending[0][0] <= block:
            pending.pop(0)[1]()
        result, buf = audiocore.get_buffer(instrument.output)
        chunk = bytes(buf)
        f.write(chunk)
        hasher.update(chunk)
        data_len += len(chunk)
        if frames_per_block is None:
            frames_per_block = len(chunk) // 4  # 16-bit stereo
        frames_done += frames_per_block
        block += 1
    f.seek(0)
    f.write(wav_header(data_len, sample_rate, 2))
    f.close()
    return binascii.hexlify(hasher.digest()).decode()


def main():
    name = sys.argv[1]
    outdir = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "oneshots"
    sr = int(sys.argv[4]) if len(sys.argv) > 4 else 48000
    try:
        import os
        os.mkdir(outdir)
    except OSError:
        pass

    module = __import__("audioinstruments." + name, None, None, ("NOTE_MAP",))
    note_map = getattr(module, "NOTE_MAP", ())

    if mode == "oneshots":
        for note, label in note_map:
            inst = audioinstruments.create(name, sample_rate=sr, channel_count=2)
            fname = "%s/%02d_%s.wav" % (outdir, note, label.replace(" ", "_"))
            digest = render(inst, 2.0, sr,
                            [(0, lambda n=note: inst.note_on(n, 100))], fname)
            inst.deinit()
            try:
                import gc
                gc.collect()
            except ImportError:
                pass
            print("%-24s %s" % (fname.rsplit("/", 1)[-1], digest[:16]))
    elif mode == "kit":
        inst = audioinstruments.create(name, sample_rate=sr, channel_count=2)
        evs = [(0, lambda n=note: inst.note_on(n, 100)) for note, _ in note_map]
        digest = render(inst, 2.0, sr, evs, outdir + "/kit.wav")
        inst.deinit()
        print("kit.wav %s" % digest[:16])
    elif mode == "phrase":
        # Two bars, 120 BPM: BD quarters, SD 2+4, CH eighths, OH bar-end,
        # second bar adds toms/cowbell/clap. Block-quantized.
        inst = audioinstruments.create(name, sample_rate=sr, channel_count=2)
        result, buf = audiocore.get_buffer(inst.output)
        fpb = len(bytes(buf)) // 4
        inst.reset()
        beat = 60.0 / 120.0
        def at(t):
            return int(t * sr / fpb)
        evs = []
        for bar in (0, 1):
            for q in range(4):
                t = (bar * 4 + q) * beat
                evs.append((at(t), lambda: inst.note_on(36, 110)))
                if q in (1, 3):
                    evs.append((at(t), lambda: inst.note_on(38, 100)))
                for e in (0.0, 0.5):
                    evs.append((at(t + e * beat), lambda: inst.note_on(42, 80)))
        evs.append((at(3.5 * beat), lambda: inst.note_on(46, 90)))
        evs.append((at(4 * beat + 2 * beat), lambda: inst.note_on(39, 100)))
        evs.append((at(4 * beat + 3 * beat), lambda: inst.note_on(56, 90)))
        for i, tom in enumerate((48, 45, 41)):
            evs.append((at(7 * beat + i * 0.33 * beat), lambda n=tom: inst.note_on(n, 100)))
        digest = render(inst, 8 * beat + 1.0, sr, evs, outdir + "/phrase.wav")
        inst.deinit()
        print("phrase.wav %s" % digest[:16])
    else:
        raise SystemExit("mode must be oneshots|kit|phrase")


main()
