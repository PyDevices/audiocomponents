"""Transient shaping in the SPL Transient Designer's shape.

Turn the stick up or down without touching the room, and the room up or down
without touching the stick. There is no threshold and no ratio here: both
control voltages are *differences between two envelopes of the same signal*,
so over the levels this holds at, a ghost note is shaped as hard as a
rimshot.

**Where it holds, measured** (dossier T1, and the Phase 2 refutation pass
that narrowed it): the gain trace agrees within 0.5 dB point by point over
**-20 to -40 dBFS at any Attack setting** (spread 0.163 dB), and over -6 to
-40 dBFS only where the render does not clip - Attack +6 or less, spread
0.160 dB. It does **not** hold as first written: at Attack +12 over
-6/-20/-40 dBFS the point-by-point spread is **3.422 dB**, because the
-6 dBFS render clips 578 samples at full scale, and the peak readout is one
setting's number too (at Attack -12 the peak spread over -6...-60 dBFS is
**1.395 dB**). Below -60 dBFS the node's own +1e-5 envelope floor
(`audioif_dynamics.c:628-630`) is a -100 dBFS pedestal on a difference of
logs, so the law stops being scale-free: +11.076 dB at -80 dBFS against
+12.000 at -6. **T1 is disconfirmed as stated and true over the span above.**

**Attack** moves the first few milliseconds of every hit, +/-15 dB, and the
span tracks the setting within 0.005 dB on material with headroom.
**Sustain** moves what rings after it, +/-24 dB, and the two run at once
rather than one at a time - a snare can get more stick *and* less room from
one instance. The Sustain figure is a figure of the note as much as of the
control: on a 10 dB/s decay it reads -24.321 dB, and on a **3 dB/s** decay
it saturates **8 dB short of its stated end** (-16.353 dB over 12 s, still
climbing when the render stops). **T3's Sustain leg is disconfirmed**; the
Attack leg is not. **Output** puts the level back, -22 to +6 dB, as SPL's
own rack module does. **Attack Speed** scales the attack detector's four
time constants together, 0.2x to 5x. **Sustain Hold** is how long the
sustain envelope holds at the peak before it lets go, 0 to 500 ms; at 0 it
is a plain follower again, which is the pre-Phase-1 behaviour - and because
that setting is a knob, the dossier's T4 has no fault the panel cannot dial
and its peak-hold clause is **unmeasured**, not demonstrated.

**Latency: 0 samples, 0.00 ms, at every setting and every sample rate.** A
differential envelope cannot look ahead - the difference is between two
envelopes of the same *past* - so this class ships no look-ahead option and
adds nothing to a live pedalboard's round trip (vision section 9a).
`tail_samples` is 0: a VCA multiplies, so silence in is exactly zero out in
the same frame.

**Portability tier: audioif.** It is one `audiodynamics.Dynamics` node, and
`audiodynamics` is audioif's own module rather than a CircuitPython port
(`audioif/docs/upstream-diff.md:661`), so a stock CircuitPython board raises
`ImportError` at construction. **Cost** is one node: four one-pole
followers, a peak-hold, an RMS one-pole and one multiply per frame - and it
is still **over its Tier 3 budget on both boards**, 14.9 % of a stereo block
on the ESP32-P4 against 5 % and 31.3 % on the ESP32-S3 against 10 %
(measured 2026-09-07). **There is no `" - lean"` patch, and the measurement
says why rather than the argument**: every shipped patch costs 102-106 % of
patch 0 because no macro touches the node's build, the only cheaper
configuration that still processes is the peak detector at 89 %, and a node
of this kind in this graph doing *nothing at all* still costs 75 %
(`workspace docs/effects-internal/probes/phase2_probes/transientshaper_lean.py`). The budget needs two thirds
off. **At construction defaults this class is a wire** - a cost figure taken
there is a graph idling, so measure it at patch 1 (Snap).

**Three things this class does not claim.**

* *The time constants do not follow the material.* Both sources say SPL's
  are "automated and optimized adaptively"; neither gives a mechanism or a
  number, and the node's coefficients are computed once per block from
  fixed settings. Measured (dossier section 8 Q2): gain-trace 10-90 % rise
  times of 0.042, 0.042 and 0.041 ms across material whose own rises span
  16:1 - a ratio of 1.02:1 where the trait asked 5:1. **T6 is
  disconfirmed**, the class ships fixed constants, and **Attack Speed** is
  the manual stand-in.
* *The attack section is not settled 100 ms into a held note.* The trait
  asked for unity within 0.5 dB in the steady section 100 ms after the
  onset; measured on a 1 kHz burst at Attack +12 it reads **+0.541 dB**
  there, and falls inside the bar by 122 ms (+0.211 dB at 150 ms, +0.116 dB
  at 200 ms). The cause is the attack pair's own 25 ms slow attack still
  converging, not a standing gain - and **Attack Speed** 2x reads +0.119 dB
  at 100 ms with the transient peak still at +12.000. **T5 is disconfirmed
  on that clause at the 1x default**, and the default was not moved to fit
  the number.
* *The control is normalised over 6 dB.* The envelope difference is divided
  by 6 dB and clamped to +/-1 before it scales the setting
  (`audioif_dynamics.c:630-636`), so every transient sharper than 6 dB gets
  the whole of Attack and no more. That is the node's law, not a knob.
"""

