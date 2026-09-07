# Effects Dossier — `Vibrato` (Boss VB-2)

**Class:** `lib/audioeffects/modulation.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Modulation, roadmap Phase 3
**Standout:** Boss VB-2, proposed in vision §4.2 — **confirmed as the right
referent**, with the argument and the alternatives in §2.
**Grade:** circuit — the factory service schematic read directly as a drawing
(a low-resolution scan; App. A states what that does and does not resolve),
plus the manufacturer's own published specifications.
**Portability tier:** needs audioif-own nodes (`audioecho.FeedbackDelay`)
**Status:** seed (Phase 0)

## 1. The circuit, in one paragraph

Input through 10k/0.022 into a 2SC732 follower, then half an NJM4558DD as a
gain stage and an RC ladder (10k/0.01, 10k/47p) into the **MN3207**, a
1024-stage low-voltage bucket brigade (S1; S3 fn.1), clocked by an **MN3102**
two-phase driver (S1). What pulls the MN3102's oscillator starts at the LFO:
half a TL022CP oscillating around a twin-T of two 1 MΩ and two 0.047 µF,
tuned by the 250 kΩ **RATE** control and amplitude-limited by a diode — a
smooth, sine-family waveform, not the Small Clone's integrator/comparator
triangle (§8.4 records the confidence). That LFO passes the 50 kΩ **DEPTH**
pot, an emitter follower, and a **BA662A transconductance amplifier used as a
VCA** whose control comes from an envelope the 250 kΩ **RISE TIME** control
charges. So the footswitch does not switch the audio: it ramps the modulation
depth up from zero over 150 ms to 5 s (S2), and the **MODE** switch decides
whether that ramp latches, follows the switch while held, or is disabled —
Boss's manual says the pedal switch "does not affect the Normal/Effect
function and thereby FET switching system is not adopted" (S2). Because the
LFO moves the **clock**, the delay — N/(2·f_clk), S3 §2.1 — is its reciprocal;
at the quoted 4 ms that clock is 128 kHz (App. B). The BBD output runs two
transistor Sallen–Key sections, three poles (10k/10k/10k with 0.0027, 0.0047,
220p) then two more (10k/10k with 0.0039, 47p, 150p) — exactly the
"third-order … followed by a second-order 'corner correction'" pair S3 §2.2
names as the BBD standard, with the 10 kΩ resistors it says "the vast majority
of BBD systems" use — into the second half of the 4558 and out through
1k/1 µF. **There is no dry path in the effect:** the direct signal and the
effect output arrive on separate terminals of the bypass switch and one or the
other is routed to the jack; the panel carries no mix and no level, and the
maker quotes the frequency range as "40 Hz ~ 17 kHz (−3 dB, Vibrato)" (S1, S2).

## 2. Sources and license calls

Each was reached this run. **What each gave, and its licence text as read, is
in App. A and App. E** — nothing here comes from memory.

| Source | Licence call |
|---|---|
| **S1** Boss VB-2 factory service schematic … (App. S1) | "for hobby, historical curiosity … (App. S1) |
| **S2** Boss/Roland VB-2 **Owner's Manual** ([PDF at … (App. S2) | Roland's own document … (App. S2) |
| **S3** [Raffel & Smith, *Practical Modeling of Bucket-Brigade Device … (App. S3) | author-self-archived … (App. S3) |
| **S4** [ElectroSmash, *Boss CE-2 … (App. S4) | "Some Rights Reserved… free to copy, share … (App. S4) |
| **S5** Panasonic **MN3207 data sheet** … (App. S5) | Panasonic's own sheet (page footer "Panasonic … (App. S5) |

### The standout, argued

**Not reached:** `diystompboxes.com` VB-2 threads (403, re-confirmed);
`freestompboxes.org` (probed this run — HTTP 403, not merely unfetched); any
bench measurement of a VB-2, and none is on the bench (vision §2.3). The
MN3207 data sheet, recorded in the first draft as quoted-only, **was read**
this run and is now S5.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

Measurements are numbered M1…M7 and specified in App. G. Every row states the
conditions it is measured under; the arithmetic behind the numbers is App. B,
App. C and App. H.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| T1 | **No dry signal reaches the output when engaged.** A swept sine through the engaged class at Depth 0, 0.5 and 1.0 shows no comb: the magnitude response's peak-to-peak ripple inside any 2 kHz window above 200 Hz stays under 1 dB, and no periodic ripple appears at the 1/d spacing a dry+wet sum would make (250 Hz at the default 4 ms). A dry component only 25 dB below the wet already makes 1 dB of ripple — (1+a)/(1−a) = 1.122 at a = 0.058 — so the test resolves leakage far below audibility (App. H). | S2, read this run at `cdn.roland.com`: the … (App. T1) | high | Any periodic ripple over 1 dB peak-to-peak at 1/d spacing, at any Depth | M1 |
| T2 | **The class's default mean delay is the maker's published 4 ms, and the number it reports is the number it delivers.** At Depth 0 the impulse arrives 192 ± 1 samples after the dry reference at 48 kHz and 176 ± 1 at 44.1 kHz, equal to the reported `latency_samples` at each rate. | S2, read this run: "Delay Time … 4 ms (Depth)" | medium — the … (App. T2) | An arrival more than 1 sample from the reported `latency_samples` at either rate; or a default mean outside 2–8 ms, the wide window being what survives the "(Depth)" ambiguity and the part of this trait no source can narrow | M2 |
| T3 | **LFO rate spans 2 Hz to 15 Hz end to end**: at the Rate macro's two extremes the delay trajectory's fundamental is 2 Hz and 15 Hz, and the span between them is at least 6:1 (the circuit's is 7.5:1). | S2, read this run: "LFO Rate 2 Hz ~ 15 Hz". … (App. T3) | high | Measured endpoints outside 1.8–16 Hz, or a span under 6:1 | M3 |
| T4 | **The LFO is smooth, not a triangle.** On the `Published defaults` patch (Rate 5 Hz, Depth 0.5 = ±30 cents, clock index m ≈ 0.14) the delay trajectory's third harmonic is at least 25 dB below its fundamental; a symmetric triangle's third is 19.1 dB down (1/9), so the two separate by 6 dB. **Stated at that operating point and not at every one:** the clock law contributes its own third harmonic at ≈ m²/4 and crosses −25 dB at m ≈ 0.47, above which a perfectly smooth LFO already fails the test (App. H). | S1, read this run at native resolution: an … (App. T4) | medium — a … (App. T4) | At that operating point: straight ramps and corners in the trajectory, or a third harmonic within 22 dB of the fundamental | M4 |
| T5 | **Engagement is a ramp, not a switch.** On a held 1 kHz sine at −12 dBFS the depth envelope's 10–90 % rise equals the Rise setting within ±20 % at both extremes (0.15 s and 5 s), and no 10 ms window's RMS differs from its neighbour by more than 0.5 dB anywhere across the engagement: the audio path is never switched, only the modulation depth moves. | S2, read this run: RISE TIME "adjust the time … (App. T5) | high | A 10–90 % rise more than 20 % from the setting at either extreme, or any 10 ms window whose RMS steps more than 0.5 dB across engagement | M5 |
| T6 | **The wet path is band-limited 40 Hz to 17 kHz at −3 dB** — a *bright* BBD path, unlike the Chorus standout's ~3 kHz corner, because the clock is an order faster. Measured at Depth 0, **48 kHz, with the Delay macro at a whole number of samples** (the default 4.00 ms is exactly 192), the −3 dB points relative to the 1 kHz level are 40 Hz and 17 kHz. | S2, read this run: "Frequency Range 40 Hz ~ … (App. T6) | high | −3 dB points outside 30–60 Hz or 14–20 kHz under those conditions | M6 |
| T7 | **The clock is modulated, not the delay.** The delay trajectory carries a **second harmonic at m/2 of its fundamental, in quadrature with it** — the signature of d(t) = d₀/(1 + m·s(t)) rather than d₀ + A·s(t), which has no second harmonic at all. −23.1 dB at the `Published defaults` patch (m ≈ 0.14) and −10.3 dB at `Deep slow` (m ≈ 0.56), both computed this run (App. H). This is the trait §5's node ask exists to reach. | S1: the modulation chain runs LFO → DEPTH → … (App. T7) | high for the … (App. T7) | No second harmonic above the trajectory's noise floor at any Depth (an additive-sine law), or one more than 6 dB from m/2 at the m the same run measures, or one in phase rather than quadrature with the fundamental | M7 |

Characters: none — one standout.

### Tier 3 — cost and latency

Budget as a fraction of one stereo block's deadline: **P4 0.08, S3 0.15**.
Lean patch expected: **no** — one interpolated line, one one-pole each way.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**One node.** `audioecho.FeedbackDelay` with `feedback = 0.0` and `mix = 2.0`
— the kernel's `dry = min(2 − mix, 1)`, `wet = min(mix, 1)`
(`audioif_feedback_delay.c:201-202`) makes mix 2 wet-alone, which is T1
exactly and needs no mixer. `delay_ms = 4.0`; the line is read **per sample
with linear interpolation between two neighbours** (`:227-228`) under a
**per-sample** oscillator (`:209-213`), which is what makes a pitch vibrato
rather than a stepped one. Probed this run: an impulse at `delay_ms = 4.0`
lands at sample 192, and at `4.005` it splits 15200/4800 across 192/193 — the
fractional read is real (App. D).

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**Ask N-shape — a modulation shape table on `audioecho.FeedbackDelay`.** The
same ask `Chorus` §5 states; it serves both classes and should be filed once.

- **Trait it unblocks:** **T7** (and `Chorus` T2 and T6). *Correction to the …  *(argument in full: App. R)*
- **What the palette does instead:** the kernel adds …  *(argument in full: App. R)*
- **Refutation record.** (1) *Step `delay_ms` from Python*: a config write …  *(argument in full: App. R)*
- **The ask, additive:** an optional `wow_shape` — a one-period table (int16, …  *(argument in full: App. R)*
- **Measurement that shows the gap:** T7's trajectory FFT against a …  *(argument in full: App. R)*

No second ask. The rise-time ramp is *not* an ask: the palette can do it at
block rate, and whether that is clean is a measurement, not an assumption
(§8.2).

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | `Rate` | UNIPOLAR | 2–15 Hz, log | the RATE knob (T3) |
| 1 | `Depth` | UNIPOLAR | 0 → ±60 cents peak | the DEPTH knob |
| 2 | `Rise` | UNIPOLAR | 0.15–5 s | the RISE TIME knob (T5) |
| 3 | `Engage` | TOGGLE | off/on | the pedal switch; on ramps the depth up, off ramps it down |
| 4 | `Delay` | UNIPOLAR | 1–12 ms mean | the MN3102's clock trim (T2) |
| 5 | `Tone` | UNIPOLAR | 2–18 kHz wet −3 dB corner, Nyquist-clamped; Python pre-warps the node's nominal `damping_hz` (§4 — 17 kHz wants nominal 12.30 kHz at 48 kHz, 18 kHz wants 12.63 kHz) | the reconstruction filter (T6) |
| 6 | `Body` | UNIPOLAR | 20–200 Hz wet high-pass | the low end of T6's stated band |
| 7 | `Level` | UNIPOLAR | −12…+6 dB | nothing — output trim |

Characters: none. **MODE is not a macro:** BYPASS is the host's own bypass,
and LATCH versus UNLATCH is a gesture a host makes with `Engage` (latch = set
it and leave it; unlatch = hold it), not a state the effect stores. Recorded
here so the rebuild does not invent a mode enum.

`capabilities`: **`()`** — the VB-2's rate is a free-running oscillator and no
part of the circuit references a beat, so the class does not read the
transport.

Patches: `Ramp in slow` (rise 3 s, rate 5 Hz, depth 0.5) · `Instant on` (rise
0.15 s, rate 6 Hz, depth 0.6) · `Shallow fast` (rate 12 Hz, depth 0.25) ·
`Deep slow` (rate 2.5 Hz, depth 1.0) · `Short line bright` (delay 2 ms, tone
18 kHz) · `Long line` (delay 10 ms, tone 8 kHz) · `Published defaults` (4 ms,
rate 5 Hz, depth 0.5, rise 1 s, tone 17 kHz, body 40 Hz — S2's figures).

## 7. Defects in the current class the rebuild must not repeat

- **It is not a vibrato.** The class passes `mix=1.0` to
  `audiodelays.PitchShift` (`modulation.py:136`), and that kernel computes
  `dry = min(2 − mix, 1)` and `wet = min(mix, 1)` (`audioif_pitchshift.c:39-41`),
  so at mix 1.0 both are **1.0**: the shipped `Vibrato` sums the dry with the
  shifted signal at equal level. That is a chorus. It also propagates —
  `Rotary` builds on this class (`modulation.py:155`).
- **Wrong mechanism.** `audiodelays.PitchShift` (`:135`) is a granular window
  resampler with an overlap crossfade (`audioif_pitchshift.c:26-38`); the
  circuit is a delay line whose read rate moves. The two do not sound alike on
  transients.
- **Undeclared latency.** `window=1024` (`:136`) is in **bytes**:
  `window // 2 // channel_count` (CPython shim `audiodelays.py:156`) is 256
  stereo frames, 5.33 ms at 48 kHz. The class sets no `LATENCY_SAMPLES`, so
  `_core.py:245-248` reports 0.
