#!/usr/bin/env python3
"""Generate a REAPER project that plays audiocomponents' own copy of a named
instrument through the micropython-vst3 plug-in, for the accuracy program's
listening rig (audiocomponents#15).

    tools/generate_rig.py <instrument> [out.RPP]

What it builds, every time, for any instrument named in `rig_instruments/`:

  - Two identical tracks ("<Instrument> A" / "<Instrument> B") holding the
    SAME gesture script, over the SAME bars, unsoloed - house style for an
    A/B (see docs, ShimmerLab): stack variants, never lay them end to end,
    so a future "B = the rewrite" is one keystroke (swap B's script) and one
    solo click, not a rebuild. This prototype has only one build, so A and B
    start identical.
  - A third, armed, empty "<Instrument> - Play" track on the same
    instrument, so Brad can play it himself once the gesture tracks have run.
  - Named project markers over every gesture, from the instrument's
    `rig_instruments/<name>.py` module - which is itself sourced from the
    Phase 2 listening guide's per-instrument section (read that first; it is
    the spec this module encodes as MIDI + macro automation).
  - Macro automation (PARMENV) wherever a gesture needs it - voicing and
    tremolo move macros, never a second copy of the notes.

Every script embedded in plug-in state is a two-line loader
(`mpvst_adapter.run("audioinstruments.<name>")`) exactly like
micropython-vst3's own `piece.shared_instruments()` builds for the
soundtrack - the sidecar resolves `audioinstruments` from whatever is
staged beside it. That only reads accuracy's own code (not audioif's) if
the installed bundle has accuracy's lib/ staged over the top; see
render_rig.sh, which does that before every render. This generator embeds
nothing but the two-line loader - the instrument's actual source is never
copied into the project, so there is exactly one place a byte can come
from at render time: the bundle currently staged.

Deterministic: no wall-clock, no randomness. The only external input is
`measure_peak`, which renders through the instrument's OWN current code (see
main()) so the level-match boost in rhodes' gesture 2c tracks the code
rather than a number someone typed in and forgot to update.
"""
import ast
import base64
import hashlib
import importlib.util
import struct
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO_DIR = TOOLS_DIR.parent
LIB_DIR = REPO_DIR / "lib" / "audioinstruments"
BUILD_DIR = REPO_DIR / "build" / "rig"

PPQ = 960
TEMPO_BPM = 120.0

# Byte-exact chunk layout, taken from micropython-vst3/reaper/generate_project.py
# (captured from a project REAPER itself saved) - this rig embeds state the
# same way the soundtrack generator does, so nothing about how a script
# reaches the plug-in is reinvented here.
INSTRUMENT_VST = ('<VST "VST3i: MicroPython Script Host" '
                  'MicroPythonVST3.vst3 0 "" '
                  '896536053{60A40168727C4E7DAAF808B790961DAA} ""')
INSTRUMENT_HEADER = [0x35700DF5, 0xFEED5EEE, 0x0,
                     0x2, 0x1, 0x0, 0x2, 0x0,
                     None, 0x1, 0xFFFF]
# ordinal position of the first macro among the plug-in's registered
# parameters: 0 Bypass, 1 Reload Script, 2 Engine Ready, 3 Engine Error,
# 4 Patches, 5..20 the sixteen macros. Verified live against REAPER 7.79
# via TrackFX_GetParamName (see generate_project.py's own note).
FIRST_MACRO_PARAM = 5

STEP_EPS = 0.02   # seconds between "hold old value" and "jump to new value"


_GUID_SEED = ["rig"]
_GUID_COUNTER = [0]


def guid():
    """A stable per-project GUID.

    REAPER only needs these unique within the file, and uuid4 made the
    generator non-deterministic: two runs of the same instrument produced
    .RPP files differing on 36 lines, so a project could not be diffed
    against itself or regenerated reproducibly. Derived from a counter and
    the project seed instead, which keeps them unique and makes two runs
    byte-identical.
    """
    _GUID_COUNTER[0] += 1
    digest = hashlib.sha256(
        ("%s/%d" % (_GUID_SEED[0], _GUID_COUNTER[0])).encode()).hexdigest()
    return "{%s-%s-%s-%s-%s}" % (digest[0:8], digest[8:12], digest[12:16],
                                 digest[16:20], digest[20:32])


