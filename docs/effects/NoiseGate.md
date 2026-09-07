# Effects Dossier — `NoiseGate` (Drawmer DS201)

**Class:** `lib/audioeffects/rebuilt/noisegate.py`; the old
`dynamics.py:161-177` is read once, for §7. **Family:** Dynamics, Phase 2.
**Standout:** Drawmer DS201, confirmed without reservation by the maker's own
claim in S1 ("the worldwide 'industry standard' noise gate"); every trait
below is on its own panel. **Grade:** literature — two Drawmer schematic
sheets were reached (S5) but no trait derives from them (vision §4.1).
**Tier:** **audioif**, `REQUIRES = ("audiodynamics",)`, plus `audioroute` and
`audiomath` when built with `duck=True`. **Status: traits frozen
2026-09-07**, before a line of the rebuild was written (worktree
`ac-wt-noisegate`, branch `effects/p2-noisegate`); seeded 2026-09-06, audited
twice, §§1–8 shortened and settled here.

## 1. The circuit, in one paragraph

Audio runs input → VCA → output, past a Bypass that passes the input
unprocessed; everything the gate knows it learns from a **side chain that
never touches the sound**. The key is the channel's own input or, on Ext, a
separate jack — "making it possible to gate one sound according to the
dynamics of another" — and passes two variable filters in series, L.F.
**25 Hz–4 kHz** and H.F. **250 Hz–35 kHz**, "it is the range between the two
settings that is allowed to pass"; **Key Listen** puts that filtered band on
the output. A **Threshold** (−54 dB to infinity; S4 says "-50dBFs") arms a
four-stage envelope — **Attack 10 µs–1 s**, **Hold 2 ms–2 s**, **Decay
2 ms–4 s** — under the rule that makes it a gate rather than a follower:
"the envelope cycle will complete even if the Key source falls below the
Threshold level before the Attack phase is completed". The closed state is
not silence but **Range**, 0 dB to −80 dB of attenuation (S4 says −90),
about −15 dB recommended where full closure would make the noise floor's
coming and going more obvious than the noise. A **Gate/Duck** switch inverts
the whole sense. Quotations are S1's and the fuller reading is in **App. R2**;
S5 names the gain element a VCA and no trait rests on it. RaneNote 155
supplies the two facts the panel cannot: a gate "uses a fixed ratio of ∞:1
and a variable depth", and "like a limiter, a gate must respond very quickly
to changes in level, dictating the use of a peak detector in the side-chain"
(S2).

## 2. Sources and license calls

All fetched 2026-09-06. **This session fetched no URL** (Station A forbids
it) and added no source; it read the audioif C at the pin instead. What each
source gave and how its licence line reads is in **App. S**; the id, the URL
and the reached call are the gate conditions and stay here.

| Source | Licence | URL | Reached |
|---|---|---|---|
| **S1** Drawmer, *DS201 Operator's Manual*, 2005 capture | all-rights-reserved (chased to S4's notice) | <https://umlsrt.com/StudioDocuments/drawmer%20ds201%20manual.pdf> | yes |
| **S2** Jeffs, Holden & Bohn, RaneNote 155 | "© 2005 Rane Corporation", all rights reserved | <https://www.ranecommercial.com/legacy/pdf/ranenotes/Dynamics_Processors.pdf> | yes |
| **S3** Drawmer, DS201 product page | "© 2026 … Drawmer Electronics Ltd." | <https://www.drawmer.com/products/pro-series/ds201.php> | yes |
| **S4** Drawmer, *DS201 Operator's Manual*, current edition | "© 2008 by Drawmer Electronics, Ltd." | <https://www.drawmer.com/uploads/manuals/ds201_operators_manual.pdf> | yes |
| **S5** Drawmer service sheets — **the VCA, and that fact only** | Drawmer's, under S4's notice; host says personal use only | <https://elektrotanya.com/drawmer_ds201_comp_sch.pdf/download.html> | preview images only; full PDFs **not** obtained |
| **Local** `audioif/src/shared/audioif_dynamics.{c,h}` at pin `2f6cbc3` | MIT | — | yes |

## 3. Traits — fixed before measurement

**Tier 1** — the standard block, verbatim from vision §3, is in **App. I**
with this class's mono, rate and `capabilities` notes.

**Tier 2 — frozen 2026-09-07.** Four rows were restated in this pass because
their first drafts were not falsifiable against a one-pole envelope; each
correction carries its arithmetic in **App. C**, and none was written after
seeing a render of the rebuilt class. Source and confidence per row: **App.
T**.

