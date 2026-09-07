# Effects Dossier — `Notch` (no historical standout — design grade)

**Class:** `lib/audioeffects/eq.py` — the current implementation is read once,
for §7, and not otherwise consulted.
**Family / phase:** EQ / Filter, roadmap Phase 2
**Standout:** none, per vision §4.2 — **confirmed** (§2).
**Grade:** design
**Portability tier:** stock CircuitPython (`audiofilters.Filter` +
`synthio.Biquad`), with the stock-board caveat in §4.
**Status:** seed (Phase 0)

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

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** RBJ, *Cookbook formulae for audio EQ biquad filter coefficients* … (App. S1) | the notch and BPF coefficient blocks (which give the … (App. S1) | the `.txt` itself carries **no license … (App. S1) | https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* … (App. S3) | *"Q … resonance frequency divided by the resonator … (App. S3) | © J. O. Smith III / CCRMA Stanford … (App. S3) | https://ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html | 2026-09-06 |
| **S4** Zavalishin, *The Art of VA Filter Design* rev. 2.1.0 (discoDSP … (App. S4) | `H_N(s) = 1 − H_BP1(s) = (s²+1)/(s²+2Rs+1)` (§4.7 p. … (App. S4) | verbatim-copy-only … (App. S4) | https://www.discodsp.net/VAFilterDesign_2.1.0.pdf | 2026-09-06 |

Every S1 formula was cross-checked against the W3C/WebAudio HTML+MathML
rendering (https://webaudio.github.io/Audio-EQ-Cookbook/audio-eq-cookbook.html,
reached). **Looked for, not found:** musicdsp.org's RBJ page carries no
license text (fetched); archive.org's Zavalishin item has **no `licenseurl`
field**, so the discoDSP mirror's front-matter grant is the license read.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **Total rejection at the centre**: the zeros sit exactly on the unit circle, so a sine at f₀ **whose period is a whole number of samples at the running rate** renders bit-exact digital zero; and a sine 0.05 % away reads −53.96 dB at Q 2, ± 0.5 dB, which is the closed form, not a floor. The commensurability clause is not a hedge: at 44.1 kHz and 22.05 kHz a 1 kHz probe has 44.1 and 22.05 samples per cycle and the same filter reads −89.5 and −87.2 dB — **the source's own quantisation floor, not the filter** (A4) | S1 (notch numerator), verified analytically … (App. T1) | high | a commensurate sine exactly at f₀ producing any non-zero sample after settling; or the f₀·1.0005 reading outside −53.96 ± 0.5 dB at Q 2 | a fixed sine exactly at f₀ … (App. T1) |
| T2 | **Unity outside the band**: 0.00 ± 0.1 dB at DC and at 0.48·F_s, at every f₀ and Q — a notch changes the level of nothing but its own band | S1 (numerator and denominator sum alike at `z … (App. T2) | high | a gain at DC or 0.48·F_s outside ±0.1 dB for any Q in 0.5…32 | DC step settled value … (App. T2) |
| T3 | **Width is f₀/Q**: the −3 dB points sit at `f₀·(√(1+1/4Q²) ∓ 1/2Q)`, difference exactly f₀/Q — at f₀ 1 kHz, Q 2 that is 780.8 and 1280.8 Hz | S3, S1; measured −3.00 dB at both predicted … (App. T3) | high | either predicted edge outside −3.0 ± 0.15 dB for any Q in 0.5…32 | swept sine, the two −3 dB … (App. T3) |
| T4 | **Notch + band-pass = 1, exactly**: the two RBJ numerators sum to the shared denominator, so summing this class's output with a band-pass of the same f₀ and Q reconstructs the input to within 0.05 dB from 20 Hz to 0.4·F_s | S1 (both numerator blocks) … (App. T4) | high | a reconstruction error above 0.05 dB anywhere in 20 Hz … 0.4·F_s with both sections at the same f₀ and Q | the two branches summed … (App. T4) |
| T5 | **Depth is not a knob — and every off-centre "depth" reading is a width reading in disguise**: the zeros sit on the unit circle at every Q, so the rejection at f₀ is total for all Q in 0.5…32 (T1's commensurate probe reads bit-exact zero at each). What a probe *beside* f₀ reads moves with Q, and moves a long way: at f₀·1.0005 the closed form gives −66.00 dB at Q 0.5, −53.96 at Q 2, −41.92 at Q 8 and −29.88 at Q 32 — a **36 dB spread on one fixed probe**. So a depth control is a *mix* control, not a filter control, and a minimum-of-the-sweep comparison across Q measures the sweep's grid, not the notch | S4 fig. 4.22, p. 120 (the R = 0.2/1/5 family … (App. T5) | high | any Q in 0.5…32 whose commensurate on-centre probe does not read bit-exact zero; or any of the four f₀·1.0005 readings more than 0.5 dB from its own closed-form value | T1's on-centre commensurate probe … (App. T5) |
| T6 | **Rate-honest — against the closed form at the running rate**: at 44.1 kHz and 22.05 kHz the centre stays at f₀ within 0.1 %, T2's unity and T3's f₀/Q edges hold to their own tolerances, and the rendered response matches S1's closed form **evaluated at the running rate** within 0.1 dB up to 0.45·F_s. T1's *bit-exact* clause carries over only for a probe commensurate with the new rate; on an incommensurate probe the reading is the source's quantisation floor (−89.5 dB at 44.1 kHz, −87.2 at 22.05, A4), which is a probe fact and disconfirms nothing. Cross-rate, the same f₀ curve deviates ≤ 0.006 dB at 44.1 kHz and ≤ 0.112 dB at 22.05 kHz for f₀ ≤ 1 kHz, rising to 0.409 dB at f₀ = 2 kHz — which is why the requirement is the closed form at each rate, not the 48 kHz curve | S1 (the BLT prewarps f₀ at whatever rate is … (App. T6) | high | centre displaced >0.1 %, T2 or T3 outside its own tolerance at either rate, or any swept point more than 0.1 dB from the closed form **at that rate** | the T1–T3 measurements at 48 000 … (App. T6) |

No characters: a notch has one behaviour.

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

One `synthio.Biquad` in `NOTCH` mode inside one `audiofilters.Filter`. The
node implements RBJ's notch exactly (`audioif_biquad.c:85`: `b0 = 1;
b1 = -2*sc.c; b2 = 1`), and measured against the closed form it lands within
0.002 dB in the passband with the two −3 dB edges on their analytic
positions (A1, A2); an independent re-measurement on 2026-09-07 read
**0.0004 dB** in the passband and bit-exact zero at f₀ for Q 0.707 and Q 4 at
1 kHz (`LowPass.md` A14). `frequency` and `Q` are `synthio` block slots that C
ticks (`Filter.c:281`); Python runs nothing per block.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**None.** Every Tier 2 trait is reachable on the stock palette, and §4 shows
how.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 20 Hz … min(16 kHz, 0.4·F_s), log | the tuning knob |
| 1 | Width | UNIPOLAR | Q 0.5 … 32, log; displayed as bandwidth f₀/Q | the Q / bandwidth knob |
| 2 | Harmonics | TOGGLE | 1 notch (default) / 2 notches at f₀ and 2f₀ | a hum eliminator's harmonic switch |
| 3 | Depth | UNIPOLAR | 0 exactly … 1 (the node's `mix`); values in (0, 0.01] snap to 0 | the depth control, which T5 says must be a mix and not a Q |
| 4 | Trim | BIPOLAR | −12 … +12 dB, default 0 | output make-up |

Depth doubles as Tier 1's wire test: at 0 the class is byte-identical to its
source. `capabilities = ()`: nothing here is measured in beats (D10,
answered).

Patches: 0 **Wide Notch** (1 kHz, Q 0.707, 1 notch, full depth — the
constructor's defaults on the grid), 1 **Hum 50** (50 Hz, Q 12, 2 notches),
2 **Hum 60** (60 Hz, Q 12, 2 notches), 3 **Feedback Tamer** (2.5 kHz, Q 24,
1 notch), 4 **Mud Scoop** (300 Hz, Q 1.2, 1 notch, depth 0.6),
5 **Whistle Kill** (8 kHz, Q 30, 1 notch).

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
- **Held DC at the hum setting** — §5.
- **`reset()` reaches one node** (`_core.py:366-374`), and the `Filter` it
  reaches resets its source recursively, so the borrowed source *is* reset,
  which the contract forbids.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Gate 0's biquad answer** (§5). *Settled by:* Phase 0 Gate.
2. **Whether Harmonics should reach three or four notches** for 50/60 Hz
   hum, and whether the harmonic notches should share the width or narrow
   proportionally. *Settled by:* the implementation session at Phase 2,
   against the S3 budget.
3. **Whether `Notch` should offer an all-pass character.** RBJ's APF shares
   this denominator and differs only in its numerator, and Zavalishin gets it
   from the same core at K = −2 (S4 §4.7 p. 119) — but `Phaser` owns the
   all-pass in this catalogue and the `NAME` set is frozen. Recorded as
   considered and not taken. *Settled by:* the implementation session.

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
