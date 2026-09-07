# Effects Dossier — `Reverb` (EMT 140 plate · Fender 6G15 spring · Dattorro tank)

**Class:** `lib/audioeffects/reverb.py` — read once, for §7, and not otherwise
consulted.
**Family / phase:** Time, roadmap Phase 5
**Standout:** vision §4.2's "EMT 140 plate; Fender 6G15 spring; hall, room,
chamber (Dattorro)" — **confirmed, refined** (§2): Dattorro's network *is* the
plate-class topology, so it is the structure for **all five** characters,
re-tuned; the EMT 140 and the 6G15 fix the traits that tuning must hit.
**Grade:** **literature** — the reverberant element of both standouts is a
steel sheet and a helical spring, not a circuit, and no unit is on the bench.
Every Tier 2 number is a published model over published geometry, or a drawing
that surrounds the tank.
**Portability tier:** needs audioif-own nodes (**ask N-tank**, §5); no stock
build reaches the traits — `audiofreeverb.Freeverb` fails five of nine (§4).
**Status:** seed (Phase 0)

## 1. The circuit, in one paragraph

Three, because only one of the three families has a circuit.

**Plate (EMT 140).** A 2 m × 1 m steel sheet 0.5 mm thick, hung in a
tubular-steel chassis under tension by two wires at each corner, driven by an
electrodynamic actuator and picked up by **two accelerometers** — so the
stereo image is two positions on one sheet. No filter, no LFO, no
nonlinearity: the only control is mechanical, a **porous panel moved between
11 and 66 mm from the plate**, shortening the decay by changing the near-field
impedance and so raising radiated power (S2 §1.1.1, §3.4.3). Two facts follow
from physics, not from a panel: bending waves give a plate **approximately
constant modal density with frequency** (S2 §5.2 and its fig. 5.3, computed
from Arcas's relation) — the contrast drawn against a room's rising density is
*unsourced this run* and is not what T2 is measured against; and its
thermoelastic loss is within 5 % of its asymptote **above about 500 Hz**
(S2 §3.4.1), so above 500 Hz the decay is shaped by radiation — what the
damper moves (S2 §3.4.3).

**Spring (Fender 6G15).** The circuit is real and entirely *around* the tank
(full chain and values in App. C). Three things in it are traits. The **Dwell**
250 K-L pot sits *before* the 6K6GT driver, so it is a drive control, not a wet
level. The coupling into that driver's grid is **`.002` µF into 220 K — a
first-order high-pass at 362 Hz**, so the Gibbs/Accutronics tank (4AB3C1C,
most units 4AB3C1B, S7 — how many springs it holds is unsourced) never sees
bass, while the dry reaches the **Mixer** 250 K-L through `.1` µF and is flat
to 6.4 Hz. And the wet returns through the recovery stage — a **7025** on the
drawing, which S7 calls a 12AX7 — into the **Tone** 50 K-L pot and a `.00025`
µF series capacitor, which is a further high-pass on the wet alone (S6).

**Algorithmic (hall, room, chamber).** Dattorro Fig. 1: predelay, a one-pole
input **bandwidth** filter, four series all-pass input diffusers (142, 107,
379, 277 samples at Fs = 29761 Hz), then a cross-coupled **figure-eight
tank** — per side a modulated all-pass (672 / 908 + EXCURSION), a delay
(4453 / 4217), a one-pole **damping** filter, ×decay, a second all-pass
(1800 / 2656), a final delay (3720 / 3163) feeding the *other* side. Output is
**seven taps per channel at ±0.6** drawn from inside the tank (S1 Table 2);
the input is summed to mono and the image is made entirely by those taps
(§1.3.6). Coefficient defaults in App. A.

## 2. Sources and license calls

Every row below was fetched again, from this machine, during the licence and
citation audit of 2026-09-06: the three HTML pages with WebFetch, the **six**
PDFs over HTTP (all HTTP 200), their text extracted with `pypdf`, and the
three scanned drawings that carry no extractable text — Dattorro's Fig. 1 and
both 6G15 pages — rendered with `pypdfium2` at scale 4 and read as images.
Quotations in App. A. Nothing from memory. Where no licence text exists the
call is the vision §5 default: **unverified is treated as copyleft** —
measured or read, never ported. Where one *does* exist it is quoted (S5, S7,
S8).

| # | Source | Licence as read | Reached |
|---|---|---|---|
| S1 | [Dattorro, *Effect Design, Part 1*, JAES 45(9):660–684 … (App. S1) | no rights statement in the PDF … (App. S1) | HTTP 200; OCR text extracted, Fig. 1 rendered and read |
| S2 | [Russo, *Physical Modeling and Optimisation of a EMT 140 Plate Reverb* … (App. S2) | p. 2 carries the bare line "Copyright © … (App. S2) | HTTP 200; text extracted, copyright line read on p. 2 |
| S3 | [Parker & Bilbao, *Spring Reverberation: A Physical Perspective* … (App. S3) | no rights statement in the PDF and none on … (App. S3) | HTTP 200; text extracted |
| S4 | [Bilbao, *Numerical Simulation of Spring Reverberation* … (App. S4) | as S3 → **licence unverified … (App. S4) | HTTP 200; text extracted |
| S5 | [McQuillan & van Walstijn, *Modal Spring Reverb…* … (App. S5) | **CC BY 3.0 Unported** … (App. S5) | HTTP 200; text extracted, p. 1 rendered at scale 3 and the licence footer read |
| S6 | [Fender, *Reverb 6G15* schematic + layout … (App. S6) | no notice on the drawings … (App. S6) | HTTP 200; both pages rendered and read |
| S7 | [Wikipedia, *Fender Reverb … (App. S7) | **CC BY-SA 4.0**, read in the page footer | WebFetch, page footer read |
| S8 | [Designing Sound, *EMT 140 Plate … (App. S8) | **CC BY-NC-SA 3.0 Unported** … (App. S8) | WebFetch, notice read |
| S9 | [Vintage Technology Archive … (App. S9) | no licence, copyright or terms notice on the … (App. S9) | WebFetch, footer read |

**Audit, second pass — independent, 2026-09-06.** Every URL in this seed
re-fetched from this machine by a second agent, every quotation re-read
against the source it names, every arithmetic figure recomputed, and the §3
wire-note probe re-run. **Five corrections:**

1. **S5's licence was wrong.** It carries a Creative Commons Attribution 3.0 …  *(argument in full: App. R)*
2. **S2's licence call overstated what the page says.** "All rights reserved …  *(argument in full: App. R)*
3. **"Seven PDFs" was six**, and one of the three rendered scans
   (Dattorro's) sits inside a PDF that *does* carry extractable text.
4. **T5's "≥10 dB" is ours, not S3's.** S3 says only that the above-F_C …  *(argument in full: App. R)*
5. **App. C's quotation of the drawing's notes** was completed against both
   S6 pages, which differ by a "10% TOLERANCE" clause.

Everything else in §§1–3 was re-read against its source and stands; what was
checked, and the numbers that reproduced, are in **App. H** — including the
§3 wire-note probe, re-run on this machine to the same 9584 of 9600 samples.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

M1–M8 and their planted faults are in App. E; the figures behind T4, T5 and
T7 in App. B and C. Characters carry their own rows.

**Plate** — `Steel Plate` unless a row names another patch

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| T1 | **The density is there from the first millisecond**: the M1 echo-density curve (local maxima per 10 ms window, impulse probe) reads within ±20 % of its 200 ms value by 20 ms after onset, and no window between 20 and 200 ms sits more than 20 % below the 200 ms value. | S1 §1.2, verbatim (App. A) … (App. T1) | high for the … (App. T1) | Any 10 ms window between 20 and 200 ms more than 20 % below the 200 ms value — a density still building | M1 |
| T2 | **Modal density is flat with frequency, not rising**: over the 0.5–1.5 s tail segment (one Hann-windowed 48 000-point FFT, ≈1 Hz bins), spectral maxima of ≥6 dB prominence counted per Hz in 2–4 kHz, divided by the same count in 200–400 Hz, is **≤ 2.0**. | S2 §5.2 and fig. 5.3's caption (App. H) … (App. T2) | medium — a figure … (App. T2) | A ratio above 2.0: more modes per Hz at the top of the band than the bottom, which is a room's behaviour and not a plate's | M2 |
| T3 | **The decay is frequency-dependent, because the damper is radiation loss**: at five Decay positions (T60 targets 0.5 / 1 / 2 / 4 / 8 s) the ratio R = T60(500 Hz)/T60(4 kHz) — each T60 from a **least-squares log-envelope slope fit over −5…−35 dB**, never a −60 dB crossing (App. E, M3) — is non-decreasing as Decay shortens, and R at the shortest position exceeds R at the longest by **≥ 20 %**. | S2 §3.4.1 (loss near-constant above 500 Hz) … (App. T3) | medium for the … (App. T3) | R changing by less than 20 % end to end, or falling as Decay shortens | M3 |

**Spring** — `Long Tank`, `Surf Tank`

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| T4 | **A discrete echo train whose spacing scales with Size**: at Size 1.0 the first non-zero-lag autocorrelation peak of the wet impulse response lies in **30–53 ms** — S3's five measured springs, recomputed in App. B — at least **four** further peaks fall at integer multiples of it ±10 %, and halving Size halves that spacing ±10 % over Size 0.35–1.8. | S3 eqs. 2 and 3 over its own Tables 1–2 … (App. T4) | high for the span and … (App. T4) | No repeating peak; a Size-1.0 first peak outside 30–53 ms; fewer than four multiples; or a Size halving that does not halve the spacing within ±10 % | M4 |
| T5 | **Two regions split at F_C, the upper one faster and quieter**: on `Surf Tank` (Dispersion 1.0) the split lies in **2.5–4.9 kHz** (S3 eq. 4 over the same five springs, App. B); below it the echoes repeat at T4's spacing, above it at **≤ 0.7 ×** that spacing, and the above-F_C band energy over the first 500 ms is **≥ 10 dB below** the sub-F_C band's. | S3 §3 and eq. 4; S4 §4.3 independently (both … (App. T5) | medium-high for the … (App. T5) | One echo period across the whole band; above-F_C energy less than 10 dB down; an above-F_C period longer than 0.7 × the sub-F_C one; or a split outside 2.5–4.9 kHz at Dispersion 1.0 | M5 |
| T6 | **Each sub-F_C echo is an upward chirp**: across the first echo the M6 STFT ridge, tracked over 100 Hz–F_C, is non-decreasing frame to frame within ±5 %, and its last frame's ridge frequency is **≥ 2 ×** its first frame's. | Derived from S3 §4 and §4.1 read together … (App. T6) | medium (derived) … (App. T6) | A falling ridge, a flat one, or a rise of less than a factor of 2 across the first echo | M6 |
| T7 | **The tank sees no bass and the dry does**: with Low Cut at the spring patches' 360 Hz default the wet path is **−3 ±1 dB at 362 Hz**, falls at **6 ±1 dB/octave** over 90–180 Hz and sits **≥ 12 dB below its 1 kHz level at 90 Hz**; the dry path is within **±0.1 dB of flat from 20 Hz to 1 kHz** at every macro setting; and the wet corner follows the Low Cut macro within ±10 % across 20–500 Hz. | S6's drawing: `.002` µF into 220 K at the … (App. T7) | high for the … (App. T7) | A wet path within 1 dB of flat at 100 Hz; a slope outside 6 ±1 dB/oct; any dry-path deviation beyond ±0.1 dB above 20 Hz; or a wet corner that does not follow Low Cut | M7 |

**Hall / room / chamber**

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| T8 | **These three build their density and the plate does not** — the contrast is what makes them different characters: on `Small Room`, `Concert Hall` and `Dark Chamber` the M1 curve rises by **≥ 50 %** between 20 and 200 ms, on the probe and counting rule T1 uses to show the plate flat. | S1 §1.2, verbatim (App. A) … (App. T8) | high for the … (App. T8) | Any of the three rising less than 50 % between 20 and 200 ms: a plate wearing a hall's name | M1 |
| T9 | **The three are three tunings, not one name three times**: at the shipped patches T60(1 kHz) on `Concert Hall` is ≥ 2 × `Live Room`'s and ≥ 4 × `Small Room`'s; the first wet arrival is ≥ 25 ms on `Concert Hall` and ≤ 15 ms on both rooms; and no two of the five characters are constructed from the same tank line-length set. | **design** — §6 and App. F of this seed. No … (App. T9) | design | Any two characters built on identical line lengths, or a `Concert Hall` that does not clear the two rooms by the stated margins | M8 |

**All tank characters** — plate, hall, room, chamber

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| T10 | **Modulated tank taps move the picket fence**: on `Steel Plate` and `Concert Hall`, at Mod Depth zero the tail spectrum shows periodic notches at the tank loop period; at the source's excursion (EXCURSION 16 at 29 761 Hz ⇒ 26 samples at 48 kHz) and 1 Hz, the centre of the deepest notch below 2 kHz moves **≥ 20 cents peak-to-peak over one modulation period**. | S1 Table 1 (EXCURSION 16) … (App. T10) | medium — depth and … (App. T10) | A notch centre moving less than 20 cents peak-to-peak at full depth | M6 |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Compose-first, and it does not reach.** Three nodes were read and probed
this run; the measurements are in App. D and the Freeverb reading in App. G.

- **`audiofreeverb.Freeverb`** is a *fixed* Schroeder network. The comb and …  *(argument in full: App. R)*
- **`audioecho.FeedbackDelay`** is a two-line cross-coupled tank already: an …  *(argument in full: App. R)*
- **The tank cannot be assembled from several nodes at all**: this is a pull …  *(argument in full: App. R)*
- **`audioconvolve.Convolver`** reaches any character exactly and is the …  *(argument in full: App. R)*

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**Ask N-tank — an algorithmic reverberation tank in an audioif-own module.**

- **Traits it unblocks:** T1, T2, T3, T8, T9, T10 directly; T4, T5, T6 through the
  same node's optional dispersive all-pass chain — one node, two options.
- **What the palette does instead, and the measurement.** Freeverb is the only …  *(argument in full: App. R)*
- **The ask, additive.** A new module (`audioverb`, say) whose `Tank` takes …  *(argument in full: App. R)*
- **Refutation record (Phase 0, re-run 2026-09-07 by the palette verifier).** …  *(argument in full: App. R)*
- **Cost estimate.** ~50 multiply-adds and 12 line reads per frame; 72.6 KB of
  int16 line at 48 kHz for the plate tuning, scaled by Size.

No second ask; the dry/wet sum, the predelay and the output trim compose.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | `Decay` | UNIPOLAR | T60 0.2–12 s, log | the EMT 140 damper; Dattorro `decay` |
| 1 | `Size` | UNIPOLAR | 0.35–1.8 × reference lines | plate area; spring length (T4) |
| 2 | `Predelay` | UNIPOLAR | 0–200 ms | the send delay a studio patched by hand |
| 3 | `Diffusion` | UNIPOLAR | input diffusion 0–0.9 | Dattorro's two input-diffusion knobs, ganged |
| 4 | `Damping` | UNIPOLAR | 1–20 kHz log, clamped | the damper's frequency dependence (T3) |
| 5 | `Bandwidth` | UNIPOLAR | 500 Hz–20 kHz log, clamped | Dattorro `bandwidth` |
| 6 | `Low Cut` | UNIPOLAR | 20–500 Hz log | the 6G15's `.002`/220 K into the tank (T7) |
| 7 | `Mod Depth` | UNIPOLAR | 0–2 ms excursion | Dattorro EXCURSION (T10) |
| 8 | `Mod Rate` | UNIPOLAR | 0.1–5 Hz | S1 fn. 14's "order of 1 Hz" |
| 9 | `Dispersion` | UNIPOLAR | 0–1 → chain order and F_C | the spring itself (T5, T6) |
| 10 | `Drive` | UNIPOLAR | 0–1 into the tank's soft clip | the 6G15 **Dwell** — drive, not level |
| 11 | `Width` | UNIPOLAR | 0–1 over the tap sets | the plate's two accelerometer positions |
| 12 | `Tone` | BIPOLAR | ±12 dB wet tilt | the 6G15 **Tone** pot |
| 13 | `Mix` | UNIPOLAR | 0–1; 0 is the structural bypass | the 6G15 **Mixer** |
| 14 | `Level` | UNIPOLAR | −12…+6 dB | nothing — output trim |

Fourteen of sixteen. **Characters** are a constructor option
(`character="plate"|"spring"|"hall"|"room"|"chamber"`, default `"plate"`), not
a macro, because each re-cuts the line lengths and the tap table at
construction; every patch names its character. `capabilities`: **`()`** —
nothing in a plate, a spring or Dattorro's network references a beat (§8.3).
Patches: `Steel Plate` · `Short Plate` · `Damped Plate` · `Long Tank` ·
`Surf Tank` · `Small Room` · `Live Room` · `Concert Hall` · `Dark Chamber` ·
`Bright Chamber` · `Slow Bloom` · `Plate — lean` (the S3 escape valve, never a
compromise of `Steel Plate`). Settings in App. F.

## 7. Defects in the current class the rebuild must not repeat

- **A plate and a spring are two numbers**: `_PRESETS` gives each a
  `(roomsize, damp)` pair into the same Freeverb (`reverb.py:23-30`, `:52-54`)
  — five names, one Schroeder network, no dispersion, no plate density, no
  echo train.
- **No surface**: `MACRO_LABELS = ()`, `PATCHES = {0: ("Default", ())}`
  (`reverb.py:39`, `:41`), so `set_mix` (`:57-58`) is unreachable from a host.
- **`deinit()` leaves an intermediate node live**: the spring preset builds an
  `audiodelays.Echo` and never records it (`reverb.py:47-51`);
  `_core.py:376-384` deinitialises `_output` only. Measured: after
  `deinit()`, `audiocore.get_buffer(r.flutter)` still returns 2048 bytes
  (App. D) — the exact planted fault vision §3 names.
- **`reset()` reaches one node**, same cause (`_core.py:366-374`).
- **Latency and tail undeclared**: no `LATENCY_SAMPLES`, no `TAIL_SAMPLES`, so
  `_core.py:245-248` reports 0 and `:250-253` `None`, against a tail measured
  here at 0.85 s.
- **Not level-honest, not a wire at mix 0** — the node's fault, but the class
  puts the dry through it (`reverb.py:53`): a 30000-peak sine at `mix=0`
  returns at 28219 (App. D).
- **The "boingy pre-flutter" is a 33 ms echo at 0.45 feedback with
  `freq_shift=True`** (`reverb.py:47-49`) — a doppler, not dispersion, sitting
  *before* the reverb rather than being it.

## 8. Open questions

1. **Structural bypass at mix 0** (§3) changes `output`'s identity at runtime.
   The contract does not forbid it; nothing has exercised it. *Settles:* the
   implementation session in Phase 5, with the alternative on record — declare
   a 1-LSB tolerance and record the cause instead.
2. **The 6G15 tone/mixer network.** T7 states only the two corners the values
   give directly; the wet's route through a 50 K pot, a 250 pF capacitor and a
   250 K pot is a loaded network whose response depends on the recovery stage's
   plate impedance, which App. C brackets and does not settle. *Settles:* an
   ngspice deck under `tools/spice/6g15/` in the TS808's form, before Phase 5;
   until then `Tone` is a tilt and the bracket is recorded, not asserted.
3. **`tempo_sync`** — `()` from the standouts; whether a synced predelay is
   worth offering is the implementation session's call under D10.
4. **The Freeverb stereo collapse is an upstream bug** (§4, two line numbers):
   ~10 KB allocated and never read, every delay halved in stereo. *Settles:*
   `upstream-emissary` files it against CircuitPython. Nothing here waits on
   it — the rebuild leaves Freeverb behind.
5. **The EMT 140's reverb-time range.** Every secondary page quotes 0.5–5.5 s;
   no primary document was reached (§2), so §6's 0.2–12 s is our design span,
   not a claim about the machine.
---


## Appendix

### A. What each source said, in its own words

**S1, Dattorro, §1.2** (the sentence that confirms the standout and fixes T1
and T8): *"We also find that some recording engineers do not want an accurate
emulation of a physical space, because the reflection density takes too long
to build. Instead, they sometimes want instantaneous high-density reflections
with smooth exponential decay of the envelope, having randomization in only
the phase trail. This desire most closely describes the plate class of
reverberators, which we present here."*

**S1, §1.3.4** (the memory decision in Tier 3 and the exact-zero invariant):
*"The magnitude truncation makes the reverberator output eventually go to
absolute zero, two's complement"*, and *"If delay-line memory is 24 bits in
width, then the need for magnitude truncation is obviously lessened when
compared to having delay-line memory of only 16 bits in width."*

**S1, Table 1** (verbatim): Sample rate Fs = 29761 Hz · EXCURSION = 16 ·
decay = 0.50 · decay diffusion 1 = 0.70 · decay diffusion 2 = 0.50
(= decay + 0.15, floor 0.25, ceiling 0.50) · input diffusion 1 = 0.750 ·
input diffusion 2 = 0.625 · bandwidth = 0.9995 (full bandwidth = 0.9999999) ·
damping = 0.0005 (no damping = 0.0).

**S1, Fig. 1** (read by rendering the scanned page): input diffusers
142, 107 (input diffusion 1) and 379, 277 (input diffusion 2); tank left
672 + EXCURSION → z⁻⁴⁴⁵³ → damping → ×decay → 1800 → z⁻³⁷²⁰; tank right
908 + EXCURSION → z⁻⁴²¹⁷ → damping → ×decay → 2656 → z⁻³¹⁶³; each side's
final delay feeds the other side. Caption: *"Delay-line taps at nodes 24 and
48 are modulating."* Footnote 6 gives the whole network as *"only 22K words of
memory (not including predelay)"* — our sum of the twelve lines is 22 494,
which is the arithmetic check that the figure was read correctly.

**S1, Table 2** (output taps, ±0.6 each): left from node48_54[266],
node48_54[2974], −node55_59[1913], +node59_63[1996], −node24_30[1990],
−node31_33[187], −node33_39[1066]; right from node24_30[353],
node24_30[3627], −node31_33[1228], +node33_39[2673], −node48_54[2111],
−node55_59[335], −node59_63[121].

**S1, fn. 14:** modulation *"At a rate on the order of 1 Hz, and at a peak
excursion of about 8 samples for a sample rate of about 29.8 kHz."* Table 1's
EXCURSION of 16 is the peak-to-peak reading of the same thing; T10 uses the
Table 1 figure and names the footnote.

**S2, §1.1.1:** *"the unit consists of a 2 m × 1 m rectangular steel plate,
with a thickness of 0.5 mm… held under tension by two steel wires at each
corner… excited by an electrodynamic actuator, and the reverberated signal is
captured by two accelerometers… a porous panel is placed near and parallel to
the plate, with a distance that can be varied between 11 and 66 mm."* Weight:
S2 says the unit *"weights around 240 kg"*; S9 says *"270 kilograms
(600 lbs)"* and S8 *"roughly 600 pound"*. The two figures disagree, both are
recorded, and neither is a trait. *(Audit: an earlier reading of this line
reconciled them by calling S9's 270 kg the cabinet's weight — S9 says no such
thing, and the reconciliation is struck.)*

**S2, §3.4.1:** thermoelastic damping *"reaches the 95% of σ∞ at around
500 Hz, making the damping almost constant for higher frequencies"*, with
Carbon Steel SAE 1010 coefficients R₁ = 9.664 × 10⁻³, C₁ = 0.1855 × 10⁻³.

**S2, §5.2:** *"the EMT 140 possesses an approximately constant modes density
[31]"*, illustrated in its fig. 5.3.

**S3, §3:** *"There appear to be two distinct regions within the impulse
response, a region of lower-frequency dispersive echoes and a region of
high-frequency (and less dispersive) echoes… In the majority of springs
measured, the region of high frequency echoes above F_C is of much lower
amplitude."* **§4.1:** *"The limit as β → 0 is chosen, as this is the point of
maximum propagation velocity within the low-frequency dispersive region"*, and
**§4:** *"The local maximum in the dispersion relation therefore corresponds
with a point of minimum propagation velocity"* at F_C. T6 is the consequence
of those two sentences taken together and is labelled derived for that reason.

### B. Derivations and arithmetic (all run this session)

**Spring T_D and F_C.** S3 eq. 2, T_D ≈ 4LR / (r·√(E/ρ)); eq. 4,
F_C ≈ 3r√(E/ρ) / (16√5 π R²); eq. 3, L = √((2πRN)² + H_L²). S3's own
material constants: E = 2 × 10¹¹ N/m², ρ = 7800 kg/m³, so √(E/ρ) = 5063.7 m/s.
Over S3's Tables 1 and 2:

| Unit / spring | H_L | helix Ø | turns | wire Ø | L | **T_D** | **F_C** |
|---|---|---|---|---|---|---|---|
| Olson X-82 #1 | 6.5 cm | 0.54 cm | 148 | 0.035 cm | 2.512 m | 30.6 ms | 3244 Hz |
| Olson X-82 #2 | 6.5 cm | 0.61 cm | 133 | 0.035 cm | 2.550 m | 35.1 ms | 2543 Hz |
| Leem KA-1210 #1 | 16.3 cm | 0.44 cm | 303 | 0.035 cm | 4.192 m | 41.6 ms | 4887 Hz |
| Leem KA-1210 #2 | 16.3 cm | 0.45 cm | 280 | 0.035 cm | 3.962 m | 40.2 ms | 4672 Hz |
| Leem KA-1210 #3 | 16.3 cm | 0.46 cm | 351 | 0.035 cm | 5.075 m | 52.7 ms | 4471 Hz |

Neither unit is the 6G15's tank — S7 names that as a Gibbs/Accutronics
4AB3C1C or 4AB3C1B, and no geometry for it was reached. T4 and T5 therefore
state a **span the class must be able to cover**, not the 6G15's own numbers,
and say so.

**Dattorro at 48 kHz.** Scale 48000/29761 = 1.6128. Input diffusers
142, 107, 379, 277 → 229, 173, 611, 447 (4.77, 3.60, 12.73, 9.31 ms). Tank
left 672, 4453, 1800, 3720 → 1084, 7182, 2903, 6000 (22.58, 149.63, 60.48,
125.00 ms). Tank right 908, 4217, 2656, 3163 → 1464, 6801, 4284, 5101 (30.51,
141.70, 89.24, 106.28 ms). Sum 22 494 words at 29761 Hz → **36 279 words at
48 kHz** = 72.6 KB int16, 145 KB float32. EXCURSION 16 samples = 0.538 ms
= 26 samples at 48 kHz. Per-frame arithmetic: 8 all-passes (2 mults each),
4 line reads, 2 one-pole filters, 4 decay multiplies, 14 tap multiplies ≈ 50
multiply-adds — the number behind Tier 3's "no lean patch for arithmetic".

**Freeverb line lengths in time.** Combs 1116…1617 samples are 25.31–36.67 ms
at 44.1 kHz and **23.25–33.69 ms at 48 kHz** (never scaled), and **11.62–16.84
ms** in stereo, where the interleaved stream runs through one bank. All-passes
556, 441, 341, 225 → 11.58, 9.19, 7.10, 4.69 ms at 48 kHz. Total line memory
12 587 words = 25.2 KB.

### C. The 6G15's first-order corners, from the drawing's values

| Network | Values read (S6) | Corner |
|---|---|---|
| Into the reverb driver's grid | `.002` µF series, 220 K to ground | **361.7 Hz** (T7) |
| Tone pot's return to ground | `.01` µF, 50 K pot | 318.3 Hz |
| Wet into the Mixer | `.00025` µF (250 pF), 250 K pot | 2546.5 Hz (§8.2) |
| Recovery coupling into the Tone pot | `.1` µF, 50 K | 31.8 Hz |
| Dry coupling into the Mixer | `.1` µF, 250 K | **6.4 Hz** (T7) |

Other values read from the same two drawings, used in §1 and not in a trait:
12AT7 stages 100 K plate load / 1500 Ω cathode / 25 µF bypass, +105 V and
+120 V; Dwell 250 K-L; 6K6GT 1000 Ω 2 W cathode, 25 µF, +285 V plate, driver
transformer TR2 = 125A12A, power transformer TR1 = 68319-A; 7025 recovery
1500 Ω / 250 µF / 100 K, +160 V; second 7025 half 2.2 M + 2.2 M grid divider,
`.05` coupling, 100 K plate load, +130 V; Mixer 250 K-L; Tone 50 K-L. The
**schematic** page's own notes, verbatim: *"1 - VOLTAGES READ TO GROUND WITH
ELECTRONIC VOLTMETER. VALUES SHOWN + or - 20%."*, *"2 - ALL RESISTORS ½ WATT
IF NOT SPECIFIED."*, *"3 - ALL CAPACITORS AT LEAST 400 VOLTS IF NOT
SPECIFIED."* *(Audit note: the **layout** page, S6's other page, writes the
resistor note as "ALL RESISTORS ½ WATT, **10% TOLERANCE**, IF NOT SPECIFIED"
— the two pages differ by that clause, and every value in this table was read
off the schematic.)*

### D. Palette measurements taken this session

CPython, `audiocomponents/.venv`, 48 kHz stereo unless stated.

- **Freeverb RT60** — *re-measured 2026-09-07 by the palette verifier, and the
  earlier single numbers replaced.* A Freeverb RT60 is not one number: it moves
  with the **probe level** (the feedback path truncates in int16, so a quieter
  impulse dies sooner) and with the **estimator**. Stated here as both, from a
  full-scale-ish impulse (peak 30000), 50 ms RMS windows, 12 s render: a
  least-squares log-envelope slope fit over −5…−35 dB extrapolated to −60,
  and, in parentheses, the first window below −60 dB of peak.

  | roomsize, damp | stereo T60 fit (cross) | mono T60 fit (cross) |
  |---|---|---|
  | 0.00, 0 | 0.26 s (0.30) | 0.53 s (0.55) |
  | 0.50, 0 | 0.54 s (0.55) | 1.06 s (1.05) |
  | 0.88, 0 | 1.62 s (1.55) | 3.24 s (2.85) |
  | 1.00, 0 | **4.14 s** (3.40) | **8.38 s** (6.90) |
  | 0.88, 0.35 — the shipped `"hall"` | 1.13 s (0.95) | 2.04 s (1.55) |
  | 0.88, 0.60 | 1.07 s (0.85) | 1.92 s (1.35) |
  | 0.88, 1.00 | 0.96 s (0.70) | 1.68 s (1.10) |

  The level dependence, measured at roomsize 1.0 damp 0 stereo: peak 30000 →
  4.14 s fit, peak 10000 → 3.86 s, peak 3000 → 3.07 s. A decay time that
  follows how hard the input hit is not a plate, and it is one more reason the
  rebuild leaves this node behind.
- **Freeverb tail** reaches exact zero (no held DC) in every configuration
  probed — one invariant the ported node does hold.
- **Freeverb comb taps**, mono impulse: peaks at samples 1116, 1188, 1277,
  1356, 1422, 1491 (23.25–31.06 ms). Stereo, same settings: 558, 594, 639,
  678, 711, 746 — exactly half, which is the collapse in §4.
- **Freeverb stereo cross-talk**: impulse on the left channel only →
  peak 1229 left, **1139 right**.
- **Freeverb at mix 0**, 0.2 s of 440 Hz: amplitude 9000 → out peak 8999,
  9584 of 9600 samples altered, max error 1 LSB; amplitude 30000 → out peak
  **28219**; amplitude 32700 → out peak **28513**. Cause: dry is
  `sample·32767 >> 15` (`audioif_freeverb.c:23`, `:53`) and the output passes
  `audioif_mix_down_sample(word, 0xfffffff/(65536−28000), −28000, 28000)`
  (`:55-56`), a soft knee above 28000/32768 = −1.37 dBFS (`audioif_synth_dsp.c:20-28`).
- **Freeverb at 22.05 kHz**, roomsize 1.0, damp 0: RT60 did not reach −60 dB
  within a 6 s render — consistent with the fixed sample tunings doubling in
  time. Recorded as an observation, not a trait.
- **Cycles**: `d1.play(s); d2.play(d1); d1.play(d2)` constructs; the first
  `audiocore.get_buffer(d2, False, 0)` raises `RecursionError`.
- **The current class after `deinit()`**: `Reverb(source,
  preset="spring")` → `latency_samples 0`, `tail_samples None`,
  `MACRO_LABELS ()`, `capabilities ()`; after `deinit()`,
  `audiocore.get_buffer(r.flutter, False, 0)` returns `(1, 2048 bytes)`.

**Added 2026-09-07 by the palette verifier**, same venv and rate:

- **The palette does have a negative gain.** `audiomath.Multiply` against a
  constant modulator of −32768 inverts exactly: `max|out + in| = 0` over 2048
  frames of a 440 Hz sine at 20000. At −0.7×32768 the output tracks −0.7·x to
  within 1.3 LSB (`audioif_multiply.c:38-39` is the Q15 product; the shift
  floors, which is where the fraction of an LSB goes). `audiomixer.Mixer`'s
  voice level cannot: it is limited to 0.0…1.0 before scaling
  (`audiomixer/Mixer.c:332`).
- **A Schroeder all-pass composes from four palette nodes, and it is flat.**
  `Splitter(taps=2)` → tap 0 into `FeedbackDelay(delay 142 frames,
  feedback 0.7, mix=2.0)` → `Multiply` by the constant 1−g² → `Mixer` voice 0;
  tap 1 → `Multiply` by the constant −g → `Mixer` voice 1. Impulse in
  (peak 30000): out[0] = −21000 = −g·x, out[142] = 15299, and the DFT
  magnitude is 30000.0 / 29997.7 / 29995.7 / 29997.3 / 29999.5 / 29998.0 /
  29999.9 at 100 / 300 / 1000 / 3000 / 7000 / 12000 / 18000 Hz — **0.00 dB
  across the band**, which is what an all-pass is. This refutes the earlier
  draft's "`FeedbackDelay` cannot be the diffuser" and changes nothing about
  the ask, because the recirculating half of the tank still needs a cycle.
- **Cycles, re-verified.** `d1.play(src); d2.play(d1); d1.play(d2)` constructs
  without complaint; `audiocore.get_buffer(d2, False, 0)` raises
  `RecursionError: maximum recursion depth exceeded`.
- **`audioconvolve.Convolver`, re-measured** (it is the alternative in §5's
  refutation (3)): unloaded, `max|out − in| = 0` over 1 s of 440 Hz stereo
  while `node.latency` still reports 256 (`audioconvolve/Convolver.c:240-243`
  returns the constant); with a 1024-tap impulse loaded, a click at frame 0
  first appears at frame **256**, value 19999 from an input of 20000. At
  `mix = 0` with an impulse loaded, `out[i+512] == in[i]` for every sample and
  the first 512 samples are zero. `max_taps = 512·256 + 1` raises
  `ValueError: impulse is too long` (`Convolver.c:32`); 512·256 = 131 072 taps
  = 2.731 s at 48 kHz constructs.

### E. Measurements, and the planted fault each must catch

All take the sample rate as a parameter and record it; all run at 48 kHz and
44.1 kHz, Tier 1 additionally at 22.05 kHz.

- **M1 — echo-density profile.** From the impulse probe: count local maxima
  above −40 dB of the running RMS in each 10 ms window; report the curve.
  *Planted fault:* replace the input diffusers with a wire — the plate
  patch's 20 ms density must collapse and T1 go red while T8 stays green.
- **M2 — modal-density ratio.** One Hann-windowed 48 000-point FFT of the
  0.5–1.5 s tail segment (≈1 Hz bins); count spectral maxima of ≥6 dB
  prominence per Hz in 200–400 Hz and in 2–4 kHz and report the upper/lower
  ratio. The prominence rule is part of the measurement, not a detail: a bare
  local-maximum count is set by the FFT's resolution rather than by the tail.
  *Planted fault:* halve every tank line length — the ratio must move.
- **M3 — band T60.** Third-octave-filtered decay at 500 Hz and 4 kHz across
  the Decay macro, each T60 from a **least-squares slope fit of the
  log-envelope over −5…−35 dB** extrapolated to −60 dB — the shape
  `tools/measure_hits.py:80-90` already uses — and **never** from the first
  window that crosses −60 dB. The estimator is part of the trait: on this
  run's convolver renders a −60 dB crossing on 20 ms windows read 2–8 % high
  where the slope fit read within 0.5 % of the same decays
  (`ConvolutionReverb.md` App. A), which is more than T3's whole margin.
  *Planted fault:* make Damping frequency-flat; T3 must go red.
- **M4 — echo spacing.** Autocorrelation of the wet impulse response, first
  non-zero-lag peak. *Planted fault:* set the spring tuning's loop length to
  the plate's; the peak must move outside the 30–53 ms window.
- **M5 — two-region split.** STFT of the wet impulse response; echo period
  and energy above and below the patch's F_C. *Planted fault:* remove the
  dispersive chain; one period across the band, T5 red.
- **M6 — STFT ridge tracking.** Instantaneous frequency of the first echo
  (T6) and of the deepest tail notch across one modulation period (T10).
  *Planted fault:* set Mod Depth to zero with the patch claiming otherwise —
  T10 red; reverse the all-pass chain's coefficient sign — T6 red.
- **M7 — wet/dry magnitude response.** Swept sine, wet-only and dry-only,
  30 Hz to Nyquist. *Planted fault:* move the Low Cut into the dry path;
  T7's dry clause must go red.

- **M8 — character separation.** M1's first-arrival time and M3's band T60
  on `Small Room`, `Live Room`, `Concert Hall` and `Dark Chamber`, plus a
  construction-time read of the line-length set each character builds.
  *Planted fault:* construct the `hall` character with the `room` character's
  line lengths and leave the patch names alone — M8 must go red while every
  other measurement stays green, which is the whole reason it exists.

Every measurement is also run with the class's own **control**: the same
probe through a wire, which must *pass* the invariant tests and *fail* the
trait tests, so the suite is not one that only ever fails.

### F. Patch settings

Macro order is §6's. Values are engineering units; the implementation session
converts to the 0–127 integers `PATCHES` stores.

| Patch | Char. | Decay | Size | Predelay | Diff. | Damping | Low cut | Mod d/r | Disp. | Drive | Width | Tone | Mix |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Steel Plate | plate | 2.4 s | 1.0 | 0 ms | 0.75 | 7 kHz | 40 Hz | 0.3 ms / 1.0 Hz | 0 | 0 | 0.7 | 0 | 0.35 |
| Short Plate | plate | 0.9 s | 0.6 | 0 ms | 0.75 | 9 kHz | 60 Hz | 0.2 ms / 1.2 Hz | 0 | 0 | 0.7 | +2 | 0.30 |
| Damped Plate | plate | 0.5 s | 0.8 | 0 ms | 0.75 | 3 kHz | 80 Hz | 0.2 ms / 1.0 Hz | 0 | 0 | 0.6 | −3 | 0.30 |
| Long Tank | spring | 3.0 s | 1.6 | 0 ms | 0.4 | 5 kHz | 360 Hz | 0 | 0.8 | 0.30 | 0.4 | 0 | 0.40 |
| Surf Tank | spring | 1.8 s | 1.0 | 0 ms | 0.4 | 6 kHz | 360 Hz | 0 | 1.0 | 0.75 | 0.4 | +6 | 0.55 |
| Small Room | room | 0.4 s | 0.5 | 6 ms | 0.6 | 6 kHz | 60 Hz | 0.2 ms / 0.8 Hz | 0 | 0 | 0.6 | 0 | 0.25 |
| Live Room | room | 1.1 s | 0.8 | 14 ms | 0.6 | 8 kHz | 50 Hz | 0.3 ms / 0.7 Hz | 0 | 0 | 0.7 | +2 | 0.30 |
| Concert Hall | hall | 2.8 s | 1.5 | 32 ms | 0.7 | 5 kHz | 45 Hz | 0.6 ms / 0.6 Hz | 0 | 0 | 0.9 | 0 | 0.35 |
| Dark Chamber | chamber | 1.8 s | 1.1 | 12 ms | 0.7 | 2.5 kHz | 70 Hz | 0.3 ms / 0.9 Hz | 0 | 0 | 0.6 | −4 | 0.32 |
| Bright Chamber | chamber | 1.6 s | 1.1 | 12 ms | 0.7 | 12 kHz | 90 Hz | 0.3 ms / 0.9 Hz | 0 | 0 | 0.6 | +4 | 0.32 |
| Slow Bloom | hall | 4.5 s | 1.5 | 40 ms | 0.8 | 4 kHz | 45 Hz | 1.4 ms / 0.4 Hz | 0 | 0 | 0.9 | 0 | 0.45 |
| Plate — lean | plate | 1.6 s | 0.5 | 0 ms | 0.6 | 7 kHz | 60 Hz | 0 / — | 0 | 0 | 0.5 | 0 | 0.30 |

`Plate — lean` is the S3 escape valve of vision §7.2: half the line memory and
no modulation. It is a *separate* patch and never a change to `Steel Plate`.

### G. Reading the Freeverb stereo collapse

The module allocates `8 * channel_count` comb buffers and `4 * channel_count`
all-pass buffers (`audiofreeverb/Freeverb.c:95`, `:111`) with the second
bank's sizes set alongside the first (`:87-94`, `:107-110`), which reads as an
intent to give each channel its own network. It does not happen. Upstream
CircuitPython declares `uint32_t channel_comb_offset = 0, channel_allpass_offset
= 0;` **inside** the per-sample loop
(`cmods/circuitpython/shared-module/audiofreeverb/Freeverb.c:281`, loop opens
at `:273`), so the toggle at `:315-321` sets a variable that is re-initialised
to 0 on the next iteration; the comb loop at `:287` and the all-pass loop at
`:300` therefore always run over banks 0–7 and 0–3. audioif's kernel
reproduces the *effective* behaviour with a single bank
(`audioif_freeverb.c:30`, `:43`) and `audiofreeverb/Freeverb.c:254-258` hands
it `n`, the interleaved sample count.

Consequences, all measured in App. D: a stereo stream runs through one mono
network at twice the frame rate, so every delay is **half** its intended time;
the two channels are not independent, so an impulse in one appears in the
other at nearly the same level; and roughly 10 KB of comb and all-pass buffer
is allocated and never read. This is upstream's, not audioif's, and the ported
node is never modified (vision §2.2) — it is filed as an upstream report
(§8.4) and the rebuild leaves the node behind.

### H. The second audit pass, 2026-09-06 — what was re-reached

An independent agent re-fetched every URL in §2 from this machine, re-read
every quotation against the source it names, recomputed every derived figure,
and re-ran the one measurement §3 depends on. Method: `curl` for the six
PDFs (HTTP status and byte count recorded), `pypdf` 6.16.2 for text,
`pypdfium2` for the pages that carry none, WebFetch for the three HTML pages
and for the four "not reached" URLs.

**S1, Dattorro.** HTTP 200, 2 335 819 bytes, 25 pages, text extractable. The
§1.1 sentence ("Fig. 1 shows one particular network for producing
reverberation"), the §1.2 paragraph behind T1 and T8, and both §1.3.4
sentences behind Tier 3 and the exact-zero invariant read verbatim. Table 1
read in full, including the line App. A quotes as the `decay + 0.15` rule and
the "full bandwidth = 0.9999999 / no damping = 0.0" entries. Table 2's
fourteen taps read one by one and match App. A. Footnote 6 ("Given a 30-kHz
sample rate and having only 22K words of memory (not including predelay)")
and footnote 14 ("At a rate on the order of 1 Hz, and at a peak excursion of
about 8 samples for a sample rate of about 29.8 kHz") verbatim. **Fig. 1**
carries no extractable numbers at all beyond "672 + EXCURSION" and "908 +
EXCURSION", so page 3 was rendered at scale 4 and read as two images: input
diffusers 142 and 107 (input diffusion 1), 379 and 277 (input diffusion 2);
left tank 672 + EXCURSION → z⁻⁴⁴⁵³ → damping → decay → 1800 → z⁻³⁷²⁰; right
tank 908 + EXCURSION → z⁻⁴²¹⁷ → damping → decay → 2656 → z⁻³¹⁶³; node labels
23/24, 30, 31/33, 39, 46/48, 54, 55/59, 63 as Table 2 uses them, and the
caption "Delay-line taps at nodes 24 and 48 are modulating." The paper's own
running feet give 660 and 684, the range §2 cites. No rights statement
anywhere in the file and none in its PDF metadata; the author's CCRMA index
page carries none and does not link the file.

**S2, Russo.** HTTP 200, 73 pages. §1.1.1's plate sentence, §3.4.1's
thermoelastic sentence with R₁ = 9.664 × 10⁻³ and C₁ = 0.1855 × 10⁻³ for
Carbon Steel SAE 1010, §3.4.2's radiation damping, §3.4.3's porous panel
("increase the radiated power, thus increasing loss"), and §5.2's constant
modal density all read. Fig. 5.3's caption is *"Modal density of the EMT 140
in modes per Hertz, calculated with the relation provided by Arcas [31]"*,
and [31] resolves in the bibliography to Kevin Arcas, "Physical Modelling and
Measurements of Plate Reverberation", ICA 2007 — so §1's "computed from
Arcas's relation" is the caption's own words. The 240 kg is at §1.1.1 too.
Licence: p. 2, bare copyright line, nothing else.

**S3 / S4 / S5, the spring papers.** All HTTP 200. S3's equations 2, 3 and 4
read verbatim and its Appendix A gives the material constants
E = 2 × 10¹¹ N/m² and ρ = 7800 kg/m³ and both measurement tables — Olson
X-82 springs 1 and 2, Leem Pro KA-1210 springs 1, 2 and 3, with helix length,
helix diameter, turns and wire diameter. Recomputing App. B from those
numbers alone reproduces every figure to the digit: L = 2.512 / 2.550 / 4.192
/ 3.962 / 5.075 m, T_D = 30.6 / 35.1 / 41.6 / 40.2 / 52.7 ms, F_C = 3244 /
2543 / 4887 / 4672 / 4471 Hz. S3 §3 and §4/§4.1 carry the sentences T5 and T6
rest on. S4 §4.3 confirms the two regions independently: *"spectrograms
exhibit a complex region, under a cutoff frequency … over which multiple
families of dispersive echoes are visible. Above the cutoff, a single family
of dispersive chirp-like echoes persists."* Page 1 of S3 and of S4 rendered
and their footers read: funding footnotes only, no rights statement, and
dafx.de's paper-archive index carries none either. **S5 is the exception** —
its page-1 footer carries the CC BY 3.0 Unported notice §2 now quotes. It is
worth saying how it was missed, because the same trap is waiting in every
DAFx 2020-and-later paper in this program: `pypdf` extracts the body, the
running head and the page number of that file and **not** the italic
left-column copyright block, so a text-only pass sees no licence and
concludes there is none. Grepping the extracted text for "creative commons",
"open-access", "distributed under" and "attribution" returns nothing on a
paper that is plainly CC BY. The only check that works is rendering page 1
and looking at it.

**S6, the 6G15 drawings.** HTTP 200, 2 pages, 64 characters of extractable
text between them, so both were rendered at scale 4 and read as images. Page
2 is the schematic and every value in App. C was read from it: the `.002`
into 220 K at the 6K6GT grid, the `.1` into the Mixer 250 K-L on the dry, the
`.00025` between Tone and Mixer, the `.01` on the Tone pot, the `.1` out of
the recovery stage, Dwell 250 K-L sitting between the two 12AT7 halves and so
ahead of the driver, TR1 = 68319-A and TR2 = 125A12A, and the plate voltages.
Page 1 is the layout and agrees, with the one wording difference App. C now
records.

**S7 / S8 / S9, the HTML pages.** Wikipedia gives 1961–1966, "a 12AT7 tube as
a preamplifier; a 6K6 tube as the reverb driver; and a 12AX7 as the reverb
recovery tube", and the full tank sentence: *"The vertically mounted tank
should be a 4AB3C1C … but most actually shipped with 4AB3C1B tanks"* — and
says nothing about how many springs the tank holds, which is why §1 calls
that unsourced. Footer: CC BY-SA 4.0. Designing Sound gives 1957, "roughly
600 pound", the 1961 stereo model and the remote damping pad, under an
explicit CC BY-NC-SA 3.0 Unported notice. Vintage Technology Archive gives
"2.4 meters (8 feet) long by 1.2 meters (4 feet) high", "270 kilograms
(600 lbs)" for the unit, and "-3 dB (.55 V) into 600 ohms at 1 kHz", with no
notice of any kind on the page or its footer.

**Not reached, re-tested.** UA's manual 403; `vintagedigital.com.au` 403;
`secure.aes.org` 522; `archive.org/metadata/emt-140-plate-reverb` still
returns `{}`. Arturia's page loads and is still no source: it says the unit
"weighed more than 4 people" in one sentence and "more than 3 people" in
another, and gives no specification. The EMT 140's 0.5–5.5 s reverb-time
range was not found in any primary document this pass either, and stays out
of the traits.

**The one measurement §3 rests on, re-run.** Freeverb at `mix = 0`, 0.1 s of
440 Hz stereo at amplitude 30000, CPython in `audiocomponents/.venv`:
**9584 of 9600 samples altered, peak in 30000 → peak out 28219, max error
1782**. App. D's numbers exactly. And the `audiomixer` line numbers the first
pass corrected were re-checked with `grep -n`: `ALMOST_ONE` is defined at
`Mixer.c:296`, used for panning at `:333`, while `level` is limited to 1.0
and scaled by `1 << 15` at `:332`.

### I. The trait critic pass, 2026-09-07 — what changed and why

Nine rows in, ten out; no source was added and none was re-fetched, so no row
gained a claim about the world that the audit passes had not already checked.
What moved is falsifiability.

| Row | Was | Is | Why |
|---|---|---|---|
| T1 | "within 20 % of its 200 ms value by 20 ms after onset", sourced to S1 §1.2 at high confidence | same criterion, plus the no-window-below rule, the patch named, and the ±20 % labelled ours | S1 says *instantaneous high-density* and gives no figure; the row read as though 20 % came from the paper |
| T2 | trait "less than 2×", disconfirmation "above 3" | one threshold, 2.0, either side; FFT length, window and a ≥6 dB prominence rule stated | a measured 2.5 confirmed nothing and disconfirmed nothing; and an unqualified "count the resonances" is set by FFT resolution, not by the plate |
| T3 | "rises monotonically" across the Decay range; disconfirmation "flat within 10 %" | five named Decay positions, a ≥20 % end-to-end change, non-decreasing between adjacent positions, and the estimator pinned to a slope fit | monotonicity over a continuum cannot be measured, and the two thresholds did not meet. The estimator matters more than the threshold: see M3 |
| T4 | "spacing T_D in 30–53 ms … first peak at the patch's T_D ±10 %"; disconfirmation window 25–60 ms | the span is stated at Size 1.0, "repeats" becomes four multiples ±10 %, and the Size law is its own clause; disconfirmation moved to 30–53 ms | no patch had a stated T_D, so "the patch's T_D" was a hook with nothing on it; and the two windows differed by 5 ms at each end |
| T5 | "repeating faster and ≥10 dB lower"; disconfirmation "within 6 dB" | ≤0.7 × the sub-F_C spacing, ≥10 dB either side, F_C span tied to Dispersion 1.0 | the row's own note says a measured 8 dB disconfirms our floor — the disconfirmation column said 6 dB and contradicted it. "Faster" had no number at all |
| T6 | "the STFT ridge … rises monotonically over its length" | non-decreasing frame to frame within ±5 %, last frame ≥2 × the first, band stated | an STFT ridge is noisy; strict monotonicity is a coin toss on real data |
| T7 | "−3 dB at 362 Hz and −6 dB/oct below; the dry is flat below 10 Hz" | tolerances on both numbers, a 90 Hz depth, the dry stated as a flatness band over 20 Hz–1 kHz, and the corner required to follow Low Cut | "flat below 10 Hz" is a claim about the 6G15's coupling capacitor, not about a digital dry path; and neither corner had a tolerance |
| T8 | "rises ≥50 %", sourced to S1 §1.2 at high confidence | same criterion, the three patches named, the 50 % labelled ours, and the tie to T1's counting rule made explicit | the 50 % is not in S1 either; and the contrast is only a trait if both halves are measured the same way |
| T9 | *(did not exist)* | hall, room and chamber must differ from each other by stated margins, and no two characters may share a line-length set | vision §10.7: a character that fails cannot hide behind one that passes. Three characters shared one row, so one tuning under three names passed everything |
| T10 | old T9: "≥20 cents"; disconfirmation "static within 5 cents"; cited S1 §1.3.7 | one threshold, 20 cents peak-to-peak, the notch identified, the patches named; the citation narrowed to S1's Table 1, Fig. 1 caption and fn. 14 | the gap between 5 and 20 cents again; and §1.3.7 is a section pointer this seed never quotes and this run did not reach — the three passages App. A does quote carry the whole claim |

Two things this pass did **not** do. It did not re-fetch S1–S9: every source
call here is the audit passes', and the rewrites only narrow citations, never
extend them. (§1's and §4's "S1 §1.3.6" for the mono input sum is the other
unquoted section pointer in the seed; it is outside a trait row and is left
for the source audit to reach or strike.) And it did not touch §2, §6 or the
patch table, so the margins T9 asks for are read off App. F as it stands.

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

*Wire note.* The node that would carry the dry path is not a wire: Freeverb's
dry term altered **9584 of 9600 samples at mix 0** in this session's probe,
re-measured in the audit (peaks 8999 / 28219 / 28513 from inputs of 9000 /
30000 / 32700, App. D). So the wire invariant is met by **structural bypass**:
at `mix == 0` the class exposes the source as its `output` and reports zero
latency, and the kit measures that, not a 1-LSB tolerance. A choice, so it is
recorded (§8.1). *(Audit correction: the earlier claim that no summing node on
this palette is exactly unity cited `ALMOST_ONE = 32767/32768` at
`audiomixer/Mixer.c:296`. That constant is real at that line but bounds
**panning** (`Mixer.c:333`); a voice's `level` is limited to 1.0 and scaled by
`1 << 15` (`Mixer.c:332`), so a mixer voice at level 1.0 with panning 0 is
unity by that arithmetic. Whether a `Mixer` is byte-transparent end to end is
unmeasured and is the implementation session's to settle in §8.1 — it is no
longer offered here as a reason.)*

*Rate note.* T4 and T6–T10 hold at 22.05 kHz. T5's F_C reaches 4.9 kHz, so at
22.05 kHz the spring character clamps F_C below 0.4 × Nyquist and the trait's
**span narrows** — the one Tier 2 trait a lower rate changes.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| # | Source | Licence as read | Reached |
|---|---|---|---|
| S1 | [Dattorro, *Effect Design, Part 1*, JAES 45(9):660–684, 1997](https://ccrma.stanford.edu/~dattorro/EffectDesignPart1.pdf) — Fig. 1, every delay length, Tables 1–2, magnitude truncation | no rights statement in the PDF; the author's CCRMA index page carries none either and does not link the file → **licence unverified — treated as copyleft**; read as a paper, nothing ported | HTTP 200; OCR text extracted, Fig. 1 rendered and read |
| S2 | [Russo, *Physical Modeling and Optimisation of a EMT 140 Plate Reverb*, MSc, Aalborg, 2021](https://projekter.aau.dk/projekter/files/517547034/Master_Thesis_Russo.pdf) — plate size, suspension, damper range, thermoelastic corner, flat modal density | p. 2 carries the bare line "Copyright © Aalborg University 2021" and nothing else; no grant, no terms, and the words "all rights reserved" appear nowhere in the document → **licence unverified — treated as copyleft**; read as a paper, nothing ported | HTTP 200; text extracted, copyright line read on p. 2 |
| S3 | [Parker & Bilbao, *Spring Reverberation: A Physical Perspective*, DAFx-09](https://www.dafx.de/paper-archive/2009/papers/paper_84.pdf) — the T_D and F_C closed forms (eqs. 2–4), the two-region response, five spring geometries | no rights statement in the PDF and none on dafx.de's paper archive index → **licence unverified — treated as copyleft**; read as a paper | HTTP 200; text extracted |
| S4 | [Bilbao, *Numerical Simulation of Spring Reverberation*, DAFx-13](https://www.dafx.de/paper-archive/2013/papers/22.dafx2013_submission_19.pdf) — independent confirmation of the two-region structure (§4.3) | as S3 → **licence unverified — treated as copyleft** | HTTP 200; text extracted |
| S5 | [McQuillan & van Walstijn, *Modal Spring Reverb…*, DAFx-20in21](https://dafx2020.mdw.ac.at/proceedings/papers/DAFx20in21_paper_23.pdf) — a third helical-spring model | **CC BY 3.0 Unported**, stated at the foot of the PDF's own p. 1: *"Copyright: © 2021 Jacob McQuillan et al. This is an open-access article distributed under the terms of the Creative Commons Attribution 3.0 Unported License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source are credited."* The only *paper* here with a stated licence *(audit correction — see App. H)* | HTTP 200; text extracted, p. 1 rendered at scale 3 and the licence footer read |
| S6 | [Fender, *Reverb 6G15* schematic + layout (H-FA)](https://el34world.com/charts/Schematics/Files/Fender/Fender_reverb_6g15.pdf) — every value in §1 and App. C | no notice on the drawings; el34world.com's home page carries no terms → **licence unverified — treated as copyleft**; a drawing read as a **document, read only** (vision §5), nothing reproduced | HTTP 200; both pages rendered and read |
| S7 | [Wikipedia, *Fender Reverb Unit*](https://en.wikipedia.org/wiki/Fender_Reverb_Unit) — 1961–1966, tubes (12AT7 preamp, 6K6 driver, 12AX7 recovery), tank 4AB3C1C/4AB3C1B, Gibbs and Accutronics | **CC BY-SA 4.0**, read in the page footer | WebFetch, page footer read |
| S8 | [Designing Sound, *EMT 140 Plate Reverb*](https://designingsound.org/2012/12/11/emt-140-plate-reverb/) — 1957, ~600 lb, stereo 1961, remote damping pad | **CC BY-NC-SA 3.0 Unported**, stated on the page | WebFetch, notice read |
| S9 | [Vintage Technology Archive, EMT 140](https://vintagetechnologyarchive.com/synth/emt/140/) — cabinet 2.4 m × 1.2 m, unit weight "270 kilograms (600 lbs)", −3 dB (.55 V) into 600 Ω at 1 kHz | no licence, copyright or terms notice on the page or its footer → **licence unverified — treated as copyleft**; read only | WebFetch, footer read |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| T1 | **The density is there from the first millisecond**: the M1 echo-density curve (local maxima per 10 ms window, impulse probe) reads within ±20 % of its 200 ms value by 20 ms after onset, and no window between 20 and 200 ms sits more than 20 % below the 200 ms value. | S1 §1.2, verbatim (App. A), for *instantaneous* high density; **the ±20 % is ours** — S1 gives no figure | high for the structure; design for the ±20 % | Any 10 ms window between 20 and 200 ms more than 20 % below the 200 ms value — a density still building | M1 |
| T2 | **Modal density is flat with frequency, not rising**: over the 0.5–1.5 s tail segment (one Hann-windowed 48 000-point FFT, ≈1 Hz bins), spectral maxima of ≥6 dB prominence counted per Hz in 2–4 kHz, divided by the same count in 200–400 Hz, is **≤ 2.0**. | S2 §5.2 and fig. 5.3's caption (App. H); **the ratio and the counting rule are ours** | medium — a figure caption, not a table; design for the 2.0 | A ratio above 2.0: more modes per Hz at the top of the band than the bottom, which is a room's behaviour and not a plate's | M2 |
| T3 | **The decay is frequency-dependent, because the damper is radiation loss**: at five Decay positions (T60 targets 0.5 / 1 / 2 / 4 / 8 s) the ratio R = T60(500 Hz)/T60(4 kHz) — each T60 from a **least-squares log-envelope slope fit over −5…−35 dB**, never a −60 dB crossing (App. E, M3) — is non-decreasing as Decay shortens, and R at the shortest position exceeds R at the longest by **≥ 20 %**. | S2 §3.4.1 (loss near-constant above 500 Hz) and §3.4.3 (the panel raises radiated power); the *direction* is derived from those two, and the 20 % and the five positions are ours | medium for the direction; design for the 20 % | R changing by less than 20 % end to end, or falling as Decay shortens | M3 |
| T4 | **A discrete echo train whose spacing scales with Size**: at Size 1.0 the first non-zero-lag autocorrelation peak of the wet impulse response lies in **30–53 ms** — S3's five measured springs, recomputed in App. B — at least **four** further peaks fall at integer multiples of it ±10 %, and halving Size halves that spacing ±10 % over Size 0.35–1.8. | S3 eqs. 2 and 3 over its own Tables 1–2, recomputed in App. B; the four peaks, the ±10 % and the Size law are ours (eq. 2's T_D ∝ L·R/r is what makes Size a length control) | high for the span and the closed form; design for the tolerances | No repeating peak; a Size-1.0 first peak outside 30–53 ms; fewer than four multiples; or a Size halving that does not halve the spacing within ±10 % | M4 |
| T5 | **Two regions split at F_C, the upper one faster and quieter**: on `Surf Tank` (Dispersion 1.0) the split lies in **2.5–4.9 kHz** (S3 eq. 4 over the same five springs, App. B); below it the echoes repeat at T4's spacing, above it at **≤ 0.7 ×** that spacing, and the above-F_C band energy over the first 500 ms is **≥ 10 dB below** the sub-F_C band's. | S3 §3 and eq. 4; S4 §4.3 independently (both quoted, App. A and H). The split, the faster repetition and "much lower amplitude" are S3's; **the 10 dB and the 0.7 × are ours** — S3 gives no figure, so a measured 8 dB disconfirms our floor and not S3 | medium-high for the structure; design for the two numbers | One echo period across the whole band; above-F_C energy less than 10 dB down; an above-F_C period longer than 0.7 × the sub-F_C one; or a split outside 2.5–4.9 kHz at Dispersion 1.0 | M5 |
| T6 | **Each sub-F_C echo is an upward chirp**: across the first echo the M6 STFT ridge, tracked over 100 Hz–F_C, is non-decreasing frame to frame within ±5 %, and its last frame's ridge frequency is **≥ 2 ×** its first frame's. | Derived from S3 §4 and §4.1 read together (App. A): maximum propagation velocity as β → 0 and minimum at F_C, so one echo's low frequencies arrive before those near F_C. Not stated in words there; the 2 × and the ±5 % are ours | medium (derived); design for the 2 × | A falling ridge, a flat one, or a rise of less than a factor of 2 across the first echo | M6 |
| T7 | **The tank sees no bass and the dry does**: with Low Cut at the spring patches' 360 Hz default the wet path is **−3 ±1 dB at 362 Hz**, falls at **6 ±1 dB/octave** over 90–180 Hz and sits **≥ 12 dB below its 1 kHz level at 90 Hz**; the dry path is within **±0.1 dB of flat from 20 Hz to 1 kHz** at every macro setting; and the wet corner follows the Low Cut macro within ±10 % across 20–500 Hz. | S6's drawing: `.002` µF into 220 K at the 6K6GT grid = 361.7 Hz, `.1` µF into 250 K on the dry = 6.4 Hz (App. C); the tolerances are ours | high for the arithmetic; medium for a hand-drawn topology — the loaded tone network is bracketed, not settled (§8.2) | A wet path within 1 dB of flat at 100 Hz; a slope outside 6 ±1 dB/oct; any dry-path deviation beyond ±0.1 dB above 20 Hz; or a wet corner that does not follow Low Cut | M7 |
| T8 | **These three build their density and the plate does not** — the contrast is what makes them different characters: on `Small Room`, `Concert Hall` and `Dark Chamber` the M1 curve rises by **≥ 50 %** between 20 and 200 ms, on the probe and counting rule T1 uses to show the plate flat. | S1 §1.2, verbatim (App. A) — "the reflection density takes too long to build" is the space these engineers wanted away from; **the 50 % is ours** | high for the contrast; design for the 50 % | Any of the three rising less than 50 % between 20 and 200 ms: a plate wearing a hall's name | M1 |
| T9 | **The three are three tunings, not one name three times**: at the shipped patches T60(1 kHz) on `Concert Hall` is ≥ 2 × `Live Room`'s and ≥ 4 × `Small Room`'s; the first wet arrival is ≥ 25 ms on `Concert Hall` and ≤ 15 ms on both rooms; and no two of the five characters are constructed from the same tank line-length set. | **design** — §6 and App. F of this seed. No source reached this run distinguishes a hall from a chamber and none is claimed; the margins are read off the patch table | design | Any two characters built on identical line lengths, or a `Concert Hall` that does not clear the two rooms by the stated margins | M8 |
| T10 | **Modulated tank taps move the picket fence**: on `Steel Plate` and `Concert Hall`, at Mod Depth zero the tail spectrum shows periodic notches at the tank loop period; at the source's excursion (EXCURSION 16 at 29 761 Hz ⇒ 26 samples at 48 kHz) and 1 Hz, the centre of the deepest notch below 2 kHz moves **≥ 20 cents peak-to-peak over one modulation period**. | S1 Table 1 (EXCURSION 16), Fig. 1's caption ("Delay-line taps at nodes 24 and 48 are modulating") and fn. 14 ("on the order of 1 Hz… about 8 samples"), all quoted in App. A; **the 20 cents is ours** | medium — depth and rate are sourced, the 20 cents is our floor and its disconfirmation is a legitimate result | A notch centre moving less than 20 cents peak-to-peak at full depth | M6 |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Standout confirmed, refined.** S1 §1.2 says its network is for engineers who
want "instantaneous high-density reflections with smooth exponential decay…
This desire most closely describes the plate class of reverberators, which we
present here" (App. A). The vision's split is therefore one topology at five
tunings — which *removes* a node ask rather than adding one. No swap.

*(from §2)*

**Not reached**, each re-tested in the audit: UA's EMT 140 manual (403);
`vintagedigital.com.au` (403); Arturia's Rev PLATE-140 page (loads; gives no
hardware specification — its only physical claim is that the unit "weighed
more than 4 people"); an archive.org EMT identifier (metadata API returns
`{}`); the AES-published Dattorro (`secure.aes.org` now returns 522 — the
author's copy used); **and the 0.5–5.5 s reverb-time range every secondary
page quotes for the EMT 140** — no primary EMT document was reached, so it is
not a trait and §6's decay span is *our* design range.

*(from §2)*

**Audit, first pass, 2026-09-06.** Corrections then applied: the licence
calls restated in the vision §5 form with the page or index where the absence
was checked; S9's 270 kg is the *unit's* weight as that page states it, not
the cabinet's, and the App. A reconciliation that said otherwise struck; the
§3 wire note's `audiomixer` clause corrected (the constant it cited bounds
panning, not level); §1's "a room's grows as f²" marked unsourced.

*(from §2)*

1. **S5's licence was wrong.** It carries a Creative Commons Attribution 3.0
   Unported notice at the foot of its own p. 1 — invisible to `pypdf`, which
   is how the first pass called it unverified. Nothing in this seed rests on
   S5 (it corroborates T5's two-region structure and fixes no value), so no
   trait moves; the correction is to the licence call alone, and it moves
   S5 from copyleft-treated to attributable.

*(from §2)*

2. **S2's licence call overstated what the page says.** "All rights reserved
   as read" was not read anywhere: p. 2 carries a bare copyright line and no
   terms. Restated as the vision §5 default. (`instrument-sources.md`:
   "unverified" and "verified all-rights-reserved" are different, checkable
   claims — say which one you found.)

*(from §2)*

4. **T5's "≥10 dB" is ours, not S3's.** S3 says only that the above-F_C
   region is "of much lower amplitude" and gives no figure. The trait now
   says which half of it the paper supports, so a measured 8 dB disconfirms
   our number rather than the source.

*(from §3)*

**Trait critic pass, 2026-09-07.** Every row above was rewritten so that the
criterion and its disconfirmation meet at one threshold instead of leaving a
band where a measurement could do neither; so that each names the patch, the
probe and the estimator it is judged on; and so that a number no source
carries is labelled **ours**. **T9 is new** — hall, room and chamber shared a
single row and three identical tunings under three names would have passed
it. The modulation row is now **T10**. Row by row in **App. I**.

*(from §3)*

Budget as a fraction of one stereo block's deadline (256 frames, 5.333 ms at
48 kHz): **P4 0.06, S3 0.18.** Lean patch expected: **no** for arithmetic
(~50 multiply-adds per frame, App. B); **yes for memory** on the S3 —
Dattorro's lines scaled to 48 kHz total **36 279 words**, 72.6 KB as int16 or
145 KB as float32. Hence **int16 line memory with magnitude truncation, float
state**, which S1 §1.3.4 recommends for exactly this reason and which is also
what makes the tail reach absolute zero: the memory budget and the Tier 1
invariant are one decision.

*(from §3)*

**Latency: zero.** No character looks ahead. Predelay is on the wet path and
is the effect, not latency; the dry path is the current frame.
`latency_samples` is 0 at every macro setting, patch and character, and **no
option adds latency** — no lookahead, no partition, no pitch window exists in
this class. `tail_samples` is declared per patch as the longest T60 that patch
reaches, checked by the burst-then-silence probe.

*(from §4)*

- **`audiofreeverb.Freeverb`** is a *fixed* Schroeder network. The comb and
  all-pass lengths that reach the DSP are hard-coded in the **ported binding**
  — 1116…1617 and 556/441/341/225, assigned with no `sample_rate` term
  (`audiofreeverb/Freeverb.c:87-94`, `:107-110`), so they are fixed sample
  counts at every rate. `roomsize` reaches only the comb feedback
  (`audioif_freeverb.c:19`), `damp` only a one-pole per comb (`:20-21`,
  `:35-36`), and the loop (`:26-57`) modulates no tap and disperses none.
  Measured this run: the first wet arrival is the shortest comb — frame 1116,
  23.25 ms at 48 kHz mono — and in stereo every tap lands at **half** its
  index because the two channels share one bank (App. G, an upstream defect,
  §8.4); `mix = 0` is not a wire; RT60 tops out at 4.14 s stereo / 8.38 s mono
  and **moves with the input level**, the int16 feedback path truncating
  (App. D). Against the traits it fails **T1** (that 23 ms arrival: the four
  all-passes sit *after* the combs, `:43-51`, so nothing diffuses the input),
  **T4** and **T9** (line lengths no class can reach), **T5** and **T6** (no
  dispersive all-pass) and **T10** (no modulator). **T2, T3 and T7 are not
  shown unreachable here** and the ask does not rest on them: `damp` and
  `roomsize` are independent block inputs, so a control law could co-vary
  them (T3), neither modal density nor the band-T60 ratio was measured this
  run (T2), and T7's tank-input cut composes — an `audiofilters.Filter` ahead
  of the node run wet-only (`mix = 1`, so its own dry term is zero,
  `audioif_freeverb.c:23-24`) with the class summing the dry itself.

*(from §4)*

- **`audioecho.FeedbackDelay`** is a two-line cross-coupled tank already: an
  in-loop one-pole low-pass and high-pass, a soft clip, cross-feed between
  channels and a per-sample interpolated read under a per-sample sine
  (`audioif_feedback_delay.c:227-228`, `:209-213`, `:231-243`, `:247-249`).
  One tap per channel, one shared sine, `int16_t` line (`.h:93`). **The node
  alone is a comb, not a diffuser** — `line[w] = x + fb·(filtered delayed)`
  (`:255-256`), no −g feed-forward, and neither coefficient can go negative
  (dry is `2−mix` capped at 1 over a `mix` clamped `0..2`, `:201`, `:99`,
  `:260-261`; feedback clamped `0..0.99`, `:90`). **The palette
  composes an all-pass anyway**, and this run measured it flat to 0.00 dB from
  100 Hz to 18 kHz out of `Splitter` + wet-only `FeedbackDelay` + two constant
  `Multiply` gains, one of them negative, + `Mixer` (App. D). So Fig. 1's
  *input diffusion* is reachable today; its *recirculation* is not.

*(from §4)*

- **The tank cannot be assembled from several nodes at all**: this is a pull
  graph with no cycles. `d1.play(s); d2.play(d1); d1.play(d2)` constructs, and
  the first `get_buffer` raises `RecursionError` — re-verified this run
  (App. D). A figure-eight has to live inside one node's sample loop; feeding
  a block back through Python instead quantises every tank line to 256 frames,
  5.33 ms, longer than most of Fig. 1's lines.

*(from §4)*

- **`audioconvolve.Convolver`** reaches any character exactly and is the
  sibling class, at 5.33 ms of latency and ~377 KB per stored second per IR
  channel — a different product from a zero-latency stompbox reverb.

*(from §4)*

**The build.** One new audioif-own node (§5) holding Fig. 1 with the delay
lengths as **construction parameters, not constants**, so one node serves all
five characters. Python computes on CPython at construction — scaled line
lengths (`round(n · Fs/29761 · size)`), the five coefficient sets, the damping
and bandwidth one-poles, the tap table, and the spring's dispersive
coefficients — and C runs the tank per sample; nothing is recomputed on a
board. **Portability tier: audioif** — on a stock board the module imports and
`Reverb(...)` raises a clear `ImportError`, the guarded shape `drive.py:29-32`,
`:331-332` already uses. **Mono:** the tank sums its input to mono by
construction (S1 §1.3.6), so a mono source gets the same tank with the two tap
sets summed — the mono sum of the stereo behaviour, which the kit measures.

*(from §5)*

- **What the palette does instead, and the measurement.** Freeverb is the only
  reverberation network on it; the line lengths that reach its DSP are
  hard-coded in a **ported binding** (`audiofreeverb/Freeverb.c:87-94`,
  `:107-110`), and against the trait set it fails **T1, T4, T5, T6, T9 and
  T10** — T1 and the stereo collapse measured this run, the rest read off the
  kernel, which carries no modulator, no dispersion and no length control
  (§4). T2, T3 and T7 are *not* claimed unreachable there; each composes or
  was not measured, and the ask does not need them. The one thing that
  closes the compose-first door is structural: assembling a tank from other
  nodes needs a cycle, and a cycle here is a `RecursionError` on the first
  pull (App. D). It is **not** true that the palette has no all-pass — the
  node alone has no −g feed-forward (`audioif_feedback_delay.c:255-256`,
  `:201`, `:90`), but `Splitter` + `FeedbackDelay` + `audiomath.Multiply` +
  `Mixer` compose one, measured flat to 0.00 dB across the band this run
  (§4, App. D). The diffusers are reachable; the recirculation is not.

*(from §5)*

- **The ask, additive.** A new module (`audioverb`, say) whose `Tank` takes
  delay lengths, four decay coefficients, two diffusion coefficients,
  bandwidth, damping, excursion, modulation rate and the output tap table as
  construction parameters, with **int16 line memory and magnitude truncation**
  (S1 §1.3.4) and float filter/all-pass state. One option, off by default: a
  **dispersive all-pass chain** on the tank input for the spring character.
  Nothing ported is touched; D1 covers it.

*(from §5)*

- **Refutation record (Phase 0, re-run 2026-09-07 by the palette verifier).**
  (1) Re-tune Freeverb from Python — refused: the lengths are constants in the
  ported binding, and the `_banks` kernel that would take them is reached only
  through that binding. (2) Compose the tank from `FeedbackDelay` + `Filter` +
  `Splitter` + `Mixer` — refused: the recirculation needs a cycle and the first
  pull raises `RecursionError`, re-measured this run. (2b) **Compose the
  all-passes**, which the earlier draft said was impossible — *this one
  succeeds*: a Schroeder all-pass built from `Splitter` + wet-only
  `FeedbackDelay` + two constant `Multiply` gains (one negative) + `Mixer`
  measures flat to 0.00 dB, 100 Hz to 18 kHz (§4). It buys the input
  diffusion and nothing else, at five nodes and one int16 requantisation per
  all-pass — Fig. 1's eight all-passes would be forty nodes, and four of the
  eight are inside the loop that cannot exist. (3) Use the Convolver for every
  character — *exact*, but 5.33 ms of latency (re-measured this run: an impulse
  loaded, first arrival at frame 256) and ~377 KB/s per channel forecloses the
  stompbox use vision §9a names, and a fixed IR cannot modulate (T10). (4)
  Reach T10 alone on `FeedbackDelay`'s per-sample sine — the *modulation
  mechanism* is on the palette already (`audioif_feedback_delay.c:209-213`,
  `:227-228`); it is the tank it would modulate that is missing, which is why
  the ask is for a tank and not for a modulator. The ask survives.