- **Block-rate pitch control.** `semitones=self.lfo` (`:135`) with
  `synthio.LFO` (`:134`) updates about 187 times a second on a *pitch*
  parameter.
- **No surface, no engagement behaviour.** `MACRO_LABELS = ()` (`:130`),
  `PATCHES = {0: ("Default", ())}` (`:132`); nothing corresponds to Rise Time
  or to the ramp, which is half of what the standout is.
- **`reset()`/`deinit()` reach one node** (`_core.py:366-374`, `:376-384`).

## 8. Open questions

1. **What "Delay Time … 4 ms (Depth)" means** (S2). Read as the mean delay,
   T2 follows; read as the swing at full depth, the mean is unstated and T2
   must be re-fixed. No second source was found and no unit is on the bench.
   *Settles:* the implementation session states which reading it took; the
   seed takes the mean-delay reading and App. B says why.
2. **Whether the block-rate rise ramp is audible.** `wow_depth_ms` is a config
   write; the ramp steps once per 256-frame block. *Settles:* a class-gate
   measurement of the delay trajectory during a 150 ms rise. If it steps
   audibly, the ask is a slew on `wow_depth_ms` — filed then, with the
   measurement, not now.
3. **What a pure-wet class reports as `latency_samples`** — the mean delay
   (this seed's answer, Tier 3) or zero (what `Chorus` reports on the same
   node, because it has a dry path). The two classes must not answer
   differently by accident. *Settles:* Phase 3, once, for every wet-only
   class; it changes `Rack`'s sums and the Phase 6 pedalboard latency table.