def seconds_to_tick(t):
    return int(round(t * (TEMPO_BPM / 60.0) * PPQ))


# --- plug-in state (verbatim byte layout) -----------------------------------

def vst_chunk_lines(script_source, macros, header_words=INSTRUMENT_HEADER):
    comp = struct.pack("<ii", 2, 0)                      # version, bypass
    for index in range(16):
        comp += struct.pack("<f", macros.get(index, 0.5))
    comp += struct.pack("<ii", 4, len(script_source))    # pipeline, bytes
    comp += script_source

    data = struct.pack("<II", len(comp), 1) + comp + b"\0" * 8
    words = [len(data) if word is None else word for word in header_words]
    header = struct.pack("<%dI" % len(words), *words)
    footer = b"\0" * 6

    lines = [base64.b64encode(header).decode()]
    encoded = base64.b64encode(data).decode()
    lines += [encoded[i:i + 128] for i in range(0, len(encoded), 128)]
    lines.append(base64.b64encode(footer).decode())
    return lines


def envelope_block(kind, header_extra, points):
    lines = ["    <%s%s" % (kind, header_extra)]
    lines += ["      EGUID %s" % guid(),
              "      ACT 1 -1",
              "      VIS 1 1 1",
              "      LANEHEIGHT 0 0",
              "      ARM 0",
              "      DEFSHAPE 0 -1 -1"]
    for time_s, value, shape in points:
        lines.append("      PT %.9f %.9f %d" % (time_s, value, shape))
    lines.append("    >")
    return lines


def marker_line(index, position, name):
    # Verified 2026-09-02 against a live REAPER 7.79 save
    # (reaper.AddProjectMarker2 -> Main_SaveProjectEx -> read back): the
    # trailing " 0 0 1 R {GUID} 0 2" is what a plain point marker (not a
    # region) writes for every marker regardless of name/position, so it is
    # reused verbatim rather than guessed at.
    return '  MARKER %d %.9f "%s" 0 0 1 R %s 0 2' % (index, position, name,
                                                       guid())


def midi_events(notes):
    """Sorted (tick, order, message) - note-offs before note-ons at a tie."""
    events = []
    for start, dur, pitch, vel in notes:
        v = max(1, min(127, int(round(vel))))
        on = seconds_to_tick(start)
        off = seconds_to_tick(start + dur)
        if off <= on:
            off = on + 1
        events.append((on, 1, "90 %02x %02x" % (pitch, v)))
        events.append((off, 0, "80 %02x 00" % pitch))
    events.sort()
    return events


# --- macro automation: turn (time, value-or-None) transitions into a clean
#     step envelope, never a ramp between unrelated gestures --------------

def step_points(default, raw_points, eps=STEP_EPS):
    """`raw_points`: unsorted (time_s, value_0_1_or_None). None resolves to
    `default`. Returns REAPER (time, value, shape) points that hold each
    value flat until the next transition, then jump - never glide - because
    two macro-driven gestures several seconds apart must not audibly slide
    into each other in between.
    """
    pts = sorted(((t, default if v is None else v) for t, v in raw_points),
                 key=lambda p: p[0])
    out = []
    if not pts or pts[0][0] > eps:
        out.append((0.0, default, 0))
    prev_value = default
    for t, v in pts:
        if out and t - out[-1][0] > eps:
            out.append((max(0.0, t - eps), prev_value, 0))
        out.append((t, v, 0))
        prev_value = v
    return out


def vol_points(total_seconds, boosts, eps=STEP_EPS):
    """Track volume envelope: 1.0 (0 dB) everywhere except the declared
    (start, end, gain) windows, stepped the same way macro automation is."""
    events = [(0.0, 1.0)]
    for start, end, gain in sorted(boosts):
        events.append((max(0.0, start - eps), 1.0))
        events.append((start, gain))
        events.append((end, gain))
        events.append((min(total_seconds, end + eps), 1.0))
    events.sort()
    return [(t, v, 0) for t, v in events]


