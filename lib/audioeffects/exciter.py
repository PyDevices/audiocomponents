"""`Exciter` - dry plus a one-sided high-passed harmonic branch.

Rebuilt from scratch at Phase 4 against
`workspace docs/effects-internal/dossiers/Exciter.md`, traits frozen
2026-09-17 at Station A. The old class in `drive.py` was consulted only for
the defects that dossier §7 names: no macros, no Harmonics knob, Mix to
1.0, no transient character, and an unexplained mixer buffer size. That
module went when this class was adopted on the boards on 2026-09-18.

**What it is.** The note always passes at unity. A second-order Butterworth
high-pass (Tune) feeds a 1N914 one-sided clipper; that wet branch is
summed under the dry at Mix ≤ 0.7. Character `classic` is the 1977 patent
(fixed threshold). Character `transient` puts `DYN_TRANSIENT` ahead of the
clipper so harmonics are loud at onset (S2's shape), **+6 dB over 8 ms**.
Envelope-following `Waveshaper.bias` was not granted; bias is static.
Transient Time is not on the surface: T5's τ clause is disconfirmed.

**Harmonics is 0…+14 dB of drive across the diode, not 0…+24.** Measured
on this class's own curve, the top ten of those twenty-four decibels buy
**1.76 dB** of h2 at −6 dBFS and cost **6.7 dB** of alias: past the knee
the 1N914's shape has stopped changing, while the time the signal takes
to cross the knee keeps shrinking, and a shorter corner folds harder. At
+24 dB T7 was red at four points of its own grid (−57.0 to −59.0 dB at
Tune 5000 and 6000, 48 and 44.1 kHz) and at 22.05 kHz above Harmonics
≈ 0.3; at +14 dB the whole grid is green at all three rates, worst
**−63.7 dB**, and both of those exclusions are withdrawn — see the 22.05 kHz
bullet below for what replaces the second one. The knob's own
0…1 span is unchanged; a user who wants the old drive turns it further
up. Raising `oversample` to ×8 would have fixed the same four points
(−72.9 to −77.2 dB) and does not fit: the palette sum on the S3 is
3.804 ms/block on `classic` and 4.557 on `transient`, which against the
2026-09-17 board run is 5.106 ms total (**rt 1.04**) and 5.859 ms
(**rt 0.91**).

**Output is an output.** The Output macro is −24…0 dB and trims the
whole effect — both mixer voices — so wet:dry does not move with it.
Before 2026-09-17 it reached `Waveshaper.post_gain` only, which trimmed
the wet branch alone and meant the class could not attenuate its own
output anywhere on its surface; its old +6 dB top also put the wet over
the dry (audiocomponents#72). There is no makeup gain above unity: the
dry path is already unity and the sum is s16.

**Tune is clamped to rate/7.** A biquad's bilinear transform compresses
the frequency axis towards Nyquist, so the sidechain's high-pass reads
steeper than second order as its corner rises — by an amount that is a
function of Tune/rate alone (rate/8 → 12.95 dB down an octave below,
rate/6 → 13.50, rate/5 → 14.14, against T1's 12.3 ± 1.5 dB). At 48 and
44.1 kHz rate/7 is above the macro's own 6 kHz top and never bites. **At
22.05 kHz Tune tops out at 3150 Hz**, whatever the knob reads.

**Portability: audioif.** `audioshaper.Waveshaper` at ×4, `audiobiquad`
for the high-pass, `audioroute.Splitter` for the dry copy, and
`audiodynamics.Dynamics` **only on `transient`**. It will not import on a
stock CircuitPython board.

**Cost**, re-derived 2026-09-18 at the rows both boards took that morning.
`classic` is Splitter-2 0.207/0.368 + **2×**Biquad 0.216/0.408 +
Waveshaper ×4 1.069/1.918 + a two-voice Mixer 0.050/0.175 + glue 0
= **1.542 / 2.869 ms → 29 % / 54 %** of a 5.333 ms stereo block. Two
Biquads and not three: `_chain` is an *alias* — it is `_hp` on `classic`
and `_dyn` on `transient`, never a node of its own. `transient` adds
`Dynamics@transient` 0.495/0.985: **2.037 / 3.854 ms → 39 % / 73 %**.

**The `Dynamics` row is not priced at the wrong settings, and that was the
open question.** The palette builds it with both gains at 0 dB, where it
applies unity, and this class runs it at +6 / −12 dB with an 8 ms fast
release — so the board asked whether the row under-prices the node
(audiocomponents#72). Measured on desktop MicroPython, order-balanced,
8000 blocks a run, three reps each, twice: **a ratio of 1.034 and 1.062**
between this class's own gains and 0 dB. A few per cent, not the 27 % the
S3 is missing. **The gains are not what the row was missing.**

**What the boards measured on the 128-frame graph is 32.3 % / 57.8 % and
42.5 % / 81.6 %** — over by 3.4 / 4.0 and 4.3 / 9.3 points. The S3's extra
five points on
`transient` are the `Dynamics` costing this class **1.234 ms** where the
palette prices it 0.985, against **0.537 against 0.495 on the P4**: 27 %
over on the S3 and 9 % on the P4. The suspect, unproven: the class handed
back a **128-frame** block, and a `Dynamics` renders in 256-frame blocks by
construction (`audioif_dynamics.h:56`, "the effects library's latency
assumptions … are written around it"), so it sat in a graph shaped the
wrong way for it. `MIXER_BUFFER_BYTES × channel_count` makes one pull one
block, and it **moves no byte** — `59f2e64ed63c1362` at patch 0 and
`56b7966ed074ab8b` at patch 1, at either length, on all three interpreters.
**Desktop MicroPython cannot confirm the saving and in one arrangement
reads the other way** (the node behind a 128-frame mixer measured 0.850× a
256-frame one, over six order-balanced runs); an x86 build's per-call
overhead is under a microsecond, which is why. **The second board pass
measured the 256-frame graph on 2026-09-18**: 28.9 % / 54.3 % on `classic`,
39.3 % / 77.0 % on `transient`, 39.4 % / 77.5 % at the costliest patch. The
block was worth 3.4 / 3.5 points on `classic` and 3.2 / 4.6 on `transient`;
the `Dynamics` on the S3 is still 22 % over its row and still unexplained.

**Alone on an ESP32-S3 this uses 54 % of a block on `classic` and 77 % on
`transient`, 78 % at its costliest patch; there is no lean patch, so run it
alone or with something cheap.**

(Setting `transient_fast_release_ms` still costs nothing — the four
transient time constants are config fields whose defaults are the literals
the node used before they were fields, `audioif_dynamics.c:48-53`.)
**No lean position.** `oversample=2` was documented as one until
2026-09-17 on the strength of the two points that sentence named. Over
T7's own grid ×2 is red at **12 of 48** readings, worst **−45.1 dB**
(44.1 kHz, Tune 5000, Harmonics 1.0), and at the drive this class shipped
until today it was red on patch 2 `Mix Sheen` as well (−59.9 dB; it reads
−63.4 now). A position that does not hold the trait is not a lean
position; the constructor argument stays, undocumented as a saving.

**Latency: zero samples** at every macro setting. The dry tap is a copy.
`oversample` (constructor, default 4) puts group delay on the *wet
branch only*: ×4 is 3.3 samples / **0.069 ms** at 48 kHz, ×8 is 3.9 /
**0.081 ms**, ×1 is 0. It is not on the sixteen-macro surface.
`tail_samples` is **4096** since the third fix round - the 30 Hz output
coupling pole rings, and the worst measured is **3 085 frames** across
three rates and eight builds after a 0 dBFS burst. It was 512. There is no
delay line.

**What this class gives up, and where its traits are weaker than at a
convenient setting.** Patch 0 is Tune 4 kHz, Harmonics 0.25, Mix 0.3,
`classic`, Output 0 dB, and every headline below is that default:

- **No makeup gain, and a stated input ceiling.** Output is −24…0 dB and
  the dry path is already unity, so the class only attenuates and has no
  headroom control at all. What it has instead is a number:
  `INPUT_CEILING_DBFS` is **−3 dBFS**, measured with sines at 1, 3, 5.5
  and 8 kHz over every shipped patch and the Harmonics-max / Mix-max
  corner — the first railed sample anywhere is at −2 dBFS (patch 6,
  5.5 kHz, 250 of 4 800) and −3 dBFS is clean everywhere (audit 3 (p)4,
  ruling (o)).
- **There is a coupling capacitor behind the diode now.** The diode is
  asymmetric on purpose and the only high-pass was **upstream** of it, so
  the rectified offset walked out on any in-band tone: −122 to −1601 LSB
  on the shipped patches and **−4310 LSB (−17.6 dBFS)** at Harmonics 1.0 /
  Mix max / −1 dBFS. A silence test never saw it, because the offset only
  exists under material. `DC_BLOCK_HZ` is 30 Hz, far below Tune's own
  floor; the same cells read **−1.8 LSB** and **−0.1** now, and
  `tail_samples` went 512 → 4096 for the pole's own ring (audit 3 (p)5).
- **T1 is a −40 dBFS row and says so.** The trait holds Harmonics 0 and
  −40 dBFS fixed, which is where the clipper is within 0.05 dB of linear,
  and it holds there at all three rates. Walked up the level axis it
  leaves its 10.8–13.8 dB bar at **32 of 72 readings, in 9 of 9 rows** —
  and every one of them is at **−12 dBFS or hotter**. At −40, −30 and
  −20 dBFS it is inside the bar at 27 of 27 cells, at all three rates and
  at Harmonics 0, 0.25 and 1.0. The worst reading anywhere is
  **−9.635 dB** (48 kHz, Harmonics 0.25, 0 dBFS), 1.165 dB outside.
  (Audit 3 (p)7 quoted 13 of 72 in 6 of 9 rows and audit 4 recorded it as
  not re-derived; re-derived here at `ac96c72`, after the coupling pole,
  the count is 32 and the rows are all nine.)
- **At 22.05 kHz the corner tops out at 3150 Hz** (rate/7), whatever
  Tune reads back.
- **At 22.05 kHz T7 is disconfirmed, and the column is not green.** The
  claim that "the whole 22.05 kHz column is green (worst −64.4 dB)"
  appeared in four places and was read at the Tune grid's own stops:
  walked at **every eighth MIDI stop** with Harmonics at maximum, **6 of
  12 readable stops are over the −60 dB bar** — −41.661 at Tune MIDI 56
  (1656 Hz), −52.393 at MIDI 24, −56.584 at 48, −56.767 at 72, −57.773 at
  16, −59.935 at 40 — every one of them a fold landing between 8.8 and
  11.0 kHz. The row is claimed at **48 and 44.1 kHz** and disconfirmed at
  22.05 kHz, where the class's own harmonic series runs out of room
  before the bar does (audit 3 (p)1 and (p)2).
- **T7 is claimed up to the stated input ceiling and no further.** At
  48 kHz with Tune and Harmonics at maximum the worst in-band line is
  **−63.461 dB at −6 dBFS and −63.475 at −3**, which is
  `INPUT_CEILING_DBFS`, and **−59.856 at −1 dBFS and −59.058 at 0** — over
  the bar, above a level this class already says it cannot take without
  railing (ruling (m)).
- **The class's own harmonics fold at 22.05 kHz whatever the factor.**
  Send it a tone whose harmonics
  reach past the output Nyquist and they fold, and no oversampling factor
  reaches them, because the fold is in the last decimation stage and that
  stage's transition band sits on the output Nyquist. A 1010 Hz tone at
  full drive puts its 11th harmonic at 11110 Hz against a Nyquist of
  11025 and reads **−48.7 dB at 10940.8 Hz**; a 3010 Hz tone puts its 4th
  there (**−51.9**); a 8662.5 Hz tone puts its *second* there
  (**−54.9**). At 48 and 44.1 kHz the same sweep is green to rate/8
  (−68.5 and −66.3).
- **On material with step edges the wet exceeds the dry.** T4's 20–70 %
  is a claim about a tone at or above the corner: at Mix maximum a
  1 kHz **square** puts the wet at **164.7 %** of the dry, because the
  high-pass differentiates the edge and the reverse side of the 1N914
  curve is a wire. That is the circuit, not a defect, and Mix is the
  control for it.
- **The class adds content BELOW the corner, and no trait covers it.**
  The high-pass sits *upstream* of the diode, so the difference tones the
  diode makes out of two highs land under the corner with nothing to
  remove them. Two tones both above it — 5000 + 5500 Hz at −6 dBFS,
  shipped default — put their **500 Hz difference tone at −17.7 dB** on
  the wet branch and **−31.7 dB** on the mixed output at the shipped
  Mix 0.3 (−25.9 dB at Mix maximum); on noise the wet branch carries
  **12.3 dB less** below the corner than the dry does, not none. What
  you hear on dense high material is a low rumble that follows the
  music's intervals rather than its pitches — thicker than the dry, and
  it gets louder with Harmonics and with Mix. A high-pass *after* the
  diode would take it out and would also make the sidechain fourth-order,
  which is T1's own disconfirmation (24.6 dB an octave below), so this is
  disclosed rather than filtered.
- **T7 is a `classic` claim.** On `transient` the Dynamics stage's own
  gain ripple folds at base rate, ahead of the shaper, so oversampling
  cannot remove it: 12 of 36 grid readings above the bar, worst
  **−52.3 dB**, the same at ×2, ×4 and ×8, where `classic` at the same
  settings reads −90.6. The shorter onset boost improved it by 12.8 dB
  and did not clear it.
- **On `transient`, T4 is read after the onset.** The onset is what the
  character is for: on a steady sine at Mix maximum the wet is
  **59.6–61.9 %** of the dry once the render's own start has passed, and
  **124–135 %** over a window that still contains it. That is the same
  named exception as a step edge, and the boost is spent within ~25 ms.
- T6 is a `transient` row and is **disconfirmed**: onset emphasis is
  ≥6 dB at both of its levels now (**17.6 dB** at −30 dBFS, **6.7 dB** at
  −6 dBFS, 48 kHz) but the two differ by 11.0 dB against a 3 dB bar. T5's
  shape holds on `transient` (**12.75 dB** at the frozen 5 kHz/−18 dBFS
  against 6 dB) and is false at the shipped `classic` default, which is
  the control: **0.00 dB**.
"""