4. **The LFO waveform.** T4 rests on reading a twin-T network off a scanned
   drawing. *Settles:* a second independent VB-2 schematic, or a SPICE deck of
   the oscillator; either would raise T4 from medium. The trait as stated is
   falsifiable without it.
5. **A shipped patch sits outside T4's range.** `Deep slow` (2.5 Hz, full
   depth) needs m ≈ 0.56 for ±60 cents, and there the clock law's *own* third
   harmonic is −20.6 dB (App. H) — past T4's bar with a perfectly smooth LFO.
   Either the patch's depth comes down or T4 is confined to the low-index
   patches and the surface says so. *Settles:* the implementation session, when
   the Depth law is written — not a red measurement at the class gate.
6. **Depth in cents is not linear in m at low rates.** App. B's first-order
   Δf/f = 2π·f·A holds only while m is small: at 2 Hz, m = 0.70 the exact peak
   deviation is 186 cents where first order says 60 (App. H), and up-swing and
   down-swing stop being equal. *Settles:* the class solves for m exactly, and
   the cents ranges are re-derived when it does.

---


## Appendix

### A. What each source gave

**S1 — the factory service schematic.** The PDF carries no extractable text
(`pypdf` returns an empty string for its single page). **Audit correction:**
the first draft said it was "rendered at 400 dpi"; what the page actually
contains is eight embedded bitmaps of 780×82 pixels each — 780×656 for the
whole drawing — so no render adds information past 780 px across the sheet.
The strips were extracted and assembled and the drawing read at that native
resolution, upscaled. Everything below was legible at it. Read from it: IC1 NJM4558DD,
**IC2 MN3207**, **IC3 MN3102**, **IC4 BA662A**, IC5 TL022CP, IC6 BA634;
Q1–Q4 2SC732TM-GR, Q5–Q9 and Q11 2SC945-P, Q10 2SA733-P; D1–D7 1SS133, D8
RD5.1EB3, D9 RD11FB3. Controls: **RATE VR1 250 kC**, **DEPTH VR2 50 kB**,
**RISE TIME VR3 250 kA**, plus internal trims VR4 100 kB and VR5 10 kB.
Signal path: R2 10k/C1 .022 → Q1 → IC1 (R15 15k, R16 15k, R13 47k, R14 47k,
C9 33p) → R17 10k/C10 .01, R18 10k/C12 47p → IC2; IC2 out → R28 10k/C18
.0027, R27 10k/C17 .0047, R26 10k/C16 220p → Q4 → R21 10k/C14 .0039, R20
10k/C15 47p, C13 150p → Q3 → IC1 (R11 47k, R10 47k, C6 33p) → R8 1k/C5 1/50
→ the switch. The direct path reaches the same switch through R5 1k/C4 1/50
with an R9 10k/R6 100k trim. LFO: an RC network around IC5 — **R47 1 M and
R48 1 M in series, and directly above them C24 0.047 and C25 0.047 in series**,
the two chains sharing their end nodes (IC5 pin 2 on the left, IC5 pin 1 on the
right); the capacitor junction taps up to a rail that runs through R53 1 M to
the R30 6k8 / R51 33k node, and the resistor junction taps down. R54 4k7,
R45 100k, R46 470k, R50 220k, D4 on the second IC5 half. Read as a twin-T of
1 M and 0.047 µF, that network's centre is 1/(2π·1 M·0.047 µF) = **3.39 Hz**,
inside S2's published 2–15 Hz span — an arithmetic check on the reading, not a
second source. Then R52 33k → Q8 → the
DEPTH pot → R42 330k → IC4 (BA662A) with R44 1k, R43 1k, R41 100k → R37 470k,
R55 33k → Q9 → the MN3102's oscillator node (C20 47p, R34 33k, R33 2k7, VR4
100k, R36 1k8, R35 8k2, D3, C21 .047). The printed service note reads
"RATE / MODE: LATCH   DEPTH: Midpoint / 1. Check the sweep rate at the
extremities of RATE setting: 2 cycles at FCCW; 15 cycles at FCW."

*Audit corrections to this reading, 2026-09-06.* (a) **R14 and R11 are 47k,
not the 4k7 the first draft recorded.** Both read "47k" on the drawing, the
same glyphs as the R13 and R10 beside them, and the sheet writes sub-10 k
values with a decimal point (R54 "4.7k", R39 and R40 "4.7k"), so a plain "47k"
is 47 kΩ. Neither value carries a trait; the seed simply had them wrong.
(b) The first draft described the series capacitors above R47/R48 as
unlabelled and then named C24/C25 separately, as if they were two different
pairs — they are one pair, their designators legible at native resolution, so
all four twin-T parts are read and the scan's resolution is not what holds T4
at medium.

