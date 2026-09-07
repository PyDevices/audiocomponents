# Effects Dossier — `Exciter` (Aphex Aural Exciter)

**Class:** `lib/audioeffects/drive.py` — read once, for §7, and not otherwise
consulted.
**Family / phase:** Drive, roadmap Phase 4
**Standout:** Aphex Aural Exciter, per vision §4.2 — **confirmed.** The
originating patent is reached and read (S1), the 1993 revision that gives the
class its second character is reached and read (S2), and the manufacturer's own
manual and block diagram are reached and read (S3). Nothing argues for a swap;
the effect category is named after this box.
**Grade:** **literature.** S1's preferred embodiment names component values
(two 0.01 µF capacitors, 56 K and 27 K, a 1N914, a 10 K threshold pot, a 47 K
output resistor) but they were read from the patent's own tabulated element
list for FIG. 6 ("629 0.01 μf 631 0.01 μf 633 56K 635 27K … 643 1N914 645 10K
… 648 47K"), not off the drawing, and no netlist was run. The upgrade path to
a `circuit` grade is named in §8.
**Portability tier:** **audioif** — `audioroute.Splitter` carries the
dry/sidechain split, and the transient character needs §5's node.
**Capabilities:** `()` — nothing here is tempo-related (D10).
**Status:** seed (Phase 0), written 2026-09-06

## 1. The circuit, in one paragraph

The input splits two ways: a straight-through path that is never processed,
and a sidechain. The sidechain opens with a **two-pole Butterworth high-pass**
on one op-amp — two 0.01 µF capacitors with 56 K and 27 K, specified "4KHZ, 2
pole, high pass" in the solid-state embodiment (S1) — which strips the
fundamental region. The patent's phase figure — "a linear frequency dependent
phase shift of about 360° over a frequency range from about 100 HZ to about 22
KHZ", with "the point of zero phase shift … about 2KHZ" — is stated for the
whole exciter circuit (FIG. 4), and the patent credits the filter with it:
"the phase change in the signal resulting from passing the signal through the
filter". What survives goes to a harmonic creator that is **one diode**: a
1N914 across an op-amp with a 10 K threshold pot and a 47 K output resistor,
using "the voltage to current characteristics of the diode … to softly clip
the peaks of the incoming signal at a threshold determined by the adjustable
potentiometer" — and clipping **one side only**, so that "both odd and even
harmonics are created" (S1). The result is uniformly attenuated and summed
back under the untouched path, "to about between 20% and 70% of the amplitude
of the unaltered signal" (S1). The 1993 revision makes the threshold move: the
diode charges an RC network as the signal sustains — "the time constant of
resistor R3 and capacitor C1 determine the slope of the attack parameter" (4.7
kΩ, 0.1 µF), while R1 (270 kΩ) serves "mainly … a suitable discharge path for
C1 after the input signal is removed"; the AGC variant of the same patent
quotes an "attack time of about 20ms" — so "each subsequent audio cycle …
moves further out of conduction of diode D1 by the developing DC bias voltage"
— harmonics loud at onset, falling over a time constant, low in steady state
(S2). The panel is three knobs: **Tune** sets the high-pass corner (600 Hz–5
kHz in the manual's text, 12 o'clock ≈ 3 kHz; its own block diagram prints 800
Hz–6 kHz — §8 Q1), **Harmonics** sets the clipper's threshold, **Mix** sets
the attenuator. There is no LFO and nothing sweeps. Full quotations: Appendix
C.

## 2. Sources and license calls

