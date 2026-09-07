"""Station C measurements for `TransientShaper` (Phase 2 class gate).

Everything `docs/effects/TransientShaper-evidence.md` states comes from one
run of this file, and every trait it calls *demonstrated* is run twice: once
clean, and once with a fault of the same kind planted in the class, so a
green result means something.

    audiocomponents/.venv/bin/python \
        tools/phase2_probes/transientshaper_evidence.py [--tier1-only]

The class is driven through `audioeffects.create()`, never through a raw
node: at Station C the subject is the class. Renders taken on MicroPython
and the patched CircuitPython come from `tools/render_effect.py` on those
interpreters; the analysis is CPython's, as the kit spec's section 1 says.
"""

import math
import os
import sys
import wave
from array import array

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "lib"))

import audioeffects                                       # noqa: E402
from audioeffects._component import macro_value as \
    _component_macro_value                                # noqa: E402
import effect_measurements as kit                         # noqa: E402
from support import kit_probes as probes                  # noqa: E402
from support import kit_faults as faults                  # noqa: E402

#: The faulted subclasses below live in this module, and
#: `_component` reads VENDOR off a class's defining module.
VENDOR = "PyDevices"

CLASS = "TransientShaper"
RATES = (48000, 44100, 22050)
PROBES = os.path.join(ROOT, "tools", "effect_probes")

#: Attack +12 dB, Sustain 0, Output 0, Speed 1x, Hold 150 ms -- the settings
#: T1, T3 and T5 are stated at. MIDI, because that is what the renderer and
#: `set_macro` take.
ATTACK_UP = {0: 127 * (12.0 + 15.0) / 30.0}
SUSTAIN_DOWN = {1: 127 * (-12.0 + 24.0) / 48.0}
BOTH_SET = {0: ATTACK_UP[0], 1: SUSTAIN_DOWN[1]}


# -- faults planted in the class, one per demonstrated trait ---------------

def _faulted(**overrides):
    """A TransientShaper whose node is built with `overrides` applied. The
    surface, the macros and the patches are untouched: only the node option
    named moves, which is what makes each of these a fault *of the same
    kind* as the trait it breaks."""
    base = audioeffects.TransientShaper

    class Faulted(base):
        NAME = base.NAME

        def _build(self, **options):
            base._build(self, **options)
            self._node.set(**overrides)
    Faulted.__name__ = "Faulted" + "".join(
        part.title() for part in sorted(overrides))
    return Faulted


class StuckDcTail(audioeffects.TransientShaper):
    """TAIL's fault: +1 LSB of DC held after the node has seen signal - the
    audioif#23 residue, on a class whose clean tail is exact zero."""

    NAME = audioeffects.TransientShaper.NAME

    def _build(self, **options):
        audioeffects.TransientShaper._build(self, **options)
        stuck = faults.StuckDc(self._output, residue_lsb=1)
        self._own(stuck)
        self._output = stuck


class LiveAfterDeinit(audioeffects.TransientShaper):
    """STATE's fault: the node the class built is not released, because it
    was registered with `deinit=False`."""

    NAME = audioeffects.TransientShaper.NAME

    def _build(self, **options):
        audioeffects.TransientShaper._build(self, **options)
        self._deinits[0] = False


class HalvedAttackSpan(audioeffects.TransientShaper):
    """T3's fault: the Attack span halved *inside the macro*, so the knob
    still reads +-15 dB and the node gets half of it. A fault written into
    `_build` would be undone by the macro seeding that follows it, which is
    itself worth knowing."""

    NAME = audioeffects.TransientShaper.NAME

    def _apply_macro(self, index, position):
        if index == 0:
            value = _component_macro_value(self._MACRO_RANGES[0], position)
            self._node.set(attack_gain_db=value / 2.0)
            return
        audioeffects.TransientShaper._apply_macro(self, index, position)


class NoPeakHold(audioeffects.TransientShaper):
    """T4's fault: Sustain Hold forced to 0, so the sustain envelope is a
    plain follower and the differential falls away with the note instead of
    growing through it."""

    NAME = audioeffects.TransientShaper.NAME

    def _apply_macro(self, index, position):
        if index == 4:
            self._node.set(slow_hold_ms=0.0)
            return
        audioeffects.TransientShaper._apply_macro(self, index, position)