VENDOR = "PyDevices"

from array import array

import audiocore
import audiomixer

from . import _component

try:
    import audiobiquad
except ImportError:
    audiobiquad = None
try:
    import audiodynamics
except ImportError:
    audiodynamics = None
try:
    import audioroute
except ImportError:
    audioroute = None
try:
    import audioshaper
except ImportError:
    audioshaper = None


#: The output coupling pole, third fix round. Far below Tune's own floor
#: (2 kHz), so it takes nothing this class makes and removes the
#: rectification offset the asymmetric diode leaves on the output.
DC_BLOCK_HZ = 30.0

#: The input ceiling, stated because this class **adds** a harmonic branch
#: to a dry note at unity and its `Output` macro spans -24 to 0 dB, so it
#: only attenuates: there is no headroom control and there never was
#: (audit 3 (p)4, ruling (o)). Measured with sines at 1, 3, 5.5 and 8 kHz
#: over every shipped patch and the Harmonics-max / Mix-max corner: the
#: first railed sample anywhere is at **-2 dBFS** (patch 6 at 5.5 kHz, 250
#: of 4 800; the corner, 150 of 4 800), and **-3 dBFS is clean
#: everywhere**. The 30 Hz pole bought some of that back - the offset it
#: removes was riding on the peaks - and the rest is the class's own gain
#: structure.
INPUT_CEILING_DBFS = -3.0

