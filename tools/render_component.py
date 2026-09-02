"""Render an audioinstruments component's one-shots, kit hit, or phrases.

    python tools/render_component.py <name> <outdir> [MODE] [sr]
    MODE = oneshots | kit | phrase | transitions

Deliberately dual-runtime: runs under CPython and the workspace MicroPython
(MICROPYPATH=<repo>:<repo>/lib), so Station B's cross-interpreter check and
Station C's evidence renders come from the same code. stdlib-free of numpy,
argparse, pathlib, and wave on purpose.

- oneshots: one WAV per NOTE_MAP entry, fresh instrument each, 2.0 s.
- kit: every NOTE_MAP note struck at t=0 in map order on ONE instrument
  (the voice-stealing probe: if the pool exhausts, the first-struck voices
  vanish from the mix), 2.0 s.
- phrase: a fixed two-bar groove at 120 BPM for A/B listening.
- transitions: every shared-circuit pitch pair, played so that an inherited
  envelope is audible as a mismatch between two hits of the SAME voice. Unlike
  the other three this mode is CPython-only, because discovery instruments
  synthio.Synthesizer.press (see tools/shared_circuits.py).

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
    elif mode == "transitions":
        # The listening case the two-bar phrase cannot make: a voice heard
        # once in its sibling's shadow and once on its own, back to back.
        #
        # Several kits give two voices ONE permanent synthio.Note and
        # reconfigure it per hit. A target that re-reads the envelope every
        # block plays both hits identically; one that bakes the envelope into
        # the state at press time lets the second voice keep stepping the
        # first's decay, and a closed hat struck after an open one rings as an
        # open hat. That defect survived a listening pass in eight of ten kits
        # because no material ever put the two hits side by side - a long hat
        # still sounds like a hat. Here they are adjacent, so the fault is a
        # mismatch anyone can hear without being told what to listen for.
        #
        # Imported inside the branch: discovery replaces a synthio class
        # attribute, which only takes on the CPython twin, and the other three
        # modes must stay runnable under MicroPython.
        try:
            from shared_circuits import (differing, frames_per_block,
                                         gap_blocks, solo_decay)
        except ImportError:                       # run as -m, MICROPYPATH
            from tools.shared_circuits import (differing, frames_per_block,
                                               gap_blocks, solo_decay)
        pairs = sorted(pair
                       for circuit in differing(name, sample_rate=sr,
                                                channel_count=2)
                       for pair in circuit.pairs())
        if not pairs:
            print("%s: no shared circuit assigns differing envelopes, "
                  "nothing to render" % name)
            return
        labels = dict(note_map)

        def label(pitch):
            return "%d %s" % (pitch, labels.get(pitch, "?"))

        inst = audioinstruments.create(name, sample_rate=sr, channel_count=2)
        result, buf = audiocore.get_buffer(inst.output)
        fpb = len(bytes(buf)) // 4
        inst.reset()
        def at(t):
            return int(t * sr / fpb)
        # 0.25 s is where the fault was measured across all ten kits (a closed
        # hat struck 250 ms after an open one). 1.5 s for the solo repeat: the
        # longest voice on any of these circuits is gone by 0.76 s, so even a
        # hit that inherited the sibling's full decay has ended and the repeat
        # is a genuinely fresh press - it is the control, not a second symptom.
        # A 3.0 s leg then leaves ~0.7 s of silence before the next one, which
        # is what keeps the pairs from blurring into each other.
        # The gap is taken from the FIRST voice's own decay, never fixed, and
        # it is the difference between material that exposes the fault and
        # material that does not. A fixed 0.25 s was tried first: on a broken
        # floor it left 31 of the 52 legs across these kits bit-identical to a
        # healthy one, because the fault can only express while the first
        # note's envelope is still stepping. Any voice shorter than the gap has
        # already finished, the next press builds a fresh state, and the leg
        # sounds correct however broken the floor is. tr707 - the kit with the
        # worst fault of all - exposed 1 of its 8 pairs that way.
        #
        # `gap_blocks` is the same rule the overlap gate measures at, imported
        # from the same module, so what a listener hears here and what the gate
        # asserts are the same moment. Solo decays are cached: 26 pairs need
        # far fewer than 52 renders.
        fpb_seconds = frames_per_block(sr) / float(sr)
        decay_cache = {}

        def decay_seconds(pitch):
            if pitch not in decay_cache:
                _peak, blocks = solo_decay(name, pitch, sample_rate=sr)
                decay_cache[pitch] = (blocks or 0) * fpb_seconds
            return decay_cache[pitch]

        # One velocity throughout: order is meant to be the only variable.
        evs = []
        start = 0.0
        print("%s: %d shared-circuit pair%s, %d legs"
              % (name, len(pairs), "" if len(pairs) == 1 else "s",
                 2 * len(pairs)))
        for a, b in pairs:
            for first, second in ((a, b), (b, a)):
                lead = decay_seconds(first)
                tail = decay_seconds(second)
                overlap = max(2 * fpb_seconds,
                              gap_blocks(int(round(lead / fpb_seconds)))
                              * fpb_seconds)
                # Control FIRST, then the pair. Ordering it the other way
                # round puts the two hits being compared max(lead, tail) +
                # tail apart, because the control has to outwait a hit that
                # may have wrongly inherited the first voice's whole decay -
                # 1.74 s on the tr707 open hat, which is longer than anyone
                # holds a timbre in mind. Hearing the voice alone first and
                # then in shadow needs only its OWN decay to clear: the same
                # comparison at 0.93 s.
                lead_in = tail + 0.15
                pair_at = lead_in + overlap
                leg = pair_at + max(lead, tail) + 0.5
                evs.append((at(start), lambda n=second: inst.note_on(n, 100)))
                evs.append((at(start + lead_in),
                            lambda n=first: inst.note_on(n, 100)))
                evs.append((at(start + pair_at),
                            lambda n=second: inst.note_on(n, 100)))
                print("  %6.2f s  %s alone, then %s under %s "
                      "(gap %5.1f ms, %4.2f s apart)"
                      % (start, label(second), label(second), label(first),
                         overlap * 1000.0, pair_at))
                start += leg
        digest = render(inst, start, sr, evs, outdir + "/transitions.wav")
        inst.deinit()
        print("transitions.wav %s" % digest[:16])
    else:
        raise SystemExit("mode must be oneshots|kit|phrase|transitions")


main()