class LevelDependent(audioeffects.TransientShaper):
    """T1's fault: a threshold, which is the one thing DET does not have.
    The node is swapped for a peak-detected compressor whose gain therefore
    tracks absolute level."""

    NAME = audioeffects.TransientShaper.NAME

    def _build(self, **options):
        audioeffects.TransientShaper._build(self, **options)
        import audiodynamics
        self._node.set(threshold_db=-30.0, ratio=4.0, attack_ms=1.0,
                       release_ms=120.0)
        node = audiodynamics.Dynamics(
            audiodynamics.DYN_COMPRESS, sample_rate=self._sample_rate,
            channel_count=self._channel_count, threshold_db=-30.0,
            ratio=4.0, attack_ms=1.0, release_ms=120.0, makeup_db=0.0)
        node.play(self._source)
        self._own(node)
        self._output = node


# -- material --------------------------------------------------------------

def probe_pcm(name, rate, channels=2):
    path = "%s/%d/%dch/%s.wav" % (PROBES, rate, channels, name)
    with wave.open(path, "rb") as handle:
        return handle.readframes(handle.getnframes()), handle.getnframes()


def decaying(db_per_s, seconds=1.0, hz=220.0, dbfs=-6.0, attack_ms=1.0,
             rate=48000, channels=2):
    count = int(rate * seconds)
    peak = (10 ** (dbfs / 20.0)) * 32767
    out = array("h", bytes(2 * count * channels))
    for index in range(count):
        moment = index / rate
        envelope = 10.0 ** (-db_per_s * moment / 20.0)
        rise = 1.0 if attack_ms <= 0 else min(1.0,
                                              moment / (attack_ms / 1000.0))
        value = int(max(-32768, min(32767, round(
            peak * envelope * rise * math.sin(2 * math.pi * hz * moment)))))
        for channel in range(channels):
            out[index * channels + channel] = value
    return bytes(memoryview(out).cast("B")), count


def burst(hz, on_ms=250.0, seconds=0.5, dbfs=-6.0, rate=48000, channels=2):
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


# -- rendering through the class ------------------------------------------

def render(pcm, frames, rate=48000, channels=2, cls=None, macros=None,
           patch=None, block=256, label=None):
    cls = cls or audioeffects.TransientShaper
    source = probes.ArraySource(pcm, rate=rate, block=block,
                                channels=channels)
    effect = cls(source, sample_rate=rate)
    if patch is not None:
        effect.program_change(patch)
    for index, value in (macros or {}).items():
        effect.set_macro(index, value)
    out = probes.render(effect.output, frames, rate=rate, channels=channels,
                        block=block, probe=label or "probe",
                        class_name=getattr(cls, "__name__", CLASS))
    effect.deinit()
    return out


def dry(pcm, rate=48000, channels=2, label=None):
    return kit.Render.from_pcm(pcm, rate, channels, label=label or "dry")


def trace(pcm, frames, hop=1.0, floor=-90.0, **options):
    wet = render(pcm, frames, rate=options.pop("rate", 48000), **options)
    result = kit.gaintrace(wet, dry(pcm, wet.rate, wet.channels),
                           hop_ms=hop, floor_db=floor)
    values = result["values"]
    return (np.array(values["trace_ms"]),
            np.array([np.nan if v is None else v
                      for v in values["trace_gr_db"]], dtype=float))


def _dc_removed_frame(pcm, channels):
    """Where `dc_step` stops supplying the offset -- the last frame whose
    magnitude is still at the held level."""
    data = np.frombuffer(pcm, dtype="<i2").reshape(-1, channels)
    live = np.nonzero(np.abs(data[:, 0]) > 1000)[0]
    return int(live[-1]) + 1 if live.size else data.shape[0]


def line(tag, text):
    print("  %-34s %s" % (tag, text))


# -- Tier 1 ----------------------------------------------------------------