VENDOR = "PyDevices"

from . import _component

try:
    import audiodynamics
except ImportError:      # a stock CircuitPython board, or an old audioif
    audiodynamics = None


class TransientShaper(_component.Component):
    """SPL Transient Designer - Differential Envelope Technology on
    `audiodynamics.Dynamics(DYN_TRANSIENT)`."""

    NAME = 'TransientShaper'
    DISPLAY_NAME = 'Transient Shaper'
    CATEGORIES = ('Dynamics',)
    VERSION = '0.1.0'

    TIER = _component.AUDIOIF
    REQUIRES = ("audiodynamics",)

    #: No tempo input on the panel and no `self._transport()` read here.
    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 0

    MACRO_LABELS = ("Attack", "Sustain", "Output", "Attack Speed",
                    "Sustain Hold")
    MACRO_MODES = {0: "BIPOLAR", 1: "BIPOLAR", 2: "BIPOLAR",
                   3: "UNIPOLAR", 4: "UNIPOLAR"}
    _MACRO_RANGES = ((-15.0, 15.0), (-24.0, 24.0), (-22.0, 6.0),
                     (0.2, 5.0, "log"), (0.0, 500.0))
    PATCHES = {
        0: ("Flat", (64, 64, 100, 64, 38)),
        1: ("Snap", (102, 64, 100, 64, 38)),
        2: ("Room Off", (64, 32, 109, 64, 64)),
        3: ("Room On", (64, 87, 91, 64, 76)),
        4: ("Soften Pick", (30, 64, 109, 36, 38)),
        5: ("Kick Punch", (114, 53, 100, 91, 30)),
        6: ("Ambient Swell", (13, 95, 82, 27, 102)),
    }

    #: The attack pair's four time constants at Attack Speed 1x, which are
    #: the node's own defaults (`audioif_dynamics.c:43-46`). Attack Speed
    #: divides all four by its factor, so the pair keeps its shape and only
    #: its rate changes.
    _ATTACK_MS = (1.0, 50.0, 25.0, 300.0)

    #: The sustain pair's fast envelope attacks instantaneously, because the
    #: peak-hold beside it does (`audioif_dynamics.c:646-649`): a 1 ms
    #: partner opens the differential at every onset and fires Sustain on
    #: the transient - measured 11.832 dB below the trace's running maximum
    #: inside the first 200 ms, where the dossier's T4 allows 0.25, and half
    #: a decibel off the attack peak with it. `ms <= 0` is coefficient 1.0
    #: in the C (`:9-14`), so this is exact at every rate.
    _SUSTAIN_FAST_ATTACK_MS = 0.0

    #: A 3 ms RMS window rather than the rectified peak. Peak-detected, the
    #: two attack envelopes have different attack/release ratios and never
    #: converge on a periodic signal, so a steady tone sits under a standing
    #: attack gain: at Attack +12 on a 1 kHz burst the steady section reads
    #: +3.505 dB peak-detected at 100 ms and +2.187 dB at 150 ms, against
    #: +0.541 and +0.211 dB here, with the transient peak +12.000 dB either
    #: way. It buys most of T5's steady clause; see the docstring for the
    #: part it does not buy.
    _RMS_MS = 3.0

    def _build(self, attack_db=0.0, sustain_db=0.0, output_db=0.0,
               attack_speed=1.0, sustain_hold_ms=150.0, patch=None):
        node = self._own(audiodynamics.Dynamics(
            audiodynamics.DYN_TRANSIENT,
            sample_rate=self._sample_rate,
            channel_count=self._channel_count,
            # Both differences applied at once, rather than one of them
            # selected by the sign of the first: the dossier's T2, and the
            # reason this is one node and not two in series.
            transient_dual=True,
            sustain_fast_attack_ms=self._SUSTAIN_FAST_ATTACK_MS,
            detector="rms", rms_ms=self._RMS_MS))
        node.play(self._source)
        self._node = node
        self._output = node
        self._init_macros((attack_db, sustain_db, output_db, attack_speed,
                           sustain_hold_ms), patch)

    def _apply_macro(self, index, position):
        value = _component.macro_value(self._MACRO_RANGES[index], position)
        if index == 0:
            self._node.set(attack_gain_db=value)
        elif index == 1:
            self._node.set(sustain_gain_db=value)
        elif index == 2:
            self._node.set(makeup_db=value)
        elif index == 3:
            fast_attack, fast_release, slow_attack, slow_release = \
                self._ATTACK_MS
            self._node.set(transient_fast_attack_ms=fast_attack / value,
                           transient_fast_release_ms=fast_release / value,
                           transient_slow_attack_ms=slow_attack / value,
                           transient_slow_release_ms=slow_release / value)
        else:
            self._node.set(slow_hold_ms=value)