| # | Trait (falsifiable as stated) | Disconfirmed by | Meas. |
|---|---|---|---|
| G1 | **The envelope is one-shot.** Once the key crosses the threshold the attack runs to full open even if the key falls back below threshold first: a 1 ms full-scale burst under a 200 ms attack reaches within 0.5 dB of 0 dB of attenuation, after the burst has gone | The gain never leaving the Range floor; or a peak that scales with the burst's length | GAINTRACE |
| G2 | **Hold is a real stage**, 2 ms–2 s, timed from the key falling below threshold: at Hold 20, 100, 500 and 1000 ms the time the gain stays within 0.5 dB of full open after the key drops is within 10 % of the setting, and only then does the decay begin | An open time that does not track the Hold setting; decay beginning at the threshold crossing | GAINTRACE |
| G3 | **The key path is a band** with two separately settable ends, low cut 25 Hz–4 kHz and high cut 250 Hz–Nyquist: with the band at 500 Hz–2 kHz, the input level at which a 250 Hz tone and a 4 kHz tone first open the gate is **at least 4 dB above** the level at which a 1 kHz tone does. Key Listen puts the filtered band on the output instead of the audio | A shift of 1 dB or less at either end — which is what no key filter gives | GAINTRACE level search |
| G4 | **The closed state is Range, not zero.** With the input 30 dB below threshold the settled closed gain equals the Range setting within 0.5 dB at 0, −20, −40, −60 and −80 dB. The law is a fixed depth, not a slope: two inputs 10 dB apart, both at least 20 dB below threshold, get the same gain within 0.5 dB | A settled closed gain more than 0.5 dB from the setting; a closed gain that tracks the input level (the memoryless computer's ~8 dB per dB, A1) | CURVE |
| G5 | **Attack and decay are exponential stages whose time constant is the setting.** Decay: measured t63 within 15 % of the setting at 10, 100, 1000 and 4000 ms. Attack: measured 10–90 % within 15 % of 2.197 × the setting at 1, 10, 100 and 1000 ms. At the fastest attack (0.01 ms) the gate reaches full open within **0.2 ms** at 48 kHz — inside one cycle of 5 kHz, so a transient's leading edge is not clipped | A time constant more than 15 % from the setting at any of the eight; a fastest attack slower than 0.2 ms | GAINTRACE |
| G6 | **Peak detection.** A sine and a square of **equal peak** open the gate at thresholds within 0.5 dB of each other; the same pair at **equal RMS** open at thresholds about 3.0 dB apart (the square's crest advantage) | Equal-**RMS** material of different crest factors opening at the same threshold, which is what RMS detection gives | GAINTRACE level search |
| G7 | **Duck inverts the sense.** Built with `duck=True`, the gain is 0.00 ± 0.05 dB below threshold and settles at the Range setting within 0.5 dB above it, at Range 0, −6, −20 and −40 dB, on the same attack/hold/decay envelope | A resting gain other than unity below threshold; a ducked gain more than 0.5 dB from the setting; an envelope that ignores Hold in Duck | CURVE; GAINTRACE |

No characters: gate and duck are one mechanism under a switch, and G7 states
the switch. G3–G5 are shared with `Expander` and are demonstrated separately
in each class's own evidence pack.

**Tier 3.** Budget as a fraction of one stereo block's real-time deadline:
ESP32-P4 **6 %**, ESP32-S3 **12 %**. Lean patch expected: **no** — the
default build is one node. **Latency budget 0 samples**, met by the default
build; the one latency-adding option is `lookahead_ms`, default 0.0 (§6).

## 4. Modeling approach on the palette

**One `audiodynamics.Dynamics(DYN_GATE)` with the gate machine on.** Every
ask this seed filed landed in Phase 1 and is on the pin — `hold_ms`,
`hysteresis_db`, `depth_db`, `sidechain_lp_hz`, `sidechain_poles`,
`key_listen`, an external `key(sample)`, a `detector=` choice
(`upstream-diff.md:969-1099`). Only duck mode did not land (§5).

Two facts read out of the C at the pin, not recalled, shape the class. **The
gate machine is on only when `hold_frames != 0`** (`audioif_dynamics.c:452`);
below that the node is the old memoryless computer — the `over * 8.0f`
slope, no hold, no one-shot — so the class always passes `hold_ms` and its
Hold macro floors at 2 ms (96 frames at 48 kHz, 44 at 22.05 kHz) and the
machine cannot be off by accident (measured, App. P1). And **`depth_db`
positive means unset** (`:387-388`), so `range_db = 0.0` is a real setting
giving a floor of exactly unity — this class's wire condition, a gate having
no mix knob.

**Duck by composition, and only when asked:** `Splitter(taps=2)` →
[`Dynamics` → `Multiply` against a constant −32768] and the dry tap, both
into a two-voice `Mixer` — `x − b·g·x`, with `b = 1 − 10^(Range/20)` carried
in the node's own `makeup_db` so it is a float rather than the `Mixer`'s Q15
voice level. Measured at 48 kHz, settled ducked gain at Range −6/−10/−20/−40:
**−5.999 / −9.998 / −19.997 / −39.991 dB**, and below threshold a wire to
1 LSB (App. P3). Cost argument: **App. R2**.

**Tier: audioif.** `audiodynamics` is audioif's own module, not a
CircuitPython port (`upstream-diff.md:661`). Python computes coefficients at
construction and on a macro move; C runs the detector, the key filters, the
four-stage machine and the VCA per sample.

## 5. Node asks

**All closed.** N-GATE-1 (hold and a committed attack), N-GATE-2 (a settable
depth) and N-GATE-3 (a two-ended key band and an external key) landed in
Phase 1 inside `audiodynamics`, where §8.1 recommended they go; N-GATE-5
recorded that look-ahead already existed and pre-ramping was not asked for.

**N-GATE-4 (duck mode) did not land** and is not re-filed: the enum still has
five modes and no duck (`audioif_dynamics.h:21-27`), and the seed's own
palette verification refuted the ask, `Multiply` against a constant −32768
being an exact sign flip (`audioif_multiply.c:38`). What the composition
costs — 32 KB of `Splitter` ring, two extra nodes, and a **source-block
ceiling of 8192 frames** (App. P3) — is a Tier 3 argument for a flag on the
node, filed for a later phase, not a trait the palette cannot reach.

## 6. Surface — settled

**Eight macros**, every one a DS201 panel control.

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Threshold | UNIPOLAR | −80 … 0 dB | Threshold (−54 dB … ∞) |
| 1 | Attack | UNIPOLAR | 0.01 … 1000 ms, log | Attack (10 µs … 1 s) |
| 2 | Hold | UNIPOLAR | 2 … 2000 ms, log | Hold |
| 3 | Release | UNIPOLAR | 2 … 4000 ms, log | Decay |
| 4 | Range | UNIPOLAR | 0 … −80 dB | Range |
| 5 | Key Low | UNIPOLAR | 25 … 4000 Hz, log | L.F. |
| 6 | Key High | UNIPOLAR | 250 … 35000 Hz, log, clamped to 0.98 Nyquist | H.F. |
| 7 | Key Listen | TOGGLE | off / on | Key Listen |

Three proposed macros left the surface and none is lost; the arguments are in
**App. R2**. **Duck** became the construction option `duck=False` — gate
versus duck is a wiring decision, and no level-only change turns a built duck
graph back into a plain gate. **Lookahead** became `lookahead_ms=0.0`
(0…50 ms), because `latency_samples` is a static class field and a macro that
moved the latency could not be reported honestly (App. P2). **Hysteresis** is
**struck** under this seed's own §8.2 rule, no source having been reached for
any figure. Two further construction options, neither a control a performer
moves: `key=None`, the Ext key jack, a borrowed second source the class never
owns, resets or deinitialises and which starves the node if it runs dry
first (`Dynamics.c:255-259`); and `key_poles=1`, one or two poles per end of
the key band (5.29 and 10.31 dB/octave upstream), left at the node's default
because neither source states the DS201's filter order.

**Patches.** 0 **Default**, 1 **Tom Tighten**, 2 **Gated Reverb** (long hold,
fast decay), 3 **Vocal Breath Trim** (shallow Range, wide key), 4 **Amp
Hiss** (key 2–8 kHz, −80 Range), 5 **Drum Bleed** (key 100 Hz–1 kHz, short
hold). Key Listen is off in every patch: it replaces the output, and no patch
should hand a host a different signal.

**`capabilities` = `()`.** A gated-reverb hold in bars is tempting and
neither source's box has one; the class does not read the transport.

## 7. Defects in the current class the rebuild must not repeat

- **No surface, and no docstring at all.** `MACRO_LABELS = ()` at
  `dynamics.py:167`, `PATCHES = {0: ("Default", ())}` at `:169`, and the
  class body at `:161-177` carries no docstring — the only dynamics class
  without one. Threshold, attack and release (`:170-171`) are
  construction-only.
- **No Range**, so it inherits the node's fixed −80 dB clamp and cannot offer
  the −15 dB setting S1 recommends for exactly the case a gate is most often
  used in.
- **No hold**, so it cannot make the gated-reverb sound the DS201's own
  manual names as a headline use — and, on the landed node, no hold means the
  four-stage machine is off entirely.
- **The gate law is a slope and nothing says so.** A caller reading "noise
  gate" gets ~8 dB of attenuation per dB below the knee (A1): an expander at
  ratio 9.
- **The threshold default is −50 dB** (`:170`) with no key filter, so on any
  real source the gate chatters on hum and hiss it cannot be told to ignore.

## 8. Open questions — settled

1. **Where N-GATE-1's machine belongs.** *Settled by Phase 1:* inside
   `audiodynamics`, as this seed recommended (`upstream-diff.md:1030-1040`).
2. **Hysteresis.** *Settled: struck.* No source reached states a figure and
   this session fetched none. §6 records it.
3. **Whether Key Listen belongs on a macro surface.** *Settled: it stays, a
   TOGGLE, off in every patch.* It does change what the output is, which no
   other macro here does — but S1 says the position may simply be left there
   to use the box as a filter, so it is a use and not only a diagnostic, and
   the docstring says so in one line.
4. **The DS201 schematic** exists on elektrotanya and was not obtained. No
   trait depends on a component value. *Arthur's, for the survey; unchanged.*

## Appendix

Probes ran 2026-09-06 against the CPython build of audioif in
`audiocomponents/.venv`, 48 kHz, stereo, 16-bit. A1 and A4–A6 are recorded in
full in `Expander.md`'s appendix and are not repeated; the numbers this seed
leans on are:

**A1 — the palette's gate law (`DYN_GATE`, threshold −40 dB, 1 kHz sine).**
Output-minus-input in dB. Gain is 0 until the *peak* crosses threshold (RMS
−42.01 dBFS = peak −39.0), then −2.26, −10.26, −18.47 at 1, 2 and 3 dB
further down and −45.31 at 6 dB down: about 8 dB per dB, matching
`cut = over * 8.0f`. Below −50 dBFS RMS the int16 output is exactly zero —
quantisation, not the −80 dB clamp, and a reminder that "the output is silent"
is not evidence the gate closed.

**A6 — the one-shot rule refuted on the palette.** A 1 ms full-scale burst then
silence into `DYN_GATE`, threshold −40 dB, `attack_ms=200`: the reported gain
stayed at −80.00 dB for all 90 blocks rendered. This is the planted-fault
shape the class gate needs — a measurement that already goes red on today's
node, so a green result after N-GATE-1 lands means something.

**A7 — chatter, and what the probe could not show.** A 1 kHz tone whose level
wobbled ±6 dB at 4 Hz around a −36 dB threshold opened the gate exactly 4
times in 1.0 s with the gain ranging −68.1 to 0.0 dB. That is *correct*
behaviour on clean material and therefore **not** a chatter demonstration: a
hysteresis or hold trait needs material whose level crosses the threshold many
times per open — noise, or a decaying tail — and the kit's chatter probe must
be specified that way or it will pass on everything.

---

### Palette verification, 2026-09-06

Independent run against the CPython build of audioif in
`audiocomponents/.venv`, 48 kHz, stereo, 16-bit.

**V-G1 — the palette has a retriggerable per-sample VCA.**
`audiomath.Multiply(source=<audio>, modulator=<synthio.Synthesizer>, mix=1.0)`
with one note carrying a 64-sample constant waveform and
`synthio.Envelope(attack_time=0.05, release_time=0.05, sustain_level=1.0)`.
Pressing at block 4 and releasing at block 20, the per-block gain of the
Multiply output relative to its input, in dB:

```
blocks 0-3  : silent
blocks 4-12 : -25.6 -19.4 -15.9 -13.5 -11.4 -9.9 -8.7 -7.3 -6.3
blocks 13-20: -6.1 -6.0 -6.0 -6.1 -6.0 -6.0 -6.1 -6.0   (sustain plateau)
blocks 21-29: -7.0 -8.2 -9.3 -10.8 -12.8 -14.8 -17.9 -22.8 -33.9
blocks 30+  : silent
```

A smooth attack, a flat hold and a smooth release, all per sample — no
block-rate step. (The plateau sits 6 dB down because synthio's note amplitude
defaults to half scale; a `Note(amplitude=…)` or the mixer level corrects it.)
This is the fact that kills the first draft's reason for N-GATE-1. What it does
not give is a trigger: `press()`/`release()` are Python calls, and the contract
gives a component no per-block hook to make them from
(`docs/audio-component-api.md:231-233`).

**V-G2 — duck by composition (the N-GATE-4 refutation).** Graph:
`RawSample → Mixer(guard) → Splitter(taps=2)`; tap 0 →
`Dynamics(DYN_GATE)` → `Multiply(modulator = constant −32768, mix=1.0)`;
tap 1 → dry; both into a two-voice `Mixer` at levels 1.0 and `1 − Range`.

- Inverter check: 512 frames of a 1 kHz sine at 0.5 amplitude,
  `max |out + in| = **0 LSB**` — an exact sign flip, as
  `(a · −32768) >> 15 = −a` predicts (`audioif_multiply.c:38`).
- Gate open (threshold −60 dB, loud signal): duck output **all zeros**.
- Gate shut (threshold 40 dB above the signal): duck output **−0.00 dB** —
  bit-for-bit the input.
- With a Range setting: below threshold −0.000 dB at every setting; above
  threshold −6.00, −10.00, −20.00, −39.97 and −59.70 dB for Range settings of
  −6, −10, −20, −40 and −60 dB.
- Programme material (a 440 Hz burst for 8000 frames, then the same tone
  34 dB down), threshold −20 dB: **exact silence** through the burst,
  **−41.29 dBFS** afterwards, matching the source's own −41.29 dBFS.

**V-G3 — the mixer cannot invert, which is why the first draft's refutation
looked right.** `synthio_block_slot_get_limited(&voice->level, 0.0, 1.0)`
(`src/audiomixer/Mixer.c:332`) clamps a voice level to 0…1 before the Q15
multiply, so a negative level is silently zero. The inversion has to come from
`audiomath.Multiply`.

### App. C — the four Tier 2 rows restated on 2026-09-07, with the arithmetic

Written **before** the rebuild, from the sources and from
`audioif/src/shared/audioif_dynamics.c` at the pin, not from any render of
the rebuilt class. Nothing is deleted: each row's first draft is quoted here
beside what replaced it and why.

**G2 — which of S1's two Hold statements the class implements.** The audit
flagged that S1 says Hold is "the amount of time the gate is held open after
the signal falls below the Threshold" and, two paragraphs later, that "the
Hold cycle starts as soon as the Threshold is crossed". *The first reading is
picked*, because it is the one the landed node implements: HOLD is entered
when the attack completes, `hold_left` **reloads** while the key stays above
the hysteresis point and only decrements once it falls below
(`audioif_dynamics.c:697-711`). The second statement is about the *envelope
cycle* committing at the crossing, which is G1, not G2. The first draft's
"the measured open time equals attack + hold + decay within 10 %" is struck:
attack-to-full for a one-pole is about 6.9 time constants and decay-to-floor
about 13.8, so the sum of the three *settings* is not the open time under any
correct implementation and the row could not go green. Replaced by a clause
that varies Hold alone and holds the open time to it.

**G3 — the out-of-band clause.** The first draft asked that an out-of-band
tone "swept from −60 dBFS to 0 dBFS moves the gain less than 1 dB off the
Range floor at every level". No key filter of any order can do that: a
one-pole at an octave outside gives about 6 dB of rejection, so a full-scale
out-of-band tone still presents about −6 dBFS to the detector and opens any
gate whose threshold is below that. The row is restated as the **shift in the
opening level**, which is what a stopband actually is, is falsifiable (no
filter gives 0 dB of shift), and is what the kit's level search measures.

**G5 — the tolerance, and the fast end.** *Tolerance:* for a one-pole whose
coefficient is `1 − exp(−1000/(ms·rate))` (`audioif_dynamics.c:9-14`) the
setting is the **time constant**; the 10–90 % transition is
`ln(9) = 2.197` time constants. The first draft's "the measured 10–90 %
transition is within 15 % of the setting" is therefore 120 % out by
construction. Restated: decay by its t63 (which the kit exports directly) and
attack by 10–90 % against 2.197 × the setting. *Fast end:* the first draft
asked for "one sample or less" at settings below one sample period. At the
panel's fastest, 10 µs, the coefficient is
`1 − exp(−1000/(0.01·48000)) = 0.876`, so the gain runs 0.876, 0.985, 0.998
and reaches the machine's 0.999 snap on the seventh sample — 0.146 ms. One
sample is unreachable for any setting above about 1.25 µs, where the
coefficient rounds to 1.0 in `float`. Restated against S1's own claim for the
control ("ensures that the gate does not clip the leading edge of extremely
fast transients") as **full open within 0.2 ms at 48 kHz**, one cycle of
5 kHz.

**G4 and G7 — the ends of their spans.** G4 keeps −80 dB because the node's
`depth_db` reaches it exactly. G7 is stated to −40 dB rather than −80: the
composed duck subtracts two nearly equal int16 streams, so its floor is the
subtraction's own quantisation and not the setting. Measured this session,
App. P3.

### App. P — probes run 2026-09-07, before the rebuild

CPython, `audiocomponents/.venv/bin/python` with audioif at the pin
`2f6cbc3`, 48 kHz, stereo, 16-bit, driving the **nodes** rather than any
class. Scripts under the session's scratch directory; the numbers are quoted
in §4 and §6.

**P1 — the gate machine is on only when `hold_frames != 0`.** A 1 kHz sine at
0.5 amplitude (peak −6.02 dBFS) into `DYN_GATE`, threshold −6 dB, attack
1 ms, release 50 ms, `depth_db=-40`, settled gain of the last block against
the source:

```
hold_ms=  0.0 settled gain  -3.58 dB  gain_reduction_db -3.47
hold_ms=  2.0 settled gain -40.04 dB  gain_reduction_db -40.00
hold_ms= 20.0 settled gain -40.04 dB  gain_reduction_db -40.00
```

At `hold_ms=0` the node is the memoryless computer and its `over * 8.0f`
slope; at 2 ms and above it is the four-stage machine and `depth_db` is an
exact floor.

**P1b — the one-shot, and its planted-fault shape.** A 1 ms full-scale 1 kHz
burst then silence, threshold −20 dB, attack 200 ms, `depth_db=-80`:

```
hold_ms=20  gains at blocks 0,10,50,100,150,179:
            -31.60  -11.89  -2.58  -0.61  -0.16  -0.07 dB
            max -0.07 dB at block 179
hold_ms=0   max -80.00 dB   (the gate never opens at all)
```

**P2 — latency is the look-ahead and nothing else.** One full-scale sample at
frame 100 of an 8192-frame stereo probe, gate forced open:

```
lookahead_ms=0.0 -> impulse out at frame 100 (delay  0)
lookahead_ms=1.0 -> impulse out at frame 148 (delay 48)
lookahead_ms=2.0 -> impulse out at frame 196 (delay 96)
```

48 frames is exactly 1.000 ms at 48 kHz.

**P2b — Key Listen replaces the output.** A 220 Hz tone at 0.5 amplitude with
the key high-passed at 4 kHz: `key_listen=True` peaks at **684**, the
ordinary output at **16384**.

**P3 — the composed duck, and the Splitter's source-block ceiling.**
`Splitter(taps=2)` → [`Dynamics(DYN_GATE)` → `Multiply` against a constant
−32768] and the dry tap into a two-voice `Mixer` at level 1.0 each, with
`b = 1 − 10^(Range/20)` in the node's `makeup_db`. Loud material (gate open,
so the duck is at its depth):

```
Range   -6.0 dB -> settled  -5.999 dB
Range  -10.0 dB -> settled  -9.998 dB
Range  -20.0 dB -> settled -19.997 dB
Range  -40.0 dB -> settled -39.991 dB
Range  -60.0 dB -> settled -59.679 dB
Range  -80.0 dB -> settled -78.268 dB
```

The last two are the int16 subtraction's own floor, not the `Mixer`'s Q15
level, which the `makeup_db` route bypasses: subtracting `0.9999·x` from `x`
leaves about one LSB. G7 is stated to −40 dB for that reason.

Below threshold, with the source re-blocked to 256 frames through a
transparent `audiofilters.Filter` adapter (the renderer's own device):
`max |out − dry| = **1 LSB**` over 28 672 samples, **−0.0005 dB**.

The same test with the probe handed straight from a 24 000-frame
`audiocore.RawSample`, whose `get_buffer` returns the whole array in one
call: `max |out − dry| = **28 377 LSB**`. That is the `Splitter`'s
8192-frame ring being lapped (`audioif_splitter.h:20`) — the same failure
`MultibandCompressor.md` A-M5 records — and it is why §5 states an
8192-frame source-block ceiling for the duck build. The plain gate build has
no `Splitter` and no ceiling.

### App. R2 — prose moved out of §§1–6 on 2026-09-07

*(from §1)* The fuller reading of S1, kept verbatim where §1 now paraphrases:
Bypass "routes the input signal to the output with no processing"; the
schematic sheet is titled "DS 201 (Fig.1) Audio and VCA Circuits" and the
setting-up procedure probes the "output of V.C.A. op. amp channel 1" (S5), so
the gain element is a VCA and that is sourced. Attack: "the fastest Attack
time ensures that the gate does not clip the leading edge of extremely fast
transients". Hold: "the amount of time the gate is held open after the signal
falls below the Threshold … instrumental in creating the classic gated reverb
sound". Range: "the amount of attenuation applied to the input signal when
the gate is closed, variable from 0 dB to −80 dB". Key Listen: the manual
notes it can simply be left there to use the box as a filter.

*(from §6)* **Why Duck is a construction option and not macro 8.** A live
toggle needs the `Splitter`, `Multiply` and `Mixer` built on every instance —
32 KB of ring, two extra nodes on the audio path and the 8192-frame source
ceiling of App. P3, paid by every plain gate — or a graph rebuilt inside
`_apply_macro`. Neither is acceptable, and there is no third way: the `Mixer`
clamps a voice level to 0…1 before its Q15 multiply (`Mixer.c:332`) so it
cannot subtract, and `Multiply` against +32767 is not a wire — 32767/32768 is
the WIRE planted fault exactly. Gate versus duck is a wiring decision and it
is taken at construction.

*(from §6)* **Why Lookahead is a construction option and not macro 9.**
`_component.Component.latency_samples` reads `type(self).LATENCY_SAMPLES`, a
class field, so two instances of one class cannot report different latencies
and a macro that moved the latency would be reported wrongly by every host
that asked. The class overrides the property to report its own instance's
figure, declares `LATENCY_SAMPLES = 0` for the default build, and takes the
option at construction where a host can read the answer once and route around
it. S2's numbers stand behind the default: a look-ahead of 16 samples
(333 µs at 48 kHz) "allow[s] accurate reproduction of signals at or above
750 Hz" and 96 samples (2 ms) is "somewhere around" the live-sound limit.

*(from §6)* **Why Hysteresis is struck.** §8.2 of this seed set the rule
before any of this was built: the macro "ships only if Phase 0 or the
implementation session reaches a source; otherwise it is struck and the seed
records why". Neither manual edition uses the word, RaneNote 155 gives no
figure for any unit, and Station A forbids fetching. The node's
`hysteresis_db` exists and defaults to 0.0; the class does not set it and
claims nothing about it.

### App. I — Tier 1 invariants, the standard block

Verbatim from vision §3, moved out of §3 under the length rule. It is the
same block in every seed; a class-specific note on it is kept with it here.

- [ ] Silence in gives silence out; a decaying tail reaches exact zero — no
      held DC (the audioif#23 class of defect).
- [ ] `mix` at zero, or drive at zero, is a wire (byte-identical to source).
- [ ] Level-honest: unity through the dry path, no hidden gain.
- [ ] Reported `latency_samples` / `tail_samples` match what is measured —
      latency by a click against the dry path at 48 kHz and 44.1 kHz, tail
      by the burst-then-silence probe.
- [ ] `reset()` leaves every node the class built silent and stateless and
      the borrowed source untouched (planted faults: a delay line left full;
      an upstream instrument reset through a Filter- or Phaser-tailed chain).
- [ ] `deinit()` deinitialises every node the class built and leaves the
      source rendering (planted fault: an intermediate node left live).
- [ ] `capabilities` names exactly the optional behaviours the class honours
      (`"tempo_sync"` declared if and only if the transport is read).
- [ ] Pulling `output` allocates nothing.
- [ ] CPython and desktop MicroPython render identical bytes on the probe
      material, or the cause is recorded here; the P4 and S3 digests match
      the desktop's or carry a recorded cause (float width is the expected
      one, never the class).
- [ ] Rate-honest: designed and stated at 48 kHz; every invariant also holds
      at 44.1 kHz and 22.05 kHz; Hz-valued spans and options clamp below
      Nyquist at the running rate, never refuse; any Tier 2 trait that cannot
      hold at a lower rate is named here with why.
- [ ] Every invariant also holds at `channel_count` 1; a stereo-by-definition
      class states in §4 what a mono source gets (a wire, or the mono sum of
      its stereo behaviour), and the kit measures that statement.

**Mono:** one gain from a channel-linked detector applied to every channel, so
a mono source gets identical processing; the DS201's Stereo Link is what the
class does by default and its unlinked mode is out of scope for a single
component. **Rate:** G3's key span tops at 35 kHz, above Nyquist at every rate
here; it clamps (Tier 1) and G3 is stated against the clamped top. **G5's**
10 µs attack (audit: the first draft wrote G1 here; the attack span is G5) is
0.48 of a sample at 48 kHz and 0.22 at 22.05 kHz — the trait is stated as "one
sample or less", which holds at every rate.
**`capabilities` (D10): `()`.** A gated-reverb hold in bars is tempting and
neither source's box has one; the class does not read the transport.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Drawmer, *DS201 Dual Noise Gate Operator's Manual* (manufacturer's text, from `drawmer.com/op201.htm`, 7 pp.) | Every control range in §1, the envelope-completion rule, the Range advice and the −15 dB recommendation, Gate/Duck, Ext key, Key Listen, Stereo Link, the click-on-fast-attack passage, the HF-filter trigger-delay note | The PDF carries no licence line; its header prints `http://www.drawmer.com/op201.htm`, 31 Jan 2005 — Drawmer's own page on a third-party mirror (UMass Lowell SRT, whose only notice, "Copyright © 2026 UML SRT", covers the mirror, not the text). Chased to the rights holder: Drawmer's own manual (S4) says it "may not be duplicated in whole or in part without the written consent of Drawmer" — **verified all-rights-reserved**. Read as a document, nothing reproduced | <https://umlsrt.com/StudioDocuments/drawmer%20ds201%20manual.pdf> | yes — PDF fetched, text via `pypdf` |
| **S2** Jeffs, Holden & Bohn, *Dynamics Processors*, RaneNote 155 | The ∞:1-plus-depth law and gate block diagram (Figs. 17a/b); peak detection for gates; hold 0–3 s, depth 0 to −80 dB; the look-ahead and pre-ramping numbers (96 samples = 2 ms at 48 kHz, 16 samples = 333 µs reproduces ≥750 Hz, "look-ahead one quarter of a cycle"); the measured 16 dB of above-10 kHz energy a step-opened gate adds | PDF line "© 2005 Rane Corporation"; the site's Terms of Use (reached this run, <https://www.ranecommercial.com/legacy/terms-of-use.html>) is "Copyright © 2012-2018 inMusic Brands, Inc. All rights reserved." — personal, non-commercial viewing only, no redistribution without written permission. **Verified all-rights-reserved**, not "no further terms". Read only | <https://www.ranecommercial.com/legacy/pdf/ranenotes/Dynamics_Processors.pdf> | yes — PDF fetched, text via `pypdf` |
| **S3** Drawmer, DS201 product page | Feature list and audio specs; confirms Gating/Ducking, the external key and Key Listen | Footer: "Copyright © 2026 All rights reserved. Drawmer Electronics Ltd." — **verified all-rights-reserved**, not merely unstated. Read only | <https://www.drawmer.com/products/pro-series/ds201.php> | yes — HTML; this host answers WebFetch with HTTP 429, so the audit fetched it directly (HTTP 200) |
| **S4** Drawmer, *DS201 Operator's Manual*, the manufacturer's own current edition, 14 pp. | The same control descriptions, and **two values that differ from S1's 2005 capture**: Threshold "-50dBFs - infinate" and Range "0dB - 90dB". Also an explicit copyright line, and a block diagram on p. 14 (an image, not extracted) | "This manual is copyrighted © 2008 by Drawmer Electronics, Ltd. With all rights reserved. Under copyright laws, this manual may not be duplicated in whole or in part without the written consent of Drawmer." Read only | <https://www.drawmer.com/uploads/manuals/ds201_operators_manual.pdf> | yes — PDF fetched (HTTP 200, 14 pp.), text via `pypdf`; **added by the audit run**, where the first run had recorded this URL as unreachable |
| **S5** Drawmer, *DS201 Service Information* (7 pp.) and *DS201 Comp Sch* (3 pp.) — the manufacturer's own service documents, reached as `elektrotanya.com`'s own preview page images (first two pages of each) | Two legible hand-drawn Drawmer sheets with component values: "DS 201 (Fig.1) Audio and VCA Circuits" (signal and key inputs, Int/Ext key source, Threshold, Range, By-Pass/Key Listen, control voltage, "All Op. Amps. TL072 or LF353") and "DS 201 (Fig. 2) Rectifier. Attack, Hold, Decay Circuits"; and a setting-up procedure naming the "output of V.C.A. op. amp channel 1" and a "F.e.t. bias pre-set". **Used here for one fact only: the gain element is a VCA.** | The drawings are Drawmer's, under S4's all-rights-reserved notice; the host's own terms read "Please do not offer the downloaded file for sell only use it for personal usage" — **personal use only**. Read as a document (vision §5); nothing reproduced, no component value carried into a trait | <https://elektrotanya.com/drawmer_ds201_comp_sch.pdf/download.html> (preview images under `/PREVIEWS/63463243/23432455/drawmer/`) | yes — preview images fetched (HTTP 200) and read; the full PDFs were **not** obtained. Added by the audit run |

### App. T — Tier 2 rows: the sources, the confidence, and the pre-freeze drafts

Two things live here. **The Source and Conf. columns are live** — §3 dropped
them under the length rule and this is where they are read. **The trait
statements below are the seed's pre-freeze drafts**, superseded by §3 as of
the freeze of 2026-09-07 and kept unchanged under "delete nothing"; where a
row here and §3 disagree, §3 is the frozen trait and **App. C** carries the
arithmetic for the change. G1, G4 and G6 are unchanged between the two.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| G1 | **The envelope is one-shot.** Once the key crosses the threshold the attack runs to full open even if the key falls back below threshold first — a 1 ms key burst under a 200 ms attack still reaches 0 dB of attenuation | S1, verbatim ("the envelope cycle will complete even if the Key source falls below the Threshold level before the Attack phase is completed") | high — stated as a rule, in the manual's own Note | The gate not reaching full open, or opening only in proportion to the burst's length | ONESHOT |
| G2 | **Hold is a real stage**, variable 2 ms–2 s, timed from the key falling below threshold; through it the gain sits at 0 dB and only then does the decay begin, so the measured open time equals attack + hold + decay within 10 % | S1 (Hold description); S2 (hold "typical range of 0 to 3 seconds") | high | Decay starting at the threshold crossing, or an open time that tracks attack + decay alone | ENV |
| G3 | The key path is a **band**: low cut settable 25 Hz–4 kHz, high cut 250 Hz–35 kHz (clamped below Nyquist), and with the band set to 500 Hz–2 kHz a tone an octave outside either end, swept from −60 dBFS to 0 dBFS, moves the gain less than 1 dB off the Range floor at every level; Key Listen puts that band on the output | S1 (L.F., H.F., Key Listen) | high | An out-of-band tone at any level up to full scale moving the gain more than 1 dB off the floor; a gate that opens fully as an out-of-band tone is raised. *(Two clauses of the first draft are struck as unsourced: "a skirt shallower than 12 dB/oct at either end" — neither source states the key filters' order, which is a design choice, §5 — and "at any level", which is unbounded and therefore unfalsifiable; the level span the kit actually drives is named instead. **Critic pass, 2026-09-06.**)* | KEY |
| G4 | **The closed state is Range, not zero**: with the input 30 dB below threshold at −6 dBFS, the settled closed gain equals the Range setting within 0.5 dB at 0, −20, −40 and −60 dB, and the control's full span reaches at least −80 dB (S1's 2005 edition; S4's 2008 manual says "0dB - 90dB"). The law is a fixed depth, not a slope: two inputs 10 dB apart, both at least 20 dB below threshold, get the same gain within 0.5 dB | S1 (Range); S2 ("a gate uses a fixed ratio of ∞:1 and a variable depth") | high | A settled closed gain more than 0.5 dB from the setting at any of the four; a closed gain that tracks the input level, i.e. a finite slope (the shipped node's ~8 dB per dB, A1); a span that stops short of −80 dB | LAW at four Range settings |
| G5 | **Attack spans 10 µs to 1 s and decay 2 ms to 4 s**: at settings 1, 10, 100 and 1000 ms of attack and 10, 100, 1000 and 4000 ms of decay the measured 10–90 % transition is within 15 % of the setting, and at the fast end (settings below one sample period, 20.8 µs at 48 kHz) the open transition is one sample or less | S1 (Attack, Decay) | medium — panel ranges, no measured curves in the sources | A measured transition more than 15 % from the setting at any of the eight; a fastest attack longer than one sample; a slowest decay whose measured 10–90 % time is under 3.4 s (15 % short of 4 s) | ENV |
| G6 | **Peak detection**: a sine and a square of **equal peak** open the gate at thresholds within 0.5 dB of each other, while the same pair at **equal RMS** open at thresholds about 3.0 dB apart (the square's crest advantage); and with attack at its fastest a burst whose peak crosses the threshold reaches full open within one cycle of its own fundamental | S2 ("a gate must respond very quickly to changes in level, dictating the use of a peak detector") | medium — general to gates, not stated of the DS201 | Equal-**RMS** material of different crest factors opening at the same threshold, which is what RMS detection gives; or an equal-peak pair whose opening thresholds differ by more than 0.5 dB. *(Critic pass, 2026-09-06: the first draft's leading clause — first-cycle opening — was measured by LAW, a steady staircase that cannot see it. The clause is kept and given ENV; the equal-peak/equal-RMS pair is what LAW measures.)* | LAW with sine and square, at equal peak and at equal RMS; ENV for the first-cycle clause |
| G7 | **Duck mode inverts the sense**: with Duck selected, gain is 0.00 ± 0.05 dB below threshold and settles at the Range setting within 0.5 dB above it, on the same attack/hold/decay envelope — the measured open time obeys G2's attack + hold + decay within 10 % in Duck as in Gate | S1 (Gate/Duck); S3 | high | A settled ducked gain more than 0.5 dB from the Range setting; a resting gain other than unity below threshold; an envelope that ignores Hold in Duck | ENV |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

*Licence and citation audit, 2026-09-06 — **two passes**. Second pass (unit
`gate-deesser-transient-multiband`): every URL above re-fetched from this
machine with `curl` (all HTTP 200), every PDF re-extracted with `pypdf` and
every quotation re-read against the document's own text, every licence line
read on the page that carries it, and every "not reached" claim re-tested.
Corrections are marked inline.*

*(from §2)*

No copyleft source was reached, so none was measured; no emulator was opened.
**Partly found, by the licence audit:** `elektrotanya.com` lists
`drawmer_ds201_sm.pdf` (7 pages) and `drawmer_ds201_comp_sch.pdf` (3 pages) and
serves the **first two pages of each as preview images**. The audit run fetched
and read all four, and two are legible Drawmer schematic sheets with component
values — cited as S5 above. The full PDFs were not obtained, so the third
schematic page and the rest of the service manual remain unread. *Corrected by
the audit: the first run recorded the schematic as not obtained and "VCA" as
unsourced; both are now wrong. It also described both entries as one 7-page
document — only the service manual is.* Drawmer's own manual (S4) prints a block
diagram, not a schematic. *Also corrected by the audit: the first run recorded
`drawmer.com`'s own manual PDF as unreachable (HTTP 429); that host answers
WebFetch with 429 (re-confirmed this run) but serves a direct request
(HTTP 200), and the manual is cited as S4.*
**Unsourced, therefore absent from the trait table:** any
DS201 hysteresis figure — neither manual edition uses the word, and later
Drawmer boxes are not this one; and any statement about whether the DS201's
own detector is peak or RMS, which S1 never says (G6 rests on S2's general
claim, not on the DS201). *Audit note on the second: S5's second sheet is
titled "Rectifier. Attack, Hold, Decay Circuits", so a drawing of the detector
now exists in reach — but the audit derived nothing from it, and G6 stays
sourced to S2 until someone does.*

*(from §3)*

Kit: **ENV** = burst-then-silence, per-block gain trace; **ONESHOT** = a 1 ms
key burst under a long attack; **LAW** = 1 kHz steady-sine staircase, 1 dB
steps, output RMS per step; **KEY** = swept sine at fixed amplitude,
gain-reduction trace; **CLICK** = the gate opened onto a 100 Hz sine with the
threshold at 80 % of peak, spectrum of the output above 10 kHz.

*(from §3)*

**Audit flag on G2.** S1 states the Hold timing twice and the two statements
disagree: the Hold control description says Hold is "the amount of time the gate
is held open after the signal falls below the Threshold" (G2's reading), while
the Note two paragraphs later says "the Hold cycle starts as soon as the
Threshold is crossed". G1 quotes the rest of that same Note and is unaffected.
The implementation session picks a reading for G2's origin and records which.

*(from §3)*

**Latency: zero by default.** The DS201 has no look-ahead — no source reached
describes one, and its Bypass "routes the input signal to the output with no
processing" — so `latency_samples` is 0 and G1–G7 are all stated at zero latency.
One option adds latency and **defaults off**: RaneNote 155 argues that
"superior gating requires look-ahead and pre-ramping", and gives the numbers a
default must respect — a look-ahead of 16 samples (333 µs at 48 kHz)
"allow[s] accurate reproduction of signals at or above 750 Hz", 96 samples
(2 ms) is "somewhere around" the live-sound limit, and the rule is to look
ahead one quarter of a cycle of the lowest frequency to be preserved (S2).
So: **`lookahead_ms` defaults to 0**; when set, the smallest useful value is
16 samples and the class reports it in `latency_samples` the moment it is
turned on and names it in milliseconds in the docstring. The knob that trades
CPU for latency here is not CPU at all but low-frequency fidelity, and the
docstring says so. Measured, `Dynamics` with look-ahead off returns an impulse
in the frame it arrived; at `lookahead_ms=5.0` it returns 240 frames later,
exactly 5.00 ms (A5 in `Expander.md`).

*(from §4)*

- **G1** — the follower has no trigger state: it is two coefficients and a
  one-pole (`audioif_dynamics.c:302-307`). Measured, a 1 ms full-scale burst
  under `attack_ms=200` left the reported gain pinned at −80.00 dB for all 90
  blocks rendered; **the gate never opened at all** (`Expander.md` A6).

*(from §4)*

- **G4** — the gate law is a *slope*, not a depth: `cut = over * 8.0f` clamped
  at −80 (`audioif_dynamics.c:191-192`). Measured, gain falls −2.26, −10.26,
  −18.47 and −45.31 dB at 1, 2, 3 and 6 dB below the knee — about 8 dB of
  attenuation per dB of input, where G4 requires a flat floor (A1). *(Partly
  composable: the slope clamps at −80 dB within 10 dB of threshold, and a dry
  blend through `Mixer` sets a flat floor per sample from 0 to −50 dB within
  0.2 dB. It stops there — see §5's N-GATE-2 and `Expander.md` V-E4.)*

*(from §4)*

- **G7** — there is no duck mode in the enum (`audioif_dynamics.h:21-27`), but
  the trait is reachable without one: `Multiply` against a constant −32768
  modulator inverts exactly, so `dry − gated` is a duck. Measured to 0.03 dB of
  the Range setting above threshold and 0.000 dB below it (V-G2). §5 records
  the refutation.

*(from §4)*

**Composition was tried again in the palette verification of 2026-09-06, and
the first draft's reason for failure was wrong.** It said "the only per-sample
gain on the palette is `audiomath.Multiply`, whose modulator is a looping
table, not an envelope the class can retrigger." `Multiply`'s modulator is any
audiosample (`Multiply.c:55-63`, `:86-97`), including a live
`synthio.Synthesizer`, and a note carrying a constant waveform and a
`synthio.Envelope` renders a **retriggerable per-sample envelope as a stream**
— measured, that graph gives a smooth click-free VCA that opens over its
attack, holds, and closes over its release (V-G1). The palette has the gain
element a gate needs.

*(from §4)*

What it does not have is anywhere to take the *decision*. The trigger would
have to come from Python reading `gain_reduction_db()`, and a component has no
per-block hook to run that in: the live surface is frozen (roadmap §3) and
*"pulling from `output` must not allocate, block, perform I/O, or depend on
garbage collection"* (`docs/audio-component-api.md:231-233`). Even given a
hook, the decision would be quantised to a 256-frame block — 5.3 ms — which
misses G6's "full open within one cycle of its own fundamental" for anything
above about 190 Hz and puts a floor of 5.3 ms under G2's 2 ms hold. So the
rebuild's shape is still **one `Dynamics` node with a real gate envelope behind
it**, and the asks in §5 are what make that node a gate — but the reason is the
trigger, not the VCA.

*(from §4)*

**Portability tier: audioif** — `audiodynamics` is audioif's own module, not a
CircuitPython port (`audioif/docs/upstream-diff.md:661`); the class carries the
guarded import and a construction-time `ImportError` on a stock board. Python
computes coefficients at construction and on a macro move; C runs the
follower, the envelope stage machine and the VCA per sample.

*(from §5)*

- **N-GATE-1 — a gate envelope with hold and a committed attack (unblocks G1,
  G2, G5).** A four-stage state machine — closed / attack / hold / decay —
  with `hold_ms` (default 0) and attack committed on the threshold crossing
  (default off, so today's follower is the default). Palette: a plain one-pole
  follower; measured, a 1 ms burst under a 200 ms attack never opens the gate
  (`Expander.md` A6, re-measured this run as −80.00 dB across all 90 blocks,
  `Expander.md` V-E2), and there is no hold at all. *Refutation, re-run
  2026-09-06 and corrected:* the palette **does** have a retriggerable
  per-sample VCA — `audiomath.Multiply` modulated by a `synthio.Synthesizer`
  note with a constant waveform and an envelope, measured smooth and click-free
  (V-G1) — so the first draft's reason ("a looping table with no retrigger")
  is wrong. What the palette lacks is the trigger: a component has no per-block
  hook to run the decision in (`docs/audio-component-api.md:231-233`; roadmap
  §3 freezes the live surface), and even given one the decision quantises to
  5.3 ms, which misses G6's one-cycle opening above ~190 Hz and floors G2's
  2 ms hold. Ask stands. **This is the one ask without which the class cannot
  be a DS201-informed gate at all.**

*(from §5)*

- **N-GATE-2 — a settable depth (unblocks G4).** `depth_db`, default −80 for
  `DYN_GATE` (today's clamp) and −60 for `DYN_EXPAND`, range 0 to −80, and
  the gate law becomes a floor rather than the `over * 8.0f` slope when a depth
  is set. Palette: the literals at `:191-192`, measured as ~8 dB per dB (A1).
  **Ask stands, but only for the deep end.** *(Palette verification,
  2026-09-06; the first draft's refutation — "clamping in Python is block-rate
  again" — answered the wrong composition.)* Blending the dry signal back
  through `audiomixer.Mixer` sets the floor per sample, not at block rate:
  measured, the settled closed gain tracks the setting to −0.00 / −0.01 /
  −0.06 / −0.18 dB at 0, −20, −40 and −50 dB, the open state stays a wire to
  0.001 dB, and G4's second clause is met because the `over * 8.0f` slope
  clamps at −80 dB within 10 dB of threshold. It fails at −60 dB (0.72 dB out,
  0.32 with the dry attenuation split across two mixers) and cannot reach
  −80 dB at all: the `Mixer` level is a Q15 integer
  (`src/audiomixer/Mixer.c:332`) with no value between −80.8 and −78.3 dB
  (`Expander.md` V-E4). G4 asks for 0.5 dB at −60 **and** a span to −80, so the
  ask survives for the last 20 dB — and for cost, since the composition spends
  a 32 KB `Splitter` ring (`audioif_splitter.h:20`, `:29`) and two `Mixer`s
  where the option is one float. *Same ask as `Expander`'s N-EXP-3; file
  once.*

*(from §5)*

- **N-GATE-3 — a two-ended key band and an external key (unblocks G3).**
  `sidechain_lp_hz` beside `sidechain_hz`, both 12 dB/octave, and a `key`
  source the node reads instead of the audio. *Refutation, re-run 2026-09-06:*
  `Splitter` + `Filter` build the band but nothing can hand it to `Dynamics` as
  a detector — the keyword table has no `key` and no second corner
  (`Dynamics.c:20-30`; both `set()` calls raise `TypeError: unknown Dynamics
  option`), and the detector reads the same buffer the VCA scales
  (`audioif_dynamics.c:239`, `:254`, `:313`). Ask stands. *Same ask as
  `Expander`'s N-EXP-2; file once.*

*(from §5)*

- **N-GATE-4 — duck mode (unblocks G7).** A fifth mode, or a `duck=True`
  option on `DYN_GATE`, inverting the gain computer's sense. Palette: not in
  the enum (`audioif_dynamics.h:21-27`).

*(from §5)*

  **REFUTED BY PALETTE: the subtraction *is* on the palette, and the composed
  duck meets G7 as written.** *(Palette verification, 2026-09-06.)* The first
  draft's "the subtraction is not on the palette" is true of `audiomixer.Mixer`
  alone — its voice level is clamped to 0…1 and quantised to Q15
  (`src/audiomixer/Mixer.c:332`), so a mixer cannot invert. But
  `audiomath.Multiply` computes `(a·b) >> 15` on signed int16
  (`audioif_multiply.c:38`), so a modulator held at the negative rail
  (−32768) is an **exact** sign flip: measured over 512 frames of a 1 kHz sine,
  `max |out + in| = 0 LSB`. The duck is then
  `Splitter → [Dynamics(DYN_GATE), dry] → Multiply(−1) on the gated branch →
  Mixer`, i.e. `x − b·g·x`. Measured with `b = 1 − Range`: below threshold
  **−0.000 dB** (G7 allows ±0.05), above threshold **−6.00 / −10.00 / −20.00 /
  −39.97 / −59.70 dB** at Range settings of −6, −10, −20, −40 and −60 dB (G7
  allows 0.5), and on burst-then-quiet material the signal ducks to exact zero
  under the burst and returns at its full level after it (V-G2). What the
  composed duck inherits is the *envelope* — it follows whatever `Dynamics`'
  one-pole does, so G7's "on the same attack/hold/decay envelope" clause is
  delivered by N-GATE-1, not by this ask. It also spends a 32 KB `Splitter`
  ring, a `Multiply` and a `Mixer` where a `duck=True` flag would spend
  nothing; that is a Tier 3 argument for the flag, not a trait the palette
  cannot reach, and Phase 1 should treat it as one.
- **N-GATE-5 — look-ahead already exists** (`lookahead_ms`, capped at 50 ms,
  `audioif_dynamics.h:53`) and needs nothing. Pre-ramping (S2) is **not**
  asked for in Phase 0: no trait in this set requires it, and it would be a
  new claim rather than a sourced one. Recorded here so a later run does not
  mistake its absence for an oversight.