# --- reading the instrument's own declared metadata -------------------------

def literal_metadata(path):
    tree = ast.parse(path.read_text(), str(path))
    values = {}
    wanted = ("NAME", "DISPLAY_NAME", "MACRO_LABELS", "MACRO_MODES", "PATCHES")
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                values[target.id] = ast.literal_eval(node.value)
    return values


def patch0_macros(meta):
    """Patch 0's macros as {index: normalized 0.0-1.0 float}. Same reasoning
    as micropython-vst3's tools/piece.py::patch_macros: an unset macro
    resolves to what the instrument's own author intended (patch 0), not to
    the middle of its range."""
    patches = meta.get("PATCHES")
    if not patches or 0 not in patches:
        raise SystemExit("%s: no PATCHES[0] - every instrument must declare "
                          "a patch 0" % meta.get("NAME", "?"))
    _name, values = patches[0]
    return {i: v / 127.0 for i, v in enumerate(values)}


def shim_script(meta):
    """The two-line loader micropython-vst3's own shared_instruments() would
    generate - see the module docstring for why this, and not the literal
    instrument source, is what gets embedded."""
    name = meta["NAME"]
    lines = ["# mpvst-module: audioinstruments.%s" % name,
             "NAME = %r" % name]
    for field in ("DISPLAY_NAME", "MACRO_LABELS", "MACRO_MODES", "PATCHES"):
        if field in meta:
            lines.append("%s = %r" % (field, meta[field]))
    lines += ["", "import mpvst_adapter", "",
              'mpvst_adapter.run("audioinstruments.%s")' % name, ""]
    return "\n".join(lines).encode("utf-8")


# --- assembling one track ----------------------------------------------------

def gesture_track(name, pan, script, base_macros, macro_env, notes,
                  total_seconds, muted_solo="0 0 0"):
    lines = ["  <TRACK %s" % guid(),
             '    NAME "%s"' % name,
             "    TRACKHEIGHT 0 0 0 0 0 0",
             "    VOLPAN 1 %.6f 1 -1 1" % pan,
             "    MUTESOLO %s" % muted_solo,
             "    NCHAN 2",
             "    FX 1",
             "    TRACKID %s" % guid(),
             "    PERF 0",
             "    MIDIOUT -1 -1",
             "    MAINSEND 1 0"]
    lines += envelope_block("VOLENV2", "",
                            vol_points(total_seconds, macro_env.pop("__vol__", [])))
    lines.append("    <FXCHAIN")
    lines.append("      SHOW 0")
    lines.append("      LASTSEL 0")
    lines.append("      DOCKED 0")
    lines.append("      BYPASS 0 0 0")
    lines.append("      " + INSTRUMENT_VST)
    for chunk_line in vst_chunk_lines(script, base_macros):
        lines.append("        " + chunk_line)
    lines += ["      >", "      FLOATPOS 0 0 0 0", "      FXID %s" % guid()]
    for index in sorted(macro_env):
        points = step_points(base_macros.get(index, 0.5), macro_env[index])
        lines += ["  " + line for line in envelope_block(
            "PARMENV", " %d 0 1 0.5" % (FIRST_MACRO_PARAM + index), points)]
    lines.append("      WAK 0 0")
    lines.append("    >")

    if notes:
        lines += midi_item(name, notes, total_seconds)
    return lines