def tier1(rate, channels):
    print("\nTier 1 -- %d Hz, %d channel(s), cpython" % (rate, channels))
    effect_latency = audioeffects.TransientShaper.LATENCY_SAMPLES

    pcm, frames = probe_pcm("ramp_fs", rate, channels)
    wet = render(pcm, frames, rate=rate, channels=channels, label="ramp_fs")
    result = kit.wire(wet, dry(pcm, rate, channels),
                      latency_samples=effect_latency)
    line("WIRE ramp_fs", "%s  %d of %d samples differ"
         % ("pass" if result["passed"] else "FAIL",
            result["values"]["differing_samples"],
            result["values"]["compared_samples"]))
    fault = render(pcm, frames, rate=rate, channels=channels,
                   cls=_faulted(makeup_db=0.002), label="ramp_fs")
    faulted = kit.wire(fault, dry(pcm, rate, channels),
                       latency_samples=effect_latency)
    line("  planted: +0.002 dB of output",
         "%s  %d samples differ"
         % ("RED" if not faulted["passed"] else "still green",
            faulted["values"]["differing_samples"]))

    pcm, frames = probe_pcm("burst_silence", rate, channels)
    end = int(rate * 0.2)
    declared = audioeffects.TransientShaper.TAIL_SAMPLES
    dc_pcm, dc_frames = probe_pcm("dc_step", rate, channels)
    dc_wet = render(dc_pcm, dc_frames, rate=rate, channels=channels,
                    macros=BOTH_SET, label="dc_step")
    dc_removed = _dc_removed_frame(dc_pcm, channels)
    for tag, cls in (("TAIL burst_silence + dc_step", None),
                     ("  planted: +1 LSB of held DC", StuckDcTail)):
        wet = render(pcm, frames, rate=rate, channels=channels, cls=cls,
                     macros=BOTH_SET, label="burst")
        this_dc = dc_wet if cls is None else render(
            dc_pcm, dc_frames, rate=rate, channels=channels, cls=cls,
            macros=BOTH_SET, label="dc_step")
        result = kit.tail(wet, burst_end_frame=end,
                          declared_tail_samples=declared,
                          dc_render=this_dc, dc_removed_frame=dc_removed)
        values = result["values"]
        verdict = ("pass" if result["passed"]
                   else ("RED" if cls is not None else "FAIL"))
        line(tag, "%s  tail %s samples (declared %s), residual %s LSB, "
                  "dc residual %s LSB"
             % (verdict,
                0 if values["tail_samples"] is None else values["tail_samples"],
                declared, values["residual_lsb"],
                values.get("dc_residual_lsb")))

    pcm, frames = probe_pcm("noise_det", rate, channels)
    wet = render(pcm, frames, rate=rate, channels=channels, label="noise")
    result = kit.level(wet, dry(pcm, rate, channels))
    line("LEVEL noise_det", "%s  wet:dry RMS %s dB"
         % ("pass" if result["passed"] else "FAIL",
            result["values"]["rms_db"]))

    pcm, frames = probe_pcm("click_stereo", rate, channels)
    for tag, macros in (("defaults", None), ("patch 1 Snap", None)):
        wet = render(pcm, frames, rate=rate, channels=channels,
                     patch=1 if "Snap" in tag else None, label="click")
        result = kit.click(wet, dry(pcm, rate, channels), effect_latency)
        line("CLICK click_stereo, %s" % tag,
             "%s  measured %s samples against a reported %d"
             % ("pass" if result["passed"] else "FAIL",
                result["values"]["measured_latency_samples"],
                effect_latency))
    wet = render(pcm, frames, rate=rate, channels=channels, label="click")
    faulted = kit.click(wet, dry(pcm, rate, channels), effect_latency + 256)
    line("  planted: latency reported 256 short",
         "%s  (audio digest %08x, unchanged)"
         % ("RED" if not faulted["passed"] else "still green", wet.digest))
    return wet.digest