#: What the shipped x4 is worth against x1, in dB of worst in-band line,
#: **wherever Tune puts the sidechain high enough to fold** - which is
#: Tune MIDI 64 and up, 1915 Hz at 48 kHz. Under the absolute -60 dB bar
#: alone `BaseRate` was healthy at 21 of 276 positions, all of them the
#: bottom of the Tune macro and shipped patch 3 (audit 3 (p)3, ruling
#: (i)): not because the oversampling is idle there but because a
#: sidechain at 600 Hz makes nothing high enough to alias. Measured over
#: the macro at 48 kHz with the row's own probe rule, the cost is **+19.1
#: to +46.2 dB** from MIDI 56 up and **-2.2 to +7.1 dB** below it. `x1`'s
#: own cost is 0 dB by construction, so it is red at every position the
#: clause is claimed over.
ALIAS_OVERSAMPLE_COST_DB = 15.0

#: Where that clause is claimed: the sidechain corner above which the
#: class makes enough high harmonics for the factor to matter.
OVERSAMPLE_CLAUSE_TUNE_HZ = 1900.0

TUNE_DEFAULT = 4000.0
HARMONICS_DEFAULT = 0.25
MIX_DEFAULT = 0.3
OUTPUT_DEFAULT = 0.0

#: Volts the Harmonics macro puts across the 1N914 at its top, in dB over
#: 0 dBFS = 1 V. **14 dB, not 24** since 2026-09-17: measured on this class's
#: own curve, the top ten of those twenty-four decibels buy 1.76 dB of h2 at
#: -6 dBFS (h2 -10.107 at +14 dB against -8.345 at +24) and cost 6.7 dB of
#: alias (T7's worst in-scope cell -63.74 at +14 against -57.05 at +24),
#: because past the knee the diode's shape has stopped changing while the
#: time it takes to cross the knee keeps shrinking, and a shorter corner is
#: more fold. See the pack, S13.
HARMONICS_SPAN_DB = 14.0

#: `transient`'s onset gain and how long it lasts. **+6 dB over 8 ms, not
#: +12 dB over 50** since 2026-09-17. T4 is a claim `transient` makes too
#: (dossier S3's Char. column), and at +12 dB / 50 ms the wet sat at
#: **72.2-76.0 %** of the dry at Mix maximum on T4's own material, read over
#: the SETTLED half where nothing is a transient any more - over T4's 20-70 %
#: ceiling (audiocomponents#72, second audit item 3). Shortening the boost
#: rather than only lowering it keeps the onset and drops what follows it:
#: **61.72 %** worst settled now, and T5's shape is *stronger* than before,
#: **12.75 dB** of onset emphasis at the frozen 5 kHz / -18 dBFS against a
#: 6 dB bar, with `classic` reading 0.00 dB as the control.
#:
#: `sustain_gain_db` cannot carry the emphasis on its own: it acts on the
#: DECAY, not on the steady state (`audioif_dynamics.c:755-759` - the sign of
#: fast-minus-slow picks which gain applies), so at attack 0 dB the character
#: is a wire on a sustained tone (0.00 dB of emphasis, measured). The decay
#: time is not a trait: T5's tau clause is frozen as DISCONFIRMED, so what
#: the boost's length owes is disclosure, which is this.
#:
#: `transient_fast_release_ms` costs nothing: the four transient time
#: constants are config fields whose defaults are the literals the node used
#: before they were fields (`audioif_dynamics.c:48-53`), so a node that sets
#: one computes exactly what a node that sets none computes. The budget keeps
#: the palette's bare `Dynamics` row.
TRANSIENT_ATTACK_DB = 6.0
TRANSIENT_SUSTAIN_DB = -12.0
TRANSIENT_FAST_RELEASE_MS = 8.0