**S2 — the manufacturer's manual.** Specification page, read verbatim:
Controls "RATE, DEPTH, RISE TIME, MODE (LATCH↔BYPASS↔UNLATCH)"; Others
"Vibrato ON/OFF Switch, Indicator"; Maximum Input Level −5 dBm (at 1 kHz);
Output Load Impedance 10 kΩ or more; **Frequency Range 40 Hz ~ 17 kHz (−3 dB,
Vibrato)**; **Delay Time 4 ms (Depth)**; **LFO Rate 2 Hz ~ 15 Hz**; **Rise
Time 150 ms ~ 5 s**; S/N Ratio −92 dB (IHF-A); "Printed in Japan '82 Mar."
Panel text: MODE selects LATCH ("turn a vibrato effect on and off by pressing
the Pedal Switch"), BYPASS ("A vibrato is not obtainable even if you press the
Pedal Switch") and UNLATCH ("obtain a vibrato effect only while you are
pressing the Pedal Switch"); RISE TIME "adjust the time needed for a vibrato
to reach its maximum … clockwise, the rise time will become longer"; PEDAL
SWITCH "does not affect the Normal/Effect function and thereby FET switching
system is not adopted."

**S3 — the DAFx paper.** "For any BBD, the total time delay is given by Delay
Time (s) = N/(2·f_cp)"; footnote 1 names "MN3007, MN3207, MN3005, and MN3205,
which are high and low-voltage variants of 1024 and 4096 stage BBDs"; §2.2
"A common implementation is to use a third-order filter for anti-aliasing and
a third-order filter followed by a second-order 'corner correction' filter for
reconstruction", "The majority of BBD-based circuits use Sallen-Key low-pass
filters" together with "A typical, transistor-based Sallen-Key filter …"
(**the audit's correction here is itself withdrawn, 2026-09-06,
trait-critic pass:** the audit struck the quotation "the vast majority of BBD
circuits use transistor-based Sallen-Key circuits" as absent from the paper.
It is present, verbatim, as **footnote 2** — "Interestingly, the vast majority
of BBD circuits use transistor-based Sallen-Key circuits, but op-amp based
filters are not uncommon" — re-fetched and re-searched this run. The paper has
*two* "vast majority" sentences, footnote 2's and the body's about R = 10 kOhm,
and the audit conflated them), and "the vast majority
of BBD systems use R = 10 kOhm for all of the resistances in all three
filters" — which the VB-2 does
exactly; §4.4 THD = 1.01^(N/1024) − 1, "not a clipping distortion", "less
important for choruses, flangers, and vibratos … typically left out"; §4.2
insertion gain 0…2 dB at LF falling to −4…−6 dB at Nyquist.

### B. The clock, the delay, and the depth

With N = 1024 and delay = N/(2·f_clk) (S3), a 4 ms mean delay puts the MN3102's
clock at **128.0 kHz** — inside the 10–200 kHz clock range the MN3207's own
data sheet specifies (S5) and comfortably above twice the 17 kHz the manufacturer specifies as the
passband (S2), which is why this circuit is bright where the Small Clone,
clocked near 58 kHz, is dark.

**The "(Depth)" ambiguity.** S2 lists "Delay Time … 4 ms (Depth)" with no
further gloss. Two readings: (a) 4 ms is the mean delay and the qualifier
notes that it *varies* with Depth — the reading this seed takes, and the one
consistent with 128 kHz sitting mid-range for the part; (b) 4 ms is the
peak-to-peak *swing* at full depth, which would imply a mean well above 4 ms
and a clock well below 128 kHz. No second source was reached. T2 states
reading (a) at medium confidence with a 2–8 ms disconfirmation window that
does not depend on which is right.

**Depth in cents.** For a delay d(t), the pitch offset is Δf/f = −d′(t). With a
sinusoidal delay swing of amplitude A at LFO frequency f, the peak fractional
deviation is 2π·f·A:

| swing A | LFO f | peak deviation |
|---|---|---|
| 0.4 ms | 5 Hz | 1.26 % = **21.6 cents** |
| 0.4 ms | 15 Hz | 3.77 % = **64.1 cents** |
| 0.1 ms | 5 Hz | 0.31 % = **5.4 cents** |

Note what this means for the surface: **depth in milliseconds is not depth in
cents**, because the deviation scales with the rate. The `Depth` macro is
specified in cents (§6) and the class converts, so that turning Rate up does
not deepen the vibrato — a departure from the circuit, stated here rather than
discovered later.

### C. Why the clock law has a measurable signature

The LFO moves the clock, so d(t) = d₀/(1 + m·s(t)) rather than d₀ + A·s(t).
For sinusoidal s, 1/(1 + m·s) = (1 + m²/2) − m·s − (m²/2)·cos 2θ − …: the
trajectory carries a second harmonic of relative amplitude m/2, **in
quadrature** with the fundamental. That quadrature term is why §5's cascade
workaround cannot reach the trait on today's node, and it is why the palette's
additive sine is a different effect and not merely a different depth. T4 is
stated on the *third* harmonic instead, because that is what separates a
smooth LFO from a triangle regardless of the clock law, and the two questions
should not be entangled in one measurement.

### D. Probes run this run

On the repository's CPython build of audioif
(`audiocomponents/.venv/bin/python`):

- `audioecho.FeedbackDelay(max_delay_ms=30, delay_ms=4.0, feedback=0, mix=2.0)`
  — impulse arrives at sample 192 (exactly 4.000 ms at 48 kHz); at
  `delay_ms=4.005` it splits 15200/4800 across samples 192/193, confirming the
  fractional interpolated read of `audioif_feedback_delay.c:227-228`.
- `_audioif.FEEDBACK_DELAY_FRAMES` is **256**, which is the block the
  rise-ramp steps on (§4).
- `audiodelays.Chorus` with `voices=1/2/3` at `delay_ms=20`: arrivals at
  {0}, {0, 959}, {0, 479, 958} — integer taps, and no delayed voice at all
  with one voice (`audioif_chorus.c:15-16`). Recorded here because it is the
  measurement that refutes the stock-tier alternative for both modulation
  classes.

### E. Licence notices as read

S1's host states: "All manuals are collected from the World Wide Web and
provided for hobby, historical curiosity, study and research, and may not be
used for any commercial purposes." S2 is Roland's own PDF served from
`cdn.roland.com`; **no rights notice is printed anywhere in it** (cover,
specification page and back checked this run — the back page carries only
"BOSS Products of Roland", "Printed in Japan '82 Mar. C-3" and the UPC), so
"© Roland" is an attribution of authorship, not a notice read, and its
specification and panel text are read as facts about the product. S3 carries no rights statement anywhere in the PDF —
author-self-archived, read under the vision §5 "unverified" treatment, as a
paper and not for code (it offers none). S4's mirror page footer reads "Some
Rights Reserved, you are free to copy, share, remix and use all material.
Trademarks, brand names and logos are the property of their respective
owners." S5 is Panasonic's own MN3207 data sheet page (the sheet's own
footer reads "Panasonic  −80−"); **no rights notice is printed on it either**,
and no terms could be read from the host — `experimentalistsanonymous.com`
serves the PDF but its site root returns a ModSecurity "Not Acceptable" block,
so the mirror is **licence unverified, treated as copyleft**, and the sheet is
read the way any data sheet is — for its published figures, never reproduced. Nothing from any source is reproduced here; the
schematic was read as a drawing and its values are facts about a circuit.

*Audit, 2026-09-06.* Every source row above and every URL in this file was
re-fetched independently on 2026-09-06 (curl from this machine). All five
resolved; S1's eight 780×82 strips were re-extracted and re-assembled and the
drawing re-read at native resolution, S2's and S5's scanned pages re-rendered
and re-read, S3's text re-searched for every sentence quoted from it. The
Roland manual served by `cdn.roland.com` and the copy on `synthxl.com` are
byte-identical (md5 `e409fe20…`), as the S2 row claims. Corrections applied by
that pass: **S2's and S5's licence calls** (neither document prints a rights
notice, so a "©" call was replaced by what was actually read), T4's confidence
rationale, and App. A's R14/R11 values and LFO description. The
not-reached claims were re-probed and stand: `diystompboxes.com` topic 65989
and `freestompboxes.org` t=4212 both return HTTP 403.

### F. What was looked for and not found

A second independent VB-2 schematic — both forums that host one return 403,
probed again this run. A DAFx/AES paper on this specific circuit — none found;
S3 is the family paper. A bench measurement of a VB-2's LFO waveform, clock or
delay — none reached, none on the bench. A SPICE deck of the oscillator or the
MN3102 injection node — not attempted this run; named in §8.4 as what would
raise T4 from medium.

*Found on audit, and struck from this list:* the Panasonic MN3207 data sheet.
The first draft recorded it as "fetched but no extractable text, so quoted
only". It has no text layer, but its five pages are scanned bitmaps that
extract cleanly as images; read that way it gives the part's own figures
directly, and it is now S5. The lesson is the general one — a PDF with an
empty text layer is an image-extraction job, not an unreadable document.

### G. The measurements, specified

- **M1 (T1).** Swept sine at 48 kHz through the class at Depth 0.5 and 1.0;
  magnitude response, tested for notch spacing near 1/delay. *Planted fault:*
  set `mix` to 1.0 (dry + wet) — a comb must appear and M1 must go red.
- **M2 (T2).** Impulse at Depth 0; arrival index at 48 and 44.1 kHz.
  *Planted fault:* change `delay_ms` without updating `latency_samples`.
- **M3 (T3).** LFO period from the delay trajectory (impulse train) at both
  Rate extremes. *Planted fault:* halve `wow_hz`.
- **M4 (T4).** Delay trajectory over ≥8 LFO periods from an impulse train, **on
  the `Published defaults` patch**; FFT; third-harmonic level relative to the
  fundamental, with the implied m reported alongside so a reader can see the
  clock law's own contribution (≈ m²/4, App. H). *Planted fault:* drive the node
  from a triangle table — the third harmonic must rise to ≈19 dB down.
  *Control that must pass:* the same render at m ≈ 0.14 with the smooth table,
  which must come back at or below −25 dB; a suite of only faults proves only
  that the probe always fires.