def tier1_state(rate=48000, channels=2):
    print("\nTier 1 -- STATE, %d Hz, %d channel(s), cpython" % (rate,
                                                                channels))
    pcm, _ = probes.burst_silence(hz=1000.0, on_ms=200.0, total_s=2.0,
                                  rate=rate, channels=channels)
    source = probes.ArraySource(pcm, rate=rate, block=256, channels=channels)
    quiet = probes.ArraySource(probes.silence(2 * rate, channels=channels),
                               rate=rate, block=256, channels=channels)
    switch = probes.SwitchableSource(source)
    effect = audioeffects.TransientShaper(switch, sample_rate=rate)
    effect.set_macro(0, ATTACK_UP[0])
    effect.set_macro(1, SUSTAIN_DOWN[1])

    def pull(blocks):
        return probes.render(effect.output, blocks * 256, rate=rate,
                             channels=channels, block=256,
                             probe="burst_silence", class_name=CLASS)

    result = kit.state(effect, pull=pull, swap=switch.swap,
                       probe_source=source, silent_source=quiet,
                       blocks=64, alloc_pulls=100)
    values = result["values"]
    line("STATE", "%s  reset residual %s LSB, live nodes after deinit %s, "
                  "source resumed %s, allocated %s bytes"
         % ("pass" if result["passed"] else "FAIL",
            values["reset_residual_lsb"], values["live_nodes_after_deinit"],
            values["resumed"], values["alloc_growth_bytes"]))
    line("capabilities", "%r declared; transport read: no"
         % (audioeffects.TransientShaper.CAPABILITIES,))
    if not result["passed"]:
        line("  red", "; ".join(result["red"]))

    again = probes.ArraySource(pcm, rate=rate, block=256, channels=channels)
    switch = probes.SwitchableSource(again)
    faulted_effect = LiveAfterDeinit(switch, sample_rate=rate)

    def pull_faulted(blocks):
        return probes.render(faulted_effect.output, blocks * 256, rate=rate,
                             channels=channels, block=256,
                             probe="burst_silence", class_name=CLASS)

    faulted = kit.state(faulted_effect, pull=pull_faulted, swap=switch.swap,
                        probe_source=again, silent_source=quiet,
                        blocks=64, alloc_pulls=100)
    line("  planted: the node not released",
         "%s  live nodes after deinit %s"
         % ("RED" if not faulted["passed"] else "still green",
            faulted["values"]["live_nodes_after_deinit"]))


# -- Tier 2 ----------------------------------------------------------------

def t1_levels():
    print("\nT1 LEVELS -- one hit at five levels, Attack +12, 48 kHz")
    peaks = {}
    for cls, tag in ((None, "class"), (LevelDependent, "planted: a "
                                       "threshold (DYN_COMPRESS)")):
        row = []
        for level in ("-6", "-20", "-40", "-60", "-80"):
            pcm, frames = probe_pcm("hit_levels_%s" % level, 48000)
            times, gains = trace(pcm, frames, cls=cls, macros=ATTACK_UP,
                                 label="hit")
            window = (times <= 200.0) & ~np.isnan(gains)
            row.append(np.abs(gains[window])[
                np.abs(gains[window]).argmax()])
        peaks[tag] = row
        held = row[:4]
        spread = max(held) - min(held)
        line(tag, "peak gain %s dB; spread over -6..-60 %.3f dB (bar 0.500)"
             % (" ".join("%+.3f" % v for v in row), spread))
    return peaks


def t2_both():
    print("\nT2 BOTH -- attack boost and sustain cut on one hit, 48 kHz")
    pcm, frames = probe_pcm("hit_levels_-6", 48000)
    for tag, cls in (("class (transient_dual=True)", None),
                     ("planted: transient_dual=False",
                      _faulted(transient_dual=False))):
        both = trace(pcm, frames, cls=cls,
                     macros=BOTH_SET, label="hit")[1]
        only_a = trace(pcm, frames, cls=cls, macros=ATTACK_UP,
                       label="hit")[1]
        only_s = trace(pcm, frames, cls=cls, macros=SUSTAIN_DOWN,
                       label="hit")[1]
        count = min(len(both), len(only_a), len(only_s))
        both, only_a, only_s = both[:count], only_a[:count], only_s[:count]
        live = ~(np.isnan(both) | np.isnan(only_a) | np.isnan(only_s))
        overlap = int((live & (only_a > 0.5) & (only_s < -0.5)).sum())
        drift = float(np.abs(both - (only_a + only_s))[live].max())
        line(tag, "%3d of %3d hops carry both at once; each section's effect "
                  "moves %.3f dB alone vs in company (bar 0.500)"
             % (overlap, int(live.sum()), drift))