#: The blend mixer's buffer, per channel. `Mixer._render_size` is
#: `buffer_size // 2 // 4 * 4` BYTES, so the 1024 this class shipped handed
#: back **128 stereo frames** and everything behind it was pulled TWICE per
#: 256-frame block — including, on `transient`, an `audiodynamics.Dynamics`
#: whose own output block is 256 frames by construction
#: (`audioif_dynamics.h:56`, "the effects library's latency assumptions —
#: notably the Splitter ring's depth — are written around it"). The board's
#: own rows are where the suspicion comes from: adding the `Dynamics` cost
#: this class **0.537 ms on the P4 and 1.234 ms on the S3** where the
#: palette prices it at 0.495 / 0.985 — 9 % over on the P4 and **27 % over
#: on the S3**. `1024 * channel_count` is one pull per block at either
#: channel count, which is what `Distortion` already does (`_pcm_mixer`),
#: and the three classes that missed their budget on these boards are three
#: of the four that handed back 128 frames. **The second board pass measured
#: the 256-frame graph: it is worth 3.4 / 3.5 points on `classic` and
#: 3.2 / 4.6 on `transient`, so the block was most of the P4's miss and
#: about half the S3's. What the `Dynamics` costs over its row — 22 % on the
#: S3 — is not the block and is still unexplained.**
MIXER_BUFFER_BYTES = 1024