- **M7 (T7).** The same trajectory FFT as M4, reporting the **second** harmonic's
  magnitude *and phase* relative to the fundamental, and the m implied.
  *Planted fault:* run the node on its internal additive sine (no `wow_shape`)
  — the second harmonic must vanish into the noise floor. *Control that must
  pass:* the shape table at Depth 0, where fundamental and second harmonic are
  both absent and the measurement must report "no modulation", not "agreement".
- **M5 (T5).** Held 1 kHz sine, engage at t = 0; track the instantaneous-
  frequency deviation envelope, fit 10–90 % rise at both Rise extremes, and
  check output RMS continuity across the engagement block. *Planted fault:*
  apply the depth as a step instead of a ramp.
- **M6 (T6).** Swept sine at 48 kHz, Depth 0, **the Delay macro at a whole
  number of samples and the fraction reported with the result**; −3 dB points
  relative to 1 kHz. Asserted at 48 kHz only (Tier 1 note). *Planted fault:*
  remove `cut_hz` — the 40 Hz point must vanish. *Second planted fault, for the
  top end:* offset the delay by half a sample — 17 kHz must fall about 7 dB and
  M6 must go red, which is what proves the measurement sees the interpolator
  rather than reading through it.

Every measurement takes the sample rate as a parameter and records it in what
it exports (roadmap Phase 0, kit spec).

### H. The trait critic's arithmetic and probes, 2026-09-06

Computed or measured **in this run** — the probes on the repository's CPython
build of audioif (`audiocomponents/.venv/bin/python`), the arithmetic in plain
CPython. No source supplies these numbers; they constrain how the traits above
may be *measured*, not what the circuit does.

**1. The node's interpolated read is a low-pass in its own right.**
`audioif_feedback_delay.c:227-228` interpolates linearly between two
neighbours, so its magnitude at a half-sample fraction is cos(π·f/f_s).
Measured wet-only (`mix=2.0`, `feedback=0`, no damping), referred to 1 kHz:

| f_s | delay | fraction | 10 kHz | 17 kHz |
|---|---|---|---|---|
| 48 000 | 4.000 ms (192.000 samples) | 0.000 | 0.00 dB | 0.00 dB |
| 48 000 | 4.01042 ms (192.5) | 0.500 | −1.99 dB (theory −2.01) | −7.07 dB (theory −7.09) |
| 44 100 | **4.000 ms (176.400)** | 0.400 | −2.27 dB | **−7.97 dB** |
| 44 100 | 4.00227 ms (176.5) | 0.500 | −2.40 dB (theory −2.42) | −9.05 dB (theory −9.07) |
| 22 050 | 8.77551 ms (193.5) | 0.500 | −16.65 dB (theory −16.74) | above Nyquist |

Measurement and theory agree within 0.1 dB. The 44.1 kHz row at the published
4 ms is why T6 is a 48 kHz trait. **Control that passes:** the fraction-0 row,
where the loss is exactly zero. The first attempt at this probe set `delay_ms`
as an *attribute*, which the CPython shim ignores — options go through the
constructor or `set()` — and every row came back +0.00 dB: absence reading as
agreement, caught only by the impulse control below.

**2. The impulse control** (App. D re-run): impulse at index 10, 48 kHz, mono.
`mix=2.0`, `delay_ms=4.0` → one arrival at index 202; `delay_ms=4.005` →
15200/4800 across 202/203; `mix=1.0` → arrivals at 10 *and* 202. This is what
proves the node was in the path at all.

**3. What the clock law puts in the trajectory.** FFT of 1/(1 + m·sin θ),
4096 points:

| m | 2nd/1st | = m/2 | 3rd/1st | 3rd in dB |
|---|---|---|---|---|
| 0.10 | 0.0501 | 0.0500 | 0.0025 | −52.0 |
| **0.14** | 0.0703 | 0.0700 | 0.0050 | **−46.1** |
| 0.28 | 0.1429 | 0.1400 | 0.0204 | −33.8 |
| 0.35 | 0.1807 | 0.1750 | 0.0327 | −29.7 |
| 0.474 | 0.2521 | 0.2370 | 0.0635 | −23.9 |
| **0.56** | 0.3063 | 0.2800 | 0.0938 | **−20.6** |
| 0.70 | 0.4084 | 0.3500 | 0.1668 | −15.6 |

So second/first ≈ m/2 (T7) and third/first ≈ m²/4. A delay-linear **triangle**
gives second/first = 0 and third/first = 1/9 = −19.08 dB — which is the number
T4 separates against, and also why T4 must name its operating point: the third
harmonic crosses −25 dB at m ≈ 0.47 on the clock law alone.

**4. The index each patch needs**, from Δf/f = 2π·f·d₀·m at d₀ = 4 ms, with the
harmonics from the m²/4 and m/2 approximations (table 3 carries the exact FFT
values, which run 1–2 dB higher on the third at large m):

| patch | rate | depth | m | 3rd/1st (≈m²/4) | 2nd/1st (≈m/2) |
|---|---|---|---|---|---|
| `Published defaults` | 5 Hz | ±30 cents | 0.139 | −46.3 dB | −23.1 dB |
| `Shallow fast` | 12 Hz | ±15 cents | 0.029 | −73.6 dB | −36.8 dB |
| `Deep slow` | 2.5 Hz | ±60 cents | 0.561 | **−22.1 dB** (exact −20.6) | −11.0 dB |
| (macro floor) | 2 Hz | ±60 cents | 0.702 | **−18.2 dB** (exact −15.6) | −9.1 dB |

The last two rows are §8.5: T4's bar cannot be met there by any LFO shape.

**5. Where the first-order cents formula stops.** Exact peak |d′| for
d₀/(1 + m·sin θ) against 2π·f·d₀·m:

| f | m | exact | first order |
|---|---|---|---|
| 5 Hz | 0.139 | 31.1 cents | 30.0 cents |
| 15 Hz | 0.093 | 60.9 cents | 59.9 cents |
| 2.5 Hz | 0.561 | 116.7 cents | 60.0 cents |
| 2 Hz | 0.700 | 186.1 cents | 59.9 cents |

App. B's table is first-order and is honest only in the top two rows; §8.6.

**6. T1's ripple threshold.** A dry component a summed with a unit wet gives
peak-to-peak ripple 20·log₁₀((1+a)/(1−a)). 1 dB of ripple needs a = 0.058, i.e.
a dry leak 24.8 dB below the wet — the number quoted in T1.

### I. Palette verification, 2026-09-06

Run by the unit's palette verifier against the CPython build of audioif in
`audiocomponents/.venv` (`audioecho`, `audiodelays`, `audiocore`); sources
read with `grep -n` under `audioif/src/shared/` and `audioif/src/audioecho/`.
Every number below came out of a render, not out of arithmetic about the
node. The shared probes and the fuller tables are in `Chorus.md` App. J; what
follows is what this class turns on.

**`mix = 2.0` is wet alone, and the read is fractional.** One full-scale
stereo impulse, `delay_ms = 4.0`, `feedback = 0`, 48 kHz: a single arrival at
**frame 192**, full amplitude, nothing at frame 0. At `delay_ms = 4.005` it
splits **15200 at 192 and 4800 at 193** — the linear interpolation of
`audioif_feedback_delay.c:227-228`, and the seed's App. D reading confirmed
independently. `mix = 0` returned the source at frame 0 and nothing after it.