def midi_item(name, notes, total_seconds):
    lines = ["    <ITEM",
             "      POSITION 0",
             "      SNAPOFFS 0",
             "      LENGTH %.9f" % total_seconds,
             "      LOOP 0",
             "      ALLTAKES 0",
             "      FADEIN 0 0 0 1 0 0 0",
             "      FADEOUT 0 0 0 1 0 0 0",
             "      MUTE 0 0",
             "      SEL 0",
             "      IGUID %s" % guid(),
             "      IID 1",
             '      NAME "%s"' % name,
             "      VOLPAN 1 0 1 -1",
             "      SOFFS 0 0",
             "      PLAYRATE 1 1 0 -1 0 0.0025",
             "      CHANMODE 0",
             "      GUID %s" % guid(),
             "      <SOURCE MIDI",
             "        HASDATA 1 %d QN" % PPQ,
             "        CCINTERP 32",
             "        POOLEDEVTS %s" % guid()]
    cursor = 0
    for tick, _order, message in midi_events(notes):
        lines.append("        E %d %s" % (tick - cursor, message))
        cursor = tick
    end_tick = seconds_to_tick(total_seconds)
    lines.append("        E %d b0 7b 00" % max(0, end_tick - cursor))
    lines += ["        CCINTERP 32",
              "        CHASE_CC_TAKEOFFS 1",
              "        GUID %s" % guid(),
              "        IGNTEMPO 0 %d 4 4" % int(TEMPO_BPM),
              "        SRCCOLOR 2",
              "        EVTFILTER 0 -1 -1 -1 -1 0 0 0 0 -1 -1 -1 -1 0 -1 0 -1 -1",
              "      >",
              "    >",
              "  >"]
    return lines


def play_track(name, script, base_macros):
    """An armed, empty track on the same instrument, so Brad can play it
    himself. REC line verified 2026-09-02 against a live REAPER 7.79 save
    (I_RECARM=1, I_RECMON=1, I_RECINPUT = all-MIDI-inputs/all-channels)."""
    lines = ["  <TRACK %s" % guid(),
             '    NAME "%s"' % name,
             "    TRACKHEIGHT 0 0 0 0 0 0",
             "    VOLPAN 1 0 1 -1 1",
             "    MUTESOLO 0 0 0",
             # Monitoring ON so it is playable, record-arm OFF so a stray
             # transport-record keystroke cannot overwrite anything.
             "    REC 0 5088 1 0 0 0 0 0",
             "    NCHAN 2",
             "    FX 1",
             "    TRACKID %s" % guid(),
             "    PERF 0",
             "    MIDIOUT -1 -1",
             "    MAINSEND 1 0",
             "    <FXCHAIN",
             "      SHOW 0",
             "      LASTSEL 0",
             "      DOCKED 0",
             "      BYPASS 0 0 0",
             "      " + INSTRUMENT_VST]
    for chunk_line in vst_chunk_lines(script, base_macros):
        lines.append("        " + chunk_line)
    lines += ["      >", "      FLOATPOS 0 0 0 0", "      FXID %s" % guid(),
              "      WAK 0 0", "    >", "  >"]
    return lines


