# Effects Dossier — `Notch` (no historical standout — design grade)

**Class:** `lib/audioeffects/rebuilt/notch.py`. The old
`lib/audioeffects/eq.py` implementation is read once, for §7, and not
otherwise consulted.
**Family / phase:** EQ / Filter, roadmap Phase 2
**Standout:** none, per vision §4.2 — **confirmed** (§2).
**Grade:** design
**Portability tier:** **audioif** — `REQUIRES = ("audiobiquad",)`, §8 D1.
**Status:** traits frozen; Station A settled 2026-09-07 (§8, A16)

## 1. The circuit, in one paragraph

The referent is the two-pole band-stop: the Twin-T's job done with a
resonator. Zavalishin gets it from the state-variable core by subtracting the
normalised band-pass from the input, `H_N(s) = 1 − H_BP1(s) = (s² + 1)/(s² +
2R·s + 1)` (S4 §4.7 p. 119), which is the whole design in one line — a notch
*is* "everything except the band", and its two controls are therefore the
band's: **centre frequency** f₀ and **width**, with the −3 dB points
separated by exactly f₀/Q (S3; S1 states the bandwidth is measured *"between
−3 dB frequencies for BPF and notch"*). There is no nonlinearity. Digitised,
the numerator is `1, −2cos ω₀, 1` (S1, verbatim) — a conjugate pair of zeros
exactly on the unit circle at ±ω₀, so the rejection at the centre is not deep
but **total**, and the numerator's coefficients sum to the same value as the
denominator's at both `z = 1` and `z = −1`, so the filter is exactly unity at
DC and at Nyquist. That last property is what makes a notch usable on a full
mix: it removes a whistle, a hum harmonic or a feedback tone and changes the
level of nothing else. The same identity gives the class its most useful
structural fact — **notch + band-pass = 1 exactly**, since RBJ's two
numerators `(1, −2c, 1)` and `(α, 0, −α)` sum to the shared denominator
`(1+α, −2c, 1−α)` — which is the split `DynamicEQ` is built on.

*Total* is the paper's word and it survives a `double`, not a `float`: §8 D2
measures 35 dB at the mains-hum setting rather than ∞. That is arithmetic,
measured before a line of the class was written; the circuit is unchanged.

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** RBJ, *Cookbook formulae for audio EQ biquad filter coefficients* (App. S) | the notch and BPF coefficient blocks, which give the sum identity (App. S) | licence unverified, treated as copyleft (App. S) | https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* — "Quality Factor (Q)" (App. S) | *"Q … resonance frequency divided by the resonator bandwidth"* (App. S) | © CCRMA Stanford, no grant. Read as a paper (App. S) | https://ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html | 2026-09-06 |
| **S4** Zavalishin, *The Art of VA Filter Design* rev. 2.1.0 (App. S) | `H_N(s) = 1 − H_BP1(s) = (s²+1)/(s²+2Rs+1)`, §4.7 p. 119; fig. 4.22 p. 120 (App. S) | verbatim-copy-only, no derivatives (A0). Read as a paper (App. S) | https://www.discodsp.net/VAFilterDesign_2.1.0.pdf | 2026-09-06 |

Every S1 formula was cross-checked against the W3C/WebAudio rendering; all
three licences were re-read at their own sources twice more (A10, A11). What
was looked for and not found, the struck "30–50 dB" Twin-T figure and the
struck Boss/Maestro attribution are in **App. R**.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

**Frozen.** No row was added, dropped, renumbered or re-thresholded at
Station A, and the first line of the class was written afterwards. Where
A16's runs refute a row the row stands and the evidence pack records it
*disconfirmed with its cause* — never a moved bar.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **Total rejection at the centre**: the zeros sit exactly on the unit circle, so a sine at f₀ **whose period is a whole number of samples at the running rate** renders bit-exact digital zero; and a sine 0.05 % away reads −53.96 dB at Q 2, ± 0.5 dB, which is the closed form, not a floor. The commensurability clause is not a hedge: at 44.1 kHz and 22.05 kHz a 1 kHz probe has 44.1 and 22.05 samples per cycle and the same filter reads −89.5 and −87.2 dB — **the source's own quantisation floor, not the filter** (A4) | S1 (notch numerator), verified analytically … (App. T1) | high | a commensurate sine exactly at f₀ producing any non-zero sample after settling; or the f₀·1.0005 reading outside −53.96 ± 0.5 dB at Q 2 | a fixed sine exactly at f₀ … (App. T1) |
| T2 | **Unity outside the band**: 0.00 ± 0.1 dB at DC and at 0.48·F_s, at every f₀ and Q — a notch changes the level of nothing but its own band | S1 (numerator and denominator sum alike at `z … (App. T2) | high | a gain at DC or 0.48·F_s outside ±0.1 dB for any Q in 0.5…32 | DC step settled value … (App. T2) |
| T3 | **Width is f₀/Q**: the −3 dB points sit at `f₀·(√(1+1/4Q²) ∓ 1/2Q)`, difference exactly f₀/Q — at f₀ 1 kHz, Q 2 that is 780.8 and 1280.8 Hz | S3, S1; measured −3.00 dB at both predicted … (App. T3) | high | either predicted edge outside −3.0 ± 0.15 dB for any Q in 0.5…32 | swept sine, the two −3 dB … (App. T3) |
| T4 | **Notch + band-pass = 1, exactly**: the two RBJ numerators sum to the shared denominator, so summing this class's output with a band-pass of the same f₀ and Q reconstructs the input to within 0.05 dB from 20 Hz to 0.4·F_s | S1 (both numerator blocks) … (App. T4) | high | a reconstruction error above 0.05 dB anywhere in 20 Hz … 0.4·F_s with both sections at the same f₀ and Q | the two branches summed … (App. T4) |
| T5 | **Depth is not a knob — and every off-centre "depth" reading is a width reading in disguise**: the zeros sit on the unit circle at every Q, so the rejection at f₀ is total for all Q in 0.5…32 (T1's commensurate probe reads bit-exact zero at each). What a probe *beside* f₀ reads moves with Q, and moves a long way: at f₀·1.0005 the closed form gives −66.00 dB at Q 0.5, −53.96 at Q 2, −41.92 at Q 8 and −29.88 at Q 32 — a **36 dB spread on one fixed probe**. So a depth control is a *mix* control, not a filter control, and a minimum-of-the-sweep comparison across Q measures the sweep's grid, not the notch | S4 fig. 4.22, p. 120 … (App. T5) | high | any Q in 0.5…32 whose commensurate on-centre probe does not read bit-exact zero; or any of the four f₀·1.0005 readings more than 0.5 dB from its own closed-form value | T1's on-centre commensurate probe … (App. T5) |
| T6 | **Rate-honest — against the closed form at the running rate**: at 44.1 kHz and 22.05 kHz the centre stays at f₀ within 0.1 %, T2's unity and T3's f₀/Q edges hold to their own tolerances, and the rendered response matches S1's closed form **evaluated at the running rate** within 0.1 dB up to 0.45·F_s. T1's *bit-exact* clause carries over only for a probe commensurate with the new rate; on an incommensurate probe the reading is the source's quantisation floor (−89.5 dB at 44.1 kHz, −87.2 at 22.05, A4), which is a probe fact and disconfirms nothing. Cross-rate, the same f₀ curve deviates ≤ 0.006 dB at 44.1 kHz and ≤ 0.112 dB at 22.05 kHz for f₀ ≤ 1 kHz, rising to 0.409 dB at f₀ = 2 kHz — which is why the requirement is the closed form at each rate, not the 48 kHz curve | S1 (the BLT prewarps f₀ at whatever rate is running) … (App. T6) | high | centre displaced >0.1 %, T2 or T3 outside its own tolerance at either rate, or any swept point more than 0.1 dB from the closed form **at that rate** | the T1–T3 measurements at 48 000 … (App. T6) |

No characters: a notch has one behaviour.

### Tier 3 — cost and latency

**Latency budget: 0 samples, 0.000 ms**, at every rate and every setting.
Nothing in this class looks ahead; no option it offers adds a lookahead, a
partition or a window, so there is no latency-adding option to default off
and none to name in milliseconds (A8, re-measured on the rebuild in the
evidence pack).

**Cost budget**, as a fraction of one stereo block's real-time deadline:
**ESP32-P4 ≤ 1.5 %, ESP32-S3 ≤ 5 %** for the one-notch default;
**≤ 2.5 % / ≤ 9 %** with the harmonic notch engaged. Lean patch expected:
**no**. The basis is in **App. R**. *Station C found the split unmeetable
half at a time*: all three sections are built at every setting and the kernel
runs each recursion before it blends, with no branch on `mix`
(`audioif/src/shared/audioif_filter_f32.c:216-241`), so one notch costs what
two cost and the higher pair is the pair that governs
([`Notch-evidence.md`](Notch-evidence.md) §4). The budget is not rewritten
here — the board run is what settles it.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Three `audiobiquad.Biquad` sections in series, and nothing else.** All
three are the same node over `shared/audioif_filter_f32.c` — `double`
coefficient algebra stored as `float`, `float` state, any state word below
1e-20 written as exact zero (`audioif/docs/upstream-diff.md:1953`), which is
why the tier moved (§8 D1). `frequency`, `Q`, `gain_db` and `mix` are live
slots read once per chunk, so a macro move is a float store.

| Section | Mode | What it is | Patch 0 |
|---|---|---|---|
| 1 | `NOTCH` | the fundamental: `b0 = 1, b1 = −2cos ω₀, b2 = 1` over the shared denominator | active |
| 2 | `NOTCH` | the harmonic notch at 2f₀, Q doubled so its width in **hertz** matches the fundamental's (§8 D3) | wire |
| 3 | `HIGH_SHELF` @ 5 Hz | the make-up trim; a subsonic shelf is the palette's only route to gain above unity | wire |

At `mix = 0` the kernel writes `to_s16(x0)` — the input sample unchanged
(`audioif/src/shared/audioif_filter_f32.c:239`) — so an unused section costs
a pass and changes no byte, and **Depth 0 is a byte-exact wire with all three
sections still in the chain**. Depth *is* the fundamental's `mix`, and the
gain at f₀ is `1 − mix` (A13).

**The A9 cascade-mix hazard does not reach this class**: it is
`audiofilters.Filter`'s (`Filter.c:234`), and this class builds no `Filter`.
`audiobiquad`'s `mix` is per-section and the same C on all three
interpreters, so the seed's `(0, 0.01]` snap goes with the node it was for
(§8 D4).

*(The seed's stock-palette version of this section, its struck stock-board
claim, and the mono reading are in **App. R** — moved under the length rule,
nothing deleted.)*

## 5. Node asks

**One, new at Station A.** Every Tier 2 trait's *shape* is reachable on the
Phase 1 palette and §4 shows how; T1's **depth** at low f₀ is not, and the
ask is arithmetic rather than a feature:

> **A `NOTCH` whose numerator is derived from the stored denominator rather
> than rounded beside it.** The centre's rejection is
> `|2b₀·cos ω₀ + b₁|·(1+α)/(2α·sin ω₀)`, and `b₀` and `b₁` are rounded to
> `float` independently, so the cancellation at ω₀ survives only while
> `2α·sin ω₀` is large. Measured from the shipped coefficients (A16): `NOTCH`
> reads −10.98 dB at 20 Hz Q 32 and −35.54 at 60 Hz Q 12, while the
> **`BAND_PASS` mode's own** `|1 − H(f₀)|` reads −47.25 and −45.83 — 17 to
> 36 dB better from the same kernel, because its `b₂ = −b₀` is exact where
> the notch's `b₁ = −2c·b₀` is not. **Trait it serves: T1.** Filed as an
> audioif issue reminder in the evidence pack's §11.

Two builds of the same identity were weighed and not taken, both in
**App. R**: a parallel `Splitter → BAND_PASS → inverter → Mixer` (four extra
nodes and an int16 sum on the dry path, which T2 and LEVEL are stated
against), and a four-pole cascade of two notch sections (which would double
the rejection in dB and **disconfirm T4 by construction**).

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Surface — frozen at Station A

Five macros, inside the sixteen the contract allows; the spans are the
seed's own, unchanged.

| # | Label | Mode | Span (`_MACRO_RANGES`) | Generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 20 … 16 000 Hz, log; clamped at run time to 0.4·F_s (§8 D5) | the tuning knob |
| 1 | Width | UNIPOLAR | Q 0.5 … 32, log; displayed as the bandwidth f₀/Q | the Q / bandwidth knob |
| 2 | Harmonics | TOGGLE | 0 = one notch (default), 1 = two, at f₀ and 2f₀ | a hum eliminator's harmonic switch |
| 3 | Depth | UNIPOLAR | 0 exactly … 1 — the section's own `mix`; 0 is a wire | the depth control T5 says must be a mix and not a Q |
| 4 | Trim | BIPOLAR | −12 … +12 dB, default 0; under 0.2 dB the section is a wire | output make-up |

`capabilities = ()` (§8 D7). Depth doubles as Tier 1's wire test: at 0 the
class is byte-identical to its source with all three sections in the chain.

**Patches**, named for settings and never for products; the grid is
`macro_of()` of the setting beside it, so patch 0 is the constructor's own
defaults to within a step.

| # | Name | Setting | Grid |
|---|---|---|---|
| 0 | Wide Notch | 983 Hz, Q 0.72, one notch, depth 1, trim 0 | `(74, 11, 0, 127, 64)` |
| 1 | Hum 50 | 48.9 Hz, Q 11.98, two notches | `(17, 97, 127, 127, 64)` |
| 2 | Hum 60 | 60.4 Hz, Q 11.98, two notches | `(21, 97, 127, 127, 64)` |
| 3 | Feedback Tamer | 2535 Hz, Q 23.8, one notch | `(92, 118, 0, 127, 64)` |
| 4 | Mud Scoop | 293 Hz, Q 1.21, one notch, depth 0.60 | `(51, 27, 0, 76, 64)` |
| 5 | Whistle Kill | 8072 Hz, Q 30.0, one notch | `(114, 125, 0, 127, 64)` |

The setting column is what the grid actually stands for, not what was asked
for: a 7-bit step on a log span from 20 Hz to 16 kHz is 5.4 %, so patch 0's
"1 kHz" lands on 983.1 Hz and patch 2's "60 Hz" on 60.4. Trim 64/127 is
+0.09 dB, under the 0.2 dB floor, so the trim section is a wire in every
patch.

**`tail_samples` = 143 360** (2.99 s at 48 kHz) — a ceiling over the whole
span, because the contract reads one number off the class and not off the
current setting, so the seed's per-setting `ceil(4·Q·F_s/f₀)` is not
expressible. Measured worst case: 20 Hz Q 32, harmonic on, trim +12 dB,
full-scale burst — **140 405** samples after the source went silent (A16).
Loose by design everywhere else: patch 0's own tail is 88 samples.

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/eq.py`.

- **No surface at all.** `MACRO_LABELS = ()` (`eq.py:156`).
- **The width knob does not exist and cannot be made to exist.** `q` is a …  *(argument in full: App. R)*
- **No depth control.** `mix` is taken at `eq.py:101` and forwarded at
  `eq.py:105` and is then unreachable — so the shipped class is total
  rejection or nothing.
- **`set_frequency` is off-contract and it raises** — `_core.check_hz` raises
  at or above Nyquist (`_core.py:471-474`) instead of clamping, against the
  rate-honest invariant.
- **No tail is declared** (`TAIL_SAMPLES = None`, `_core.py:141`), although a
  notch's poles ring exactly as a band-pass's do.
- **Held DC at the hum setting** — §8 D1.
- **`reset()` reaches one node** (`_core.py:366-374`), and the `Filter` it
  reaches resets its source recursively, so the borrowed source *is* reset,
  which the contract forbids.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Decisions — every open settled at Station A, 2026-09-07

Nothing here is open. Each decision's run is in **A16**; none of them is a
number recalled from another class.

| # | Decision | Settled by |
|---|---|---|
| D1 | **Portability tier: audioif**, on `audiobiquad` — the seed's §5 Gate 0 item, answered. Every setting in this class's span reaches exact zero on it; on `synthio.Biquad` the mains-hum setting `Notch(60 Hz, q=8)` holds −2 LSB and `Notch(20 Hz, q=32)` −18 LSB, for ever. The cost is D2, stated and not hidden | A3, A16 |
| D2 | **T1's *total* rejection does not survive `float` coefficients at low f₀, and the class ships anyway.** On-centre, commensurate probe, level 6000, 48 kHz: **−35.65 dB at 60 Hz Q 12**, **−10.98 at 20 Hz Q 32**, under 1 LSB from 500 Hz up at Q ≤ 12. §5's law, read off the node's own `coefficients`, tracks every figure to 1.5 dB — arithmetic, not a build error. **T1 is recorded disconfirmed below ~250 Hz** | A16 |
| D3 | **Harmonics is two notches, and the harmonic's Q doubles so its width in hertz matches the fundamental's.** At 60 Hz Q 12: fundamental 5.00 Hz wide, shared Q gives 10.00 Hz at 120 Hz, doubled Q gives 5.00 — and mains harmonics are exact multiples. Not three or four (§6 froze a TOGGLE; the S3 cost of two more always-built sections is unmeasured). Above Q 30 the doubled Q hits `MAX_Q` 60 and the harmonic is up to 6.7 % wider | A16 |
| D4 | **The seed's `(0, 0.01]` Depth snap is dropped** with the node it was for: `Filter.c:234` carries that threshold, `audiobiquad` does not, and both desktop targets run the same C kernel | A9, A16 |
| D5 | **Frequency spans a fixed 20 Hz … 16 kHz, log, clamped live to `min(16 kHz, 0.4·F_s)`** — the seed's own span. `_MACRO_RANGES` is a class attribute and cannot know the rate. 0.4·F_s and not `_hz()`'s 0.49·F_s, because a notch centred higher has its *own band* over T2's 0.48·F_s probe | A16 |
| D6 | **`tail_samples` = 143 360**, the measured worst corner rounded to the next multiple of 2048 (§6) | A16 |
| D7 | **`capabilities = ()`.** Nothing in a notch is measured in beats — its controls are hertz and a dimensionless Q — and the class never reads `self._transport()` | — |
| D8 | **No all-pass character** (the seed's open 3): `Phaser` owns the all-pass and the `NAME` set is frozen. Considered, not taken, unchanged | seed §8.3 |
| D9 | **The seed's stock-board claim is struck.** Neither cited line says the Q15 numerator turns T1's rejection into a shallow dip (`biquad-band-edges.md:140-150` is a `LOW_PASS`/`HIGH_PASS` table), and measured, the ported kernel is 40 dB **deeper** there (D2). A stock CircuitPython 10.2.1 board is a third thing no interpreter here runs (`upstream-diff.md:1215-1229`). Old text kept in **App. R** with the strike beside it | A16 |

---

## Appendix

Run 2026-09-06 on this machine. CPython target:
`audiocomponents/.venv/bin/python`. MicroPython: `cmods/bin/micropython` with
`MICROPYPATH=audiocomponents:audiocomponents/lib`. Probes were scratch
scripts, not committed. A0, A3, A5, A7 and A9 share their runs with
`LowPass.md`.

### A0. The Zavalishin license, verbatim

*"© Vadim Zavalishin. The right is hereby granted to freely copy this
revision of the book in software or hard-copy form, as long as the book is
copied in its full entirety (including this copyright note) and its contents
are not modified."* Verbatim-copy-only, no derivatives — a paper for our
purposes. `pypdf` extracted the text the fetch tool could not.

### A1. Magnitude response against the closed form (48 kHz, stereo, level 6000, `mix=1`)

```
  no f0= 1000.0 Q=2.000 probe=   500.0  measured   -0.458 dB  ideal   -0.456 dB  dev  -0.002 dB
  no f0= 1000.0 Q=2.000 probe=  1000.0  measured -180.000 dB  ideal -180.000 dB  dev  +0.000 dB
  no f0= 1000.0 Q=2.000 probe=  2000.0  measured   -0.452 dB  ideal   -0.451 dB  dev  -0.000 dB
```

### A2. Depth, width, and the probe that lies about depth

Depth against how far the probe sits from the centre (f₀ 1 kHz, Q 2):

```
  probe  1000.00 Hz ->  -240.00 dB      (the measurement floor: output is bit-exactly zero)
  probe  1000.50 Hz ->   -53.95 dB
  probe   997.30 Hz ->   -39.30 dB
```

**A sine exactly at f₀ that also has an integer number of samples per cycle
reads a fake −240 dB**, because the zero pair annihilates it exactly and the
output is literally zero — which is true, and tells you nothing about how the
notch behaves on real material. T1's measurement therefore needs *both*
probes, and the swept-sine minimum is the honest headline. That is also T1's
planted fault: move the zeros off the unit circle (multiply `b1` by 1.001)
and the exact-f₀ probe must stop reading zero.

−3 dB edges at the closed-form positions:

```
  Q=2.000 edges   780.78/ 1280.78  measured -2.999 / -2.994 dB
  Q=8.000 edges   939.45/ 1064.45  measured -2.998 / -2.997 dB
```

T4's identity, measured through the shipped `DynamicEQ` (which is exactly
`notch(f₀,Q) + bandpass(f₀,Q)` summed, with its compressor idle), f₀ 3 kHz,
Q 2:

```
     500.0 Hz  reconstruction gain  -0.010 dB
    1500.0 Hz  reconstruction gain  -0.000 dB
    3000.0 Hz  reconstruction gain  +0.000 dB
    6000.0 Hz  reconstruction gain  -0.001 dB
   12000.0 Hz  reconstruction gain  +0.000 dB
```

and an impulse through the same split comes out at its input peak (20 000 in,
20 000 out). T4's planted fault: detune one branch by 1 % and the
reconstruction must break by more than 0.05 dB near f₀ (it breaks by ≈ 0.4 dB).

### A3. Held DC after silence, and the probe design that hid it

The first version of this probe pulled a few blocks past the end of the
`RawSample`. When a `Filter`'s source is exhausted, `Filter.c:202-223` takes
the `sample == NULL` branch and **memsets the output to zero without running
the biquads at all** — every configuration read exactly 0 and the defect
looked absent. Corrected by staying strictly inside a source still supplying
digital silence (0.09 s of 440 Hz at 12 000, then 3.0 s of zeros; 287 of 289
available blocks). That correction is the planted fault: two blocks longer
and it goes green on a filter still holding DC. CPython and MicroPython
agreed on every row: `Notch(60 Hz, q=8)` −2 LSB held, `Notch()` 0,
`LowPass(100 Hz)` −1, `LowPass(40 Hz, q=8)` −4, `HighPass(30 Hz)` −8,
`BandPass(80 Hz, q=4)` −1, all four classes at their 1 kHz defaults 0,
`CombFilter` and `DynamicEQ` 0.

**Reading it.** Of Gate 0's three candidates, a *block-rate tail gate in
Python* cannot see the residual — it lives in the biquad's sub-sample state
(`audioif_biquad.h:14`) — so it would have to zero the output on a silence
heuristic and would clip quiet material; recommended against. A *DC-clean
biquad in an audioif-own module*, decided once with the per-sample phaser
question, is what this seed recommends. A *recorded disconfirmation* is
honest and leaves DC in every rest at low centres.

### A4–A7. Mono, rates, DC/Nyquist, cost

Mono notch at f₀ 1 kHz Q 2: −0.455 / −180.00 / −0.451 dB at 500 / 1000 /
2000 Hz, matching the closed form to 0.001 dB. At 44.1 kHz and 22.05 kHz the
centre reads −89.5 dB and −87.2 dB rather than −240 — **the source's own
quantisation floor**, because 1 kHz is not commensurate with those rates;
the filter is unchanged. DC and Nyquist, f₀ 1 kHz Q 0.707: `NOTCH @10 Hz
+0.07 dB, @23 000 Hz +0.00 dB`; the `+0.07` is the reference, not the filter
(a 10 Hz int16 sine's true RMS differs from `level/√2` by about that much),
so the kit must compute its reference from the rendered source. Cost:
146.6 ns per stereo frame for one section, 195.1 ns for four, against
20 833 ns of real time per frame.

### A8. Latency

Impulse at frame 50 through `Notch()`: first non-zero output at frame **50**,
peak 18 310 of 20 000; `latency_samples` reports **0**. Agreed.

### A9. `mix` cross-target divergence

```
             CPython   MicroPython
  mix=0.0          0             0
  mix=0.005       80             0
  mix=0.01       159             0
  mix=0.02       317           317
```

`Filter.c:234` bypasses the cascade when `mix <= 0.01`; the CPython target
(`src/cpython/_audioif.c:605-613` via `src/cpython/audiofilters.py:137-147`)
has no such threshold. The Depth macro (§6) must therefore snap anything in
`(0, 0.01]` to 0.

### A10. Licence and citation audit, 2026-09-06

This seed's §2 carries the corrections themselves; this is the full
re-verification record behind them. Every source row in §2 and every URL
anywhere in this seed was re-fetched by a second agent that read none of the
first run's notes. Corrections applied in place: **S1's licence call** now
records the repository's root `LICENSE.md` (full CC BY 4.0), which the first
draft did not mention — downgraded to *licence unverified, treated as
copyleft*, because that grant is the mirror's and the chain to RBJ is unshown;
treatment unchanged. **The Twin-T's "30–50 dB" rejection figure is struck as
unsourced** — no Twin-T schematic, datasheet or measurement was reached in
either run, and a number from memory is not evidence. Fig. 4.22's page (120)
added; the `H_N = 1 − H_BP1 = (s²+1)/(s²+2Rs+1)` line at §4.7 p. 119 is
verbatim and stands, as does the K = −2 allpass in §8.
Re-verified exactly as the seed states them: RBJ's coefficient blocks and the
`α`/`w0` definitions in the `.txt`; the CCRMA pages' *"Copyright © … Julius O.
Smith III / CCRMA, Stanford University"* with **no** licence grant anywhere on
them; Zavalishin's front-matter grant (A0, verbatim, p. ii of rev. 2.1.0);
musicdsp.org's RBJ page carrying no licence, copyright or terms text at all;
native-instruments.com's copy of the book **404** (still not reached); and the
archive.org item `the-art-of-va-filter-design-rev.-2.1.2` carrying **no**
`licenseurl` and no `rights` field (metadata API, per the sources module).

The Twin-T's remaining attributes (depth set by resistor matching, a Q that
degrades when tuned) are likewise unsourced general knowledge, carried for the
scope argument only; nothing in §3 rests on them.

### A11. Second licence and citation audit, 2026-09-06 (the re-fetch pass)

**Second licence-and-citation audit, 2026-09-06** — a third pass, run
independently of the first audit, in which **every URL in this seed was
re-fetched in this run** and every licence read again at its own source. What
came back, so the calls above rest on this run and not on a prior one:

- `raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt`
  — reached; the file carries **no** occurrence of *license*, *licence*,
  *copyright*, *(c)*, *warranty* or *public domain*.
- `…/master/LICENSE.md` — reached; it is the full **Creative Commons
  Attribution 4.0 International Public License** text.
- `api.github.com/repos/shepazu/Audio-EQ-Cookbook` — reached; `license.key`
  `"other"`, `license.name` `"Other"`, `license.spdx_id` **`"NOASSERTION"`**.
- `webaudio.github.io/Audio-EQ-Cookbook/audio-eq-cookbook.html` — reached;
  the only rights language is *"Adapted from Audio-EQ-Cookbook.txt, by Robert
  Bristow-Johnson, with permission"* and *"Special thanks to Robert
  Bristow-Johnson for creating the Audio EQ Cookbook and permitting its
  adaption and use for the Web Audio API"*. The chain from the mirror to the
  author is still **not** shown, so the S1 call stands as *licence unverified,
  treated as copyleft*.
- `ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html` — reached; the
  definition is verbatim *"The quality factor (Q) of a resonator may be
  defined as the resonance frequency divided by the resonator bandwidth"*, and
  the page's only rights line is *"Copyright © 2026-08-21 by Julius O. Smith
  III, Center for Computer Research in Music and Acoustics (CCRMA), Stanford
  University"* — no licence granted, so *read as a paper* stands.
- `www.discodsp.net/VAFilterDesign_2.1.0.pdf` — reached (4.9 MB, 520 pages,
  rev. 2.1.0 of 28 October 2018); WebFetch could not read it, `pypdf` could.
  The front matter (printed p. ii) carries the whole grant, verbatim:
  *"© Vadim Zavalishin. The right is hereby granted to freely copy this
  revision of the book in software or hard-copy form, as long as the book is
  copied in its full entirety (including this copyright note) and its contents
  are not modified."* Verbatim-copy-only, no derivatives — confirmed.
- Re-checked and still not reached: `musicdsp.org`'s RBJ page (reached, but
  carries no licence text at all); `native-instruments.com`'s
  `VAFilterDesign_2.1.0.pdf` (**HTTP 404**);
  `archive.org/metadata/the-art-of-va-filter-design-rev.-2.1.2` (reached; **no
  `licenseurl` field and no `rights` field**), which is why the discoDSP
  mirror's own grant is the licence actually read.

Every Zavalishin page number cited in this seed was checked against the
extracted text, page by page.

**One correction from this pass**, applied above: the dropped candidate's
naming of the **Boss and Maestro families** is struck as unsourced — no
schematic, manual or product page for either was reached in any run, and a
product attribution from memory is not evidence, exactly as the earlier pass
struck the "30–50 dB" figure. The general framing (a Twin-T as used in hum
eliminators and anti-feedback boxes) is kept, and the candidate is still
dropped on scope, not on any value. Both Zavalishin citations were opened in
the extracted text and are correct as printed: `H_N(s) = 1 − H_BP1(s) =
1 − 2R·H_BP(s) = (s²+1)/(s²+2Rs+1)` at §4.7 p. 119, and Fig. 4.22 on p. 120
(*"Amplitude response of a 2-pole notch filter. The amplitude scale is
linear."*, drawn for R = 0.2, R = 1 and R = 5 — which is what T5 rests on).
T2, T3 and T4 were re-derived from S1's own coefficients: −0.0000 dB at
23 kHz, −3.00/−2.99 dB at the two predicted edges at Q 2, and the notch plus
the band-pass summing to 1.000000 at 20 Hz, 100 Hz, 1 kHz, 5 kHz and 19 kHz.

### A12. Trait-critic pass, 2026-09-06 — the derivations behind T1, T5 and T6

Re-derivations from S1's own coefficients at 48 kHz in float64
(`audiocomponents/.venv/bin/python`, numpy 2.5.2). Arithmetic on the published
formulae, not a render.

**T5, and why its old disconfirmation was self-refuting.** Notch gain at a
*fixed* probe beside f₀ = 1 kHz, against Q:

| Q | at f₀ exactly | f₀·1.0005 | f₀·1.005 | f₀·1.01 |
|---|---|---|---|---|
| 0.5 | −∞ (exact zero) | −65.998 dB | −46.017 dB | −40.018 dB |
| 2 | −∞ | −53.957 | −33.978 | −27.984 |
| 8 | −∞ | −41.916 | −21.963 | −16.045 |
| 32 | −∞ | −29.879 | −10.317 | −5.380 |

The old row would have been failed by a correct filter: Q 32 reads 24.1 dB
above Q 2 on the same probe, four times its 6 dB band. The column that is
actually Q-invariant is the first one, and the seed's own A2 already showed
that column reads −240 dB (bit-exact zero) only when the probe is commensurate
with the rate.

**T1's detuned figure.** The measured −53.95 dB at 1000.5 Hz (A2) against a
closed form of −53.957 dB — agreement to 0.007 dB. The old wording's
≥ 45 dB claim and −40 dB disconfirmation both sat about 14 dB slacker than the
filter's own arithmetic, so a notch 13 dB shallower than the design would have
passed.

**T6, the cross-rate deviation.** Same f₀, compared against the 48 kHz
response over f ≤ 2205 Hz: 44.1 kHz ≤ 0.006 dB for f₀ ≤ 1 kHz and 0.020 dB at
2 kHz; 22.05 kHz 0.001 dB at 100 Hz, 0.007 at 250 Hz, 0.028 at 500 Hz, 0.112
at 1 kHz, 0.409 at 2 kHz.


### A13. Palette verification pass, 2026-09-07

Every §4/§5 claim about what an audioif node can and cannot do re-measured
independently; the run and its numbers are in `LowPass.md` A14, which covers
the whole simple-filter unit. What it changed here:

- **`NOTCH` against the closed form:** passband worst **−0.0004 dB**; at f₀
  the rendered output is bit-exact zero (DFT magnitude 0.0000, peak |y| 0) at
  1 kHz for Q 0.707 and Q 4. `audioif_biquad.c:85` reads as §4 quotes it.
- **T5's depth law measured, not assumed:** gain at f₀ is exactly `1 − mix` —
  mix 1.0 → bit-exact zero, 0.5 → −6.021 dB, 0.25 → −2.499 dB, 0.0 →
  +0.000 dB. §4 now carries the numbers.
- **A3's −2 LSB at `Notch(60 Hz, q=8)` reproduced**, same probe, same 287
  blocks; the same configuration also shows the residual as a peak |y| of 2 in
  the steady-state rejection probe, which is the DC hold and not the design.
  §5's number stands.
- **A new cross-target divergence**, recorded in §4, and it is worse here than
  anywhere else in the unit because Depth *is* `mix` and the harmonic option
  *is* a second cascade stage. Not in `audioif/docs/upstream-diff.md`; it needs
  an audioif issue.
- **The stock-CircuitPython citation was pointing at the wrong column** and is
  corrected in §4.
- **No node ask survives or arises here.** §5's "None" stands.

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

Two already carry Phase 0 measurements. **Byte-identity is green** except for
`mix` in `(0, 0.01]`, where `Filter.c:234` bypasses the cascade on
MicroPython while the CPython target blends (A9) — §6 keeps the macro out of
that band. **Exact zero after silence is red at low centres**:
`Notch(frequency=60.0, q=8.0)` — the mains-hum setting, the one a user is
most likely to reach for — holds −2 LSB for ever on both interpreters, while
the 1 kHz default reaches exact zero (A3). Routed to Gate 0, §5.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** RBJ, *Cookbook formulae for audio EQ biquad filter coefficients* (plain text, shepazu mirror) | the notch and BPF coefficient blocks (which give the sum identity), `α = sin(w0)/(2Q)`, and the bandwidth definition, verbatim | the `.txt` itself carries **no license, copyright or warranty line** (re-verified 2026-09-06, all five terms searched) — but the repository serving it does: its root `LICENSE.md` is the full **CC BY 4.0** text (read at https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/LICENSE.md; GitHub's own licence API reports the repo as `NOASSERTION`). That is the *mirror's* grant, not RBJ's: the mirror's HTML rendering says only *"Adapted from Audio-EQ-Cookbook.txt, by Robert Bristow-Johnson, with permission"*, so the chain to the author is **not** shown (sources module: a repackager's label is an assertion). **License unverified — treated as copyleft:** read as a document for its mathematics, never ported | https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* — "Quality Factor (Q)" | *"Q … resonance frequency divided by the resonator bandwidth"* | © J. O. Smith III / CCRMA Stanford; no license granted. Read as a paper | https://ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html | 2026-09-06 |
| **S4** Zavalishin, *The Art of VA Filter Design* rev. 2.1.0 (discoDSP mirror, text via `pypdf`) | `H_N(s) = 1 − H_BP1(s) = (s²+1)/(s²+2Rs+1)` (§4.7 p. 119) and the amplitude-response family for R = 0.2/1/5 (fig. 4.22, printed on p. 120) | verbatim-copy-only, no derivatives (grant quoted in A0). Read as a paper | https://www.discodsp.net/VAFilterDesign_2.1.0.pdf | 2026-09-06 |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **Total rejection at the centre**: the zeros sit exactly on the unit circle, so a sine at f₀ **whose period is a whole number of samples at the running rate** renders bit-exact digital zero; and a sine 0.05 % away reads −53.96 dB at Q 2, ± 0.5 dB, which is the closed form, not a floor. The commensurability clause is not a hedge: at 44.1 kHz and 22.05 kHz a 1 kHz probe has 44.1 and 22.05 samples per cycle and the same filter reads −89.5 and −87.2 dB — **the source's own quantisation floor, not the filter** (A4) | S1 (notch numerator), verified analytically; measured −240 dB on-centre and −53.95 dB at f₀·1.0005 (A2), against a closed form of −53.957 dB re-derived in A12 | high | a commensurate sine exactly at f₀ producing any non-zero sample after settling; or the f₀·1.0005 reading outside −53.96 ± 0.5 dB at Q 2 | a fixed sine exactly at f₀, chosen commensurate with the rate, **and** one at f₀·1.0005, and the swept-sine minimum — all three are needed, and the swept minimum is the honest headline (A2) |
| T2 | **Unity outside the band**: 0.00 ± 0.1 dB at DC and at 0.48·F_s, at every f₀ and Q — a notch changes the level of nothing but its own band | S1 (numerator and denominator sum alike at `z = ±1`), verified analytically; measured +0.00 dB at 23 kHz (A6) | high | a gain at DC or 0.48·F_s outside ±0.1 dB for any Q in 0.5…32 | DC step settled value; a ±FS alternating sequence; a swept sine's endpoints |
| T3 | **Width is f₀/Q**: the −3 dB points sit at `f₀·(√(1+1/4Q²) ∓ 1/2Q)`, difference exactly f₀/Q — at f₀ 1 kHz, Q 2 that is 780.8 and 1280.8 Hz | S3, S1; measured −3.00 dB at both predicted edges for Q ∈ {2, 8} (A2) | high | either predicted edge outside −3.0 ± 0.15 dB for any Q in 0.5…32 | swept sine, the two −3 dB crossings located by interpolation |
| T4 | **Notch + band-pass = 1, exactly**: the two RBJ numerators sum to the shared denominator, so summing this class's output with a band-pass of the same f₀ and Q reconstructs the input to within 0.05 dB from 20 Hz to 0.4·F_s | S1 (both numerator blocks), derived analytically; S4 §4.7 p. 119 states the same identity as `H_N = 1 − H_BP1`; measured through the shipped `DynamicEQ` split to 0.015 dB (A2) | high | a reconstruction error above 0.05 dB anywhere in 20 Hz … 0.4·F_s with both sections at the same f₀ and Q | the two branches summed, swept sine in, response differenced against a wire |
| T5 | **Depth is not a knob — and every off-centre "depth" reading is a width reading in disguise**: the zeros sit on the unit circle at every Q, so the rejection at f₀ is total for all Q in 0.5…32 (T1's commensurate probe reads bit-exact zero at each). What a probe *beside* f₀ reads moves with Q, and moves a long way: at f₀·1.0005 the closed form gives −66.00 dB at Q 0.5, −53.96 at Q 2, −41.92 at Q 8 and −29.88 at Q 32 — a **36 dB spread on one fixed probe**. So a depth control is a *mix* control, not a filter control, and a minimum-of-the-sweep comparison across Q measures the sweep's grid, not the notch | S4 fig. 4.22, p. 120 (the R = 0.2/1/5 family all reach zero at ω_c on a linear amplitude scale); the Q-dependence of the off-centre reading re-derived from S1 in A12 | high | any Q in 0.5…32 whose commensurate on-centre probe does not read bit-exact zero; or any of the four f₀·1.0005 readings more than 0.5 dB from its own closed-form value | T1's on-centre commensurate probe repeated for Q ∈ {0.5, 2, 8, 32}, and the f₀·1.0005 probe repeated for the same four, **each compared with the closed form and never with each other** |
| T6 | **Rate-honest — against the closed form at the running rate**: at 44.1 kHz and 22.05 kHz the centre stays at f₀ within 0.1 %, T2's unity and T3's f₀/Q edges hold to their own tolerances, and the rendered response matches S1's closed form **evaluated at the running rate** within 0.1 dB up to 0.45·F_s. T1's *bit-exact* clause carries over only for a probe commensurate with the new rate; on an incommensurate probe the reading is the source's quantisation floor (−89.5 dB at 44.1 kHz, −87.2 at 22.05, A4), which is a probe fact and disconfirms nothing. Cross-rate, the same f₀ curve deviates ≤ 0.006 dB at 44.1 kHz and ≤ 0.112 dB at 22.05 kHz for f₀ ≤ 1 kHz, rising to 0.409 dB at f₀ = 2 kHz — which is why the requirement is the closed form at each rate, not the 48 kHz curve | S1 (the BLT prewarps f₀ at whatever rate is running); measured at three rates (A5); the cross-rate deviations re-derived in A12 | high | centre displaced >0.1 %, T2 or T3 outside its own tolerance at either rate, or any swept point more than 0.1 dB from the closed form **at that rate** | the T1–T3 measurements at 48 000 / 44 100 / 22 050 Hz, each differenced against its own closed form, T1's on-centre probe chosen commensurate at each rate |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Standout confirmed.** The candidate weighed and dropped was the **Twin-T
notch** as used in hum eliminators and anti-feedback boxes. (The first draft
named the Boss and Maestro families here; that attribution is **unsourced** —
no schematic, manual or product page for either was reached in either run —
and is struck.) It is a real, well-documented network, but its distinguishing traits
are those of a *fixed* notch — a depth set by resistor matching, a Q that
falls apart when the frequency is tuned, and a rejection limited by component
tolerance rather than by design (the first draft put "30–50 dB" here; that
figure is **unsourced** — no Twin-T schematic, datasheet or measurement was
reached in either run — and is struck) — and this class is a swept utility notch whose whole
value is that it tunes cleanly and rejects totally. Importing the Twin-T's
traits would make the class worse on purpose. Design grade stands; Tier 2 is
stated anyway because it is free and falsifiable.

*(from §2)*

**Independent licence and citation audit, 2026-09-06** (a second agent, none
of the first run's notes read; full record in Appendix A10). Corrections
applied above: **S1's licence call** now records the root `LICENSE.md` (full
CC BY 4.0) the serving repository carries — downgraded to *licence unverified,
treated as copyleft* because that grant is the mirror's and the chain to RBJ
is unshown; treatment unchanged. **The Twin-T's "30–50 dB" rejection figure is
struck as unsourced** — no Twin-T schematic, datasheet or measurement was
reached in either run, and a number from memory is not evidence; its remaining
attributes are unsourced general knowledge too, carried for the scope argument
only. Fig. 4.22's page (120) added. The `H_N = 1 − H_BP1 = (s²+1)/(s²+2Rs+1)`
line at §4.7 p. 119 is verbatim and stands, as does the K = −2 allpass.

*(from §2)*

**Second licence-and-citation audit, 2026-09-06** (a third pass, independent
of the first audit; **every URL in this seed re-fetched in this run**). The S1
and S4 calls are re-confirmed unchanged, and both Zavalishin citations are
correct as printed (§4.7 p. 119 and Fig. 4.22 on p. 120). **One correction,
applied above:** the dropped candidate's naming of the **Boss and Maestro
families** is struck as unsourced — no schematic, manual or product page for
either was reached in any run — the same treatment the earlier pass gave the
"30–50 dB" figure. The candidate is still dropped on scope, not on any value.
Full record in `A11`.

*(from §3)*

**Trait-critic pass, 2026-09-06.** T1, T5 and T6 rewritten in place. T5 was
the serious one: its disconfirmation — *"any Q in 0.5…32 whose minimum is more
than 6 dB above the Q = 2 minimum on the same probe"* — is refuted by the
filter's own closed form, which puts a **36 dB** spread on one fixed off-centre
probe across that Q range. It was claiming depth-invariance and testing width;
it now claims what the unit-circle zeros give and tests that. T1's "renders
digital zero" gained the commensurate-probe clause it needs to survive T6's own
rates — this seed's A4 already recorded −89.5 dB at 44.1 kHz, which old T1 and
T6 read together would have called a failure — and its detuned figure is
tightened from a slack ≥ 45 dB to the closed form's −53.96 ± 0.5 dB. T6 is
restated against the closed form at each rate. T2, T3, T4 unchanged. Full
argument in A12. **Six Tier 2 rows after the pass.**

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: **ESP32-P4
≤ 1.5 %, ESP32-S3 ≤ 5 %** for one section, **≤ 2.5 % / ≤ 9 %** for the
two-notch (harmonic) setting §6 proposes. Lean patch expected: **no**.
Basis: 76 instructions per sample per biquad on Cortex-M4/M7
(`audioif/docs/upstream-diff.md:1172`); desktop anchor 147 ns per stereo
frame against a 20 833 ns budget, +16 ns per extra section (A7).

*(from §3)*

**Latency: zero.** Nothing looks ahead; `latency_samples` is 0 at every rate
and setting and **no option this class offers adds any**. Measured: impulse
at frame 50 in, frame 50 out, peak 18 310 of 20 000 (A8). `tail_samples`
follows the pole pair, `ceil(4·Q·F_s/f₀)`, and is reported — a notch's poles
ring exactly as a band-pass's do, which is easy to forget because the
ringing is what is being subtracted.

*(from §4)*

*The harmonic option* — a second `Biquad` at 2f₀ or 3f₀ in the same cascade —
is the one thing a hum notch actually needs, since mains hum is a series and
a single notch at 50 or 60 Hz leaves the buzz. Both sections share the width
macro. *Mix* is `Filter`'s own slot (`Filter.c:232`), clamped away from
`(0, 0.01]`, and it is the class's **depth** control (T5): measured, the gain
at f₀ is exactly `1 − mix` — mix 1.0 bit-exact zero, 0.5 → −6.021 dB, 0.25 →
−2.499 dB (`LowPass.md` A14). *Mono:* identical filter, measured exact (A4).

*(from §4)*

**One palette hazard, and it lands on this class's two headline controls.**
`Filter`'s `mix` blends the source against the **whole cascade's** output on
MicroPython/CircuitPython (`audioif/src/audiofilters/Filter.c:279-283` then
`:288`) and against the **last stage's input** on the CPython target
(`audioif/src/cpython/audiofilters.py:140`). One biquad at any `mix`, and any
cascade at `mix` 0 or 1, agree byte for byte; two biquads at `mix = 0.5`
render different bytes on the two desktop targets (`LowPass.md` A14). The
harmonic option *is* a second biquad and Depth *is* `mix`, so the two together
break Tier 1's identical-bytes invariant and, worse, make Depth mean two
different things: on the desktop CPython target the "dry" half of the blend is
the signal already notched at f₀. If the harmonic option ships, its section
belongs in a second `Filter` after the mixed one — or the divergence is fixed
in audioif. A palette defect, not a class defect, but this class cannot ignore
it.

*(from §4)*

**Portability tier: stock.** On a *stock CircuitPython* board the Q15 biquad's
coefficients quantise the numerator's `−2cos ω₀` at low f₀, which moves the
zeros off the unit circle and turns T1's *total* rejection into a shallow dip.
Upstream's own measured band-edge numbers are at
`audioif/docs/upstream-reports/biquad-band-edges.md:145-147` and the
stock-board note at `audioif/docs/upstream-diff.md:1223-1226`; the far worse
"before" column at `upstream-diff.md:1111-1121` is *this port's* pre-fix
arithmetic, disowned at `:1127-1135`, and is not what a stock board does. The
class runs; its headline trait does not hold there below a few hundred hertz.
Documented on the class.

> **STRUCK at Station A, 2026-09-07 — §8 D9.** The paragraph above is kept
> verbatim because nothing is deleted, and it is wrong in three places.
> (1) Neither citation says what it is cited for:
> `audioif/docs/upstream-reports/biquad-band-edges.md:140-150` is a
> `LOW_PASS`/`HIGH_PASS` band-edge table and names no `NOTCH` row, and
> `audioif/docs/upstream-diff.md:1223-1226` is inside the *interleaved biquad
> state* entry, not a coefficient-quantisation note. (2) Measured, the ported
> integer kernel is **deeper** at low f₀, not shallower: −78.87 dB at 60 Hz
> Q 12 and −40.04 at 20 Hz Q 32, against `audiobiquad`'s −35.65 and −10.98
> (A16). The shallow-dip failure is the **float32** kernel's, and it is now
> §8 D2 on the class this dossier actually ships. (3) What a stock
> CircuitPython 10.2.1 board does is a third thing, and no interpreter in this
> workspace runs it: its single interleaved biquad state puts every frequency
> an octave high and couples the two channels
> (`audioif/docs/upstream-diff.md:1215-1229`).

*(from §5)*

One **Tier 1** item is red and routed to Gate 0 rather than asked here: the
held-DC residual (audioif#23) — `Notch(60 Hz, q=8)` holds −2 LSB for ever
(A3). The configuration matters: 60 Hz at Q 8 is the mains-hum setting, so
this is the residual a user meets first. Recommendation and reasoning: A3.

*(from §7)*

- **The width knob does not exist and cannot be made to exist.** `q` is a
  bare float into `synthio.Biquad` (`eq.py:104`) while `frequency` gets a
  block (`eq.py:102-103`). For a notch, whose second control *is* the width,
  this is the class's central omission.


*(from §4, the seed's stock-palette version — superseded by §8 D1, kept
whole)*

One `synthio.Biquad` in `NOTCH` mode inside one `audiofilters.Filter`. The
node implements RBJ's notch exactly (`audioif_biquad.c:85`: `b0 = 1;
b1 = -2*sc.c; b2 = 1`), and measured against the closed form it lands within
0.002 dB in the passband with the two −3 dB edges on their analytic
positions (A1, A2); an independent re-measurement on 2026-09-07 read
**0.0004 dB** in the passband and bit-exact zero at f₀ for Q 0.707 and Q 4 at
1 kHz (`LowPass.md` A14). `frequency` and `Q` are `synthio` block slots that C
ticks (`Filter.c:281`); Python runs nothing per block.

*(from §5, the seed's answer — superseded by §5's one ask)*

**None.** Every Tier 2 trait is reachable on the stock palette, and §4 shows
how.

*(from §5, Station A: the two builds weighed and not taken)*

**A parallel `1 − BAND_PASS`.** `audioroute.Splitter` → one dry tap and one
`audiobiquad.Biquad(BAND_PASS)` tap → an `audioshaper` inversion →
`audiomixer.Mixer`, which is T4's identity built rather than measured. It is
not taken: four extra nodes against three, an int16 quantisation at every
stage, and — the deciding one — an int16 **sum on the dry path**, which is
exactly what T2's ±0.1 dB unity and Tier 1's level-honesty are stated
against. `MixerVoice.level` clamps to 0…1 so the inversion cannot live in
the mixer, which is why the shaper is in the count.

**A four-pole cascade**, two `NOTCH` sections at one f₀ with Q' chosen so the
pair's −3 dB width is still f₀/Q. It would double the centre's rejection in
dB — −71 dB rather than −35.65 at 60 Hz Q 12 — and keep T3. It is not taken
because §1's referent is *the two-pole band-stop*, and because T4 rests on a
single section: `notch + band-pass = 1` is false for a squared numerator, so
the cascade would **disconfirm a frozen trait by construction**. Recorded as
considered, with the arithmetic, rather than left to be re-proposed.

*(from §6, the seed's surface paragraph)*

Depth doubles as Tier 1's wire test: at 0 the class is byte-identical to its
source. `capabilities = ()`: nothing here is measured in beats (D10,
answered).

Patches: 0 **Wide Notch** (1 kHz, Q 0.707, 1 notch, full depth — the
constructor's defaults on the grid), 1 **Hum 50** (50 Hz, Q 12, 2 notches),
2 **Hum 60** (60 Hz, Q 12, 2 notches), 3 **Feedback Tamer** (2.5 kHz, Q 24,
1 notch), 4 **Mud Scoop** (300 Hz, Q 1.2, 1 notch, depth 0.6),
5 **Whistle Kill** (8 kHz, Q 30, 1 notch).

### A16. Station A's own runs, 2026-09-07 — the nine decisions

Every figure here is from `tools/phase2_probes/notch_bench.py`, run under
`PYTHONPATH=lib audiocomponents/.venv/bin/python` in this worktree, audioif
at the pin `2f6cbc3`. Nothing in it builds the `Notch` class — Station A runs
before the class exists — so every probe drives the palette nodes directly
and the decisions are made from what the nodes do.

**D1 — held DC after silence, on both kernels.** The seed's A3 probe, exactly
(0.09 s of 440 Hz at 12 000, then 3.0 s of zeros, 287 of the 289 available
blocks pulled so the source never runs out). Last sample of the render, and
the largest magnitude in the final 4096 frames:

```
   setting                       synthio   audiobiq  |y| synth    |y| f32
   60 Hz  q=8  (mains hum)            -2          0          2          0
   50 Hz  q=8                          3          0          3          0
   120 Hz q=8  (2f0 of 60)             0          0          0          0
   1 kHz  q=0.707 (default)            0          0          0          0
   20 Hz  q=32 (span corner)         -18         -1         18          2
```

The `audiobiquad` −1 at 20 Hz Q 32 is **a tail still decaying, not a held
value**: that setting's ring is 2.65 s (D6 below) and this probe is 1.53 s
long. The `synthio` residuals do not decay — the seed measured them held to
3000 blocks.

**D2 — the on-centre floor, both kernels, against the closed form read off
the node's own coefficients.** Commensurate probes, level 6000, 48 kHz, peak
`|y|` over the last 1.0 s of a 6.0 s render. `predicted` is
`20·log₁₀|H(ω₀)|` evaluated from `Biquad.coefficients` — the shipped `float`
values — not from the algebra:

```
f0       Q        own peak     own dB   stock pk   stock dB predicted dB
20.0     0.707          46     -42.31          1     -75.56       -42.46
20.0     2.000         111     -34.66          1     -75.56       -34.47
20.0     12.000        602     -19.97          3     -66.02       -19.88
20.0     32.000       1651     -11.21          7     -58.66       -10.98
50.0     12.000         47     -42.12          1     -75.56       -41.85
60.0     0.707           4     -63.52          1     -75.56       -65.00
60.0     2.000          11     -54.74          1     -75.56       -53.20
60.0     12.000         99     -35.65          1     -75.56       -35.54
60.0     32.000        150     -32.04          3     -66.02       -32.46
120.0    12.000         17     -50.95          1     -75.56       -52.48
250.0    12.000          5     -61.58          1     -75.56       -63.53
500.0    32.000          3     -66.02          1     -75.56       -64.93
1000.0   2.000           0       -inf          0       -inf      -109.38
1000.0   32.000          1     -75.56          0       -inf       -84.15
4000.0   0.707           0       -inf          0       -inf      -142.52
8000.0   30.000          0       -inf          0       -inf      -283.36
```

`-75.56 dB` is one LSB against a 6000 level — the measurement's floor, not a
reading. The measured column tracks the predicted one to 2 dB wherever
either is above that floor — the widest gap, 1.95 dB at 250 Hz Q 12, is 14 dB
above the floor, where the int16 rounding is a third of the reading. That
agreement is what says this is the coefficient arithmetic and not a build
error. It is a floor and not an unfinished transient: held to 40 s at 20 Hz
Q 32 (`1.0s: 1650  2.0s: 1638  4.0s: 1649  8.0s: 1650  39.5s: 1647`) and to
16 s at 60 Hz Q 12 (`1.0s: 99  2.0s: 99  4.0s: 99  8.0s: 99  15.5s: 99`).

**D2's node ask, measured.** `|1 − H_BAND_PASS(f₀)|` from the same kernel's
own coefficients, beside `|H_NOTCH(f₀)|`:

```
  f0=20.0    Q=32.0   |1 - H_BP(f0)| = 4.339e-03 ( -47.25 dB)   |H_NOTCH(f0)| = 2.825e-01 ( -10.98 dB)
  f0=60.0    Q=12.0   |1 - H_BP(f0)| = 5.113e-03 ( -45.83 dB)   |H_NOTCH(f0)| = 1.671e-02 ( -35.54 dB)
  f0=60.0    Q=32.0   |1 - H_BP(f0)| = 7.090e-03 ( -42.99 dB)   |H_NOTCH(f0)| = 2.383e-02 ( -32.46 dB)
  f0=1000.0  Q=2.0    |1 - H_BP(f0)| = 3.775e-06 (-108.46 dB)   |H_NOTCH(f0)| = 3.396e-06 (-109.38 dB)
```

`b₂ == −b₀` is exactly true for `BAND_PASS` at all four settings. At 1 kHz
the two forms agree; at the hum settings the band-pass form is 17 to 36 dB
better. That difference is §5's ask, and it is why the ask names the
arithmetic and not a feature.

**D2's control — the ported kernel is really notching**, so its deeper
column is not a filter that is doing nothing:

```
  notch f0=60.0    Q=12.0  probe     60.0 Hz ->   -78.87 dB
  notch f0=60.0    Q=12.0  probe    600.0 Hz ->    -0.00 dB
  notch f0=60.0    Q=12.0  probe   1000.0 Hz ->    -0.00 dB
  notch f0=20.0    Q=32.0  probe     20.0 Hz ->   -40.04 dB
  notch f0=20.0    Q=32.0  probe   1000.0 Hz ->    -0.00 dB
```

**D3 — the harmonic notch's width law.** −3 dB width in hertz at 2f₀ under
each law, with the two predicted edges measured to confirm the prediction:

```
   f0=60.0    Q=12.0   share Q        width    10.00 Hz (fundamental     5.00)  edges measured  -3.015 /  -3.001 dB
   f0=60.0    Q=12.0   scale Q by 2   width     5.00 Hz (fundamental     5.00)  edges measured  -3.003 /  -3.008 dB
   f0=50.0    Q=12.0   share Q        width     8.33 Hz (fundamental     4.17)  edges measured  -2.912 /  -3.058 dB
   f0=50.0    Q=12.0   scale Q by 2   width     4.17 Hz (fundamental     4.17)  edges measured  -3.182 /  -3.102 dB
   f0=1000.0  Q=2.0    share Q        width  1000.00 Hz (fundamental   500.00)  edges measured  -2.968 /  -2.947 dB
   f0=1000.0  Q=2.0    scale Q by 2   width   500.00 Hz (fundamental   500.00)  edges measured  -2.965 /  -2.955 dB
```

The two rows outside T3's ±0.15 dB are the **probe's** settling and not the
filter's: a 0.35 s tone with a 0.15 s skip does not outlast a Q 24 section's
ring at 100 Hz. The evidence pack's own RESPONSE runs use a settling window
derived from the section's Q.

**D4 — the mix threshold.** Peak `|wet − dry|` on a 1 kHz tone at f₀,
CPython, both node families:

```
   mix 0.000    audiobiquad      0      audiofilters      0
   mix 0.005    audiobiquad    100      audiofilters    100
   mix 0.010    audiobiquad    200      audiofilters    200
   mix 0.020    audiobiquad    400      audiofilters    400
   mix 0.500    audiobiquad  10000      audiofilters  10000
   mix 1.000    audiobiquad  20000      audiofilters  20000
```

Linear in `mix` with no step at 0.01, and `mix = 0` is bit-exact. The seed's
A9 divergence is `Filter.c:234`'s and lives on the MicroPython side of
`audiofilters`; the cross-interpreter half is the evidence pack's §3.

**D5 — the span's top.** `min(16 kHz, 0.4·F_s)`, and what the closed form
says at T2's 0.48·F_s probe:

```
  0.28*Fs    48000 Hz: -0.1005 dB (f0  13440.0)  |  22050 Hz: -0.1005 dB (f0   6174.0)
  0.33*Fs    48000 Hz: -0.1966 dB (f0  15840.0)  |  22050 Hz: -0.1966 dB (f0   7276.5)
  0.40*Fs    48000 Hz: -0.6516 dB (f0  19200.0)  |  22050 Hz: -0.6516 dB (f0   8820.0)
```

At Q 0.5, T2's ±0.1 dB at 0.48·F_s holds only up to **0.2796·F_s**; at
Q 0.707 up to 0.3304·F_s. The span is **not** narrowed to fit: T2's own bar
stays where it was frozen and the evidence pack records the corner where it
fails, with the cause — at f₀ = 16 kHz and Q 0.5 the notch's band is 32 kHz
wide, so the 0.48·F_s probe is *inside* the band, which is a fact about the
probe and not a filter that leaks. DC at those corners reads −0.00002 dB or
better at every rate.

**D6 — the tail ceiling.** Full-scale burst at 60 Hz for 0.2 s inside a 40 s
source, then digital silence still supplied by the source; the last non-zero
output frame:

```
   20 Hz  Q 32, one section        127202 after the source went silent (2.65 s)
   20 Hz  Q 32 + 40 Hz Q 60        140405 after the source went silent (2.93 s)
   20 Hz Q32 + 40 Hz Q60, trim +12 140405 after silence (2.93 s)
   20 Hz Q32 + 40 Hz Q60, trim -12 127202 after silence (2.65 s)
   trim +12 alone (5 Hz shelf)      15227 after silence (0.32 s)
   50 Hz  Q 12 + 100 Hz Q 24        34620 after the source went silent (0.72 s)
   1 kHz  Q 0.707 (patch 0)            88 after the source went silent (0.00 s)
```

Every configuration reaches **exact** zero and stays there, which is D1's
whole point. 140 405 → declared 143 360, the next multiple of 2048.

**D3's stated clamp and D5's, together.** `audiobiquad` clamps `Q` to
0.05…60 (`AUDIOIF_FILTER_F32_MIN_Q`/`MAX_Q`,
`audioif/src/shared/audioif_filter_f32.c:21-22`), so the doubled harmonic Q
saturates above Q 30: at Width 32 the harmonic notch is 64/60 = 6.7 % wider
in hertz than the fundamental.

**The trim shelf (§4's third section), measured here rather than borrowed.**
Worst deviation from the requested gain over 20 Hz…10 kHz:

```
    48000 Hz  trim  +6.0 dB   worst deviation  -0.099 dB at     20.0 Hz
    48000 Hz  trim +12.0 dB   worst deviation  -0.043 dB at     20.0 Hz
    44100 Hz  trim -12.0 dB   worst deviation  +0.105 dB at     20.0 Hz
    22050 Hz  trim -12.0 dB   worst deviation  +0.099 dB at     20.0 Hz
```

**The closed form, palette against S1, at three settings** (the run that says
T2, T3 and T6 are reachable before any class exists) is in the bench's `D7`
block; its 60 Hz rows are the ones D2 explains, and every 1 kHz and 8 kHz row
is within 0.012 dB of the closed form.