def t3_range():
    print("\nT3 RANGE -- measured peak gain against the setting, 48 kHz")
    pcm, frames = probe_pcm("hit_levels_-6", 48000)
    worst = 0.0
    for setting in (-15.0, -12.0, -6.0, 0.0, 6.0, 12.0, 15.0):
        position = 127 * (setting + 15.0) / 30.0
        times, gains = trace(pcm, frames, macros={0: position}, label="hit")
        window = (times <= 60.0) & ~np.isnan(gains)
        got = gains[window][np.abs(gains[window]).argmax()]
        worst = max(worst, abs(got - setting))
        print("    Attack %+6.1f dB -> %+7.3f dB" % (setting, got))
    note, count = decaying(10.0, seconds=3.0)
    for setting in (-24.0, -12.0, 12.0, 24.0):
        position = 127 * (setting + 24.0) / 48.0
        times, gains = trace(note, count, macros={1: position}, floor=-60.0,
                             label="note")
        window = ~np.isnan(gains)
        got = gains[window][np.abs(gains[window]).argmax()]
        worst = max(worst, abs(got - setting))
        print("    Sustain %+6.1f dB -> %+7.3f dB" % (setting, got))
    line("worst error across both spans", "%.3f dB (bar 1.000)" % worst)
    position = 127 * (12.0 + 15.0) / 30.0
    times, gains = trace(pcm, frames, cls=HalvedAttackSpan,
                         macros={0: position}, label="hit")
    window = (times <= 60.0) & ~np.isnan(gains)
    got = gains[window][np.abs(gains[window]).argmax()]
    line("planted: the span halved in the node",
         "Attack +12.0 dB -> %+7.3f dB  %s"
         % (got, "RED" if abs(got - 12.0) > 1.0 else "still green"))


def t4_decay():
    print("\nT4 DECAY -- the sustain envelope holds, and follows the note")
    for tag, cls in (
            ("class (Sustain Hold 150 ms)", None),
            ("planted: Sustain Hold 0 (a follower)", NoPeakHold),
            ("planted: sustain fast attack back at 1 ms",
             _faulted(sustain_fast_attack_ms=1.0))):
        results = []
        for db_per_s in (10.0, 40.0):
            note, count = decaying(db_per_s, seconds=1.0)
            times, gains = trace(note, count, floor=-60.0, cls=cls,
                                 macros=SUSTAIN_DOWN, label="note")
            window = (times <= 200.0) & ~np.isnan(gains)
            depth = -gains[window]
            drop = float((np.maximum.accumulate(depth) - depth).max())
            live = ~np.isnan(gains)
            full = -gains[live]
            peak = full.max()
            t90 = float(times[live][int(np.argmax(full >= 0.9 * peak))])
            at400 = float(-gains[int(np.searchsorted(times, 400.0))])
            results.append((drop, t90, peak, at400))
        ratio = (results[0][1] / results[1][1]) if results[1][1] else 0.0
        line(tag, "monotone drop 0-200 ms %.3f / %.3f dB (bar 0.250); "
                  "t90 %.0f vs %.0f ms = %.2f:1 (bar 2.00:1); depth at "
                  "400 ms %.3f dB"
             % (results[0][0], results[1][0], results[0][1], results[1][1],
                ratio, results[0][3]))