# BEGIN EXCITER_CURVE
CURVE_BYTES = (
    b"\x01\x80\x41\x80\x81\x80\xc1\x80\x01\x81\x41\x81\x81\x81\xc1\x81"
    b"\x01\x82\x41\x82\x81\x82\xc1\x82\x01\x83\x41\x83\x81\x83\xc1\x83"
    b"\x01\x84\x41\x84\x81\x84\xc1\x84\x01\x85\x41\x85\x81\x85\xc1\x85"
    b"\x01\x86\x41\x86\x81\x86\xc1\x86\x01\x87\x41\x87\x81\x87\xc1\x87"
    b"\x01\x88\x41\x88\x81\x88\xc1\x88\x01\x89\x41\x89\x81\x89\xc1\x89"
    b"\x01\x8a\x41\x8a\x81\x8a\xc1\x8a\x01\x8b\x41\x8b\x81\x8b\xc1\x8b"
    b"\x01\x8c\x41\x8c\x81\x8c\xc1\x8c\x01\x8d\x41\x8d\x81\x8d\xc1\x8d"
    b"\x01\x8e\x41\x8e\x81\x8e\xc1\x8e\x01\x8f\x41\x8f\x81\x8f\xc1\x8f"
    b"\x01\x90\x41\x90\x81\x90\xc1\x90\x01\x91\x41\x91\x81\x91\xc1\x91"
    b"\x01\x92\x41\x92\x81\x92\xc1\x92\x01\x93\x41\x93\x81\x93\xc1\x93"
    b"\x01\x94\x41\x94\x81\x94\xc1\x94\x01\x95\x41\x95\x81\x95\xc1\x95"
    b"\x01\x96\x41\x96\x81\x96\xc1\x96\x01\x97\x41\x97\x81\x97\xc1\x97"
    b"\x01\x98\x41\x98\x81\x98\xc1\x98\x01\x99\x41\x99\x81\x99\xc1\x99"
    b"\x01\x9a\x41\x9a\x81\x9a\xc1\x9a\x01\x9b\x41\x9b\x81\x9b\xc1\x9b"
    b"\x01\x9c\x41\x9c\x81\x9c\xc1\x9c\x01\x9d\x41\x9d\x81\x9d\xc1\x9d"
    b"\x01\x9e\x41\x9e\x81\x9e\xc1\x9e\x01\x9f\x41\x9f\x81\x9f\xc1\x9f"
    b"\x01\xa0\x41\xa0\x81\xa0\xc1\xa0\x01\xa1\x41\xa1\x81\xa1\xc1\xa1"
    b"\x01\xa2\x41\xa2\x81\xa2\xc1\xa2\x01\xa3\x41\xa3\x81\xa3\xc1\xa3"
    b"\x01\xa4\x41\xa4\x81\xa4\xc1\xa4\x01\xa5\x41\xa5\x81\xa5\xc1\xa5"
    b"\x01\xa6\x41\xa6\x81\xa6\xc1\xa6\x01\xa7\x41\xa7\x81\xa7\xc1\xa7"
    b"\x01\xa8\x41\xa8\x81\xa8\xc1\xa8\x01\xa9\x41\xa9\x81\xa9\xc1\xa9"
    b"\x01\xaa\x41\xaa\x81\xaa\xc1\xaa\x01\xab\x41\xab\x81\xab\xc1\xab"
    b"\x01\xac\x41\xac\x81\xac\xc1\xac\x01\xad\x41\xad\x81\xad\xc1\xad"
    b"\x01\xae\x41\xae\x81\xae\xc1\xae\x01\xaf\x41\xaf\x81\xaf\xc1\xaf"
    b"\x01\xb0\x41\xb0\x81\xb0\xc1\xb0\x01\xb1\x41\xb1\x81\xb1\xc1\xb1"
    b"\x01\xb2\x41\xb2\x81\xb2\xc1\xb2\x01\xb3\x41\xb3\x81\xb3\xc1\xb3"
    b"\x01\xb4\x41\xb4\x81\xb4\xc1\xb4\x01\xb5\x41\xb5\x81\xb5\xc1\xb5"
    b"\x01\xb6\x41\xb6\x81\xb6\xc1\xb6\x01\xb7\x41\xb7\x81\xb7\xc1\xb7"
    b"\x01\xb8\x41\xb8\x81\xb8\xc1\xb8\x01\xb9\x41\xb9\x81\xb9\xc1\xb9"
    b"\x01\xba\x41\xba\x81\xba\xc1\xba\x01\xbb\x41\xbb\x81\xbb\xc1\xbb"
    b"\x01\xbc\x41\xbc\x81\xbc\xc1\xbc\x01\xbd\x41\xbd\x81\xbd\xc1\xbd"
    b"\x01\xbe\x41\xbe\x81\xbe\xc1\xbe\x01\xbf\x41\xbf\x81\xbf\xc1\xbf"
    b"\x00\xc0\x40\xc0\x80\xc0\xc0\xc0\x00\xc1\x40\xc1\x80\xc1\xc0\xc1"
    b"\x00\xc2\x40\xc2\x80\xc2\xc0\xc2\x00\xc3\x40\xc3\x80\xc3\xc0\xc3"
    b"\x00\xc4\x40\xc4\x80\xc4\xc0\xc4\x00\xc5\x40\xc5\x80\xc5\xc0\xc5"
    b"\x00\xc6\x40\xc6\x80\xc6\xc0\xc6\x00\xc7\x40\xc7\x80\xc7\xc0\xc7"
    b"\x00\xc8\x40\xc8\x80\xc8\xc0\xc8\x00\xc9\x40\xc9\x80\xc9\xc0\xc9"
    b"\x00\xca\x40\xca\x80\xca\xc0\xca\x00\xcb\x40\xcb\x80\xcb\xc0\xcb"
    b"\x00\xcc\x40\xcc\x80\xcc\xc0\xcc\x00\xcd\x40\xcd\x80\xcd\xc0\xcd"
    b"\x00\xce\x40\xce\x80\xce\xc0\xce\x00\xcf\x40\xcf\x80\xcf\xc0\xcf"
    b"\x00\xd0\x40\xd0\x80\xd0\xc0\xd0\x00\xd1\x40\xd1\x80\xd1\xc0\xd1"
    b"\x00\xd2\x40\xd2\x80\xd2\xc0\xd2\x00\xd3\x40\xd3\x80\xd3\xc0\xd3"
    b"\x00\xd4\x40\xd4\x80\xd4\xc0\xd4\x00\xd5\x40\xd5\x80\xd5\xc0\xd5"
    b"\x00\xd6\x40\xd6\x80\xd6\xc0\xd6\x00\xd7\x40\xd7\x80\xd7\xc0\xd7"
    b"\x00\xd8\x40\xd8\x80\xd8\xc0\xd8\x00\xd9\x40\xd9\x80\xd9\xc0\xd9"
    b"\x00\xda\x40\xda\x80\xda\xc0\xda\x00\xdb\x40\xdb\x80\xdb\xc0\xdb"
    b"\x00\xdc\x40\xdc\x80\xdc\xc0\xdc\x00\xdd\x40\xdd\x80\xdd\xc0\xdd"
    b"\x00\xde\x40\xde\x80\xde\xc0\xde\x00\xdf\x40\xdf\x80\xdf\xc0\xdf"
    b"\x00\xe0\x40\xe0\x80\xe0\xc0\xe0\x00\xe1\x40\xe1\x80\xe1\xc0\xe1"
    b"\x00\xe2\x40\xe2\x80\xe2\xc0\xe2\x00\xe3\x40\xe3\x80\xe3\xc0\xe3"
    b"\x00\xe4\x40\xe4\x80\xe4\xc0\xe4\x00\xe5\x40\xe5\x80\xe5\xc0\xe5"
    b"\x00\xe6\x40\xe6\x80\xe6\xc0\xe6\x00\xe7\x40\xe7\x80\xe7\xc0\xe7"
    b"\x00\xe8\x40\xe8\x80\xe8\xc0\xe8\x00\xe9\x40\xe9\x80\xe9\xc0\xe9"
    b"\x00\xea\x40\xea\x80\xea\xc0\xea\x00\xeb\x40\xeb\x80\xeb\xc0\xeb"
    b"\x00\xec\x40\xec\x80\xec\xc0\xec\x00\xed\x40\xed\x80\xed\xc0\xed"
    b"\x00\xee\x40\xee\x80\xee\xc0\xee\x00\xef\x40\xef\x80\xef\xc0\xef"
    b"\x00\xf0\x40\xf0\x80\xf0\xc0\xf0\x00\xf1\x40\xf1\x80\xf1\xc0\xf1"
    b"\x00\xf2\x40\xf2\x80\xf2\xc0\xf2\x00\xf3\x40\xf3\x80\xf3\xc0\xf3"
    b"\x00\xf4\x40\xf4\x80\xf4\xc0\xf4\x00\xf5\x40\xf5\x80\xf5\xc0\xf5"
    b"\x00\xf6\x40\xf6\x80\xf6\xc0\xf6\x00\xf7\x40\xf7\x80\xf7\xc0\xf7"
    b"\x00\xf8\x40\xf8\x80\xf8\xc0\xf8\x00\xf9\x40\xf9\x80\xf9\xc0\xf9"
    b"\x00\xfa\x40\xfa\x80\xfa\xc0\xfa\x00\xfb\x40\xfb\x80\xfb\xc0\xfb"
    b"\x00\xfc\x40\xfc\x80\xfc\xc0\xfc\x00\xfd\x40\xfd\x80\xfd\xc0\xfd"
    b"\x00\xfe\x40\xfe\x80\xfe\xc0\xfe\x00\xff\x40\xff\x80\xff\xc0\xff"
    b"\x00\x00\x40\x00\x7f\x00\xbe\x00\xfd\x00\x39\x01\x73\x01\xa9\x01"
    b"\xd9\x01\x03\x02\x27\x02\x45\x02\x5e\x02\x74\x02\x86\x02\x97\x02"
    b"\xa5\x02\xb2\x02\xbd\x02\xc8\x02\xd1\x02\xda\x02\xe2\x02\xea\x02"
    b"\xf1\x02\xf7\x02\xfe\x02\x04\x03\x09\x03\x0e\x03\x13\x03\x18\x03"
    b"\x1d\x03\x21\x03\x25\x03\x29\x03\x2d\x03\x31\x03\x34\x03\x38\x03"
    b"\x3b\x03\x3e\x03\x41\x03\x44\x03\x47\x03\x4a\x03\x4d\x03\x4f\x03"
    b"\x52\x03\x55\x03\x57\x03\x59\x03\x5c\x03\x5e\x03\x60\x03\x63\x03"
    b"\x65\x03\x67\x03\x69\x03\x6b\x03\x6d\x03\x6f\x03\x71\x03\x73\x03"
    b"\x74\x03\x76\x03\x78\x03\x7a\x03\x7b\x03\x7d\x03\x7f\x03\x80\x03"
    b"\x82\x03\x83\x03\x85\x03\x86\x03\x88\x03\x89\x03\x8b\x03\x8c\x03"
    b"\x8e\x03\x8f\x03\x90\x03\x92\x03\x93\x03\x94\x03\x96\x03\x97\x03"
    b"\x98\x03\x99\x03\x9b\x03\x9c\x03\x9d\x03\x9e\x03\x9f\x03\xa0\x03"
    b"\xa2\x03\xa3\x03\xa4\x03\xa5\x03\xa6\x03\xa7\x03\xa8\x03\xa9\x03"
    b"\xaa\x03\xab\x03\xac\x03\xad\x03\xae\x03\xaf\x03\xb0\x03\xb1\x03"
    b"\xb2\x03\xb3\x03\xb4\x03\xb5\x03\xb6\x03\xb7\x03\xb8\x03\xb8\x03"
    b"\xb9\x03\xba\x03\xbb\x03\xbc\x03\xbd\x03\xbe\x03\xbe\x03\xbf\x03"
    b"\xc0\x03\xc1\x03\xc2\x03\xc2\x03\xc3\x03\xc4\x03\xc5\x03\xc6\x03"
    b"\xc6\x03\xc7\x03\xc8\x03\xc9\x03\xc9\x03\xca\x03\xcb\x03\xcc\x03"
    b"\xcc\x03\xcd\x03\xce\x03\xce\x03\xcf\x03\xd0\x03\xd0\x03\xd1\x03"
    b"\xd2\x03\xd2\x03\xd3\x03\xd4\x03\xd4\x03\xd5\x03\xd6\x03\xd6\x03"
    b"\xd7\x03\xd8\x03\xd8\x03\xd9\x03\xda\x03\xda\x03\xdb\x03\xdb\x03"
    b"\xdc\x03\xdd\x03\xdd\x03\xde\x03\xde\x03\xdf\x03\xe0\x03\xe0\x03"
    b"\xe1\x03\xe1\x03\xe2\x03\xe2\x03\xe3\x03\xe4\x03\xe4\x03\xe5\x03"
    b"\xe5\x03\xe6\x03\xe6\x03\xe7\x03\xe7\x03\xe8\x03\xe8\x03\xe9\x03"
    b"\xe9\x03\xea\x03\xeb\x03\xeb\x03\xec\x03\xec\x03\xed\x03\xed\x03"
    b"\xee\x03\xee\x03\xef\x03\xef\x03\xf0\x03\xf0\x03\xf1\x03\xf1\x03"
    b"\xf2\x03\xf2\x03\xf2\x03\xf3\x03\xf3\x03\xf4\x03\xf4\x03\xf5\x03"
    b"\xf5\x03\xf6\x03\xf6\x03\xf7\x03\xf7\x03\xf8\x03\xf8\x03\xf8\x03"
    b"\xf9\x03\xf9\x03\xfa\x03\xfa\x03\xfb\x03\xfb\x03\xfc\x03\xfc\x03"
    b"\xfc\x03\xfd\x03\xfd\x03\xfe\x03\xfe\x03\xff\x03\xff\x03\xff\x03"
    b"\x00\x04\x00\x04\x01\x04\x01\x04\x01\x04\x02\x04\x02\x04\x03\x04"
    b"\x03\x04\x03\x04\x04\x04\x04\x04\x05\x04\x05\x04\x05\x04\x06\x04"
    b"\x06\x04\x07\x04\x07\x04\x07\x04\x08\x04\x08\x04\x08\x04\x09\x04"
    b"\x09\x04\x0a\x04\x0a\x04\x0a\x04\x0b\x04\x0b\x04\x0b\x04\x0c\x04"
    b"\x0c\x04\x0d\x04\x0d\x04\x0d\x04\x0e\x04\x0e\x04\x0e\x04\x0f\x04"
    b"\x0f\x04\x0f\x04\x10\x04\x10\x04\x10\x04\x11\x04\x11\x04\x11\x04"
    b"\x12\x04\x12\x04\x12\x04\x13\x04\x13\x04\x13\x04\x14\x04\x14\x04"
    b"\x14\x04\x15\x04\x15\x04\x15\x04\x16\x04\x16\x04\x16\x04\x17\x04"
    b"\x17\x04\x17\x04\x18\x04\x18\x04\x18\x04\x19\x04\x19\x04\x19\x04"
    b"\x1a\x04\x1a\x04\x1a\x04\x1b\x04\x1b\x04\x1b\x04\x1b\x04\x1c\x04"
    b"\x1c\x04\x1c\x04\x1d\x04\x1d\x04\x1d\x04\x1e\x04\x1e\x04\x1e\x04"
    b"\x1f\x04\x1f\x04\x1f\x04\x1f\x04\x20\x04\x20\x04\x20\x04\x21\x04"
    b"\x21\x04\x21\x04\x21\x04\x22\x04\x22\x04\x22\x04\x23\x04\x23\x04"
    b"\x23\x04\x23\x04\x24\x04\x24\x04\x24\x04\x25\x04\x25\x04\x25\x04"
    b"\x25\x04\x26\x04\x26\x04\x26\x04\x27\x04\x27\x04\x27\x04\x27\x04"
    b"\x28\x04\x28\x04\x28\x04\x28\x04\x29\x04\x29\x04\x29\x04\x29\x04"
    b"\x2a\x04\x2a\x04\x2a\x04\x2b\x04\x2b\x04\x2b\x04\x2b\x04\x2c\x04"
    b"\x2c\x04\x2c\x04\x2c\x04\x2d\x04\x2d\x04\x2d\x04\x2d\x04\x2e\x04"
    b"\x2e\x04\x2e\x04\x2e\x04\x2f\x04\x2f\x04\x2f\x04\x2f\x04\x30\x04"
    b"\x30\x04\x30\x04\x30\x04\x31\x04\x31\x04\x31\x04\x31\x04\x32\x04"
    b"\x32\x04\x32\x04\x32\x04\x33\x04\x33\x04\x33\x04\x33\x04\x33\x04"
    b"\x34\x04\x34\x04\x34\x04\x34\x04\x35\x04\x35\x04\x35\x04\x35\x04"
    b"\x36\x04\x36\x04\x36\x04\x36\x04\x37\x04\x37\x04\x37\x04\x37\x04"
    b"\x37\x04\x38\x04\x38\x04\x38\x04\x38\x04\x39\x04\x39\x04\x39\x04"
    b"\x39\x04\x39\x04\x3a\x04\x3a\x04\x3a\x04\x3a\x04\x3b\x04\x3b\x04"
    b"\x3b\x04\x3b\x04\x3b\x04\x3c\x04\x3c\x04\x3c\x04\x3c\x04\x3d\x04"
    b"\x3d\x04\x3d\x04\x3d\x04\x3d\x04\x3e\x04\x3e\x04\x3e\x04\x3e\x04"
    b"\x3e\x04\x3f\x04\x3f\x04\x3f\x04\x3f\x04\x40\x04\x40\x04\x40\x04"
    b"\x40\x04\x40\x04\x41\x04\x41\x04\x41\x04\x41\x04\x41\x04\x42\x04"
    b"\x42\x04\x42\x04\x42\x04\x42\x04\x43\x04\x43\x04\x43\x04\x43\x04"
    b"\x43\x04\x44\x04\x44\x04\x44\x04\x44\x04\x44\x04\x45\x04\x45\x04"
    b"\x45\x04\x45\x04\x45\x04\x46\x04\x46\x04\x46\x04\x46\x04\x46\x04"
    b"\x47\x04\x47\x04\x47\x04\x47\x04\x47\x04\x48\x04\x48\x04\x48\x04"
    b"\x48\x04\x48\x04\x49\x04\x49\x04\x49\x04\x49\x04\x49\x04\x49\x04"
    b"\x4a\x04"
)
# END EXCITER_CURVE