**The reconstruction filters.** Wet path against an unfiltered reference node
at the same delay, steady sines, 24000 frames after a 4096-frame skip,
48 kHz, `delay_ms = 4.0` (192 samples exactly, so the interpolator
contributes nothing):

| | 100 Hz | 1 kHz | 5 kHz | 10 kHz | 14 kHz | 17 kHz | 20 kHz | 23 kHz |
|---|---|---|---|---|---|---|---|---|
| `damping_hz = 17000` | −0.00 | −0.01 | −0.24 | −0.80 | −1.28 | **−1.57** | −1.78 | −1.88 |
| `damping_hz = 12300` | — | −0.02 | — | −1.65 | — | **−3.02** | −3.35 | — |

and `cut_hz = 40`: −7.15 dB at 20 Hz, −4.45 at 30, **−3.06 at 40**, −1.60 at
60, −0.67 at 100, −0.03 at 1 kHz. So the low corner is honest at its nominal
and the high one is not. From the closed form of `y += a(x − y)` with
`a = 1 − exp(−2π·f/fs)` (`:29-38`), at 48 kHz the nominal that puts −3 dB at
17 kHz is 12.30 kHz, and the largest nominal that reaches −3 dB anywhere
below Nyquist is **13.46 kHz**.

**The primed cascade (the T7 refutation).** `set()` reaches only
`audioif_feedback_delay_configure` (`audioecho/FeedbackDelay.c:32-58`,
`:135-141`), which writes config; `state_init` runs at construction and at
`reset_buffer` (`:200-211`) alone. Holding a node at `wow_hz = 0` therefore
freezes `wow_sine`/`wow_cosine` (`audioif_feedback_delay.c:209-210` multiply
by a zero `wow_step`) and advances its phase relative to a sibling by one
block — 5.33 ms, 256 frames (`audioif_feedback_delay.h:39`) — per block held.
Demonstrated on one node: freezing 0, 8, 16 and 24 blocks moved the recovered
trajectory by 0°, 31°, 61° and 92°. Applied to a cascade at d₀ = 8 ms,
m = 0.30, f = 5 Hz, against the law `d₀/(1+m·sin θ)` whose fundamental is
2.40 ms and whose second harmonic is 0.36 ms (−16.5 dB) in quadrature: a
single node measured |A1| 115.8 frames with |A2| at −28.2 dB (the
impulse-centroid probe's floor), and the primed two-node cascade at 5 Hz and
10 Hz measured |A1| 115.8 frames with **|A2| at −14.6 dB, −87.8°**. The
cascade reaches a quadrature second harmonic. It reaches neither a third
harmonic nor a triangle.

**`audiodelays.PitchShift` and `audiodelays.Chorus`, re-confirmed as
unusable here.** PitchShift is the granular window resampler with the overlap
crossfade at `audioif_pitchshift.c:26-38`, dry and wet at `:39-41`; its
window is set in bytes and divided down at
`audioif/src/cpython/audiodelays.py:156`. `audiodelays.Chorus` at
`delay_ms=20`, `mix=1.0`, `max_delay_ms=40`, one impulse: `voices=1` gives a
single arrival at frame 0, the dry, and no delayed voice
(`audioif_chorus.c:15-16`); `voices=2` gives frames 0 and 960; `voices=3`
gives 0, 480 and 959 — whole samples, evenly spaced (`:18`, `:22`), with
`delay_ms` read once per `_process` call
(`audioif/src/cpython/audiodelays.py:75`).

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

**Two Tier 1 notes this class must carry.** *"`mix` at zero is a wire"* — a
pure-wet effect has no mix knob on the standout, so the class's `Depth` at
zero is the wire condition (the delayed signal at a fixed 4 ms, no pitch
motion; byte-identical to the source is therefore **not** achievable and the
honest invariant is that the output is the source delayed by exactly the
reported `latency_samples`, sample-for-sample). *Rate-honest:* **T6 is stated at 48 kHz alone**, and it is the
Tier 2 trait that cannot hold at a lower rate. 17 kHz is above Nyquist at
22.05 kHz and clamps there; at 44.1 kHz it is in band but out of reach, because
the node's interpolated read is itself a low-pass — cos(π·f/f_s) at a
half-sample fraction — and the published 4 ms is 176.4 samples at 44.1 kHz, a
fraction of 0.4 that costs **−7.97 dB at 17 kHz** before any tone filter acts
(measured this run, App. H; the worst case at 48 kHz is −7.07 dB, which the
default's exact 192 samples avoids). Every other Tier 2 trait holds at 44.1 kHz
and 22.05 kHz.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | Licence call |
|---|---|
| **S1** Boss VB-2 factory service schematic ([PDF](https://www.synthxl.com/wp-content/uploads/2020/04/Boss-VB-2-Schematic.pdf) via [SynthXL](https://www.synthxl.com/boss-vb-2/)) — a scan with no extractable text, **read as a drawing**; the whole page is eight 780×82 bitmaps, so 780 px across the sheet is the ceiling on what any render resolves (App. A) | "for hobby, historical curiosity, study and research… not for any commercial purposes" → document, read only (vision §5) |
| **S2** Boss/Roland VB-2 **Owner's Manual** ([PDF at cdn.roland.com](https://cdn.roland.com/assets/media/pdf/VB-2_OM.pdf); SynthXL's mirror is byte-identical) — the **manufacturer's own** specifications and panel text | Roland's own document, served from `cdn.roland.com` (SynthXL's copy md5-identical, checked this run); **no rights notice is printed anywhere in the manual** — read as the manufacturer's published facts, nothing reproduced |
| **S3** [Raffel & Smith, *Practical Modeling of Bucket-Brigade Device Circuits*, DAFx-10, CCRMA](https://colinraffel.com/publications/dafx2010practical.pdf) — the BBD delay law and the BBD filter norms | author-self-archived, **no rights statement anywhere in the PDF** (searched this run) → **licence unverified, treated as copyleft**: read as a paper, no code taken |
| **S4** [ElectroSmash, *Boss CE-2 Analysis*](https://electrosmash.mas-effects.com/boss-ce-2-analysis.html) — the sibling Boss BBD modulation circuit | "Some Rights Reserved… free to copy, share, remix" |
| **S5** Panasonic **MN3207 data sheet**, MN3200 Series p. 80 ([PDF](https://www.experimentalistsanonymous.com/diy/Datasheets/MN3207.pdf)) — "1024-STAGE … BBD", delay 2.56–51.2 ms, clock 10–200 kHz, S/N 73 dB, THD 0.4 %, insertion loss 0 dB typ. **Read this run**, not quoted: no text layer, so its five scanned pages were extracted as images (App. A) | Panasonic's own sheet (page footer "Panasonic −80−"); **no rights notice is printed on it**, and the host states no terms of its own (its site root returns a ModSecurity block) → **licence unverified, treated as copyleft**: read for its published figures, nothing reproduced |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| T1 | **No dry signal reaches the output when engaged.** A swept sine through the engaged class at Depth 0, 0.5 and 1.0 shows no comb: the magnitude response's peak-to-peak ripple inside any 2 kHz window above 200 Hz stays under 1 dB, and no periodic ripple appears at the 1/d spacing a dry+wet sum would make (250 Hz at the default 4 ms). A dry component only 25 dB below the wet already makes 1 dB of ripple — (1+a)/(1−a) = 1.122 at a = 0.058 — so the test resolves leakage far below audibility (App. H). | S2, read this run at `cdn.roland.com`: the control list is "RATE, DEPTH, RISE TIME, MODE" and nothing else, and the range is quoted "40 Hz ~ 17 kHz (−3 dB, **Vibrato**)". S1, read this run: the direct leg (R5 1k/C4) and the effect leg (R8 1k/C5) land on separate terminals of the output switch | high | Any periodic ripple over 1 dB peak-to-peak at 1/d spacing, at any Depth | M1 |
| T2 | **The class's default mean delay is the maker's published 4 ms, and the number it reports is the number it delivers.** At Depth 0 the impulse arrives 192 ± 1 samples after the dry reference at 48 kHz and 176 ± 1 at 44.1 kHz, equal to the reported `latency_samples` at each rate. | S2, read this run: "Delay Time … 4 ms (Depth)" | medium — the "(Depth)" qualifier is ambiguous (App. B), so the *figure* is medium even though the report-matches-delivery half is exact | An arrival more than 1 sample from the reported `latency_samples` at either rate; or a default mean outside 2–8 ms, the wide window being what survives the "(Depth)" ambiguity and the part of this trait no source can narrow | M2 |
| T3 | **LFO rate spans 2 Hz to 15 Hz end to end**: at the Rate macro's two extremes the delay trajectory's fundamental is 2 Hz and 15 Hz, and the span between them is at least 6:1 (the circuit's is 7.5:1). | S2, read this run: "LFO Rate 2 Hz ~ 15 Hz". S1's printed service check, read this run on the drawing: "Check the sweep rate at the extremities of RATE setting: 2 cycles at FCCW; 15 cycles at FCW" — the same two numbers, agreeing with the manual once the check's time base is read as one second, which the drawing does not itself print | high | Measured endpoints outside 1.8–16 Hz, or a span under 6:1 | M3 |
| T4 | **The LFO is smooth, not a triangle.** On the `Published defaults` patch (Rate 5 Hz, Depth 0.5 = ±30 cents, clock index m ≈ 0.14) the delay trajectory's third harmonic is at least 25 dB below its fundamental; a symmetric triangle's third is 19.1 dB down (1/9), so the two separate by 6 dB. **Stated at that operating point and not at every one:** the clock law contributes its own third harmonic at ≈ m²/4 and crosses −25 dB at m ≈ 0.47, above which a perfectly smooth LFO already fails the test (App. H). | S1, read this run at native resolution: an RC/twin-T network around IC5 TL022CP, diode-limited — R53 1 M and the pair C24/C25 0.047 read directly in this pass; App. A's R47/R48 1 M and the D4 limiter are the seed run's reading, not re-walked here | medium — a single-source reading, uncorroborated by a second drawing (both forums that host one return 403; re-probed this run) | At that operating point: straight ramps and corners in the trajectory, or a third harmonic within 22 dB of the fundamental | M4 |
| T5 | **Engagement is a ramp, not a switch.** On a held 1 kHz sine at −12 dBFS the depth envelope's 10–90 % rise equals the Rise setting within ±20 % at both extremes (0.15 s and 5 s), and no 10 ms window's RMS differs from its neighbour by more than 0.5 dB anywhere across the engagement: the audio path is never switched, only the modulation depth moves. | S2, read this run: RISE TIME "adjust the time needed for a vibrato to reach its maximum", "150 ms ~ 5 s", and PEDAL SWITCH "does not affect the Normal/Effect function and thereby FET switching system is not adopted". S1: the BA662A VCA with an envelope on its control port | high | A 10–90 % rise more than 20 % from the setting at either extreme, or any 10 ms window whose RMS steps more than 0.5 dB across engagement | M5 |
| T6 | **The wet path is band-limited 40 Hz to 17 kHz at −3 dB** — a *bright* BBD path, unlike the Chorus standout's ~3 kHz corner, because the clock is an order faster. Measured at Depth 0, **48 kHz, with the Delay macro at a whole number of samples** (the default 4.00 ms is exactly 192), the −3 dB points relative to the 1 kHz level are 40 Hz and 17 kHz. | S2, read this run: "Frequency Range 40 Hz ~ 17 kHz (−3 dB, Vibrato)". S1, S3 §2.2 | high | −3 dB points outside 30–60 Hz or 14–20 kHz under those conditions | M6 |
| T7 | **The clock is modulated, not the delay.** The delay trajectory carries a **second harmonic at m/2 of its fundamental, in quadrature with it** — the signature of d(t) = d₀/(1 + m·s(t)) rather than d₀ + A·s(t), which has no second harmonic at all. −23.1 dB at the `Published defaults` patch (m ≈ 0.14) and −10.3 dB at `Deep slow` (m ≈ 0.56), both computed this run (App. H). This is the trait §5's node ask exists to reach. | S1: the modulation chain runs LFO → DEPTH → BA662A VCA → the MN3102 clock driver, with no delay-setting element in the audio path — the IC legend (IC2 MN3207, IC3 MN3102, IC4 BA662A, IC5 TL022CP) and the filter chain were re-read this pass; App. A's pin-level trace is the seed run's. S3 §2.1, re-read this run: "For any BBD, the total time delay is given by Delay Time (s) = N/(2·f_cp)" | high for the mechanism; medium for m, which the class's own Depth law sets and the measurement reports | No second harmonic above the trajectory's noise floor at any Depth (an additive-sine law), or one more than 6 dB from m/2 at the m the same run measures, or one in phase rather than quadrature with the fundamental | M7 |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

Vision §4.2 proposes the VB-2 *(proposed)* as "a BBD pitch vibrato, the
cleanest hardware referent for a pure pitch wobble". **Confirmed**, on four
counts, three of them from the manufacturer: **(1) it is pure wet** — the
specification's control list is "RATE, DEPTH, RISE TIME, MODE
(LATCH↔BYPASS↔UNLATCH)" and nothing else (S2), and the schematic routes the
direct and effect paths to separate switch terminals rather than summing them
(S1); a vibrato that sums any dry is a chorus. **(2) Its numbers are
published by the maker** — delay 4 ms, LFO 2–15 Hz, rise 150 ms–5 s,
40 Hz–17 kHz −3 dB, S/N −92 dB (S2); nothing else in this family gives Phase 0
manufacturer figures to fix traits against. **(3) Its engagement behaviour is
a design, not an accident** — the ramp, the VCA and the three modes are
documented (S2) and are what a rebuilt class can expose to a host. **(4) It is
the Chorus's sibling by mechanism** (1024-stage BBD, clock modulated by an
LFO), which makes the two classes honestly different rather than one class
with a mix knob.

*(from §2)*

Alternatives considered: **a chorus with the dry removed** — what the old
class effectively is (§7), and what a Small Clone's well-known vibrato
modification does; a mode, not a design. **The Univibe family** — not pursued:
no schematic was reached for it this run, and asserting its topology from
memory is what the evidence rules forbid. No swap is argued.

*(from §3)*

*Which sources this trait-critic pass re-reached for itself (2026-09-06):* **S1**
(HTTP 200, md5 `b729d0b2…`; the eight 780×82 strips re-extracted, assembled and
read — the IC legend, the reconstruction chain, the LFO region and the printed
service note), **S2** (HTTP 200, md5 `e409fe20…`; the specification page and the
panel-text page read as images, every figure quoted above verified), **S3**
(HTTP 200, md5 `316a6848…`, every sentence quoted from it re-searched).
**Carried from the seed run and not re-reached here:** S4, S5. Every row above
rests on at least one source this pass read for itself.

*(from §3)*

**Latency: the mean delay, reported.** No part of the algorithm looks ahead,
so there is no lookahead, no partition and no pitch window, and nothing here
defaults to a latency-adding option. But this class has **no dry path** (T1),
so the click measurement the contract prescribes — "a click through the class
against its dry path" — returns the mean delay, and `latency_samples` must
therefore report it: **192 samples, 4.0 ms at 48 kHz** at the default, and the
current mean delay whenever the Delay macro moves. The docstring states it in
milliseconds. This is the honest number for a stompboard: five pure-wet
modulations in series add their mean delays, and `Rack`'s sum will show it.
§8.3 raises this as a program-wide question, because `Tremolo`, `AutoPan` and
`Phaser` do not have it and `Chorus` reports zero for the same node.

*(from §4)*

`damping_hz` and `cut_hz` (`:231-240`) carry T6's two −3 dB points, 17 kHz and
40 Hz — `cut_hz` at its nominal value, `damping_hz` only through a pre-warp
the verification block below measures. They are **one-pole each**, where the circuit has three-plus-two poles
at the top; T6 is stated at the −3 dB points only and the roll-off *slope* is
a recorded deviation, not a modelled trait. If Gate 0's audioif#23 answer
yields a DC-clean biquad, a short `audiofilters.Filter` cascade would carry
the slope too; until then it would import the DC hold into a class whose
Tier 1 forbids it, so the seed does not propose it.

*(from §4)*

**Palette verification (2026-09-06; probes and numbers in App. I).** **The
top corner is not `damping_hz = 17000`, and the first draft was wrong to say
it was.** The node's one-pole coefficient is `1 − exp(−2π·f/fs)` (`:29-38`) —
an RC step-response match, not a corner match — so nominal and actual −3 dB
diverge above about a quarter of the rate. Measured at 48 kHz, Depth 0, delay
192 samples exactly: `damping_hz = 17000` is **−1.57 dB at 17 kHz** and never
worse than −1.88 dB below Nyquist, and **no nominal above ≈13.46 kHz reaches
−3 dB at all**. Python must pre-warp — nominal **≈12.3 kHz** measures
−3.02 dB at 17 kHz — the move the class already makes for
`audiofilters.Phaser`'s `frequency` (vision §6); the Tone macro's range is
the corner, not the nominal. The 40 Hz end needs none: `cut_hz = 40` measured
−3.06 dB at 40 Hz, the two mappings agreeing at low f/fs. The pre-warp is
rate-dependent and computed at construction, which Tier 1's rate-honesty
covers. Also verified on the same node: `mix = 2.0` is wet alone and
`mix = 0` is a byte-exact wire.

*(from §4)*

**Python computes at construction** the mean delay, the depth in ms from the
cents target (App. B), the two corners, and — for **T7** — **one period of the
clock law as a table** (`1/(1 + m·sin θ)`, normalised) on CPython, shipped as
data (§5). The **rise-time envelope is plain Python at block rate**:
`wow_depth_ms` is rewritten once per 256-frame block along the ramp, at least
28 steps across the shortest 150 ms rise; the class gate measures whether that
stepping is audible (§8.2).

*(from §4)*

**Portability tier: audioif**; on a stock board the module imports and
construction raises a clear `ImportError` (`drive.py:30-33`/`:331-334`). The
stock alternative is refuted twice: `audiodelays.PitchShift` is a granular
window resampler with an overlap crossfade (`audioif_pitchshift.c:26-38`) — a
different mechanism, smearing transients and carrying a real window latency —
and `audiodelays.Chorus` reads whole-sample taps at fixed integer spacing with
no interpolation (`audioif_chorus.c:18`, `:22`) and cannot produce a single
voice at all (`:15-16`).

*(from §4)*

**Mono and stereo.** One line, mono in, mono out. A mono source gets the
vibrato; a stereo source gets the same delay and modulation on both channels,
the node running two lanes from one oscillator (`:209-213` sits outside the
channel loop). The class is not stereo-by-definition and offers no width macro.

*(from §5)*

- **Trait it unblocks:** **T7** (and `Chorus` T2 and T6). *Correction to the
  first draft, which named T4:* T4 is a **smoothness** test on the third
  harmonic, and the node's own additive sine is perfectly smooth — it passes T4
  outright, so T4 cannot be what the ask unblocks. What the node's own
  additive sine cannot produce **in one node** is T7's second harmonic in
  quadrature; the refutation record below records the two-node cascade that
  can, and why the ask still stands without it.

*(from §5)*

- **What the palette does instead:** the kernel adds
  `wow_depth_frames * wow_sine` to the delay (`:212-213`) — an additive
  **sine on the delay time**. The circuit puts a sine on the **clock**, so the
  delay is `d₀/(1 + m·sin θ)`, whose expansion carries a second harmonic of
  relative amplitude m/2 **in quadrature** with the fundamental (App. C).

*(from §5)*

- **Refutation record.** (1) *Step `delay_ms` from Python*: a config write
  with no slew (`:82-83`, read unsmoothed at `:212`) — one jump per 256-frame
  block (`audioif_feedback_delay.h:39`), the old class's defect in a new
  place. (2) *Cascade two nodes at f and 2f.* **The first draft said the
  cosine term cannot be made; that is wrong, and is corrected here.** `set()`
  reaches only the config writer (`audioecho/FeedbackDelay.c:32-58`,
  `:135-141`); the oscillator state is initialised at construction and at
  `reset_buffer` (`audioecho/FeedbackDelay.c:200-211`) and nowhere else, so
  holding a node at `wow_hz = 0` freezes its phase and primes it in 5.33 ms steps. Measured at
  m = 0.30, where the law wants a second harmonic 16.5 dB down in quadrature:
  a primed two-node cascade produced one at **−14.6 dB, −87.8°**, where a
  single node produced −28.2 dB, the probe's own floor (App. I). **So T7,
  taken alone, is reachable on today's palette, and this ask does not rest on
  it.** It rests on `Chorus` T2 — a triangle clock law the node's sine
  oscillator cannot approach at all — and, for this class, on what the
  cascade costs: a second int16 line and a second interpolated read in series,
  which T6's 17 kHz top can least afford; a two-term truncation that carries
  no third harmonic, where `Deep slow`'s m ≈ 0.56 puts one at −20.6 dB
  (App. H); and a 53 ms startup prime that every `reset()` destroys, which
  Tier 1 forbids depending on.

*(from §5)*

- **The ask, additive:** an optional `wow_shape` — a one-period table (int16,
  power-of-two length, computed on CPython, shipped as data) read in place of
  the internal sine at `:212-213`, `wow_hz` still setting the period and
  `wow_depth_ms` the amplitude. One detail the issue must carry: today's
  oscillator is a magic-circle pair whose state is a sine and a cosine
  (`:163-164`, stepped at `:209-210`) and whose rate is
  `2·sin(π·f/fs)` (`:113-114`), which has no index to look a table up with —
  so the shaped path needs its own phase accumulator alongside, advanced from
  the same `wow_hz`. Absent a shape, the node behaves exactly as today.
  Additive on an audioif-own module (D1); no ported node touched.

*(from §5)*

- **Measurement that shows the gap:** T7's trajectory FFT against a
  `FeedbackDelay` at the correct mean and depth — the additive sine puts **no**
  second harmonic in the trajectory at all, where the modelled law's is m/2 of
  the fundamental (−23.1 dB at m = 0.14, App. H). Measured this run at
  m = 0.30 (−16.5 dB expected): the single node read −28.2 dB, the probe's
  floor (App. I). The measurement shows the gap; it does not by itself carry
  the ask, per the refutation record above.