def t5_split():
    print("\nT5 SPLIT -- transient against steady, 1 kHz burst, Attack +12")
    tone, count = burst(1000.0)
    for tag, cls in (("class (detector rms, 3 ms)", None),
                     ("planted: the rectified peak detector",
                      _faulted(detector=0.0))):
        times, gains = trace(tone, count, hop=0.1, cls=cls, macros=ATTACK_UP,
                             label="burst")
        first = (times <= 5.0) & ~np.isnan(gains)
        peak = float(gains[first].max())

        def at(ms):
            return float(gains[int(np.searchsorted(times, ms))])
        line(tag, "peak over 0-5 ms %+7.3f dB (bar +-1.0 of +12); steady at "
                  "100 ms %+7.3f dB (bar 0.500); ratio %.2f dB (bar 10.00)"
             % (peak, at(100.0), peak - at(100.0)))
        line("  the same trace later",
             "150 ms %+7.3f dB, 200 ms %+7.3f dB, 240 ms %+7.3f dB"
             % (at(150.0), at(200.0), at(240.0)))
    # What it would take: the attack pair's own convergence is the clock.
    for speed, label in ((2.0, "Attack Speed 2x"), (5.0, "Attack Speed 5x")):
        position = 127 * math.log(speed / 0.2) / math.log(5.0 / 0.2)
        times, gains = trace(tone, count, hop=0.1,
                             macros={0: ATTACK_UP[0], 3: position},
                             label="burst")
        first = (times <= 5.0) & ~np.isnan(gains)
        line("  %s" % label, "peak over 0-5 ms %+7.3f dB; steady at 100 ms "
                             "%+7.3f dB"
             % (float(gains[first].max()),
                float(gains[int(np.searchsorted(times, 100.0))])))


def t6_onset():
    print("\nT6 ONSET -- does the gain trace's rise follow the material's?")
    rises = []
    for attack_ms in (0.5, 2.0, 8.0):
        material, count = decaying(6.0, seconds=0.5, hz=2000.0,
                                   attack_ms=attack_ms)
        times, gains = trace(material, count, hop=0.05, macros=ATTACK_UP,
                             label="onset")
        window = (times <= 60.0) & ~np.isnan(gains)
        span, values = times[window], gains[window]
        top = values.max()
        low = int(np.argmax(values >= 0.1 * top))
        high = int(np.argmax(values >= 0.9 * top))
        rises.append(float(span[high] - span[low]))
        print("    material 10-90%% %5.2f ms -> gain trace 10-90%% %6.3f ms "
              "(peak %+.3f dB)" % (attack_ms * 0.8, rises[-1], top))
    ratio = max(rises) / min(rises) if min(rises) else float("inf")
    line("rise-time ratio across a 16:1 spread",
         "%.2f:1, where T6 asks 5:1  -> DISCONFIRMED" % ratio)