CURVE = array("h", CURVE_BYTES)


class Exciter(_component.Component):
    """Dry plus a one-sided high-passed harmonic branch (Aphex structure)."""

    NAME = 'Exciter'
    DISPLAY_NAME = 'Exciter'
    CATEGORIES = ('Distortion',)
    VERSION = '0.0.1'

    TIER = _component.AUDIOIF
    REQUIRES = ("audioshaper", "audiobiquad", "audioroute", "audiodynamics")

    CAPABILITIES = ()
    LATENCY_SAMPLES = 0
    TAIL_SAMPLES = 4096
    INPUT_CEILING_DBFS = INPUT_CEILING_DBFS
    ALIAS_OVERSAMPLE_COST_DB = ALIAS_OVERSAMPLE_COST_DB
    OVERSAMPLE_CLAUSE_TUNE_HZ = OVERSAMPLE_CLAUSE_TUNE_HZ

    MACRO_LABELS = ("Tune", "Harmonics", "Mix", "Character", "Output")
    MACRO_MODES = {
        0: "UNIPOLAR", 1: "UNIPOLAR", 2: "UNIPOLAR",
        3: "TOGGLE", 4: "UNIPOLAR",
    }
    _MACRO_RANGES = (
        (600.0, 6000.0, "log"),
        (0.0, 1.0),
        (0.0, 0.7),
        (0.0, 1.0),
        (-24.0, 0.0),
    )
    PATCHES = {
        0: ("Voice Air", (105, 32, 54, 0, 127)),
        1: ("Percussive Edge", (89, 102, 82, 127, 127)),
        2: ("Mix Sheen", (127, 25, 36, 0, 127)),
        3: ("Mid Presence", (16, 64, 64, 0, 127)),
        4: ("Transient Bite", (89, 102, 82, 127, 127)),
        5: ("Transient Soft", (89, 51, 64, 127, 127)),
        6: ("Wet Sidechain", (105, 32, 127, 0, 127)),
    }

    # The sidechain's corner, as a fraction of the sample rate. A biquad's
    # bilinear transform compresses the frequency axis towards Nyquist, so a
    # HIGH_PASS reads *steeper* than its analog prototype as the corner rises
    # - and by how much is a function of Tune/rate alone, the same at every
    # rate: rate/8 reads 12.95 dB down an octave below, rate/6 13.50,
    # rate/5 14.14, against T1's 12.3 +- 1.5 dB bar. rate/7 (13.13 dB) is the
    # highest corner that keeps the second-order geometry inside that bar at
    # every rate. At 48 and 44.1 kHz it is above the macro's own 6 kHz top and
    # never bites; at 22.05 kHz Tune tops out at 3150 Hz. `_hz`'s Nyquist
    # clamp stays underneath it.
    TUNE_RATE_FRACTION = 1.0 / 7.0

    def _build(self, tune=TUNE_DEFAULT, harmonics=HARMONICS_DEFAULT,
               mix=MIX_DEFAULT, character=0.0, output_db=OUTPUT_DEFAULT,
               oversample=4, patch=None):
        rate = self._sample_rate
        channels = self._channel_count
        factor = int(oversample)
        if factor not in (1, 2, 4, 8):
            raise ValueError("oversample must be 1, 2, 4 or 8")
        self._oversample = factor

        splitter = audioroute.Splitter(self._source, taps=2)
        dry = splitter.tap(0)
        wet_in = splitter.tap(1)

        self._hp = audiobiquad.Biquad(
            mode=audiobiquad.HIGH_PASS,
            frequency=self._hz(min(tune, rate * self.TUNE_RATE_FRACTION)),
            Q=0.7071,
            sample_rate=rate, channel_count=channels, mix=1.0)
        # `Dynamics` is built the first time Character asks for `transient`,
        # and taken back out of the graph when it stops asking. On `classic`
        # - the shipped default and four of the seven patches - its gains are
        # both 0 dB, so leaving it in the chain paid 0.394 ms/block on the P4
        # and 0.753 on the S3 (palette) for a wire. That is 7.4 and 14.1
        # points of a 5.333 ms block, and it is the difference between rt 1.20
        # and rt 1.44 on the S3.
        self._dyn = None
        self._chain = None
        # The output coupling capacitor, third fix round. The diode is
        # asymmetric on purpose - that is where the even harmonics come
        # from - and the only high-pass in this graph was **upstream** of
        # it, so the rectified offset walked straight out: -300 to -1304
        # LSB on every shipped patch on its own in-band tone, and -4310
        # LSB (-17.6 dBFS) at Harmonics 1.0 / Mix max / -1 dBFS (audit 3
        # (p)5, ruling (n)). A silence test never sees it, because the
        # offset only exists under material. 30 Hz is far below Tune's own
        # 2 kHz floor, so it takes nothing this class makes.
        self._dc = audiobiquad.Biquad(
            mode=audiobiquad.HIGH_PASS, frequency=self._hz(DC_BLOCK_HZ),
            Q=0.7071, sample_rate=rate, channel_count=channels, mix=1.0)
        self._shaper = audioshaper.Waveshaper(
            sample_rate=rate, channel_count=channels, curve=CURVE,
            oversample=factor, mix=1.0, pre_gain=1.0, post_gain=1.0,
            bias=0.0, hysteresis=0.0)
        blend = audiomixer.Mixer(
            voice_count=2, **self._pcm(MIXER_BUFFER_BYTES * channels))

        self._hp.play(wet_in)

        self._splitter = splitter
        self._dry = dry
        self._wet_in = wet_in
        self._blend = blend
        self._silence = audiocore.RawSample(
            array("h", bytes(2 * 2 * channels)),
            sample_rate=rate, channel_count=channels)

        self._own(blend, reset=False)
        self._own(self._dc)
        self._own(self._shaper)
        self._own(self._hp)
        self._own(dry, reset=False)
        self._own(wet_in, reset=False)
        self._own(splitter, reset=False)
        self._own(self._silence, reset=False)

        self._output = blend
        self._primed = False
        self._ready = False
        self._init_macros((tune, harmonics, mix, character, output_db),
                          patch)

        _component.open_level_gates(
            blend, [blend.voice[0], blend.voice[1]], self._silence)
        self._ready = True
        self._prime_if_wet()

    def _value(self, index):
        return _component.macro_value(self._MACRO_RANGES[index],
                                      self._macros[index])

    def _apply_macro(self, index, position):
        del position
        self._refresh()

    def _tune_hz(self):
        """The corner the running rate can actually carry (`TUNE_RATE_FRACTION`
        first, then `_hz`'s Nyquist clamp). Read back by the tests and by
        `_refresh`; the macro itself keeps the number the caller dialled."""
        ceiling = self._sample_rate * self.TUNE_RATE_FRACTION
        return self._hz(min(self._value(0), ceiling))

    def _route_character(self, transient):
        """Put `Dynamics` in front of the clipper, or take it out.

        `classic` is S1's fixed threshold: nothing between the high-pass and
        the diode. Built that way rather than left in the chain at 0 dB, the
        node costs nothing at all instead of a palette row.
        """
        if transient:
            if self._dyn is None:
                self._dyn = self._own(audiodynamics.Dynamics(
                    audiodynamics.DYN_TRANSIENT,
                    sample_rate=self._sample_rate,
                    channel_count=self._channel_count,
                    attack_gain_db=TRANSIENT_ATTACK_DB,
                    sustain_gain_db=TRANSIENT_SUSTAIN_DB,
                    transient_fast_release_ms=TRANSIENT_FAST_RELEASE_MS))
            else:
                self._dyn.set(
                    attack_gain_db=TRANSIENT_ATTACK_DB,
                    sustain_gain_db=TRANSIENT_SUSTAIN_DB,
                    transient_fast_release_ms=TRANSIENT_FAST_RELEASE_MS)
            if self._chain is not self._dyn:
                self._dyn.play(self._hp)
                self._shaper.play(self._dyn)
                self._chain = self._dyn
        elif self._chain is not self._hp:
            self._shaper.play(self._hp)
            self._chain = self._hp

    def _refresh(self):
        tune = self._tune_hz()
        harmonics = self._value(1)
        transient = self._value(3) >= 0.5

        self._hp.frequency = tune
        self._hp.Q = 0.7071
        self._hp.mix = 1.0

        self._route_character(transient)

        gain = 10.0 ** ((HARMONICS_SPAN_DB * harmonics) / 20.0)
        # Table ±1 is ±16 V (tools/curves/exciter_curve.py UMAX). Harmonics
        # is gain into that volt scale, never a rebuilt table. `post` only
        # undoes `pre`: Output is not in it, because Output is an output.
        # The table keeps its ±16 V span though the macro now tops out at
        # 5.01 V: splitting the same volts differently between `pre` and
        # `post` changes nothing measurable (±0.04 dB on the wet-branch
        # residual at UMAX 16 / 5.5 / 3.0), so the curve is unchanged and
        # `tools/curves/exciter_curve.py --check` still agrees with it.
        pre = gain / 16.0
        post = 16.0 / gain
        self._shaper.set(pre_gain=pre, post_gain=post, mix=1.0, bias=0.0)
        self._prime_if_wet()

    def _prime_if_wet(self):
        mix = self._value(2)
        # Output trims the whole effect - both voices - so wet:dry does not
        # move with it. A wet-only trim was the 2026-09-17 defect: the class
        # could not attenuate its own output anywhere on its surface, and the
        # top of the macro put the wet over the dry (audiocomponents#72).
        out = 10.0 ** (self._value(4) / 20.0)
        if mix <= 0.0 and out >= 1.0:
            self._output = self._source
            return
        if not getattr(self, "_ready", False):
            self._output = self._blend
            return
        if not self._primed:
            self._dc.play(self._shaper)
            self._blend.voice[0].play(self._dry)
            self._blend.voice[1].play(self._dc)
            self._primed = True
        self._output = self._blend
        self._blend.voice[0].level = out
        self._blend.voice[1].level = mix * out
