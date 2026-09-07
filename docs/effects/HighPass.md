# Effects Dossier — `HighPass` (no historical standout — design grade)

**Class:** `lib/audioeffects/eq.py` — the current implementation is read once,
for §7, and not otherwise consulted.
**Family / phase:** EQ / Filter, roadmap Phase 2
**Standout:** none, per vision §4.2 — **confirmed** (§2).
**Grade:** design
**Portability tier:** **audioif** — `REQUIRES = ("audiobiquad",)`. Moved
from stock at Station A because the node the seed asked for landed; §8 D1.
**Status:** Station A, 2026-09-07 — every §8 open settled, the trait table
frozen, the surface frozen. Every number below comes from a run of
`tools/phase2_probes/highpass_bench.py` (A15) or from an appendix that names
its own run.

## 1. The circuit, in one paragraph

The referent is the two-pole analog high-pass every console's low-cut and
every synth's HPF is a version of. Zavalishin derives it from the low-pass by
the substitution `s ← 1/s` (S4 §2.10 p. 24), which in the log-frequency scale
simply mirrors the amplitude curve about the cutoff: of the 2-pole pair he
writes that *"the highpass response is a mirrored version of the lowpass
response"*, because *"applying the LP to HP substitution to a 2-pole lowpass
produces a 2-pole highpass"* (S4 §4.1 p. 97). So the same two controls
apply: **cutoff** ω_c slides the response without deforming it (S4 §2.7,
quote on p. 16), and **damping** R sets the corner peak, with `Q = 1/2R` (S4 §4.2
p. 100). There is no nonlinearity. The one property a high-pass has that a
low-pass does not, and the reason engineers reach for it, is a **transmission
zero at DC**: the numerator `(1+cos ω₀)/2, −(1+cos ω₀), (1+cos ω₀)/2` (S1,
verbatim) sums to exactly zero at `z = 1`, so a DC offset or a subsonic
rumble is not merely attenuated but removed, and a step settles to exact
zero. That single fact is the class's whole musical job, and it is also the
one Tier 2 trait the palette currently fails at low corners (§3, §5). The
panel controls are *frequency*, logarithmically, and *resonance*.

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** RBJ, *Cookbook formulae for audio EQ biquad filter coefficients* … (App. S1) | the HPF coefficients, `α = sin(w0)/(2Q)` … (App. S1) | the `.txt` itself carries **no license … (App. S1) | https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* … (App. S3) | Q = f₀/bandwidth; the envelope reaches e^{−π} in Q … (App. S3) | © J. O. Smith III / CCRMA Stanford … (App. S3) | https://ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html , …/Decay_Time_Q_Periods.html | 2026-09-06 |
| **S4** Zavalishin, *The Art of VA Filter Design* rev. 2.1.0 (discoDSP … (App. S4) | the LP→HP substitution `s ← 1/s` (§2.10 p. 24) and the … (App. S4) | verbatim-copy-only … (App. S4) | https://www.discodsp.net/VAFilterDesign_2.1.0.pdf | 2026-09-06 |

Every S1 formula was cross-checked against the W3C/WebAudio HTML+MathML
rendering (https://webaudio.github.io/Audio-EQ-Cookbook/audio-eq-cookbook.html,
reached; *"Adapted … with permission"*, nothing further). **Looked for, not
found:** musicdsp.org's RBJ page carries no license text (fetched);
native-instruments.com's `VAFilterDesign_2.1.0.pdf` 404s; archive.org's item
for rev. 2.1.2 carries **no `licenseurl` field**, so the discoDSP mirror's own
front-matter grant is the license actually read.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **Exact zero at DC**: the numerator sums to zero at `z = 1`, so a DC step or a held offset decays to *exact* zero, not to a small residue, at every f₀ from 10 Hz up and at both slopes. Stated of the wet path, at Mix 1: below that the dry path carries DC through, which is what a blend is | S1 (HPF numerator), analytic | high | any settled output not bit-exactly zero after a DC step, at any f₀ ≥ 10 Hz | DC step of ±0.5 FS, 5 s … (App. T1). **Red on the shipped node, green on the rebuilt palette** — A15 |
| T2 | **The corner gain is the resonance**: \|H(f₀)\| = Q exactly, **at both slopes** — Q 0.707 → −3.01 dB, Q 2 → +6.02, within 0.05 dB | S1, analytic + A2, A15 … (App. T2) | high | any Q in 0.5–16 more than 0.05 dB from 20·log₁₀(Q) at f₀, at either slope | steady-state sine at f₀, Q ∈ {0.5, .707, 1, 2, 4, 8, 16}, source level picked from Q … (App. T2) |
| T3 | **+12 dB/oct skirt, doubled at the steep slope, unity above**: at 12 dB/oct, −24.10 ± 0.30 dB two octaves *below* f₀ at Q 0.707 and a fitted f₀/8…f₀/4 slope of +12.03 ± 0.30 dB/oct, **for every f₀ from 20 Hz to 3.2 kHz at 48 kHz**; at 24 dB/oct both numbers double, to −48.2 ± 0.6 dB and +24.1 ± 0.6 dB/oct. And 0.00 ± 0.1 dB at Nyquist at every f₀ and Q | S4 §4.1 p. 97, S1 … (App. T3) | high | fitted slope outside +11.7…+12.3 dB/oct (+23.4…+24.6 steep) over f₀/8…f₀/4, or \|H(f₀/4)\| outside its band, at any f₀ ≤ 3.2 kHz; or a gain at 0.48·F_s outside ±0.1 dB at any f₀ | swept sine; slope fitted f₀/8…f₀/4 at f₀ ∈ {20, 160, 640, 1280, 3200} Hz, both slopes; gain read at 23 kHz (A6, A15) |
| T4 | **Shape invariance under cutoff — on the warped axis**: the axis the response is one curve on is the **bilinear-warped** one. Against f_a/f_a0 with `f_a = (F_s/π)·tan(πf/F_s)` it is f₀-independent to **0.00000 dB** for every f₀ from 20 Hz to 0.4·F_s. Against the linear f/f₀ it slides without deforming within 0.1 dB only while **f₀ ≤ 1280 Hz at 48 kHz** | S4 §2.7 p. 16 … (App. T4) | high | on the warped axis, any two f₀ in 20 Hz…0.4·F_s differing by >0.05 dB at the same f_a/f_a0; on the linear axis, two f₀ an octave apart, both ≤ 1280 Hz, differing by >0.1 dB anywhere in f₀/8 … 8f₀ | swept sine at f₀ ∈ {20, 40, 80 … (App. T4) |
| T5 | **Q is the ringing**: struck with a click it rings at f₀, envelope down to 4.3 % of peak after Q periods | S3, "Decay Time is Q Periods" | medium — stated for Q … (App. T5) | e^{−π} reached in <0.8 Q or >1.25 Q periods for Q ∈ {2, 4, 8, 16} | impulse, Hilbert envelope … (App. T5) |
| T6 | **Rate-honest — against the closed form at the running rate**: at 44.1 kHz and 22.05 kHz the corner stays at f₀ within 0.1 %, \|H(f₀)\| stays at Q, and the rendered response matches S1's closed form **evaluated at the running rate** within 0.1 dB up to 0.45·F_s, over the whole 10 Hz … 20 kHz span | S1; measured at three rates (A5, A15) … (App. T6) | high | corner displaced >0.1 %, gain at f₀ more than 0.1 dB from 20·log₁₀(Q), or any swept point more than 0.1 dB from the closed form **at that rate** | T4's sweep at 48 000 / 44 100 / 22 050 Hz, each differenced against its own closed form (A15: worst 0.063 dB over 45 combinations) |

No characters: a high-pass has one behaviour.

**T1 was disconfirmed at low corners on the shipped node** — up to −71 LSB
at f₀ = 10 Hz, held for ever (A3, A15) — and is green on the palette §4 now
names. Recording the red rather than dropping the trait is the point of
fixing the set in advance; §8 D1 is what moved it.

### Tier 3 — cost and latency

**Latency: zero.** Nothing looks ahead; `latency_samples` is 0 at every rate
and setting and **no option this class offers adds any** — so there is no
latency-adding option to default off and none to name in milliseconds.
Measured on the rebuilt cascade: click at frame 50 in, frame 50 out, at
48 000 and 44 100 Hz and at both slopes (A15; A8 is the same result on the
old node).

**`tail_samples` = 305 152** (6.36 s at 48 kHz). The seed's per-setting
`ceil(4·Q·F_s/f₀)` is not expressible — the contract reads `tail_samples`
off the class, not off the instance — so the declaration is the measured
ceiling over the whole span instead: **303 727** samples after the source
goes silent, at 10 Hz, Resonance 16, 24 dB/oct and +12 dB of trim, struck
with a full-scale burst (A15), rounded up to the next multiple of 2048. It
is loose at every setting but that one: patch 0's own tail is 7 866 samples.

**Tier 3 budget**, as a fraction of one stereo block's real-time deadline:
**ESP32-P4 ≤ 1.5 %, ESP32-S3 ≤ 5 %** at the 12 dB/oct default, **≤ 2.5 % /
≤ 9 %** with 24 dB/oct engaged. Lean patch expected: **no**. Three sections
are always built (§4), two of them wires at patch 0. The basis for the
numbers is in **App. R**.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Three `audiobiquad.Biquad` sections in one chain**: two `HIGH_PASS` poles,
then a `HIGH_SHELF` trim. Not the seed's `synthio.Biquad` inside an
`audiofilters.Filter`, and the reason is T1 — see §8 D1. `audiobiquad` keeps
float state and float coefficients and writes any state word below 1e-20 as
exact zero (`audioif/docs/upstream-diff.md`, the `audiobiquad` section), so
the tail arrives; the ported node's Q12 integer memory has fixed points and
parks on them. `frequency`, `Q`, `gain_db` and `mix` are block slots the C
reads once per chunk, so a macro move is a float store and Python runs
nothing per block.

*Slope 24 dB/oct* is the second `HIGH_PASS` section, built at every setting
because a node cannot be added to a running graph and Slope is a live macro;
at 12 dB/oct it is a wire (`mix = 0`). At 24 the pair takes the fourth-order
Butterworth Qs (0.5412, 1.3066) with the resonance riding the **second**
section alone, so the product is `0.5412 · 1.3066 · Q/0.7071 = Q` and the
knob reads the same at either slope — within **0.002 dB** of 20·log₁₀(Q) for
Q from 0.5 to 16 (A15).

*Trim* is one `HIGH_SHELF` at 5 Hz, a broadband gain everywhere above it —
measured flat to **0.0152 dB** from 50 Hz to 15 kHz at all three rates over
±6 and ±12 dB (A15). It closes the chain rather than opening it: each
section writes int16 and clips there
(`audioif/src/shared/audioif_filter_f32.c:43-51`) and a Resonance-16 corner
stands 24 dB above the passband, so the trim must sit after the peak it
trims. Why a shelf at all, and why `A` cannot do it, are in **App. R**.

*Mix* is the section-level crossfade `audiobiquad` already has, set on every
section in use at once; 0 is a byte-exact wire. What it means at 24 dB/oct,
and the node pair not taken, are in **App. R**. *Mono:* a mono source gets
the identical filter (A4).

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**None — and the one this seed made has landed.** The seed asked Gate 0 for
a DC-clean biquad in an audioif-own module (A3); Phase 1 shipped it as
`audiobiquad` on the pin `2f6cbc3`. §8 D1 adopts it, and T1 goes from red to
green with it. Nothing else in §3 needs a node that does not exist.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Surface — frozen at Station A

Five macros, well inside the sixteen the contract allows.

| # | Label | Mode | Span (`_MACRO_RANGES`) | Generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 10 … 20 000 Hz, log; `_hz()` clamps at 0.49·F_s | the low-cut knob |
| 1 | Resonance | UNIPOLAR | Q 0.5 … 16, log (R = 1/2Q, S4) | the resonance/emphasis knob |
| 2 | Slope | TOGGLE | 0 = 12 dB/oct (default), 1 = 24 | a desk's low-cut slope switch |
| 3 | Mix | UNIPOLAR | 0 exactly … 1 | a dry/wet blend; no analog low-cut had one, kept because Tier 1's wire test needs it |
| 4 | Trim | BIPOLAR | −12 … +12 dB, default 0; under 0.2 dB the section is a wire | the make-up a resonant corner needs |

`capabilities = ()` — nothing in a high-pass is measured in beats; its
controls are hertz and a dimensionless Q, and the class never reads
`self._transport()` (§8 D7). The span's floor and ceiling are §8 D2, and the
dropped `(0, 0.01]` mix snap is §8 D6.

**Patches**, named for settings and never for products; the grid column is
`macro_of()` of the setting beside it, so patch 0 is the constructor's own
defaults to within one step of the grid.

| # | Name | What it is for | Setting the grid lands on | Grid |
|---|---|---|---|---|
| 0 | Flat | subsonic protection and nothing else — the constructor's defaults | 10 Hz, Q 0.71, 12 dB/oct, mix 1, trim 0 | `(0, 13, 0, 127, 64)` |
| 1 | Rumble Cut | stage and traffic rumble off a full mix | 29.4 Hz, Q 0.71, 24 dB/oct | `(18, 13, 127, 127, 64)` |
| 2 | Stage Low-Cut | the console low-cut a live vocal gets | 81.2 Hz, Q 0.71, 12 dB/oct | `(35, 13, 0, 127, 64)` |
| 3 | Thin It Out | take the body out of a pad or a guitar | 303 Hz, Q 0.71, 12 dB/oct | `(57, 13, 0, 127, 64)` |
| 4 | Radio | a telephone voice, with the trim paying for the corner | 701 Hz, Q 1.49, 24 dB/oct, −2.93 dB | `(71, 40, 127, 127, 48)` |
| 5 | Whistle | the corner as an effect — a resonant peak you sweep | 2 057 Hz, Q 10.06, 12 dB/oct, −8.98 dB | `(89, 110, 0, 127, 16)` |

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/eq.py`.

- **No surface at all.** `MACRO_LABELS = ()` (`eq.py:132`).
- **`q` is frozen at construction.** `synthio.Biquad(self.MODE, …  *(argument in full: App. R)*
- **`mix` is accepted and then hidden** (taken `eq.py:101`, forwarded
  `eq.py:105`, unreachable after).
- **`set_frequency` is off-contract and it raises.** `eq.py:110-111` calls …  *(argument in full: App. R)*
- **The default is 1 kHz** (`eq.py:101`), which is a vocal-thinning filter,
  not a low-cut; nothing in the class points a user at the range it is for.
- **No tail is declared.** `TAIL_SAMPLES = None`, `LATENCY_SAMPLES = 0` …  *(argument in full: App. R)*
- **Held DC at low corners** — §5, and for this class it contradicts T1.
- **`reset()` reaches one node** (`_core.py:366-374`), and the `Filter` it
  reaches resets its source recursively, so the borrowed source *is* reset,
  which the contract forbids.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Decisions — every open settled at Station A, 2026-09-07

Nothing here is open. Each decision's run is in **A15**; no number below is
recalled from another class's pack.

| # | Decision | Settled by |
|---|---|---|
| D1 | **Portability tier: audioif**, on `audiobiquad` — the seed's q. 1, settled by Gate 0's node having landed. The shipped `synthio.Biquad` holds **−71 LSB at 10 Hz, −18 at 20, −8 at 30, −2 at 60, −1 at 100**, for ever; `audiobiquad` reaches **exact zero** at every setting in the span. Cost, stated not hidden: a stock CircuitPython board can no longer construct this class, where the old one ran there and quietly failed Tier 1 | A3, A15 |
| D2 | **Frequency spans 10 Hz … 20 kHz**, log, clamped by `_hz()` at 0.49·F_s. The seed's q. 2 is settled at **10**: the residual it worried about was the integer node's, and on the float node 10 Hz reads −3.010 dB against a closed form of −3.010 at all three rates. The seed's 2 kHz ceiling is **not** kept — argument in A15 | A15 |
| D3 | **`LowPass` and `HighPass` do not share an implementation class** (the seed's q. 3). One class per file is what lets sixteen rebuilds run in parallel with no shared file to conflict over — the registry rule, roadmap §3 | registry rule |
| D4 | **The trim is one `HIGH_SHELF` at 5 Hz**, not the seed's stock shelf *pair*: one section, flat to **0.0152 dB**, 50 Hz–15 kHz, three rates, ±6 and ±12 dB | A15 |
| D5 | **Slope stays 12 / 24 dB/oct**, resonance on the second section only so the knob reads the same at both (within 0.002 dB). No 36, no 48 | A15 |
| D6 | **The `(0, 0.01]` mix snap is dropped** with the node it was for: `Filter.c:234` has that threshold, `audiobiquad` does not, so A9's divergence cannot arise here | A9, evidence pack |
| D7 | **`capabilities = ()`.** Nothing in a high-pass is measured in beats; the class never reads `self._transport()` | — |
| D8 | **`tail_samples` = 305 152** — the measured worst case, 303 727 samples at 10 Hz / Resonance 16 / 24 dB/oct / +12 dB trim, rounded up to a multiple of 2048 | A15 |

**Length.** §§1–8 land at about **16 KB** against the vision's 8–12 KB band.
Where the excess is, and why it did not move: **App. R**, last entry. The
band is not met.

---


## Appendix

Run 2026-09-06 on this machine. CPython target:
`audiocomponents/.venv/bin/python`. MicroPython: `cmods/bin/micropython` with
`MICROPYPATH=audiocomponents:audiocomponents/lib`. Probes were scratch
scripts, not committed; every number is reproducible from its description.
A0–A9 share their runs with `LowPass.md`; the rows below are this class's.

### A0. The Zavalishin license, verbatim

Front matter, p. ii of rev. 2.1.0 as read: *"© Vadim Zavalishin. The right is
hereby granted to freely copy this revision of the book in software or
hard-copy form, as long as the book is copied in its full entirety (including
this copyright note) and its contents are not modified."* Verbatim-copy-only,
no derivatives — a paper for our purposes. The PDF is not text-extractable by
the fetch tool; `pypdf` read it in two lines, the route
`agent-knowledge/instrument-sources.md` already recommends.

### A1. Magnitude response against the closed form (48 kHz, stereo, level 6000, `mix=1`)

```
  hp f0= 1000.0 Q=0.707 probe=   500.0  measured  -12.323 dB  ideal  -12.323 dB  dev  +0.000 dB
  hp f0= 1000.0 Q=0.707 probe=  1000.0  measured   -3.013 dB  ideal   -3.012 dB  dev  -0.001 dB
  hp f0= 1000.0 Q=0.707 probe=  2000.0  measured   -0.260 dB  ideal   -0.260 dB  dev  -0.000 dB
  hp f0=  100.0 Q=0.707 probe=    50.0  measured  -12.320 dB  ideal  -12.305 dB  dev  -0.015 dB
  hp f0=  100.0 Q=0.707 probe=   100.0  measured   -3.016 dB  ideal   -3.012 dB  dev  -0.004 dB
  hp f0=  100.0 Q=0.707 probe=   200.0  measured   -0.268 dB  ideal   -0.264 dB  dev  -0.004 dB
```

### A2. |H(f₀)| = Q, and the trap in measuring it

```
  Q=0.500  20log10(Q)= -6.021   HPF@f0  -6.022
  Q=0.707  20log10(Q)= -3.012   HPF@f0  -3.013
  Q=1.000  20log10(Q)= +0.000   HPF@f0  -0.001
  Q=2.000  20log10(Q)= +6.021   HPF@f0  +6.019
  Q=4.000  20log10(Q)=+12.041   HPF@f0 +12.040
  Q=8.000  20log10(Q)=+18.062   HPF@f0 +14.152     <-- source level 6000
```

The Q = 8 row is a clipping artefact, not a coefficient error: at level 6000
the wet path wants ±47 600, the biquad clamps to the sample range
(`audioif_biquad.c:174-175`) and `synthio_mix_down_sample` soft-limits above
±28 000 (`Filter.c:288`). Repeated with headroom the low-pass twin reads
+18.061 dB at level 2000 and +24.082 dB at Q 16. **The kit's T2 measurement
must pick its source level from Q**, and that is also T2's planted fault:
choose a level with Q·level > 28 000 and the measurement must go red.

### A3. Held DC after silence, and the probe design that hid it

The first version of this probe pulled a few blocks past the end of the
`RawSample`. When a `Filter`'s source is exhausted, `Filter.c:202-223` takes
the `sample == NULL` branch and **memsets the output to zero without running
the biquads at all** — every configuration read exactly 0 and the defect
looked absent. Corrected by keeping every pull strictly inside a source still
supplying digital silence (0.09 s of 440 Hz at amplitude 12 000, then 3.0 s
of zeros; 287 of the 289 available 1024-sample blocks pulled). That
correction is the measurement's planted fault: run it two blocks longer and
it goes green on a filter that is still holding DC.

CPython target; MicroPython identical in every row:

```
  LowPass f=100                last     -1  max|.| final block 1
  LowPass f=40 q=8             last     -4  max|.| final block 4
  LowPass defaults(1k)         last     +0  max|.| final block 0
  HighPass defaults(1k)        last     +0  max|.| final block 0
  HighPass f=30                last     -8  max|.| final block 8
  BandPass defaults(1k q.707)  last     +0  max|.| final block 0
  BandPass f=80 q=4            last     -1  max|.| final block 1
  Notch defaults(1k q.707)     last     +0  max|.| final block 0
  Notch f=60 q=8               last     -2  max|.| final block 2
  CombFilter defaults          last     +0  max|.| final block 0
  DynamicEQ defaults           last     +0  max|.| final block 0
```

**Reading it.** Of Gate 0's three candidate answers, a *block-rate tail gate
in Python* cannot see this residual — it lives in the biquad's sub-sample
state (`audioif_biquad.h:14`) and surfaces only as an integer offset — so it
would have to zero the output on a silence heuristic and would clip quiet
material; recommended against. A *DC-clean biquad in an audioif-own module*,
decided once with the per-sample phaser question, is what this seed
recommends. A *recorded disconfirmation* is honest and leaves −72 dBFS of DC
in every rest at a 30 Hz corner, which is this class's T1.

### A4. Mono, A5. Three rates, A7. Desktop cost

Mono `LowPass` and `Notch` matched the closed form to 0.001 dB with
`channel_count=1`; the gain at f₀ = 1 kHz, Q 0.707 read −3.013 / −3.011 /
−3.012 dB at 48 000 / 44 100 / 22 050 Hz; one stereo `Filter` with one biquad
cost 146.6 ns per stereo frame and four cost 195.1 ns, against 20 833 ns of
real time per frame.

### A6. DC and Nyquist gains, f₀ = 1 kHz, Q 0.707, source level 6000

```
  LOW_PASS   @10 Hz    +0.07 dB   @23000 Hz  -240.00 dB
  HIGH_PASS  @10 Hz   -76.74 dB   @23000 Hz    +0.00 dB
  BAND_PASS  @10 Hz   -37.07 dB   @23000 Hz   -44.34 dB
  NOTCH      @10 Hz    +0.07 dB   @23000 Hz    +0.00 dB
```

Two cautions for the kit. The high-pass's theoretical gain at f₀/100 is
−80 dB; the −76.74 dB read here is the **probe's own quantisation floor**
(an int16 sine at amplitude 6000), not the filter — the T3 measurement needs
a higher level, a longer average, or a stated floor. And the `+0.07 dB` rows
are the *reference* rather than the filter: a 10 Hz int16 sine's actual RMS
differs from `level/√2` by about that much, so the kit must compute its
reference from the rendered source, not from the nominal amplitude.

### A8. Latency

Impulse at frame 50 through `HighPass()`: first non-zero output at frame
**50**, peak 18 232 of 20 000; `latency_samples` reports **0**. Agreed.

### A9. `mix` cross-target divergence

```
             CPython   MicroPython
  mix=0.0          0             0
  mix=0.005       80             0
  mix=0.01       159             0
  mix=0.02       317           317
```

(max |out − src| over eight blocks.) `Filter.c:234` bypasses the cascade when
`mix <= 0.01`; the CPython target (`src/cpython/_audioif.c:605-613` via
`src/cpython/audiofilters.py:137-147`) has no such threshold, so below 0.02
the two interpreters are not byte-identical.

### A10. Licence and citation audit, 2026-09-06

This seed's §2 carries the corrections themselves; this is the full
re-verification record behind them. Every source row in §2 and every URL
anywhere in this seed was re-fetched by a second agent that read none of the
first run's notes. Two corrections applied in place. **S1's licence call**
now records the repository's root `LICENSE.md` (full CC BY 4.0), which the
first draft did not mention; the call is downgraded to *licence unverified,
treated as copyleft* because that grant is the mirror's and the chain to RBJ
is unshown, so the treatment (read, never port) is unchanged. And **§1's
quote attributed to "S4 §4.5" does not exist**: the sentence *"the amplitude
response is flipped around ω = 1 in the logarithmic scale"* appears nowhere in
the 520-page book (whole text extracted and searched), and §4.5 is
*Normalized bandpass filter*, an unrelated section. It is replaced by the two
sentences the book does carry, verbatim, at §4.1 p. 97 — *"the highpass
response is a mirrored version of the lowpass response"* and *"applying the LP
to HP substitution to a 2-pole lowpass produces a 2-pole highpass"* — with the
`s ← 1/s` substitution itself cited to §2.10 p. 24. T3's source row is
corrected the same way, and the shape-invariance page moved from 15 to 16.
Re-verified exactly as the seed states them: RBJ's coefficient blocks and the
`α`/`w0` definitions in the `.txt`; the CCRMA pages' *"Copyright © … Julius O.
Smith III / CCRMA, Stanford University"* with **no** licence grant anywhere on
them; Zavalishin's front-matter grant (A0, verbatim, p. ii of rev. 2.1.0);
musicdsp.org's RBJ page carrying no licence, copyright or terms text at all;
native-instruments.com's copy of the book **404** (still not reached); and the
archive.org item `the-art-of-va-filter-design-rev.-2.1.2` carrying **no**
`licenseurl` and no `rights` field (metadata API, per the sources module).

**Unsourced, and flagged as such:** the dropped candidate's attributes above
(a console channel-strip low-cut with a stepped 12/18 dB-per-octave switch)
are stated from general knowledge — no desk schematic or manual was reached in
either run. Nothing in §3 rests on them.

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

**No correction was needed to this seed on this pass.** Both §1 quotes were
opened in the extracted text and are verbatim where cited: *"the highpass
response is a mirrored version of the lowpass response"* and *"applying the
LP to HP substitution to a 2-pole lowpass produces a 2-pole highpass"*, both
on printed p. 97 (§4.1); `s ← 1/s` at §2.10 p. 24; the shape-invariance
sentence on p. 16; `Q = 1/2R` in n. 2 on p. 100. T3's −24.1 dB two octaves
*below* f₀ was re-derived from S1's coefficients at 48 kHz and holds to
0.04 dB for every f₀ from 20 Hz to 1280 Hz, and the f₀/8…f₀/4 slope is
+12.03 dB/oct throughout — this seed's version of the trait looks away from
Nyquist, which is why it is robust where `LowPass`'s is not.

### A12. Trait-critic pass, 2026-09-06 — the bilinear-warp derivations

Re-derivations from S1's own coefficients at 48 kHz, Q 0.707, in float64
(`audiocomponents/.venv/bin/python`, numpy 2.5.2). Arithmetic on the published
formulae, not a render.

**T3, the linear-axis span.** `|H(f₀/4)|` and the slope fitted f₀/8…f₀/4:

| f₀ | \|H(f₀/4)\| | fitted f₀/8→f₀/4 |
|---|---|---|
| 20 Hz | −24.100 dB | +12.025 dB/oct |
| 640 Hz | −24.109 dB | +12.026 dB/oct |
| 1280 Hz | −24.138 dB | +12.027 dB/oct |
| 2400 Hz | −24.234 dB | +12.032 dB/oct |
| 3200 Hz | −24.339 dB | +12.038 dB/oct |
| 4000 Hz | −24.477 dB | +12.045 dB/oct |

3.2 kHz is the last f₀ inside −24.10 ± 0.30 dB, which is where the row's span
comes from; the slope stays inside its own band throughout. Gain at 23 kHz is
−0.0000 dB at every f₀ in the table.

**T4, the two axes.** Maximum \|deviation\| between octave-adjacent f₀ over
f₀/8…8f₀ on the linear axis: 20–40 Hz 0.000 dB, 160–320 0.002, 320–640 0.008,
640–1280 0.030, 1280–2560 **0.121**, 2400–4800 0.435. On the warped axis the
spread across f₀ ∈ {31.5, 125, 500, 1 k, 2 k, 4 k} at a fixed f_a/f_a0 is
**0.00000 dB** at every ratio from 1/8 to 8; the warped-axis values are
−36.125 / −12.305 / −3.012 / −0.264 / −0.017 / −0.001 dB for
r = 1/8, 1/2, 1, 2, 4, 8.

**T6, the cross-rate deviation.** Same f₀, compared against the 48 kHz
response over f ≤ 2205 Hz: 44.1 kHz ≤ 0.005 dB for f₀ ≤ 1 kHz and 0.018 dB at
2 kHz; 22.05 kHz 0.001 dB at 100 Hz, 0.023 at 500 Hz, 0.093 at 1 kHz, 0.380 at
2 kHz. The high-pass survives the old wording where the low-pass and band-pass
do not (their stopbands sit near 0.1·F_s, where the two rates' warps diverge);
the row is still restated against the closed form, because passing by luck of
response shape is not the same claim.


### A13. Palette verification pass, 2026-09-07

Every §4/§5 claim about what an audioif node can and cannot do re-measured
independently; the run and its numbers are in `LowPass.md` A14, which covers
the whole simple-filter unit. What it changed here:

- **`HIGH_PASS` against the closed form:** worst deviation **−0.008 dB** over
  f₀ ∈ {50, 100, 1 k, 10 k, 15 k, 20 k} Hz and probes 50 Hz…20 kHz. The
  §4 figure of 0.015 dB stands and is conservative.
- **A3's −8 LSB reproduced exactly** on the CPython target with the same probe
  and the same 287 blocks. §5's number and its −72.2 dBFS are confirmed.
- **The stock-CircuitPython figure was wrong** and is corrected in §4: a
  30 Hz high-pass on upstream reads **+9.03 dB**, not +21.6. The +21.6 is this
  port's own pre-fix arithmetic, and `upstream-diff.md:1127-1135` says so in
  terms.
- **Trim cannot fold into the biquad's `b` coefficients** — there is no route
  from Python to them, and `A` is discarded outside the shelf and peaking
  modes (measured: `A` of 0.5, 1.0, 2.0 give identical output). §4 now names
  the shelf pair, which measures flat to 0.002 dB.
- **A new cross-target divergence**, recorded in §4: `mix` strictly between 0
  and 1 over a two-biquad cascade renders different bytes on MicroPython and
  CPython. Not in `audioif/docs/upstream-diff.md`; it needs an audioif issue.
- **No node ask survives or arises here.** §5's "None" stands.

### A15. Station A bench, 2026-09-07 — the runs the decisions rest on

Every number in §§3, 4, 6 and 8 above comes from this run.
`tools/phase2_probes/highpass_bench.py`, CPython
(`audiocomponents/.venv/bin/python`, 3.12.3, numpy 2.5.2), audioif 0.2.0 at
the pin `2f6cbc3`, from `ac-wt-highpass/lib`:

```
$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/highpass_bench.py all
```

**D1 — the tier.** A3's probe, both candidate sections, every pull strictly
inside the source. `ported` and `float` are the largest absolute sample in
the last 512-frame block; `float zero@` is the block holding the last
non-zero sample the float node produced.

```
== held DC after silence: ported synthio.Biquad vs audiobiquad ==
   0.09 s of 440 Hz at 12000, then 3.0 s of zeros; 287 of the 289
   available 512-frame blocks pulled
setting                          ported      float  float zero@
f0=10       Q=0.707107          71          0           22
f0=20       Q=0.707107          18          0           16
f0=30       Q=0.707107           8          0           14
f0=60       Q=0.707107           2          0           12
f0=100      Q=0.707107           1          0           10
f0=300      Q=0.707107           0          0           10
f0=1000     Q=0.707107           0          0            9
f0=2000     Q=0.707107           0          0            9
f0=20000    Q=0.707107           0          0            9
f0=30       Q=4                  8          0           37
f0=30       Q=16                 8          0          123
f0=100      Q=16                 1          0           50
```

The ported column reproduces A3's −8 LSB at 30 Hz exactly and is worse than
A3 knew below it: **71 LSB at 10 Hz**, which is −53.3 dBFS of DC held for
ever at the corner a low-cut is most often set to. The float column is exact
zero at every setting, and reaches it.

*The planted fault for this measurement is the probe's own length.* Run it
320 blocks instead of 287 — past the end of the source, where
`audiofilters/Filter.c:202-223` memsets the output without running the
biquads at all — and the ported column reads 0 at every row:

```
$ ... highpass_bench.py dc --overrun
f0=10       Q=0.707107           0          0          312
f0=30       Q=0.707107           0          0          304
f0=30       Q=16                 0        180          320
```

The measurement goes green on a filter that is still holding DC. (The float
column's non-zeros past 289 blocks are `audiocore.RawSample` handing its
buffer back from the beginning — the burst replays — which is the same
overrun seen from the other side.)

**T2 / D5 — the corner gain at both slopes.**

```
== |H(f0)| against 20*log10(Q), audiobiquad, 48 kHz ==
Q        20logQ        12 dB/oct    24 dB/oct    worst dev
0.5      -6.021           -6.021       -6.021        0.000
0.707107 -3.010           -3.010       -3.010        0.000
1        0.000            -0.000       -0.000        0.000
2        6.021             6.021        6.021        0.000
4        12.041           12.041       12.041        0.000
8        18.062           18.062       18.062        0.000
16       24.082           24.082       24.084        0.002
```

**T6 / D2 — the rendered response against S1's closed form at the running
rate.** 45 f₀/probe/rate combinations; the rows that moved, plus every
10 Hz, 8 kHz and 20 kHz row:

```
== rendered vs closed form, audiobiquad, three rates ==
rate     f0       probe        measured     closed        dev
48000    10       10             -3.009     -3.010      0.001
48000    10       40             -0.012     -0.017      0.005
48000    20       5             -24.116    -24.099     -0.016
48000    8000     2000          -25.691    -25.692      0.001
48000    8000     8000           -3.010     -3.010      0.000
48000    20000    5000          -41.644    -41.647      0.003
48000    20000    20000          -3.010     -3.010      0.000
44100    10       10             -3.013     -3.010     -0.003
44100    10       40             -0.032     -0.017     -0.015
44100    20       5             -24.162    -24.099     -0.063
44100    30       7.5           -24.111    -24.099     -0.011
44100    8000     2000          -26.013    -26.013     -0.000
44100    8000     8000           -3.010     -3.010      0.000
22050    10       10             -3.011     -3.010     -0.000
22050    10       40             -0.013     -0.017      0.004
22050    8000     2000          -34.828    -34.828      0.000
22050    8000     8000           -3.012     -3.010     -0.002
worst deviation 0.0628 dB   (over all 45 combinations, not only those shown)
```

**T3 — the skirt, both slopes.**

```
== skirt below f0, audiobiquad, 48 kHz, Q 0.707 ==
f0       slope         |H(f0/4)|   fit dB/oct  at Nyq*0.96
20       12              -24.115       12.026        0.000
20       24              -48.193       24.073       -0.000
160      12              -24.099       12.026        0.000
160      24              -48.167       24.067       -0.000
640      12              -24.109       12.026       -0.000
640      24              -48.182       24.164        0.000
1280     12              -24.137       12.026        0.000
1280     24              -48.245       24.013       -0.000
3200     12              -24.339       12.041        0.000
3200     24              -48.655       24.242        0.000
```

**D4 — the trim shelf.** Deviation from the requested gain, in dB
(`nan` where the probe is above 0.45·F_s):

```
== trim: audiobiquad HIGH_SHELF at 5 Hz, flatness 50 Hz-15 kHz ==
rate     dB            50 Hz      1 kHz     15 kHz
48000    -12         -0.0131    -0.0001    -0.0002
48000    -6          -0.0004     0.0000     0.0000
48000    6           -0.0152    -0.0000     0.0000
48000    12           0.0013     0.0000     0.0001
44100    -12          0.0088     0.0000    -0.0000
44100    -6          -0.0095    -0.0000     0.0000
44100    6           -0.0111     0.0000    -0.0000
44100    12           0.0035     0.0000     0.0000
22050    -12          0.0070     0.0000        nan
22050    -6          -0.0019    -0.0000        nan
22050    6           -0.0031    -0.0000        nan
22050    12           0.0011     0.0000        nan
```

**D8 — the tail.** Full-scale burst then silence; `tail samples` is the
distance from the source going silent to the last non-zero output sample.

```
== tail to exact zero, audiobiquad, 48 kHz ==
   full-scale burst, then silence; first all-zero block and the
   sample index of the last non-zero frame
setting                                  zero block   tail samples
f0=10      Q=16     slope=24  trim=12          151         303727
f0=10      Q=16     slope=24  trim=0           150         302894
f0=10      Q=16     slope=12  trim=12           87         173774
f0=20      Q=16     slope=24  trim=12           98         195480
f0=30      Q=16     slope=24  trim=12           67         132293
f0=100     Q=16     slope=24  trim=12           31          57866
f0=1000    Q=16     slope=24  trim=12            8          11559
f0=10      Q=0.707107 slope=12  trim=0             6           7866
f0=20000   Q=0.5    slope=12  trim=0             3             17
worst tail after the source goes silent: 303727 samples (6.328 s at 48 kHz)
```

**Latency.**

```
== latency: click at frame 50, 48 kHz and 44.1 kHz ==
rate 48000 slope 12 dB/oct: first non-zero output frame 50 (input at 50), peak 19816
rate 48000 slope 24 dB/oct: first non-zero output frame 50 (input at 50), peak 32767
rate 44100 slope 12 dB/oct: first non-zero output frame 50 (input at 50), peak 19800
rate 44100 slope 24 dB/oct: first non-zero output frame 50 (input at 50), peak 32767
```

**D2 — the grid.** What one step of the 0-127 Frequency macro is worth on
the three candidate spans, and how much of the knob sits where a low-cut is
used:

```
== the Frequency macro's log grid ==
    10 Hz ..   2000 Hz: 7.64 octaves, 72.2 cents per step, 72 of 127 steps below 200 Hz
    10 Hz ..  20000 Hz: 10.97 octaves, 103.6 cents per step, 50 of 127 steps below 200 Hz
    20 Hz ..  20000 Hz: 9.97 octaves, 94.2 cents per step, 42 of 127 steps below 200 Hz
```

The seed's 10 Hz…2 kHz span buys 72 cents a step against 104, and 72 of 127
steps below 200 Hz against 50. Neither number is the difference between a
usable knob and an unusable one — 104 cents is under a semitone — and the
2 kHz ceiling costs a real setting (a high-pass at 4–8 kHz is how a
presence-only send or a telephone voice is made) and would have retired four
measured rows of `test_cpython_effects_dynamics_eq.py`. The wider span is
taken.

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
that band. **Exact zero after silence is red, and for this class it is worse
than for any other in the family**: `HighPass(frequency=30.0)` holds **−8 LSB
for ever** on both interpreters (A3). A high-pass exists to remove DC; the
one that removes it least is the one asked to remove it hardest.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** RBJ, *Cookbook formulae for audio EQ biquad filter coefficients* (plain text, shepazu mirror) | the HPF coefficients, `α = sin(w0)/(2Q)`, `w0 = 2π f0/Fs`, verbatim | the `.txt` itself carries **no license, copyright or warranty line** (re-verified 2026-09-06, all five terms searched) — but the repository serving it does: its root `LICENSE.md` is the full **CC BY 4.0** text (read at https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/LICENSE.md; GitHub's own licence API reports the repo as `NOASSERTION`). That is the *mirror's* grant, not RBJ's: the mirror's HTML rendering says only *"Adapted from Audio-EQ-Cookbook.txt, by Robert Bristow-Johnson, with permission"*, so the chain to the author is **not** shown (sources module: a repackager's label is an assertion). **License unverified — treated as copyleft:** read as a document for its mathematics, never ported | https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* — "Quality Factor (Q)", "Decay Time is Q Periods" | Q = f₀/bandwidth; the envelope reaches e^{−π} in Q periods | © J. O. Smith III / CCRMA Stanford; no license granted. Read as a paper | https://ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html , …/Decay_Time_Q_Periods.html | 2026-09-06 |
| **S4** Zavalishin, *The Art of VA Filter Design* rev. 2.1.0 (discoDSP mirror, text via `pypdf`) | the LP→HP substitution `s ← 1/s` (§2.10 p. 24) and the mirrored 2-pole response (§4.1 p. 97); R as damping and `Q = 1/2R` (§4.2 p. 100, and its n. 2) | verbatim-copy-only, no derivatives (grant quoted in A0). Read as a paper | https://www.discodsp.net/VAFilterDesign_2.1.0.pdf | 2026-09-06 |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T2 | **The corner gain is the resonance**: \|H(f₀)\| = Q exactly, **at both slopes** — Q 0.707 → −3.01 dB, Q 2 → +6.02, within 0.05 dB. The 24 dB/oct pair is scaled so the knob reads the same at either setting (§4) | S1, derived analytically and measured (A2, A15) | high | any Q in 0.5–16 more than 0.05 dB from 20·log₁₀(Q) at f₀, at either slope | steady-state sine at f₀, Q ∈ {0.5, .707, 1, 2, 4, 8, 16}, source level picked from Q so Q·level stays inside full scale — that choice is also T2's planted fault (A2) |
| T3 | **+12 dB/oct skirt, doubled at the steep slope, unity above**: at 12 dB/oct, −24.10 ± 0.30 dB two octaves *below* f₀ at Q 0.707 and a fitted f₀/8…f₀/4 slope of +12.03 ± 0.30 dB/oct, **for every f₀ from 20 Hz to 3.2 kHz at 48 kHz**; at 24 dB/oct the same two numbers double, to −48.2 ± 0.6 dB and +24.1 ± 0.6 dB/oct. This is the widest linear-axis span of any row in this family, because the skirt it fits sits *below* f₀ where the bilinear transform barely warps; the drift is monotonic and reaches −24.48 dB by f₀ = 4 kHz, which is where the span ends. And 0.00 ± 0.1 dB at Nyquist at every f₀ and Q: numerator and denominator both sum to 2(1+cos ω₀) at `z = −1` | S4 §4.1 p. 97 (the highpass is the mirrored lowpass), S1; the span and the −24.48 dB figure re-derived from S1 in A12; both slopes measured in A15 | high | fitted slope outside +11.7…+12.3 dB/oct (or +23.4…+24.6 at the steep slope) over f₀/8…f₀/4, or \|H(f₀/4)\| outside its band, at any f₀ ≤ 3.2 kHz; or a gain at 0.48·F_s outside ±0.1 dB at any f₀ | swept sine; slope fitted f₀/8…f₀/4 at f₀ ∈ {20, 160, 640, 1280, 3200} Hz, both slopes; gain read at 23 kHz (A6, A15) |
| T6 | **Rate-honest — against the closed form at the running rate**: at 44.1 kHz and 22.05 kHz the corner stays at f₀ within 0.1 %, \|H(f₀)\| stays at Q, and the rendered response matches S1's closed form **evaluated at the running rate** within 0.1 dB up to 0.45·F_s, over the whole 10 Hz … 20 kHz span. The high-pass happens also to satisfy the stronger cross-rate reading (A12) — but that is a property of this response shape, not the requirement: the warp belongs to the rate, and a class that reproduced the 48 kHz shape at 22.05 kHz would be the wrong filter | S1 (the BLT prewarps f₀ at whatever rate is running); measured at three rates (A5, A15); the cross-rate deviations re-derived in A12 | high | corner displaced >0.1 %, gain at f₀ more than 0.1 dB from 20·log₁₀(Q), or any swept point more than 0.1 dB from the closed form **at that rate** | T4's sweep at 48 000 / 44 100 / 22 050 Hz, each differenced against its own closed form (A15: worst 0.063 dB over 45 f₀/probe/rate combinations) |
| T1 | **Exact zero at DC**: the numerator sums to zero at `z = 1`, so a DC step or a held offset decays to *exact* zero, not to a small residue, at every f₀ from 20 Hz up | S1 (HPF numerator), verified analytically | high | any settled output not bit-exactly zero after a DC step, at any f₀ ≥ 20 Hz | DC step of ±0.5 FS, 5 s, last block read while the source still supplies the offset; then the same with the offset removed (A3's method) |
| T4 | **Shape invariance under cutoff — on the warped axis**: the axis the response is one curve on is the **bilinear-warped** one. Against f_a/f_a0 with `f_a = (F_s/π)·tan(πf/F_s)` it is f₀-independent to **0.00000 dB** for every f₀ from 20 Hz to 0.4·F_s. Against the linear f/f₀ it slides without deforming within 0.1 dB only while **f₀ ≤ 1280 Hz at 48 kHz** — the shipped probe set's own ceiling, and not a coincidence: 640 vs 1280 Hz differ by 0.030 dB, 1280 vs 2560 by 0.121 | S4 §2.7, p. 16 for the prototype's invariance; both axes re-derived from S1 in A12 | high | on the warped axis, any two f₀ in 20 Hz…0.4·F_s differing by >0.05 dB at the same f_a/f_a0; on the linear axis, two f₀ an octave apart, both ≤ 1280 Hz, differing by >0.1 dB anywhere in f₀/8 … 8f₀ | swept sine at f₀ ∈ {20, 40, 80, 160, 320, 640, 1280} Hz, resampled onto f_a/f_a0 and, for the linear-axis half, onto f/f₀ |
| T5 | **Q is the ringing**: struck with a click it rings at f₀, envelope down to 4.3 % of peak after Q periods | S3, "Decay Time is Q Periods" | medium — stated for Q ≫ ½, so the kit tests Q ≥ 2 | e^{−π} reached in <0.8 Q or >1.25 Q periods for Q ∈ {2, 4, 8, 16} | impulse, Hilbert envelope, time to −27.3 dB ÷ (1/f₀) |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §3, Tier 3, Station A)*

Basis for the Tier 3 budget: 76 instructions per sample per biquad on
Cortex-M4/M7 (`audioif/docs/upstream-diff.md:1172`); desktop anchor 147 ns
per stereo frame against a 20 833 ns budget, +16 ns per extra section (A7).

*(from §4, Station A)*

**Mix at 24 dB/oct.** At 12 dB/oct Mix is exactly the dry/wet blend it reads
as; at 24 dB/oct it is that blend applied to each of the two poles in turn —
a smooth walk from wire to cascade, but not one half of the fourth-order
response. A splitter and a mixer around the pair would cost two nodes and
put an int16 sum on the dry path, so it is not taken and the honest sentence
is in the class docstring instead.

**Why the trim is a shelf.** No node on the palette gives gain above unity
(`MixerVoice.level` clamps to 0..1, `audiomath.Multiply` only attenuates),
and there is no route from Python to a biquad's `b` coefficients:
`synthio.Biquad` exposes only `mode`, `frequency`, `Q` and `A`
(`audioif/src/synthio/Biquad.c:228-233`) and `A` is read only when
`mode >= PEAKING_EQ` (`:82-83`), so in `HIGH_PASS` mode it is discarded
(measured, A13). A shelf at a subsonic corner is how a high-pass gets its
make-up.

*(from §8, Station A)*

**The length rule is not met, and this is where the excess is.** §§1–8 are
about 16 KB. The Tier 2 table alone is 5 KB — six rows whose statements,
disconfirmations and measurement ids are what the class gate reads, so they
cannot move here without moving the gate. §6's two tables (1.7 KB) are the
frozen surface; §8's eight decisions (2.1 KB) are what Station A exists to
produce. Everything that could move has: the source readings (App. S), the
full Tier 2 rows (App. T), and eleven blocks of §§1–8 prose below.

*(from §2)*

**Standout confirmed.** The candidate weighed and dropped was a console
channel-strip low-cut (a fixed-frequency or stepped 12/18 dB-per-octave
switch): it contributes only the slope and stepped-frequency behaviour §6
adopts as macros, and naming a specific desk would imply component values
this class does not chase. Design grade stands; Tier 2 is stated anyway
because it is free and falsifiable.

*(from §2)*

**Independent licence and citation audit, 2026-09-06** (a second agent, none
of the first run's notes read; full record in Appendix A10). Two corrections
are applied above. **S1's licence call** now records the root `LICENSE.md`
(full CC BY 4.0) the serving repository carries — downgraded to *licence
unverified, treated as copyleft* because that grant is the mirror's and the
chain to RBJ is unshown, so the treatment is unchanged. And **§1's quote
attributed to "S4 §4.5" does not exist**: that sentence appears nowhere in the
520-page book, and §4.5 is *Normalized bandpass filter*, an unrelated section.
It is replaced by the two sentences the book does carry, verbatim, at §4.1
p. 97, with `s ← 1/s` cited to §2.10 p. 24; T3's source row is corrected the
same way and the shape-invariance page moved from 15 to 16. The dropped
candidate's stepped 12/18 dB-per-octave desk filter is **unsourced** general
knowledge; nothing in §3 rests on it.

*(from §2)*

**Second licence-and-citation audit, 2026-09-06** (a third pass, independent
of the first audit; **every URL in this seed re-fetched in this run**, every
licence read again at its own source, every Zavalishin page opened in the
extracted text). **No correction was needed to this seed.** The S1 and S4
calls above are re-confirmed unchanged, and both §1 quotes — *"the highpass
response is a mirrored version of the lowpass response"* and *"applying the
LP to HP substitution to a 2-pole lowpass produces a 2-pole highpass"* — are
verbatim on printed p. 97 where they are now cited. Full record, with every
quote and status code, in `A11`.

*(from §3)*

**Trait-critic pass, 2026-09-06.** T3, T4 and T6 rewritten in place for the
root defect shared across this family: the *analog* prototype's log-axis
properties were stated as though digitisation preserved them at every f₀, and
the bilinear warp does not. Each now names its axis and span, with the closed
form carrying the claim outside it. Figures re-derived from S1's coefficients
in A12; no row deleted. T1, T2 and T5 unchanged. **Six Tier 2 rows after the
pass.**

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: **ESP32-P4
≤ 1.5 %, ESP32-S3 ≤ 5 %** at the 12 dB/oct default, **≤ 2.5 % / ≤ 9 %** with
24 dB/oct engaged. Lean patch expected: **no**. Basis: 76 instructions per
sample per biquad on Cortex-M4/M7 (`audioif/docs/upstream-diff.md:1172`);
desktop anchor 147 ns per stereo frame against a 20 833 ns budget, +16 ns per
extra section (A7).

*(from §4)*

*Slope 24 dB/oct* is a second `Biquad` in the same cascade with the
Butterworth Q pair (0.5412, 1.3066) scaled by the resonance macro. *Mix* is
`Filter`'s own slot (`Filter.c:232`), clamped away from `(0, 0.01]`. *Trim*
is a `LOW_SHELF` + `HIGH_SHELF` pair at one corner sharing one `A`, appended
to the same cascade — measured flat to 0.002 dB from 50 Hz to 15 kHz over
−6…+12 dB (`LowPass.md` A14), stock, one float store per shelf on a macro
move. It cannot fold into the high-pass section's own coefficients:
`synthio.Biquad` exposes only `mode`, `frequency`, `Q` and `A`
(`audioif/src/synthio/Biquad.c:228-233`) and `A` is read only when
`mode >= PEAKING_EQ` (`:82-83`), so in `HIGH_PASS` mode it is discarded.
*Mono:* a mono source gets the identical filter (A4); nothing here is stereo
by definition.

*(from §4)*

**One palette hazard the rebuild must document.** `Filter`'s `mix` blends the
source against the **whole cascade's** output on MicroPython/CircuitPython
(`audioif/src/audiofilters/Filter.c:279-283` then `:288`) and against the
**last stage's input** on the CPython target
(`audioif/src/cpython/audiofilters.py:140`). One biquad at any `mix`, and any
cascade at `mix` 0 or 1, agree byte for byte; two biquads at `mix = 0.5`
render different bytes on the two desktop targets (`LowPass.md` A14). That is
Slope 24 dB/oct with the Mix macro off its ends, so §6's surface as proposed
breaks Tier 1's identical-bytes invariant: the rebuild keeps the mixed stage
single, or the divergence is fixed in audioif. It is a palette defect, not a
class defect.

*(from §4)*

**Portability tier: stock.** A *stock CircuitPython* board runs upstream's
Q15 biquad, where a 30 Hz high-pass reads **+9.03 dB at its own corner**
rather than −3 — upstream's own measurement, from a build of upstream `main`
(`audioif/docs/upstream-reports/biquad-band-edges.md:147`; the summary of it
at `audioif/docs/upstream-diff.md:1127-1135`, and the stock-board note at
`:1223-1226`). The **+21.6 dB** in `upstream-diff.md:1116` is *this port's*
pre-fix arithmetic, which the paragraph beneath that table disowns in terms
("Do not quote this table upstream") — it is not what a stock board does. On
such a board this class's low-corner traits still do not hold, and the
docstring and README row say so. It is a property of the board, not of the
class.

*(from §5)*

The exception is a **Tier 1** item that also disconfirms **T1**, and the
roadmap reserves it for Gate 0 rather than for a per-class ask: the held-DC
residual (audioif#23). `HighPass(frequency=30.0)` settles on **−8 LSB
(−72.2 dBFS) of DC and holds it indefinitely**, on both interpreters (A3) —
the largest residual in the family, and directly against the one thing a
high-pass is for. This seed's contribution is that number, which audioif#23
did not have (it reported the two `LowPass` configurations), and a
recommendation: the DC-clean audioif-own biquad, for the reason in A3. If
Gate 0 instead records a disconfirmation, **T1 becomes a stated limitation of
the class below about 60 Hz** and the docstring says so in dBFS.

*(from §7)*

- **`q` is frozen at construction.** `synthio.Biquad(self.MODE,
  self.frequency, Q=q)` (`eq.py:104`) takes a bare float where `frequency`
  gets a block (`eq.py:102-103`) — the corner sweeps, the resonance cannot.

*(from §7)*

- **`set_frequency` is off-contract and it raises.** `eq.py:110-111` calls
  `_core.check_hz`, which raises at or above Nyquist (`_core.py:471-474`)
  instead of clamping — against the rate-honest invariant's *"never refused
  at construction or at `set_macro`"*.

*(from §7)*

- **No tail is declared.** `TAIL_SAMPLES = None`, `LATENCY_SAMPLES = 0`
  (`_core.py:140-141`): latency 0 is right and measured right (A8), the tail
  of a ringing filter is unstated.