def refute():
    """The refutation pass, run against each trait this pack calls
    demonstrated. Each entry is the strongest argument found against the
    claim, and what the run answered."""
    print("\nRefutation pass")

    # T1: is level independence only true of the PEAK of the trace? It is
    # not, and the two places the strict reading fails are worth naming.
    levels = ("-6", "-20", "-40", "-60")
    for attack_db in (12.0, 3.0):
        position = 127 * (attack_db + 15.0) / 30.0
        traces, clipped = {}, {}
        for level in levels:
            pcm, frames = probe_pcm("hit_levels_%s" % level, 48000)
            wet = render(pcm, frames, macros={0: position}, label="hit")
            clipped[level] = int(np.count_nonzero(np.abs(wet.data) >= 32767))
            times, gains = trace(pcm, frames, macros={0: position},
                                 label="hit")
            window = (times <= 200.0) & ~np.isnan(gains)
            traces[level] = gains[window]
        length = min(len(row) for row in traces.values())
        stack = np.array([traces[level][:length] for level in levels])
        line("R1 T1: point-by-point, Attack %+.0f dB" % attack_db,
             "spread over -6..-60 %.3f dB (bar 0.500); full-scale samples "
             "%s" % (float((stack.max(axis=0) - stack.min(axis=0)).max()),
                     [clipped[level] for level in levels]))
        pairs = []
        for low, high in zip(levels, levels[1:]):
            pairs.append("%s/%s %.3f" % (low, high, float(np.abs(
                traces[low][:length] - traces[high][:length]).max())))
        line("  by adjacent pair", "; ".join(pairs) + " dB")
    line("  the node's own floor",
         "gain_to_db(env + 1e-5) (audioif_dynamics.c:628-630) is a -100 dBFS "
         "pedestal: 1 % of a -60 dBFS envelope, 10 % of a -80 dBFS one, "
         "which is the graded departure the peak readout shows")

    # T2: are the 43 overlapping hops an artefact of a 1 ms analysis hop?
    pcm, frames = probe_pcm("hit_levels_-6", 48000)
    for hop in (1.0, 0.25):
        only_a = trace(pcm, frames, hop=hop, macros=ATTACK_UP, label="hit")[1]
        only_s = trace(pcm, frames, hop=hop, macros=SUSTAIN_DOWN,
                       label="hit")[1]
        count = min(len(only_a), len(only_s))
        live = ~(np.isnan(only_a[:count]) | np.isnan(only_s[:count]))
        overlap = int((live & (only_a[:count] > 0.5)
                       & (only_s[:count] < -0.5)).sum())
        line("R2 T2: hop %.2f ms" % hop,
             "%d of %d hops carry both at once" % (overlap, int(live.sum())))

    # T3: is +14.615 at Attack +15 the control, or the render clipping?
    position = 127.0
    wet = render(pcm, frames, macros={0: position}, label="hit")
    clipped = int(np.count_nonzero(np.abs(wet.data) >= 32767))
    line("R3 T3: +15 dB reads +14.615",
         "%d of %d samples at full scale in the render -- the probe peaks at "
         "-6 dBFS and +15 dB of gain does not fit in int16"
         % (clipped, wet.data.size))

    # T4: does the 2:1 clause survive a different fraction of the peak?
    for fraction in (0.8, 0.9, 0.95):
        times = []
        for db_per_s in (10.0, 40.0):
            note, count = decaying(db_per_s, seconds=1.0)
            span, gains = trace(note, count, floor=-60.0,
                                macros=SUSTAIN_DOWN, label="note")
            live = ~np.isnan(gains)
            full = -gains[live]
            times.append(float(span[live][
                int(np.argmax(full >= fraction * full.max()))]))
        line("R4 T4: t%d instead of t90" % int(fraction * 100),
             "%.0f vs %.0f ms = %.2f:1 (bar 2.00:1)"
             % (times[0], times[1], times[0] / times[1] if times[1] else 0))

    # T6: is the flat rise-time readout the analysis floor rather than the
    # class? Re-read it an order of magnitude finer.
    for hop in (0.05, 0.005):
        rises = []
        for attack_ms in (0.5, 8.0):
            material, count = decaying(6.0, seconds=0.5, hz=2000.0,
                                       attack_ms=attack_ms)
            span, gains = trace(material, count, hop=hop, macros=ATTACK_UP,
                                label="onset")
            window = (span <= 60.0) & ~np.isnan(gains)
            values, moments = gains[window], span[window]
            top = values.max()
            low = int(np.argmax(values >= 0.1 * top))
            high = int(np.argmax(values >= 0.9 * top))
            rises.append(float(moments[high] - moments[low]))
        line("R6 T6: hop %.3f ms" % hop,
             "10-90%% rise %.4f ms (0.4 ms material) vs %.4f ms (6.4 ms "
             "material) = %.2f:1" % (rises[0], rises[1],
                                     rises[1] / rises[0] if rises[0] else 0))


def main(argv):
    print("Station C -- TransientShaper, class version %s, audioeffects "
          "through audioeffects.create()"
          % audioeffects.TransientShaper.VERSION)
    print("kit: tools/effect_measurements.py; class: %s"
          % audioeffects.TransientShaper.__module__)
    for rate in RATES:
        tier1(rate, 2)
    tier1(48000, 1)
    tier1_state(48000, 2)
    tier1_state(48000, 1)
    if "--tier1-only" in argv:
        return 0
    t1_levels()
    t2_both()
    t3_range()
    t4_decay()
    t5_split()
    t6_onset()
    refute()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