Every source reached in this run; quotations are in **Appendix C**.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1. US 4,150,253 A, "Signal distortion circuit and method of use" … (App. S1) | §1; T1–T4 | **No license or terms statement appears on … (App. S1) | https://patents.google.com/patent/US4150253A/en | yes |
| S2. EP 0 629 039 B1, "Transient discriminate harmonics generator" … (App. S2) | T5; the character split | as S1 (no license statement on the page … (App. S2) | https://patents.google.com/patent/EP0629039B1/en | yes |
| S3. Aphex, *Aural Exciter & Optical Big Bottom* owner's manual (PDF) | the block diagram, the three control ranges … (App. S3) | **license unverified … (App. S3) | http://cdn.aphex.com/assets/pdf/Aphex_Exciter_OM.pdf | yes (WebFetch cannot read this PDF; fetched with `curl`, text extracted with `pypdf` under `audiocomponents/.venv`) |
| S4. Lipshitz, Wannamaker & Vanderkooy, *JAES* 40(5) 1992 | T7's mechanism: aliasing of distortion components … (App. S4) | **license unverified … (App. S4) | https://hajim.rochester.edu/ece/sites/zduan/teaching/ece472/reading/Lipshitz_1992.pdf | yes (fetched with `curl`, text extracted with `pypdf`) |
| S5. The palette, probed under `audiocomponents/.venv/bin/python` | every measured number in §4 and Appendix A | MIT (this organization) | `audioif/src/shared/audioif_distortion.c` | yes (local) |

**Audit, 2026-09-06 (license and citation pass).** Every URL above was
re-fetched by an independent auditor, every Appendix C quotation was located
in the fetched text, and Appendix A's probe was re-measured. Every license
call above survived. One measured column did not reproduce and is restated as
a floor rather than a number; the record is **Appendix E**.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

The class carries **two characters**, and each carries its own rows: `classic`
(S1, 1977) and `transient` (S2, 1993). A character that fails its traits cannot
hide behind one that passes (vision §10.7).

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Char. | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|---|
| T1 | both | The sidechain is high-passed **second order** ahead of the nonlinearity. Measured against the wet path's own passband (taken at 8× Tune, where a second-order high-pass is within 0.1 dB of asymptotic): **12.3 ± 1.5 dB** down one octave below Tune, **3.0 ± 1.0 dB** down at Tune, and the octave from Tune/4 to Tune/2 rises **11.8 ± 1.5 dB**; the −3 dB point sits within ±10 % of the Tune setting everywhere across 600 Hz–6 kHz. | S1 ("a 2-pole slow roll off Butterworth high … (App. T1) | high | An octave-below figure outside 10.8–13.8 dB re passband — **first order reads 7.0 dB and fourth order 24.6 dB** — or a −3 dB point more than 10 % from the Tune setting | Swept-sine magnitude of the wet … (App. T1) |
| T2 | both | The clipper is **asymmetric**: with a 1 kHz sine into the sidechain at −20, −12 and −6 dBFS, h2 is within 10 dB of h3 at every one of the three — both orders present, neither at the analysis floor. | S1 ("By clipping the signal on one side only both odd and even harmonics are created") | high | h2 more than 10 dB below h3 at any of the three levels, or either order at the analysis floor. (A symmetric curve is 90 dB clear of that bar: the palette's WAVESHAPE and CLIP at `drive` 0.5 put h2 below −105 dB, App. A. On OVERDRIVE the critic pass measured \|h2−h3\| between 0.6 and 5.0 dB across −40…−1 dBFS, App. F) | Harmonic spectrum of the wet path at three levels |
| T3 | both | Harmonic generation is **amplitude-dependent**: h2/h1 and h3/h1 rise monotonically by at least 20 dB as the sidechain input rises from −40 to −6 dBFS. | S1 (a diode conducting above a threshold) … (App. T3) | high | Less than 20 dB of rise across that span, or any non-monotonic step in it. A pure power law is flat and fails outright: the palette's CLIP mode at `drive` 0.5 measures h3/h1 = −16.9 dB at every level from −40 to −1 dBFS (App. A). OVERDRIVE, re-measured by the critic pass, rises 30.0 dB (h2) and 32.9 dB (h3) over 39 dB of input (App. F) | Harmonic ratios against input … (App. T3) |
| T4 | both | The wet path is summed **under** the dry: at Mix maximum the excited signal's amplitude is between 20 % and 70 % of the unaltered signal's, and the dry path is unity at every setting. | S1 ("attenuated to about between 20% and 70% … (App. T4) | high | A Mix range whose top puts the wet at or above unity, or a dry path that is not sample-exact | Peak ratio wet:dry at Mix max … (App. T4) |
| T5 | `transient` | Harmonics are **loudest at the onset and fall**: through a constant-amplitude 1 s burst at 5 kHz with Transient Time set to τ, h2+h3 in the first 5 ms window is **≥6 dB** above the steady state (the mean of the burst's last 100 ms) and reaches within 1 dB of that steady state in **τ ± 25 %**, at τ = 8, 20 and 150 ms, with the input level unchanged throughout. | S2 for the shape ("first generates a … (App. T5) | high on the shape … (App. T5) | Under 6 dB of onset emphasis, or a decay outside τ ± 25 % at any of the three τ. `classic` is flat by construction and is the control that must **not** show emphasis | h2+h3 level in successive 5 ms … (App. T5) |
| T6 | `transient` | The onset/steady ratio is **level-independent**: T5's ratio differs by **at most 3 dB** between a −30 dBFS burst and a −6 dBFS burst, and T5's ≥6 dB emphasis holds at both. | **S3** — the manufacturer's claim … (App. T6) | low — a … (App. T6) | The two ratios differing by more than 3 dB, or the −30 dBFS burst showing under 6 dB of emphasis — a plain threshold rather than a moving bias | T5's measurement at two levels |
| T7 | both | **No audible alias products**: with Tune at 5 kHz and a 6 kHz sine at −6 dBFS, every non-harmonic component is below −60 dB of the fundamental at 48 kHz and at 44.1 kHz. | S4 (aliasing of distortion components above … (App. T7) | high on the … (App. T7) | Any inharmonic component at or above −60 dB. A memoryless curve run at 1× fails it — that is why §5 asks for oversampling, and the 1× build is the planted fault | STFT of the sine probe and of a … (App. T7) |

### Tier 3 — cost and latency

Budget as a fraction of one stereo block's deadline: **ESP32-P4 0.06**,
**ESP32-S3 0.15**. Lean patch expected: **yes** on the S3 — a lower
oversampling factor, never a compromise of the faithful patch (vision §7.2).

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

`audioroute.Splitter(source, taps=2)` → tap 0 into `audiomixer.Mixer` voice 0
at level 1.0 (probed sample-exact unity, App. A; **re-probed end to end** by
the palette verification of 2026-09-06 — source → Splitter → tap 0 → Mixer
voice at 1.0 is byte-identical to the source over 8192 frames, App. G) → tap 1
into `audiofilters.Filter` carrying **one** `synthio.Biquad` in `HIGH_PASS` at
Q = 0.7071, which *is* S1's two-pole Butterworth → into
`audiofilters.Distortion` in `OVERDRIVE` with `soft_clip=True` and `pre_gain`
carrying the Harmonics control → Mixer voice 1 at the Mix level.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

Two asks were drafted here, both **shared with `Overdrive`, `Distortion` and
`Fuzz`**. The palette verification of 2026-09-06 **refutes both for this
class**; what is left is one small, differently shaped ask on an audioif-own
node. The drive dossiers still have their own case for the waveshaper — on
curve shape and cost, not on anything this class's traits need. Refutation
records in **Appendix D**.

**Ask E1 — the oversampled table waveshaper** (vision §6's named gap).
*Trait it claimed to unblock:* **T7**.

**Ask E2 — an envelope-following bias input on that node.**
*Traits it claimed to unblock:* **T5**, **T6**.

- **Trait clause unblocked by a node:** **T5's τ clause only.**
- **Shape:** expose those four coefficients as `Dynamics` options …  *(argument in full: App. R)*
- **If it is declined:** the class ships `transient` with a fixed ≈135 ms …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Six macros against a ceiling of sixteen.

| # | Label | Mode | Range | Generalises |
|---|---|---|---|---|
| 0 | Tune | UNIPOLAR | 600 Hz … 6 kHz, log, clamped below Nyquist | The Tune knob (S3's 600 Hz–5 kHz text and its diagram's 800 Hz–6 kHz, reconciled — §8 Q1) |
| 1 | Harmonics | UNIPOLAR | 0 … 1 → 0 … +24 dB `pre_gain`, level-compensated | The Harmonics knob, "the relative richness of harmonics created" (S3) |
| 2 | Mix | UNIPOLAR | 0 … 0.7 of the dry amplitude | The Amount knob, ceilinged at S1's 70 % |
| 3 | Character | TOGGLE | `classic` / `transient`, default `classic` | The 1977 and 1993 patents |
| 4 | Transient Time | UNIPOLAR | 5 … 200 ms, default 20 ms; inert in `classic` | S2's RC constant and its "attack time of about 20ms" |
| 5 | Output | UNIPOLAR | −24 … +6 dB, default 0 | — |

**Characters:** `classic` (fixed threshold; T1–T4, T7) and `transient` (moving
bias; those plus T5, T6).

**Patches** (names describe settings, never products): 0 `Voice Air` (4 kHz,
Harmonics 0.25, Mix 0.3 — S3's "MIN … useful for voices"); 1 `Percussive Edge`
(3 kHz, 0.8, 0.45, `transient` — S3's MAX, "percussive instruments");
2 `Mix Sheen` (6 kHz, 0.2, 0.2 — S3 §5.4's advice for an already-processed
mix); 3 `Mid Presence` (800 Hz, 0.5, 0.35 — "Tune lower for more mid pickup and
presence"); 4 `Fast Transient` (3 kHz, `transient`, 8 ms); 5 `Slow Transient`
(same, 150 ms); 6 `Wet Sidechain` (Mix 0.7, for the send-return use S3 §5.3
describes).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/drive.py`.

1. **No surface.** `MACRO_LABELS = ()` and one default patch
   (`drive.py:245-247`); no setter for Tune or Amount, so the effect is fixed at
   construction (`drive.py:249`).
2. **The Harmonics control does not exist.** The sidechain drives the curve at …  *(argument in full: App. R)*
3. **The wet has no ceiling:** `amount` reaches 1.0 straight into
   `mixer.voice[1].level` (`drive.py:265`), above S1's 70 %.
4. **No transient discrimination**, and no statement that the class is the 1977
   patent only.
5. **Latency is right by default, not by statement:** every class inherits
   `LATENCY_SAMPLES = 0` (`_core.py:140`) and none overrides it.
6. **The mixer runs a different buffer size from the rest of the chain** — …  *(argument in full: App. R)*

**What the current class gets right, and the rebuild keeps:** a single
second-order high-pass at Q = 0.707 (`drive.py:250-256`) is S1's two-pole
Butterworth, and the dry tap is the Splitter's tap 0 at unity. The topology is
correct; the surface, the second knob and the second character are missing.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Which Tune range?** S3's text says 600 Hz–5 kHz with 12 o'clock at 3 kHz;
   its own block diagram prints 800 Hz–6 kHz. The seed proposes the union,
   because a generalized effect has no reason to be narrower than either printed
   range. *Settled by:* the implementation session, or a service schematic.
2. **Is `circuit` grade worth reaching?** FIG. 6 of S1 is a full schematic with
   values; an ngspice deck like `tools/spice/ts808/` would turn T2 and T3 from
   qualitative into numbered. *Settled by:* the implementation session at
   Station A, if the drive family's SPICE work is already running.
3. **Does `audiodynamics` refute E2?** **Closed 2026-09-06: yes.**
   `DYN_TRANSIENT` ahead of the clipper delivers T5's shape and T6's level
   independence on the palette (§5, App. G). What is left is T5's τ clause and
   §6's Transient Time macro, which need the node's four hard-coded envelope
   coefficients exposed (`audioif_dynamics.c:215-221`); until they are, the
   `transient` character has one fixed ≈135 ms decay and that macro cannot be
   honoured as its range is written.
4. **`Big Bottom` belongs to no class here.** S3 documents a second sidechain in
   the same box — a tunable 50–200 Hz low-pass into a "Phase & Dynamics
   Processor" — which is closest to `DynamicEQ`. The set of 46 names is frozen
   (vision §2.2), so nothing is proposed; noted for that seed.

---


## Appendix

### A. The palette's distortion curves, measured

Probed under `audiocomponents/.venv/bin/python` on 2026-09-06: a bin-centred
999.02 Hz sine (bin 341 of a 16384-point transform at 48 kHz), Hann-windowed,
straight into `audiofilters.Distortion` with `mix = 1`. Harmonics are relative
to the fundamental at the output; "gain" is the fundamental's change.

**`drive` matters, and is stated here because it must be:** OVERDRIVE ignores
it (upstream-diff.md:1228) and is measured at the node's default; the
WAVESHAPE and CLIP rows below are at **`drive` 0.5**. At the default `drive` 0
both of those modes are within a hair of linear — h3 −57.5 dB at −40 dBFS,
falling to −91.1 dB (CLIP) and −96.6 dB (WAVESHAPE) at −1 dBFS, THD ≤ 0.2 % —
and neither control failure appears at all. The 2026-09-06 audit re-measured
every row independently on the same interpreter: the OVERDRIVE table
reproduces to the decibel, and the two control rows reproduce at `drive` 0.5
in every column that carries a trait — but not in their h2 floor figures, for
the reason stated under that table.

**OVERDRIVE, `soft_clip=True` — what the class uses, and what T2/T3 need:**

| input | gain | h2 | h3 | h4 | h5 | THD |
|---|---|---|---|---|---|---|
| −40 dBFS | +0.04 dB | −56.0 | −54.0 | −76.9 | −68.7 | 0.27 % |
| −30 dBFS | −0.15 dB | −46.5 | −44.5 | −86.9 | −58.9 | 0.77 % |
| −20 dBFS | −0.60 dB | −37.6 | −37.0 | −66.7 | −51.2 | 1.95 % |
| −12 dBFS | −1.37 dB | −31.4 | −30.7 | −54.5 | −44.8 | 4.03 % |
| −6 dBFS | −2.49 dB | −27.9 | −25.5 | −45.9 | −39.4 | 6.78 % |
| −1 dBFS | −4.07 dB | −26.1 | −21.0 | −39.7 | −34.1 | 10.44 % |

h2 within 6 dB of h3 at every level (T2), and both climbing ~30 dB across the
39 dB of input range (T3). With `soft_clip=False` the same curve gives h2
−56.5 → −21.9 and h3 −53.8 → −30.2 — still asymmetric, still amplitude
dependent, with less gain loss at the top.

**The two controls that must fail T2 and T3:**

| mode | h2 range over −40 … −1 dBFS | h3 range | THD range |
|---|---|---|---|
| WAVESHAPE | −114.8 … −133.4 dB (numerical floor) | −50.1 … −16.6 dB | 0.32 … 15.89 % |
| CLIP | −111.4 … −136.4 dB (floor) | **−16.9 dB at every level** | **16.67 % at every level** |

**The h2 columns are floor, and only the floor's *order* reproduces.** The
audit's independent re-measurement on the same interpreter returned
−109.4 → −117.1 dB (CLIP) and −109.9 → −133.4 dB (WAVESHAPE) for those two
columns while reproducing every h3 and THD figure exactly. Nothing is being
measured there but the analysis window's own noise, and it moves with the
window; read the column as "h2 below −105 dB, at the numerical floor" and
never as a number.

WAVESHAPE is odd-symmetric, so a build that used it would fail T2 with h2 90 dB
below h3. CLIP is a pure power law, so its harmonic ratio does not move with
level at all — a build that used it would fail T3 flat. Both are already in the
same node, which makes them free controls rather than faults someone has to
plant.

**Mixer unity, for T4 and Tier 1's level honesty:** an `audiomixer.Mixer` voice
at level 1.0 returned the source sample-for-sample over the live span of the
probe (checked value-by-value on the first 8 samples and on the peak).

### B. Planted faults, so the measurements can fail

- **T1.** Build with one biquad replaced by a first-order high-pass; the
  12 ± 2 dB octave test must go red. Control: the correct build must pass.
- **T2.** Swap OVERDRIVE for WAVESHAPE; h2 drops to the floor and the check
  must go red. This is a *control that fails*, not a plant — App. A already
  has its numbers.
- **T3.** Swap OVERDRIVE for CLIP; the level sweep flattens and the check must
  go red.
- **T4.** Raise the Mix ceiling to 1.0; the peak-ratio test must go red. And
  attenuate the dry path by 0.5 dB; the byte-compare must go red — a wet-only
  check would not notice, which is the *absence-reads-as-agreement* shape
  `agent-knowledge/workspace-craft.md` names.
- **T5.** Run the burst probe against `classic`; it must show ≤1 dB of onset
  emphasis and the check must go red when `transient` is expected. Run it
  against `transient` with the bias time constant set to 1 µs; the onset window
  and the steady state must converge and the check must go red.
- **T7.** Force the oversampling factor to 1×; the 18 kHz alias must appear
  above −60 dB and the check must go red.

The trap this measurement set is most exposed to is a **silent sidechain**: if
the high-pass or the clipper fails to build, the wet path is zero, T4's peak
ratio reads 0 (inside "at most 70 %"), and T1's octave test reads a difference
of zero decibels between two silences. Every wet-path measurement therefore
carries an absolute floor check — the wet path must be above −60 dBFS at the
probe level before any ratio is believed.

### D. Refutation records

**Superseded 2026-09-06 by the palette verification.** Both asks were refuted
against the palette; §5 carries the measurements and what is left of each. This
appendix keeps the records as they stood, and marks what happened to them.

**E1.** *"Band-limit the sidechain instead"* — cap Tune so h5 stays under
Nyquist. It fails: at 48 kHz that caps Tune at 4.8 kHz, inside the manual's own
600 Hz–5 kHz range, and at 44.1 kHz at 4.4 kHz, so the control law would shrink
with the sample rate, which Tier 1's rate-honesty rules out. **Still true — and
overtaken**: a pair of `audiospeed.SpeedChanger`s and two biquad cascades
oversample on the palette and take the worst alias from −39.4 dB to −69.1 dB
(§5, App. G), so Tune does not have to be capped and no node is needed for T7.

**E2.** *"`audiodynamics.Dynamics` in transient mode on the sidechain"* — it
shapes the *audio*, not the clipper's threshold, so what it emphasises is the
harmonics already generated, and T4's dry-path unity is what would catch the
difference. Worth running rather than assuming: if T5's burst probe shows ≥6 dB
of onset emphasis from `Dynamics` alone, E2 is refuted and `transient` ships
stock. That probe is §8 Q3. **Run 2026-09-06, and the answer is yes** — 8.2 to
9.0 dB of onset emphasis with a 0.8 dB spread over 24 dB of input level, with
`DYN_TRANSIENT` placed *ahead* of the clipper where it shapes the drive rather
than the output. §8 Q3 is closed; the argument that it "shapes the audio, not
the threshold" was the error, because the audio *is* the drive.

### C. Source quotations, verbatim

**S1 (US 4,150,253 A)**: "a 2-pole slow roll off Butterworth high pass filter
and is made up of two capacitors 629 and 631, a pair of resistors 633 and 635
and an operational amplifier 637" · "4KHZ, 2 pole, high pass" · "a diode 643, an
adjustable potentiometer 645 and an operational amplifier 647 and a resistor
648" · "utilizes the voltage to current characteristics of the diode 643 to
softly clip the peaks of the incoming signal at a threshold determined by the
adjustable potentiometer 645" · "By clipping the signal on one side only both
odd and even harmonics are created" · "a linear frequency dependent phase shift
of about 360° over a frequency range from about 100 HZ to about 22 KHZ" · "the
excited signal is attenuated to about between 20% and 70% of the amplitude of
the unaltered signal". Component values named in the embodiment: 0.01 µF
capacitors, 56 K and 27 K resistors, 1N914 diode, 10 K threshold pot, 47 K
output resistor.

**S2 (EP 0 629 039 B1)**: "the time constant of resistor R3 and capacitor C1
determine the slope of the attack parameter. Resistor R1 serves the purpose
mainly of providing a suitable discharge path for C1 after the input signal is
removed." · the generator "first generates a relatively high level
of harmonics at an initial occurrence of the input signal, then incrementally
reduces the level of harmonics generated during a time period determined by the
control parameter … and finally produces a relatively low level of harmonics
after the end of the time period" · "Each subsequent audio cycle appearing at
point 20 moves further out of conduction of diode D1 by the developing DC bias
voltage" · C1 0.1 µF, R1 270 kΩ, R3 4.7 kΩ, R4 10 kΩ; AGC variant C100 4.7 µF,
"attack time of about 20ms"; supplies ±15 V. The patent quantifies no amplitude
ratio, which is why T5's 6 dB is our own bar and is stated as such. It also
says nothing about a dynamic range: the "over a wide dynamic range" sentence
T6 rests on is **S3's**, not this patent's (audit, 2026-09-06).

**S3 (Aphex owner's manual)**: block diagram, Aural Exciter sidechain —
"Tunable Highpass Filter" → "Transient Discriminate Harmonics Generator" →
"Variable Harmonics" / "Mix" → "SUM", labelled "Tune 800Hz-6kHz"; Big Bottom
sidechain — "Tunable Lowpass Filter" → "Phase & Dynamics Processor" →
"Variable Drive" / "Mix", labelled "Tune 50Hz-190Hz". §4.5: "The range of the
corner frequency is 600Hz (fully counter clockwise) and 5kHz (fully clockwise).
The 12 o'clock setting is approximately 3kHz." §4.6: "This control adjusts the
amount of harmonics being generated by the exciter. It controls the texture and
detail of the effect. The MIN position is generally considered NORMAL, and is
useful for voices and total mixes. The MAX position is most useful on specific
tracks, especially percussive instruments, horns, guitars and digital
instruments." §2.1: "The original Aural Exciter patent disclosed a method for
generating sonic harmonics which was amplitude dependent. In nature, generally
speaking, the higher the amplitude, the higher the amount of harmonics." §2.1
also: "Our latest patent, the Transient Discriminate Harmonics Generator, can
recognize transients (transient discriminate) over a wide dynamic range and
generate harmonics on them" — the sentence T6 rests on. §7.0 specifications:
"Frequency Response +0.5dB 10Hz-38KHz", "THD 10Hz - 22kHz @ max output,
.0003%". *(The table is headed only "AUDIO" and does not say whether the unit
is processing; reading these two rows as the unprocessed path is our
inference, not the manual's word. Nothing in §3 rests on it.)*

**S4**: "Inharmonic peaks are also present due to aliasing of distortion
components above the Nyquist frequency (22.05 kHz in this simulation) into the
baseband."

### F. Trait critic pass — 2026-09-06

Sources re-reached in this pass; nothing below rests on the earlier run's word.

- **S1 re-fetched** (`https://patents.google.com/patent/US4150253A/en`):
  "The filter 621 is a 2-pole slow roll off Butterworth high pass filter",
  "4KHZ, 2 pole, high pass", "By clipping the signal on one side only both odd
  and even harmonics are created", "the excited signal is attenuated to about
  between 20% and 70% of the amplitude of the unaltered signal". No copyright
  or licence statement on the page — §2's call holds.
- **S2 re-fetched** (`https://patents.google.com/patent/EP0629039B1/en`):
  "the time constant of resistor R3 and capacitor C1 determine the slope of the
  attack parameter"; "Resistor R1 serves the purpose mainly of providing a
  suitable discharge path for C1 after the input signal is removed"; "the AGC
  circuit 110 may have an infinite compression ratio, an attack time of about
  20ms, and a threshold 10dB below the input signal level"; R1 270 kΩ,
  R3 4.7 kΩ, C1 0.1 µF. **"Dynamic range" does not occur anywhere in S2**,
  confirming T6's attribution to S3.
- **Appendix A's OVERDRIVE probe re-run** by the critic under
  `audiocomponents/.venv/bin/python` (999.02 Hz, bin 341 of 16384 at 48 kHz,
  Hann, `soft_clip=True`, `mix=1`): gain +0.04 / −0.15 / −0.60 / −1.37 / −2.49 /
  −4.07 dB and h2 −56.03 / −46.48 / −37.62 / −31.43 / −27.85 / −26.08 dB,
  h3 −53.95 / −44.47 / −37.00 / −30.67 / −25.55 / −21.05 dB at −40, −30, −20,
  −12, −6 and −1 dBFS — reproducing Appendix A to 0.05 dB. \|h2−h3\| runs 0.62
  to 5.03 dB (T2), and h2/h1 rises 29.95 dB, h3/h1 32.90 dB, across the 39 dB
  span (T3).
- **T1's dB figures computed, not recalled.** The RBJ second-order high-pass at
  Q = 0.7071 was evaluated at Tune = 600, 1000, 3000, 5000 and 6000 Hz on both
  48 kHz and 44.1 kHz: −3.01 dB at Tune, −12.31 to −13.10 dB an octave below,
  −24.11 to −25.13 dB two octaves below, all re the passband. A first-order
  high-pass gives −6.99 dB and a fourth-order (two cascaded Butterworth pairs)
  −24.61 dB one octave below, which is what makes the row discriminate.

**Rows rewritten, and why.**

- **T1 was arithmetically wrong and a correct build would have failed it.** It
  asked for "12 ± 2 dB below its value **at Tune**"; a two-pole Butterworth is
  −3.01 dB *at* its corner, so one octave below it is only **9.3–10.1 dB** below
  that value — outside the row's own ±2 dB band at every Tune setting under
  6 kHz. The 12 dB figure is the drop re the **passband**, not re the corner.
  The row now states both anchors, the passband reference it is measured
  against, and the first- and fourth-order numbers that bracket it.
- **T2 and T3** claimed one tolerance and disconfirmed at another (10 dB vs
  20 dB; "at least 20 dB of rise" vs "flat with level"), leaving a band where a
  build was neither confirmed nor refuted. Both disconfirmation cells are now
  the exact complement of their claim.
- **T5** hung its timing on numbers its own source does not give: R3·C1 is
  0.47 ms, and S2's 20 ms belongs to the AGC block, not to the bias network.
  The trait now measures against the class's own Transient Time macro at three
  settings and says plainly which half is sourced and which is ours.
- **T6** disconfirmed by a qualitative phrase ("collapses at low level"); it now
  names the same 3 dB the claim does.
- **T7** carried an unattributed −60 dB floor; it is our engineering bar and now
  says so.

**Seven Tier 2 rows after the pass, unchanged in count.** No row was dropped and
none needed the *unmeasured* mark. Both characters keep their own rows —
`classic` T1–T4 and T7, `transient` those plus T5 and T6.

### E. Audit record — license and citation pass, 2026-09-06

Every URL in §2 was re-fetched by an independent auditor and every quotation in
Appendix C was located in the fetched text. Findings:

- **The license calls hold.** Stripped of markup, neither patent page contains
  the string `copyright` in any case; the Aphex manual's 24 pages of extracted
  text contain no `copyright`, `©`, `rights` or `terms` line either, so S3
  stays "license unverified — treated as copyleft", and S4 likewise (no rights
  string anywhere in the Lipshitz PDF's text).
- **T6's attribution is confirmed corrected.** "can recognize transients
  (transient discriminate) over a wide dynamic range and generate harmonics on
  them" is **S3's** sentence, in §2.1 of the manual. The phrase "wide dynamic
  range" does not occur anywhere in EP 0 629 039 B1. §1's transient time
  constant is R3·C1, as the patent states.
- **S2's component values check out** against the patent's own "by way of
  example only" list: C1 0.1 µF, R1 270 kΩ, R2 2.2 MΩ, R3 4.7 kΩ, R4 10 kΩ,
  −E −15 V and +E 15 V, AGC C100 4.7 µF.
- **S1's element list checks out** verbatim: "621 4KHZ, 2 pole, high pass 629
  0.01 μf 631 0.01 μf 633 56K 635 27K … 643 1N914 645 10K 647 1/2#4558 648
  47K". Inventor Curt A. Knoppel; filed 1977-01-26, granted 1979-04-17;
  assigned to Aphex Systems Ltd in 1993 from Inter Tech Exchange Ltd.
- **S3's section numbers are as cited**: §2.1 the technologies explained,
  §4.5–§4.7 the three Aural Exciter controls, §5.3 effects-loop patches, §5.4
  optimizing, §7.0 Specifications.
- **Appendix A re-measured independently.** The OVERDRIVE table reproduces to
  0.1 dB at every level (gain, h2, h3, h4, h5) and the mixer-unity check
  reproduces sample-exactly. The two control modes reproduce in the column
  that carries a trait — CLIP h3 = −16.9 dB at every level, WAVESHAPE h3
  −50.1 → −16.6 dB — but **their h2 figures did not reproduce** (audit read
  −109.4 → −117.1 for CLIP and −109.9 → −133.4 for WAVESHAPE against the
  printed −111.4 → −136.4 and −114.8 → −133.4). Those are numerical-floor
  values, not measurements of a harmonic, and they move with the analysis
  window; Appendix A now says so, and T2's disconfirmation rests on the
  90 dB gap, not on the floor's exact value.

### G. Palette verification pass — 2026-09-06

Run by the palette verifier for the bitcrusher–exciter–cabinet unit, under
`audiocomponents/.venv/bin/python`, against the C in `audioif/src/`.

**Splitter → Mixer unity.** `RawSample` 997 Hz → `audiomixer.Mixer` (buffer
2048, level 1.0) → `audioroute.Splitter(taps=2)` → tap 0 → a second Mixer voice
at 1.0: **byte-identical to the source over 8192 frames**, max difference 0.
The Mixer alone at level 1.0 is likewise exact. Fed the `RawSample` *directly*,
the Splitter's 8192-frame ring wraps before the tap is read and tap 0 starts at
source frame **39808** (= 48000 − 8192) — a probe artefact, recorded in §4
because the Tier 1 byte-compare would otherwise read it as a defect.

**`audiofilters.Distortion` harmonics**, 1 kHz, `mix=1`, h_k relative to the
output fundamental:

| mode | soft_clip | −40 dBFS | −20 | −12 | −6 | −1 |
|---|---|---|---|---|---|---|
| OVERDRIVE h2 | on | −55.5 | −37.7 | −31.4 | −27.9 | −26.1 |
| OVERDRIVE h3 | on | −54.7 | −37.0 | −30.7 | −25.6 | −21.1 |
| CLIP h3 (`drive` 0.5) | **off** | −16.93 | −16.94 | −16.94 | −16.94 | −16.94 |
| CLIP h3 (`drive` 0.5) | **on** | −16.6 | −15.8 | −15.3 | −14.7 | −14.1 |
| WAVESHAPE h2 (`drive` 0.5) | either | ≤ −115 (numerical floor) | | | | |

App. A's OVERDRIVE table reproduces; `|h2 − h3|` runs 0.9 / 0.7 / 0.7 / 2.3 /
5.0 dB, inside its stated 0.6–5.0. The CLIP row's "−16.9 at every level" is a
`soft_clip=False` reading, which App. A did not say.

**Composed oversampling (E1).** `RawSample` → `SpeedChanger(rate=1/M)` →
`Filter` (M=2: eight `LOW_PASS` biquads at 10.8 kHz in the stretched domain,
= 21.6 kHz original) → `Distortion(OVERDRIVE, soft_clip=True)` → the same
cascade → `SpeedChanger(rate=M)`. Probe 5.5 kHz at −6 dBFS, 32768-point Hann
FFT; "alias" means a folded harmonic that is **not** a multiple of the input,
peak-picked over ±3 bins:

| product | 1× | composed 2× | composed 4× |
|---|---|---|---|
| h5 → 20.5 kHz | **−39.4** | −104.8 | −86.8 |
| h6 → 15.0 kHz | −58.2 | −101.3 | −104.2 |
| h7 → 9.5 kHz | −47.9 | −105.9 | −101.5 |
| h9 → 1.5 kHz | −53.4 | −96.7 | −102.3 |
| worst of the first twenty | **−39.4** | **−69.1** | **−86.8** |

The probe is 5.5 kHz and not T7's 6 kHz because at 48 kHz every folded harmonic
of 6 kHz lands on a multiple of 6 kHz (h5 at 30 kHz folds to 18 kHz, which is
h3), so a 6 kHz probe cannot show an inharmonic product at all.

**`DYN_TRANSIENT` ahead of the clipper (E2).** `RawSample` (50 ms of silence,
then a constant 5 kHz burst) → `Dynamics(DYN_TRANSIENT, attack_gain_db=+12,
sustain_gain_db=−12)` → `Distortion(OVERDRIVE, soft_clip=True)`. h2+h3 relative
to the fundamental, first 5 ms window against the mean of 450–550 ms:

| level | onset | steady | emphasis |
|---|---|---|---|
| −30 dBFS | −29.7 | −38.6 | **8.9 dB** |
| −18 dBFS | −20.6 | −28.8 | **8.2 dB** |
| −6 dBFS | −10.8 | −19.8 | **9.0 dB** |

Decay, at −18 dBFS: flat through 25 ms, then −0.4 dB at 30 ms, −2.2 at 40,
−4.4 at 60, −6.5 at 90, −7.0 at 120, **within 1 dB of steady at ≈135 ms** — and
unmovable, the four coefficients being compile-time constants
(`audioif_dynamics.c:215-221`).

`DYN_COMPRESS` in the same place, threshold −24 dB ratio 8: emphasis 7.9 dB at
`attack_ms` 8, 7.7 at 20, 5.9 at 150 — the shape, but level-dependent (0.0 dB
at −30 dBFS against 11.5 dB at −6, and 13.5 against 25.3 at threshold −45 /
ratio 20). It passes T5 and fails T6, which is what makes it the control.

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

**Rate-honest note.** Tune clamps below Nyquist, so at 22.05 kHz the macro's
top lands at ~9 kHz. **T7 cannot hold at 22.05 kHz** as stated: a 5 kHz Tune
setting there leaves no room for even a second harmonic, so T7's alias floor is
measured at 48 and 44.1 kHz and the 22.05 kHz case is recorded as *not
applicable* rather than passed.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1. US 4,150,253 A, "Signal distortion circuit and method of use", filed 1977-01-26, granted 1979-04-17, assigned to Aphex Systems Ltd (orig. Inter Tech Exchange) | §1; T1–T4 | **No license or terms statement appears on the page** (checked in this run): a published patent disclosure, read as a document, nothing reproduced (vision §5), and treated read-only as any unverified source is | https://patents.google.com/patent/US4150253A/en | yes |
| S2. EP 0 629 039 B1, "Transient discriminate harmonics generator", Donn Werrbach / Aphex Systems Ltd, priority 1993-06-07 | T5; the character split | as S1 (no license statement on the page, checked) | https://patents.google.com/patent/EP0629039B1/en | yes |
| S3. Aphex, *Aural Exciter & Optical Big Bottom* owner's manual (PDF) | the block diagram, the three control ranges, §2.1's amplitude-dependence statement, T6's dynamic-range claim, §7.0's specification table | **license unverified — treated as copyleft**: no copyright, rights or terms line anywhere in the manual's text (checked); read as a document, nothing reproduced | http://cdn.aphex.com/assets/pdf/Aphex_Exciter_OM.pdf | yes (WebFetch cannot read this PDF; fetched with `curl`, text extracted with `pypdf` under `audiocomponents/.venv`) |
| S4. Lipshitz, Wannamaker & Vanderkooy, *JAES* 40(5) 1992 | T7's mechanism: aliasing of distortion components above Nyquist into the baseband | **license unverified — treated as copyleft**: the self-archived PDF carries no rights line at all (checked); read as a paper, nothing ported | https://hajim.rochester.edu/ece/sites/zduan/teaching/ece472/reading/Lipshitz_1992.pdf | yes (fetched with `curl`, text extracted with `pypdf`) |
| S5. The palette, probed under `audiocomponents/.venv/bin/python` | every measured number in §4 and Appendix A | MIT (this organization) | `audioif/src/shared/audioif_distortion.c` | yes (local) |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Char. | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|---|
| T1 | both | The sidechain is high-passed **second order** ahead of the nonlinearity. Measured against the wet path's own passband (taken at 8× Tune, where a second-order high-pass is within 0.1 dB of asymptotic): **12.3 ± 1.5 dB** down one octave below Tune, **3.0 ± 1.0 dB** down at Tune, and the octave from Tune/4 to Tune/2 rises **11.8 ± 1.5 dB**; the −3 dB point sits within ±10 % of the Tune setting everywhere across 600 Hz–6 kHz. | S1 ("a 2-pole slow roll off Butterworth high pass filter", "4KHZ, 2 pole, high pass", re-fetched by the critic pass); S3 (block diagram, "Tunable Highpass Filter"); the dB figures are the RBJ second-order high-pass at Q = 0.7071 evaluated by the critic pass at 600 Hz–6 kHz and 48/44.1 kHz (App. F) | high | An octave-below figure outside 10.8–13.8 dB re passband — **first order reads 7.0 dB and fourth order 24.6 dB** — or a −3 dB point more than 10 % from the Tune setting | Swept-sine magnitude of the wet path alone, normalised to its 8×-Tune value, at five Tune settings, 48 and 44.1 kHz — **probed at −40 dBFS**, where the clipper measures within 0.05 dB of linear (App. A's gain column), so the slope read is the filter's and not the nonlinearity's compression |
| T3 | both | Harmonic generation is **amplitude-dependent**: h2/h1 and h3/h1 rise monotonically by at least 20 dB as the sidechain input rises from −40 to −6 dBFS. | S1 (a diode conducting above a threshold); S3 §2.1 ("the higher the amplitude, the higher the amount of harmonics") | high | Less than 20 dB of rise across that span, or any non-monotonic step in it. A pure power law is flat and fails outright: the palette's CLIP mode at `drive` 0.5 measures h3/h1 = −16.9 dB at every level from −40 to −1 dBFS (App. A). OVERDRIVE, re-measured by the critic pass, rises 30.0 dB (h2) and 32.9 dB (h3) over 39 dB of input (App. F) | Harmonic ratios against input level, six levels over 40 dB |
| T4 | both | The wet path is summed **under** the dry: at Mix maximum the excited signal's amplitude is between 20 % and 70 % of the unaltered signal's, and the dry path is unity at every setting. | S1 ("attenuated to about between 20% and 70% of the amplitude of the unaltered signal") | high | A Mix range whose top puts the wet at or above unity, or a dry path that is not sample-exact | Peak ratio wet:dry at Mix max; byte-compare of the dry path against the source at Mix 0 |
| T5 | `transient` | Harmonics are **loudest at the onset and fall**: through a constant-amplitude 1 s burst at 5 kHz with Transient Time set to τ, h2+h3 in the first 5 ms window is **≥6 dB** above the steady state (the mean of the burst's last 100 ms) and reaches within 1 dB of that steady state in **τ ± 25 %**, at τ = 8, 20 and 150 ms, with the input level unchanged throughout. | S2 for the shape ("first generates a relatively high level of harmonics at an initial occurrence … then incrementally reduces the level", a bias developing on C1 — re-fetched by the critic pass). **The timing numbers are ours and the patent's are not these:** R3·C1 is 4.7 kΩ × 0.1 µF = **0.47 ms**, and the only "attack time of about 20ms" in S2 belongs to the AGC block ahead of the generator, not to the bias network. So the 5–200 ms macro range and the 6 dB bar are this seed's design choices, stated as such | high on the shape; the 6 dB bar and the τ tolerance are **ours** | Under 6 dB of onset emphasis, or a decay outside τ ± 25 % at any of the three τ. `classic` is flat by construction and is the control that must **not** show emphasis | h2+h3 level in successive 5 ms windows of the burst, at three Transient Time settings |
| T6 | `transient` | The onset/steady ratio is **level-independent**: T5's ratio differs by **at most 3 dB** between a −30 dBFS burst and a −6 dBFS burst, and T5's ≥6 dB emphasis holds at both. | **S3** — the manufacturer's claim, "can recognize transients (transient discriminate) over a wide dynamic range and generate harmonics on them"; the phrase is **not** in S2, which claims no dynamic-range property (re-confirmed by the critic pass: "dynamic range" does not occur in EP 0 629 039 B1) | low — a manufacturer's claim, not a measurement, and no unit was measured | The two ratios differing by more than 3 dB, or the −30 dBFS burst showing under 6 dB of emphasis — a plain threshold rather than a moving bias | T5's measurement at two levels |
| T7 | both | **No audible alias products**: with Tune at 5 kHz and a 6 kHz sine at −6 dBFS, every non-harmonic component is below −60 dB of the fundamental at 48 kHz and at 44.1 kHz. | S4 (aliasing of distortion components above Nyquist into the baseband); the arithmetic — h5 of a 6 kHz tone is 30 kHz, which folds to 18 kHz at 48 kHz and to 14.1 kHz at 44.1 kHz | high on the mechanism; **the −60 dB floor is our engineering bar**, not a figure S4 or any source states | Any inharmonic component at or above −60 dB. A memoryless curve run at 1× fails it — that is why §5 asks for oversampling, and the 1× build is the planted fault | STFT of the sine probe and of a 3–9 kHz sweep; alias floor reported per rate |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Attempted and failed, therefore not evidence.** Nothing from any of these is
cited, search-engine summaries included. Shekar & Smith, "Modeling the Harmonic
Exciter", AES 135th Convention e-brief 104 (2013) — the AES e-library is gated
and `https://www.aes.org/e-lib/online/browse.cfm?elib=9130` returns **HTTP 404**;
Semantic Scholar returned an empty page to the fetch tool. Chalupper, "Aural
Exciter and Loudness Maximizer" — `https://mediatum.ub.tum.de/doc/1138217/564026.pdf`
returns HTTP 200 but serves an Anubis "Making sure you're not a bot!"
interstitial in place of the PDF. ResearchGate copies of both: not usable.
**Nothing copyleft was consulted.**

*(from §3)*

**Latency: zero samples on the algorithm, 0.0 ms at 48 kHz.** A high-pass, a
memoryless clipper and a sum look ahead by nothing; S1's phase shift is a
*filter's* phase, not a delay, and the dry path is a wire. The one option that
can add latency is §5's oversampled waveshaper, whose up- and down-sampling
filters have real group delay: the node must report its own number, the class
must add it into `latency_samples`, and the default factor is the smallest that
meets T7's −60 dB floor — **2×**. `tail_samples` is one biquad's settling time.

*(from §4)*

**The ported node's OVERDRIVE curve already satisfies T2 and T3** — the central
finding here. Measured (App. A; the curve is `audioif_distortion.c:22-29`,
its body `:23-27` — **corrected 2026-09-06, the earlier `:21-28` pointed at the
`LOFI` case's `break`**): at −1 dBFS h2 = −26.1 dB and h3 = −21.0 dB, five
decibels apart, so both orders are present and the curve is asymmetric, exactly
S1's one-sided clip; and h2/h1 climbs 30 dB as the input rises 39 dB. Both
figures reproduced to 0.05 dB by the palette verification (App. G). Two
neighbours in the same node are free controls that must **fail**: `WAVESHAPE`
puts h2 at the numerical floor (odd-only, fails T2) and `CLIP` pins h3/h1 at
−16.9 dB at all six probe levels (fails T3) — **the CLIP figure holds with
`soft_clip=False`**, which is the bare curve; with the `soft_clip=True` the
class itself uses, the re-probe reads h3/h1 drifting −16.6 → −14.1 dB over
−40 … −1 dBFS. Either way the control fails T3's 20 dB bar by an order, but the
planted fault must state which it swapped in.

*(from §4)*

**Harmonics has to ride `pre_gain`, because `drive` does nothing here.**
`audiofilters.Distortion` ignores `drive` in OVERDRIVE
(`audioif/docs/upstream-diff.md:1228`), so the knob uses the `_push` pattern
already in the module (`drive.py:39-49`): `pre_gain` in, matching `post_gain`
out, so it buys harmonics rather than volume — which is what makes T3
measurable from the panel rather than from the source level.

*(from §4)*

**What this paragraph claimed the palette cannot reach — T5, T6 and T7 — it
can.** Corrected 2026-09-06 by the palette verification (App. G); §5 carries
the refutations and what is left of the asks. What stays true is the **price**:
the OVERDRIVE branch costs **four** `exp` and a `sqrt` in double per sample
(`audioif_distortion.c:24`, `:25`, and two at `:27`), and a **fifth** `exp`
when `soft_clip` is on (`:37`) — the earlier "three, plus a fourth" undercounted
by one, and `:23-26` did not span the calls. That is the wrong cost on a
microcontroller, and it is a Tier 3 argument, not a reachability one.

*(from §4)*

**Portability and mono.** Tier **audioif** (`audioroute.Splitter`,
`audioif_splitter.h:21` — `AUDIOIF_SPLITTER_MAX_TAPS 4u`). Everything is
per-channel: a mono source gets the mono form of the same effect, and the class
is not stereo by definition. Coefficient *choices* — mode, frequency, Q, A —
are computed in Python and shipped as data; the RBJ coefficients themselves are
derived from them **in C**, by `audioif_biquad_configure_w0`
(`audioif/src/shared/audioif_biquad.c:70`), which is deterministic on every
target because it uses this port's own sin/cos (`audioif_trig.c`) and an
adaptive fixed-point scale rather than libm's transcendentals. `synthio.Biquad` has no
raw-coefficient constructor: it takes `mode`, `frequency`, `Q`, `A` and nothing
else (`audioif/src/synthio/Biquad.c:148-152`). Nothing is rebuilt on a board
that would differ from what CPython built.

*(from §4)*

**One trap the Tier 1 byte-compare will hit.** `audioroute.Splitter` holds an
8192-frame ring (`audioif_splitter.h:20`). Fed a `RawSample` that hands over
its whole buffer in one call — as a probe file longer than 8192 frames does —
the ring wraps before the tap is ever read and tap 0 begins at source frame
(length − 8192): measured here, a 48 000-frame source came back starting at
frame 39808, exactly. Fed the same signal through a node that emits in blocks,
tap 0 is byte-identical from frame 0. The dry-path byte-compare must drive the
class the way the graph does, or it will read a shift as a defect.

*(from §5)*

**REFUTED BY PALETTE.** The palette can oversample, using nodes already in it.
`audiospeed.SpeedChanger(rate=1/M)` stretches the stream by M with a
zero-order hold (a 16.16 phase accumulator, no interpolation —
`audioif/src/audiospeed/SpeedChanger.c:160`, `:176`), an
`audiofilters.Filter` cascade removes the hold's images, the distortion runs on
M× as many samples, a second cascade removes what would fold, and
`SpeedChanger(rate=M)` decimates back. Frequencies scale with the stretch, so
an internal corner designed at 0.90 × (fs/2M) sits just under the original
Nyquist. Built and measured here (App. G), 5.5 kHz at −6 dBFS into
`OVERDRIVE`: the worst **non-harmonic** product goes from **−39.4 dB** at 1× to
**−69.1 dB** on the composed 2× path and **−86.8 dB** at 4×. T7's floor is
−60 dB; the composed 2× path clears it by 9 dB, and adds **zero algorithmic
latency** (`SpeedChanger` has no lookahead; the cascades contribute
group delay, not latency). Both `SpeedChanger`s are CircuitPython ports and are
composed, never modified.

*(from §5)*

*What survives, and it is not a trait ask.* The node would still buy two things
this compose does not: an **arbitrary curve** (the drive dossiers' need, not
this class's — `Overdrive`, `Distortion` and `Fuzz` each want their own diode
law, and `OVERDRIVE`'s is a fixed shape that ignores `drive`), and **cost** —
the compose pays four `exp` and a `sqrt` per sample *times M*, plus 32 biquad
passes per output frame per channel for the two cascades. Those belong in Tier 3
and in the drive dossiers' asks. **Exciter no longer asks for E1 on T7's
account.**

*(from §5)*

*One thing T7 itself needs fixing for, noted for §8 and the kit.* At 48 kHz a
6 kHz probe is a submultiple of the rate, so **every** alias of a harmonic of
6 kHz folds onto a multiple of 6 kHz — h5 at 30 kHz lands on 18 kHz, which *is*
h3. T7 as written ("every non-harmonic component below −60 dB") is therefore
vacuous at 48 kHz on its own probe frequency, and the numbers above use 5.5 kHz
for that reason. The trait's probe frequency has to be one whose folded
harmonics are inharmonic; that is a §3 repair for Station A, not a node ask.

*(from §5)*

**REFUTED BY PALETTE for both, with one clause left over.**
`audiodynamics.Dynamics` in `DYN_TRANSIENT` mode, placed **ahead of** the
clipper rather than after it, is a differential-envelope gain: fast envelope
minus slow envelope in dB, normalised by 6 dB, driving `attack_gain_db` on the
rising side and `sustain_gain_db` on the falling one
(`audioif/src/shared/audioif_dynamics.c:285-300`). Because it is a *ratio* of
two envelopes it is level-independent by construction, and because it sits
before the nonlinearity it changes the drive into the clipper, which is what
generates the harmonics — not, as this seed first argued, only the harmonics
already generated. Measured (App. G), a constant 5 kHz burst,
`attack_gain_db=+12` and `sustain_gain_db=−12`: h2+h3's onset emphasis over the
burst's steady state is **8.9 / 8.2 / 9.0 dB** at −30 / −18 / −6 dBFS. T5's bar
is ≥6 dB — met at every level. T6's bar is ≤3 dB of spread across that range —
measured **0.8 dB**. A `DYN_COMPRESS` stage in the same place produces the shape
too (7.9 dB at `attack_ms` 8) but fails T6 outright, spreading 11.5 dB over the
same levels, which is the control that tells the two mechanisms apart.

*(from §5)*

*What survives, re-cut and much smaller.* T5 also fixes a **time constant**:
"reaches within 1 dB of the steady state in τ ± 25 %, at τ = 8, 20 and 150 ms",
and `DYN_TRANSIENT`'s four envelope coefficients are **hard-coded** — fast
attack 1 ms, fast release 50 ms, slow attack 25 ms, slow release 300 ms
(`audioif/src/shared/audioif_dynamics.c:215-221`). Measured decay to within
1 dB of steady: **≈135 ms**, fixed, whatever the panel says. So §6's Transient
Time macro (5–200 ms) cannot be honoured today.

*(from §5)*

- **Shape:** expose those four coefficients as `Dynamics` options
  (`transient_fast_attack_ms`, `transient_fast_release_ms`,
  `transient_slow_attack_ms`, `transient_slow_release_ms`), defaulting to
  today's 1 / 50 / 25 / 300 so nothing already built moves. `audiodynamics` is
  **audioif's own** node (from micropython-vst3), so this is additive under D1
  and touches no CircuitPython port — a far smaller ask than a bias input on a
  waveshaper, and one `TransientShaper` and `Compressor` will want too.

*(from §5)*

- **If it is declined:** the class ships `transient` with a fixed ≈135 ms
  character, Transient Time becomes a two-position toggle or disappears, and
  T5's τ clause is recorded as **disconfirmed with cause** rather than dropped.

*(from §5)*

*The refutation record this replaces.* The earlier text said the palette offers
"nothing" on three grounds — `audiomath.Multiply` is ring modulation
(`audioif/docs/upstream-diff.md:714`); neither `audioif_envelope.h` (a synth
ADSR state machine, `:15-37`) nor `audiodynamics` *exports* a follower; a
Python-side follower would step at block rate. All three are true and none is
the point: `Dynamics` need not export an envelope to use one. It applies it to
the audio, and the audio is the clipper's drive.

*(from §7)*

2. **The Harmonics control does not exist.** The sidechain drives the curve at
   whatever level the high-passed signal happens to arrive at
   (`drive.py:256-260`) and the class's own comment says why — "No drive
   argument: OVERDRIVE ignores it" — while `_push` (`drive.py:39-49`), which
   solves exactly this in the same module, goes unused.

*(from §7)*

6. **The mixer runs a different buffer size from the rest of the chain** —
   `_core.pcm(1024)` at `drive.py:261` against the 2048-byte default
   (`_core.py:64`). Not shown to be wrong; shown to be unexplained.