def load_gesture_module(name):
    path = TOOLS_DIR / "rig_instruments" / (name + ".py")
    if not path.is_file():
        available = sorted(p.stem for p in
                           (TOOLS_DIR / "rig_instruments").glob("*.py"))
        raise SystemExit("no gesture module for %r at %s (have: %s)"
                         % (name, path, ", ".join(available) or "none"))
    spec = importlib.util.spec_from_file_location("rig_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_project(instrument, measure_peak):
    src = LIB_DIR / (instrument + ".py")
    if not src.is_file():
        raise SystemExit("no audiocomponents instrument at %s" % src)
    meta = literal_metadata(src)
    base_macros = patch0_macros(meta)
    script = shim_script(meta)

    gesture_module = load_gesture_module(instrument)
    spec = gesture_module.build(measure_peak)
    notes = spec["notes"]
    markers = spec["markers"]
    macro_env = {k: list(v) for k, v in spec["macro_env"].items()}
    macro_env["__vol__"] = spec.get("vol_boosts", [])
    total_seconds = spec["total_seconds"]

    display = meta.get("DISPLAY_NAME", instrument)
    lines = ['<REAPER_PROJECT 0.1 "7.79" 0',
             "  RIPPLE 0",
             "  GROUPOVERRIDE 0 0 0",
             "  AUTOXFADE 129",
             "  TEMPO %.6f 4 4" % TEMPO_BPM,
             "  SAMPLERATE 48000 0 0",
             "  MASTER_VOLUME 1.0 0 -1 -1 1",
             "  MASTER_NCH 2 2",
             "  <TEMPOENVEX",
             "    EGUID %s" % guid(),
             "    ACT 1 -1",
             "    VIS 1 0 1",
             "    LANEHEIGHT 0 0",
             "    ARM 0",
             "    DEFSHAPE 1 -1 -1",
             "    PT 0.000000000 %.6f 1" % TEMPO_BPM,
             "  >"]

    for index, (position, name) in enumerate(markers, start=1):
        lines.append(marker_line(index, position, name))

    # A and B: identical script/macros/notes today. A future rewrite swaps
    # only B's embedded script (or its macro defaults) and the comparison is
    # a solo click - see the module docstring.
    # Both tracks CENTRED, and B MUTED on open.
    #
    # Panning them apart gave the two sides of the A/B two different stereo
    # images, so a listener comparing them would be judging position as well
    # as tone. And leaving both audible summed two identical copies into the
    # master, which clipped - manufacturing exactly the grit the bark test
    # asks Brad to judge. Press play on an unfixed project and the instrument
    # sounds more aggressive than it is.
    #
    # So B ships muted: press play and hear ONE instance, centred, unclipped.
    # The A/B is then a mute or solo click, which is the house layout
    # (stacked over the same bars, solo-switched) rather than end-to-end.
    lines += gesture_track("%s A -- current" % display, 0.0, script,
                           dict(base_macros),
                           {k: list(v) for k, v in macro_env.items()},
                           notes, total_seconds)
    lines += gesture_track("%s B -- current (MUTED: unmute to A/B)" % display,
                           0.0, script,
                           dict(base_macros),
                           {k: list(v) for k, v in macro_env.items()},
                           notes, total_seconds, muted_solo="1 0 0")
    lines += play_track("%s -- Play" % display, script, dict(base_macros))
    lines.append(">")
    return "\n".join(lines) + "\n", spec


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: generate_rig.py <instrument> [out.RPP]")
    instrument = sys.argv[1]
    # Seed the GUIDs from the instrument so two instruments' projects
    # never collide, while regenerating one twice stays byte-identical.
    _GUID_SEED[0] = instrument
    _GUID_COUNTER[0] = 0
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else (
        BUILD_DIR / ("%s_rig.RPP" % instrument))
    out.parent.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(REPO_DIR / "lib"))
    import audiocore
    import audioinstruments

    def measure_peak(chord, velocity, seconds=2.0, sr=48000, macros=None):
        """Peak amplitude of `chord` at `velocity`, optionally with macros set.

        `macros` lets a gesture level-match a comparison that changes a MACRO
        rather than a velocity - the voicing test needs this, because "clangy
        versus warm" cannot be judged while the two settings also differ in
        loudness. Measured through the instrument's own current code so the
        number can never drift from what the project actually renders.
        """
        inst = audioinstruments.create(instrument, sample_rate=sr,
                                       channel_count=2)
        for index, value in (macros or {}).items():
            inst.set_macro(index, value * 127.0)
        for pitch in chord:
            inst.note_on(pitch, velocity)
        peak = 0.0
        frames = 0
        total = int(seconds * sr)
        while frames < total:
            _result, buf = audiocore.get_buffer(inst.output)
            chunk = bytes(buf)
            for i in range(0, len(chunk), 2):
                s = int.from_bytes(chunk[i:i + 2], "little", signed=True)
                v = abs(s) / 32768.0
                if v > peak:
                    peak = v
            frames += len(chunk) // 4
        inst.deinit()
        return peak

    text, spec = build_project(instrument, measure_peak)
    out.write_text(text)
    print("wrote %s (%d gestures, %.1f s, %d macro-automated params)"
          % (out, len(spec["markers"]), spec["total_seconds"],
             len(spec["macro_env"])))
    gesture_module = load_gesture_module(instrument)
    for line in getattr(gesture_module, "NOT_PLAYABLE", ()):
        print("NOT PLAYABLE: %s" % line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
