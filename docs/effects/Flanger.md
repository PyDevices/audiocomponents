# Effects Dossier — `Flanger` (Electro-Harmonix Electric Mistress)

**Class:** `lib/audioeffects/modulation.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Modulation, roadmap Phase 3
**Standout:** Electro-Harmonix Electric Mistress, per vision §4.2 —
**confirmed**, and pinned to the **original 1976 Flanger/Filter Matrix**
(Reticon SAD1024, three knobs — Color, Range, Rate — and a Filter Matrix
switch: S6, S7). The Deluxe of 1978 is the same idea with "a different LFO
and VCO circuit, leading to a wider range of settings" (S8) and is the second
reference, not the referent. No swap argued: the Electric Mistress is the
flanger the BBD-modelling literature itself names (S3 §1).
**Grade:** **literature** — no schematic of the original was reached by the
research pass or the first licence-and-citation audit (§2 lists every route and
its failure mode). The traits come from the published BBD models (S2, S3, S4),
a clone's bill of materials (S5), one prose reading of the actual circuit
(S12) and the maker's own control descriptions (S13, with S6 and S9).
**The second audit reached a drawing with values (S15)** — Tonepad's
*Rev.2.Nov.1.2005* redraw, whose own host marks it `Status UNVERIFIED` and
whose subject is the **9 V single-battery** unit, described there as "the LFO
of the Deluxe (including it's controls) and the signal path of the ORIGINAL",
not the 1976 two-battery referent. Nothing in §3 was derived from it and no
trait rests on it — the trait set was fixed before it was reached — so the
grade stays **literature** as written here, and §8.1's condition is now a
reachable file (the fetch recipe is in S15's row) instead of a dead end.
**Portability tier:** **needs audioif-own nodes** (`audioecho.FeedbackDelay`,
plus the additive option asked for in §5).
**Status:** seed (Phase 0), written 2026-09-06

## 1. The circuit, in one paragraph

The signal splits: one copy goes straight to the output mixer, the other
through an anti-alias low-pass — "nearly all bucket-brigade circuits are
preceded and followed by low-pass filters" (S2 §1.3) — into a **Reticon
SAD1024**, "a dual 512-stage Bucket-Brigade Device … the sections may be used
independently, may be multiplexed …, may be connected in series to give
increased delay at a fixed sample rate, or may be operated in a differential
mode" (S10). Whichever of those four the pedal uses, the delay law is
**t_d = N/(2·f_clk)** (S2 §2.1; S4 eq. 25), and S2 works the generic flanger
case: "a flanger effect typically requires a maximum of a 10 ms delay.
BBD-based flangers typically use a single, 1024-stage delay line, giving a
clock frequency of 1024/(2·0.010) = 51.2 kHz." **N itself is unsettled and is
flagged, not asserted:** the earlier text read "so N = 1024", but that is an
inference from S2's *generic* sentence plus one of S10's four options, and the
one reached source that reads *this* circuit says the opposite — S12: "Although
the SAD1024 has 1024 stages these are run as 2 time 512 in parallal [sic] in
the Electric Mistress which will give the same delay as a single 512 stage BBD
but will imporve [sic] performance." One trait's *numbers* move with N and no trait's
*direction* does: F1 fixes the shape of the delay-versus-clock law, F5's 10 ms
comes from S2's sentence rather than from N, but **F7's −0.55 dB becomes
−2.3 dB** on the parallel reading, and F7 now says so. The seed proceeds with
N flagged; Phase 3 settles it with a schematic and F7's figures are restated
then. The two out-of-phase clocks the chip needs come from a
**4013 flip-flop dividing a VCO by two** — "the 4013 (flip flop) is used as a
divide by 2 square wave clock driver … To pass signal the 1024 needs two
phases of clock (one hi when other low) coming from the 4013 (pins 12 and
13)" (S9) — with comparators shaping the edges: S12, reading the circuit
itself, says "the heart of all Mistresses LFOs and VCOs are comparators" and
walks the LFO through an **LM339** — the part S9's Gus also reaches for when
the clock is suspect ("then look at the lm339") — and the 4013, while S5's clone BOM carries
one LM311N and one LM324 and S11 found an LM311N and an LM324 in a real Deluxe
v2 (the earlier text's "LM311 pair" was in none of the three, and the LM339 is
in neither BOM — the part differs by version and the seed asserts no number) and a trimmer setting the BBD's input
bias (S5, S9). There is no clipper and no diode: **the
nonlinearity is the BBD itself**, a long chain of charge transfers with
limited dynamic range (S2 §3.1), plus the regeneration loop. A
**relaxation-oscillator LFO** — S12 walks it through two comparators and a
4013 flip-flop charging and discharging a 2.2 µF capacitor, so its output is a
rising and falling ramp — its speed set by **Rate**, drives the VCO through
**Range**, which
"allows you to set the lower limit of the flanger sweep … As you turn RANGE
clockwise the flanger sweeps down further into the bass region" (S13, EHX's
own manual — for the **current compact reissue** of the Deluxe, see §2; S6, a
plug-in vendor's, adds "sets the depth and lower limit"); because the delay is the *reciprocal* of the clock, a linear clock
sweep gives a delay "roughly proportional to 1/x" (S4 §5.1) — the LFO's shape
is not the delay's shape. **Color** "sets the intensity of the flanger effect.
As you turn COLOR clockwise the effect becomes more pronounced" (S13); it is
the regeneration path, and it can run away at the top — S13: "Turning COLOR to
its most clockwise setting could cause self-oscillation to occur. This is
normal!" — bounded inside the pedal by a trimmer: "the other trim pot sets a
maximum for how much output gets fed back into the input, if adjusted too high
the feedback will run away" (S9), aligned "until the unit just oscillates.
Then back off from this point until oscillation just ceases" (S9, quoting the
factory procedure). The delayed copy leaves through a reconstruction low-pass
that also kills clock bleed (S2 §2, S4 §5) and is summed with the dry copy —
**at what ratio is unsourced.** No reached source states the Mistress's mix,
so *equal weight*, which is what makes the notches true nulls, is this seed's
construction choice and is carried into F2 as one. The **Filter Matrix** switch,
in the maker's own words: "the modulation waveform is disconnected from the
flanger circuit, freezing the flanger and creating a matrix of filters. Turn
the RANGE knob to change the filters' position and use COLOR to adjust the
depth of filtering. The RATE knob has no affect when set to FILTER MATRIX
mode" (S13) — the comb stands still and Range positions it. *(The earlier
draft gave this as a quotation from S6; the words were a paraphrase of three
separate S6 sentences, and S13 says it directly.)*

## 2. Sources and license calls

Reached 2026-09-06 from this machine; nothing from memory. **Appendix C**
carries what each gave, quoted. Every row below was re-fetched and re-read by
the licence-and-citation audit of the same day; rows marked *(audit)* were
added or rewritten by that pass, and its corrections are listed at the end of
this section. Five licence calls were wrong and are corrected here; four
sources recorded as unreachable were reached.

| Source | License call | URL | Reached |
|---|---|---|---|
| S2. Raffel & Smith, DAFx-10 … (App. S2) | No licence statement in the PDF … (App. S2) | https://www.dafx.de/paper-archive/2010/DAFx10/RaffelSmith_DAFx10_P42.pdf | yes (PDF, pypdf) |
| S3. Holters & Parker, DAFx-18 … (App. S3) | No licence statement in the PDF … (App. S3) | https://www.hsu-hh.de/ant/wp-content/uploads/sites/699/2018/09/Holters-Parker-2018-A-Combined-Model-for-a-Bucket-Brigade-Device-and-its-Input-and-Output-Filters.pdf | yes (PDF, pypdf) |
| S4. Huovilainen, DAFx-05, "Enhanced Digital Models for Analog … (App. S4) | No licence statement in the PDF … (App. S4) | https://www.dafx.de/paper-archive/2005/P_155.pdf | yes (PDF, pypdf) |
| S5. PCB Guitar Mania, "Electric Lover Flanger" build doc v1.1 … (App. S5) | **Corrected by the audit.** Its "Licensing … (App. S5) | https://pcbguitarmania.com/wp-content/uploads/2018/05/Electric-Lover-Flanger-1.1v-Building-Docs.pdf | yes (partly) |
| S6. MixWave, "EHX Electric Mistress User Guide" … (App. S6) | **Corrected by the audit:** the page does … (App. S6) | https://support.mixwave.com/help/ehx-electric-mistress-user-guide | yes |
| S7. Effects Freak, "Electric Mistress v2 (1976-1977)" | **Corrected by the audit:** not "no licence … (App. S7) | https://effectsfreak.com/effect/electric-mistress-v2-1976-1977-w-original-packaging/ | yes |
| S8. Audiority, "Electric Matter" product page | **Corrected by the audit:** carries *"© … (App. S8) | https://www.audiority.com/shop/electric-matter/ | yes |
| S9. GroupDIY, "Fixing an electric mistress, help needed" | Forum posts; no copyright line on the thread … (App. S9) | https://groupdiy.com/threads/fixing-an-electric-mistress-help-needed.21271/ | yes |
| S10. DatasheetCafe's HTML page for the EG&G Reticon SAD-1024 … (App. S10) | **Corrected by the audit:** the host returns … (App. S10) | https://www.datasheetcafe.com/sad1024-pdf-datasheet-14598/ | **yes** (audit; HTTP 200) |
| S11. JonDent, "Electro harmonix Deluxe Electric Mistress - Version 2" | No licence statement found on the page … (App. S11) | https://djjondent.blogspot.com/2017/10/electro-harmonix-deluxe-electric.html | yes |
| S12. Ralf Metzger, "How the Mistress works" + its BBD and measurement … (App. S12) | *"© www.metzgerralf.de 2003-2015"* … (App. S12) | http://metzgerralf.de/elekt/stomp/mistress/how.shtml (also `bbd.shtml`, `measure.shtml`) | yes — **plain HTTP only**; the https URL fails on a certificate name mismatch, which is what earlier runs recorded, and `WebFetch` cannot reach it because it upgrades to https |
| S13. Electro-Harmonix, "Deluxe Electric Mistress Flanger/Filter Matrix" … (App. S13) | Manufacturer product documentation … (App. S13) | https://www.ehx.com/wp-content/uploads/2021/01/deluxe-electric-mistress-manual.pdf | yes (HTTP 200, PDF, pypdf) |
| S14. Fractal Audio Systems Forum, "MOAEE - Electric Mistress Flanger" … (App. S14) | Forum posts, no licence … (App. S14) | https://forum.fractalaudio.com/threads/moaee-electric-mistress-flanger.76166/page-5 | yes (HTTP 200) |
| S15. Tonepad (Francisco Peña), "Electric Mistress Flanger … (App. S15) | The licence is printed on the drawing: … (App. S15) | http://www.tonepad.com/project.asp?id=54 → `getFileInfo.asp?id=102` → `getFile.asp?id=102` | **yes** (HTTP 200, `application/pdf`, 89 372 bytes, 1 page, text layer readable). The download is session-gated, which is what defeated the first audit: `getFile.asp` alone 302s to `downloadWarning.asp` ("Please visit the relevant project(s) page before downloading"). Fetch the project page and the file-info page first **with a shared cookie jar** (`curl -c jar -b jar`) and the third request returns the PDF |
| Local: `audioif/src/shared/{audioif_feedback_delay.c,audioif_echo.c}`, `src/audioecho/FeedbackDelay.c`, `audioif/docs/upstream-diff.md`, `audiocomponents/lib/audioeffects/{modulation.py,_core.py}` | MIT | — | yes |

S2, S3 and S4 are the whole basis of the traits; S5 gives a clone's control
values, S13 (EHX's own manual) and S9 the control functions, S7/S8/S11 the
versions and the chip, S12 the only prose reading of the actual circuit.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

Numbers marked (B) are measured in Appendix B, the delay law is Appendix A, and
(E) is the trait critic's calibration in Appendix E. Every row names the macro
settings it is read at; every spectral threshold names its resolution, because a
null's measured depth is a property of the analysis as much as of the filter.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| F1 | **The delay is the reciprocal of the clock, so a linear ramp in the clock is a hyperbola in delay.** With the class's own ramp LFO (`Shape` 0.5, `Filter Matrix` off), over one monotone half-cycle with the turnarounds excluded: an affine fit to **1/t_d(t)** leaves an RMS residual under **2 % of its span**, while an affine fit to **t_d(t)** leaves at least **5 %**. An exact 4:1 hyperbola gives 8.8 % RMS for the second fit and a delay that is a triangle in milliseconds gives 0 % and fails (E1) | S2 §2.1 (t_d = N/(2·f_cp), stated generally … (App. F1) | high for the … (App. F1) | an affine fit to 1/t_d with RMS residual over 2 % of span, or an affine fit to t_d under 5 % | delay tracking: t_d from the … (App. F1) |
| F2 | **Equal-weight comb: notches at (2k+1)/(2·t_d), spacing 1/t_d, the first a null.** At `Color` 0, the sweep stopped (`Filter Matrix` on), `Mix` at the position the class documents as equal weight: every notch below 8 kHz matches the grid to **0.5 %**, and the deepest is at least **30 dB** below the mean of the same transfer over 100 Hz–8 kHz, read at **2.93 Hz** resolution (16384-point Hann, ≥ 2¹⁶ samples, as B.1) | S4 §1 and §5, both re-read this run: *"the … (App. F2) | high | a grid that is not odd-harmonic; or a floor shallower than 30 dB at `Color` 0 at the stated resolution | notch tracking on a white-noise … (App. F2) |
| F3 | **Color is regeneration — peaks, not depth.** At 3 ms held, the comb's peak gain rises **monotonically** across `Color` 0 / 0.3 / 0.6 / 0.9 and by at least **15 dB** end to end, while the notch floor *fills* by at least **10 dB** over the same span | S6 ("Higher settings emphasize the … (App. F3) | high for … (App. F3) | peaks flat or non-monotonic with `Color`; or a floor that deepens as `Color` rises | comb peak gain and notch floor … (App. F3) |
| F4 | **Filter Matrix stops the sweep and nothing else.** With the mode on: the first notch moves under **5 cents in 10 s**; its position at `Rate` 0.02 Hz and at `Rate` 8 Hz agrees within **5 cents**; `Manual` moves it monotonically across §6's whole 0.4–12 ms span; and `Color` still passes F3's test (≥ 15 dB, monotone) with the mode on | **S13, EHX's own manual … (App. F4) | high for the … (App. F4) | drift over 5 cents in 10 s; a notch position differing by more than 5 cents between the two `Rate` settings; a non-monotonic `Manual` sweep; or a `Color` peak rise under 15 dB with the mode on | notch tracking over 10 s with the … (App. F4) |
| F5 | **The sweep spans at least 4:1 in delay, topping out near 10 ms.** At `Range` max, `Filter Matrix` off, over one full LFO period: the longest t_d is **8–12 ms** and max(t_d)/min(t_d) is **≥ 4** — two octaves of notch spacing | S2 (*"a flanger effect typically requires a … (App. F5) | medium — the maximum … (App. F5) | a longest delay outside 8–12 ms at `Range` max, or a ratio under 4 | delay tracking as F1 (k-th notch … (App. F5) |
| F6 | **The delay lags the clock: a modulation step makes no discontinuity.** After a single-block step of `Manual` 1 → 6 ms: (a) the tracked t_d reaches 90 % of its new value **no sooner than one pre-step transit time (1 ms) after the step**, and (b) the largest \|y[n] − y[n−1]\| in the 50 ms *after* the step exceeds the largest in the 50 ms *before* it — same input, delay held — by no more than **10 %** | S4 §5.1, re-read this run: *"unlike with digital delays, discontinuities in the modulating signal do not produce discontinuities in the delay time"*, and eq. 25 (the transit-time average); S3 §2 | medium — the mechanism is sourced twice; both bounds are this seed's | a t_d that reaches its new value inside one transit time; or a post-step first-difference more than 10 % above the pre-step one | click test: 1 kHz tone, single-block step of `Manual` 1 → 6 ms; the two windows above, plus the tracked t_d(t) through the step. **Rewritten by the trait critic:** the old bound, *"the output's maximum sample-to-sample step never exceeds the input's"*, is already failed on a **correct** build by the seed's own B.3 — the node's per-sample sine gives 3144 against the input's 1566, because a comb sums two copies of one signal and can double its slope (E3). A criterion a correct build cannot meet cannot separate a good build from a bad one; the before/after window is the same claim with a control |
| F7 | **The wet path darkens as the delay lengthens, by the sample-and-hold's own law.** Wet only (on the node `mix = 2.0` sets dry to 0 and wet to 1, `audioif_feedback_delay.c:201-202`, read this run), at three held delays spanning the sweep: the 10 kHz level matches **\|sinc(π·10 kHz / f_clk)\|** within **0.5 dB** with f_clk = N/(2·t_d) from the build's own N; and, independent of N, that level falls **monotonically** with delay across the sweep by at least **0.4 dB** while the dry path (`Mix` 0) moves less than **0.05 dB** | S3 §2, re-read this run: the combined output *"is also convolved with a rectangular pulse of one clock period width giving rise to a high-frequency attenuation depending on the BBD clock rate"*; S2 §2 (the filters sit at 1/3–1/2 f_clk, above the band at the long end). **N is unsettled** (§1): at 10 ms the same arithmetic gives **−0.55 dB** for N = 1024 and **−2.30 dB** for S12's parallel reading, N = 512 effective — both recomputed this run (E2). The **law** is the trait and does not move with N; the two dB figures are restated once §1's N question closes | medium for the mechanism and the direction; the 0.5 dB tolerance is this seed's and survives either N once f_clk is read off the build | the wet path flat at 10 kHz across the sweep; a 10 kHz level more than 0.5 dB from the sinc law at the build's own f_clk; or a dry path that moves | wet-only magnitude at 1, 5 and 10 kHz at the sweep's two held ends and its middle; dry-path check at `Mix` 0. **Rewritten by the trait critic:** the old row asked for a "Mix wet-only" reading without establishing it was reachable. It is — at the node's `mix = 2.0` — but §6's `Mix` macro stops at 0–1, so the class must expose that position or the trait cannot be measured through `create()` (§8.6) |
| F8 | **The `Color` ceiling rings and does not run away.** At `Color` max and 3 ms held: after a burst the −60 dB tail is **≥ 2 s**, and the envelope over the following 10 s of silence is **monotonically non-increasing** | **A design requirement, not a circuit trait … (App. F8) | n/a — a design … (App. F8) | a tail under 2 s, or an envelope that rises at any point in the 10 s | burst-then-silence at `Color` … (App. F8) |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Compose first.** `audioecho.FeedbackDelay` is the node: it reads the line
**per sample with linear interpolation** (`audioif_feedback_delay.c:226-228`)
under a per-sample oscillator (`:209-213`), with **two** in-loop one-poles —
a low-pass (`damping_hz`, `:231-235`) and a high-pass (`cut_hz`, `:236-240`)
for the BBD's band-limiting — a soft-clip (`loop_drive`, `:241-243`) for its
dynamic-range limit, and cross-feed for a stereo spread. Both one-poles sit on
the value that becomes **the wet output as well as the feedback**
(`:230-244` then `:260-261`), which is why F7 is measurable at `Color` 0.
At `mix=1.0` the dry stays at unity and the wet arrives at unity (`:201-202`)
— exactly F2's equal-weight sum. **Verified this run** (B.1): at 1, 3 and 6 ms
the measured notches land on (2k+1)/(2·t_d) to the FFT bin, and the deepest is
−41.9 dB at 1 ms with feedback 0. F3's direction is verified too (B.2): the
comb peak rises +6.3 → +39.7 dB from feedback 0 to 0.99 while the floor fills
from −32.4 to −7.9 dB. The mix law was re-verified byte-exactly by the palette
verifier (G.1): at `mix=1.0` the output equals `input + input delayed by
delay_ms` to the LSB over 3000 frames, at `mix=2.0` it equals the delayed copy
alone, and at `mix=0.0` it is the source unchanged.

**Two limits the class must size around.** `delay_frames` is clamped to
`line_frames − 2` (`:82-83`) and the line is always allocated for two lanes
(`:171`), so `max_delay_ms` must be sized above the sweep's top and a mono
build pays the stereo RAM.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**A1 — `wow_shape`: a one-period shape table on `audioecho.FeedbackDelay`'s
own oscillator.** Additive, defaulting to the present sine so a delay built
without it is byte-identical to today's, per audioif's extend-never-modify
rule. Unblocks **F1** (the reciprocal-of-triangle clock law) and **F6** (no
discontinuity on a modulation step); the class bakes the clock law in Python
and C only looks the table up — the exact node the vision's §6 already
sketches ("a one-period shape table, so the dossier bakes the clock law in
Python and C only looks it up").

No second ask. F2, F3, F4, F5 and F7 are all reachable on the node as it is.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Twelve macros (the ceiling is sixteen), `UNIPOLAR` unless marked. `capabilities = ("tempo_sync",)` —
the class reads `transport()` for macros 9–10 (D10: an LFO-driven modulation
class is exactly the candidate the roadmap names).

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | `Rate` | UNIPOLAR | 0.02–8 Hz, log | the Rate knob |
| 1 | `Range` | UNIPOLAR | sweep depth and its lower delay limit, 0.4–12 ms span | the Range knob (S6) |
| 2 | `Color` | UNIPOLAR | regeneration 0–0.95 | the Color knob (S6); the ceiling is the factory trimmer (S9) |
| 3 | `Manual` | UNIPOLAR | 0.4–12 ms | where the comb sits when the sweep is stopped |
| 4 | `Filter Matrix` | TOGGLE | off / on | the panel switch: LFO disconnected (S6) |
| 5 | `Mix` | UNIPOLAR | 0–1, default 0.5 (equal weight); 0 is a wire | the pedal's fixed sum |
| 6 | `Shape` | UNIPOLAR | LFO ramp duty 0.25–0.75, default 0.5 | the LFO's ramp asymmetry |
| 7 | `Tone` | UNIPOLAR | wet-path low-pass, 2–16 kHz | the BBD's band-limiting (F7) |
| 8 | `Spread` | UNIPOLAR | stereo regeneration cross-feed 0–1, default 0 | nothing on the pedal; the node offers it |
| 9 | `Sync` | TOGGLE | off / on | tempo-locks Rate to the transport |
| 10 | `Division` | UNIPOLAR | quantised 4, 2, 1, ½, ⅓, ¼, ⅛ bars | the sync division; ignored when Sync is off |
| 11 | `Through Zero` | TOGGLE | off / on — **adds latency** (Tier 3) | nothing on the pedal; stated because it costs |

No characters — one circuit, one trait set. (The 1978 Deluxe is a second
reference, §8.4, not a character.)

**Patches:** 0 `Slow jet`; 1 `Fast metallic`; 2 `Held comb` (Filter Matrix on,
`Manual` mid); 3 `Wide sweep with resonance`; 4 `Shallow and short`;
5 `Deep and slow, no resonance`; 6 `Synced one bar`; 7 `Through zero, dry
delayed`.

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/modulation.py`. Nothing else is carried.

1. **No surface.** `MACRO_LABELS = ()` (`:47`), `MACRO_MODES = {}` (`:48`),
   `PATCHES = {0: ("Default", ())}` (`:49`) — nothing a host can turn, and no
   Filter Matrix at all.
2. **A node with no interpolation.** `audiodelays.Echo` (`:55`) reads its line …  *(argument in full: App. R)*
3. **The wrong modulation shape.** `synthio.LFO(rate, scale=depth_ms, …  *(argument in full: App. R)*
4. **The delay knob does not mean milliseconds on this node.** *(Rewritten by …  *(argument in full: App. R)*
5. **A quarter of the line is wasted:** `max_delay_ms = int(depth_ms*2+20)`
   (`:56`) allocates 25 ms for a 1.0–6.0 ms sweep.
6. **Nothing declared** — no `CAPABILITIES`, `LATENCY_SAMPLES` or …  *(argument in full: App. R)*
7. **`reset()` and `deinit()` reach one node** (`_core.py:366-374`,
   `:376-385`) — right here only because the class builds one; the rebuild
   must enumerate what it builds.
8. **The docstring promises a sound instead of describing a build** (`:40-41`,
   "the real swept comb, jet engine included") — no delay range, no latency,
   no mono statement.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **The schematic.** Four routes to the original drawing failed (§2). The
   grade moves from *literature* to *circuit* the moment one is read; the two
   worth retrying are `metzgerralf.de` (a TLS *name* mismatch, so a different
   tool may reach it) and tonepad's own PDF. *Settles:* Phase 3, or the
   dossier records the grade as final.
2. **Regeneration polarity.** The vision's §6 says this pedal has *inverted*
   feedback. Every page asserting it was a 403 (§2), so this run neither
   confirms nor denies it and **no trait and no node ask rests on it**. If it
   is confirmed, the node's `0..0.99` feedback clamp
   (`audioif_feedback_delay.c:90`) blocks it and a signed-feedback option
   becomes a second ask with F3 as its trait id. *Settles:* Phase 3 — and
   only with a schematic or a measurement, never a forum summary.
3. **The shortest delay.** S2 gives the maximum (10 ms); nothing reached
   gives the minimum, so F5 fixes a ratio, not an endpoint. *Settles:*
   Phase 3, from the VCO range if §8.1 succeeds.
4. **Original versus Deluxe.** S8 says the Deluxe has a different LFO and VCO
   "leading to a wider range of settings". The seed follows the 1976 unit and
   treats the Deluxe's wider range as macro span, not a second character.
   *Settles:* Phase 3, if a Deluxe schematic is reached.
5. **Whether F7 is worth building.** 0.55 dB at 10 kHz is small; if the kit
   cannot separate it from the reconstruction filter's own slope, F7 is
   recorded as disconfirmed-by-measurement rather than dropped. On S12's
   parallel reading of N the figure is 2.30 dB and the question largely
   answers itself, which is one more reason §1's N matters. *Settles:*
   Phase 3.
6. **Which `Mix` position is equal weight, and whether wet-only is exposed**
   *(trait critic, 2026-09-06)*. §6 gives `Mix` as "0–1, default 0.5 (equal
   weight)". On the node, dry sits at unity for any `mix` ≤ 1, equal weight is
   `mix = 1.0`, and `mix = 2.0` is wet alone
   (`audioif_feedback_delay.c:201-202`). **F2's null depends on the mapping and
   F7's measurement needs the wet-only position to exist** — a `Mix` macro that
   stops at the node's 1.0 makes F7 unmeasurable through `create()`, which is
   the shape of defect §7.4 records in the current class. *Settles:* Station A,
   in §4 and §6.
7. **F6's transit-time bound** *(trait critic, 2026-09-06)*. The row now asks
   that t_d reach 90 % of its new value no sooner than one pre-step transit
   time. S4's eq. 25 gives the averaging explicitly; whether the *90 %* point
   is the right read of it, or whether the criterion should be stated on the
   averaging window itself, is a Phase 3 question once the kit's tracker
   exists. *Settles:* Phase 3.

---


## Appendix

### A. The delay law, and what it implies for the sweep

S2 §2.1: "For any BBD, the total time delay is given by Delay Time (s) =
N/(2·f_cp) where N is the number of stages in the BBD and f_cp is the
circuit's clock frequency", and its own worked flanger case: "a flanger
effect typically requires a maximum of a 10 ms delay. BBD-based flangers
typically use a single, 1024-stage delay line, giving a clock frequency of
1024/(2·.010) = 51.2 kHz. This requires an input signal bandlimited to
25.6 kHz."

S3 §2 adds what the output does: the sampled value "is present at the
combined output from t_{N−1} to t_{N+1}", so "for a constant clock rate, the
signal is not only delayed by N/2 clock periods … It is also convolved with a
rectangular pulse of one clock period width giving rise to a high-frequency
attenuation depending on the BBD clock rate" — F7. It also names the two
aliasing sources: input components above the BBD Nyquist, and the output's
sample-and-hold images, "at least when present in small quantities …
desirable for the expected sound of a BBD".

S4 §5.1 is the sweep statement: "As the delay line length is fixed, the delay
time can be varied only by changing the clock rate. This is equivalent to
changing the sample-rate with time and has two effects: First, if the clock
rate is varied linearly, the delay time will be roughly proportional to 1/x.
Second, as the clock-rate changes, the output sample-rate is not the same as
the rate the audio was sampled in to the BBD. This causes some warping of the
delay-time curve … Note that, unlike with digital delays, discontinuities in
the modulating signal do not produce discontinuities in the delay time" —
F1 and F6. Its eq. 25 gives the smoothing explicitly, t_d =
avg(N/f_clock, N·f_s/f_clock): the delay is the instantaneous value averaged
over the transit time.

F7's number: |sinc(π·10000/51200)| = 0.9382 = **−0.55 dB** at 10 kHz for a
10 ms delay, against ≈0 dB at the short end where the clock is an order of
magnitude higher. The reconstruction filters sit at 1/3–1/2 of the clock
(S2 §2.1), i.e. 17–26 kHz at the long end — above the band, which is why S2
says that for flangers "the filters can be neglected" and why F7 rests on the
sample-and-hold rather than on them.

Companding is **not** modelled: S2 §3.1 — "In systems with shorter delay
times and a clock frequency that does not vary dramatically, such as chorus,
flanger, and vibrato circuits, these effects are generally ignored", and
§1.2, "companders are not typically used and the low-pass filters normally
have minimal effect in the audio range" for short-delay circuits. No reached
source puts a compander in the Electric Mistress.

### B. Probes run in this session

CPython, `audiocomponents/.venv/bin/python` against audioif's CPython build,
48 kHz stereo 16-bit signed, `audioecho.FeedbackDelay(max_delay_ms=25)`.

**B.1 — the comb law, on the node.** White noise in, magnitude ratio averaged
over 2¹⁶ samples in 16384-point Hann segments, `mix=1.0`, `feedback=0`:

| delay | predicted notches (2k+1)/(2τ) | measured deepest |
|---|---|---|
| 1.0 ms | 500, 1500, 2500, 3500 … | 501.0, 1500, 2499 (−41.9 dB), 4500, 5499 |
| 3.0 ms | 166.7, 500, 833.3, 1166.7 … | 1166, 2168, 2499 (−32.4 dB), 3167, 4166 |
| 6.0 ms | 83.3, 250, 416.7, 583.3 … | 750, 3750, 4084, 4251, 5915 (−30.8 dB) |

Every measured minimum falls on a predicted (2k+1)/(2τ) to the 2.93 Hz bin.
F2's mechanism is reachable as composed.

**B.2 — Color is regeneration** (3 ms, `mix=1.0`, 100 Hz–6 kHz):

| feedback | notch floor | comb peak |
|---|---|---|
| 0.00 | −32.4 dB | +6.3 dB |
| 0.30 | −13.5 dB | +8.2 dB |
| 0.60 | −8.9 dB | +11.8 dB |
| 0.90 | −6.7 dB | +23.7 dB |
| 0.99 | −7.9 dB | +39.7 dB |

Peaks rise 33 dB while the floor fills 24 dB — F3's direction, on the node.
`feedback` is clamped to `0..0.99` (`audioif_feedback_delay.c:90`); a
negative value is accepted silently and clamped to 0, which is why §8.2's
polarity question would be a node ask if it were ever confirmed.

**B.3 — block-rate stepping versus the node's own oscillator.** 1 kHz tone,
delay swept 1–6 ms by a 0.5 Hz triangle, `feedback=0`, `mix=1.0`; spurious
energy 200 Hz–6 kHz excluding ±20 Hz around the carrier, re carrier:

| how the delay moves | spurious/carrier | max \|y[n] − y[n−1]\| |
|---|---|---|
| Python `set(delay_ms=…)` once per 64-frame block | −37.4 dB | — |
| … per 128-frame block | −35.0 dB | — |
| … per 256-frame block | **−28.1 dB** | **5112** |
| … per 1024-frame block | −6.5 dB | — |
| the node's per-sample sine `wow_hz/wow_depth_ms`, same depth | **−63.3 dB** | 3144 |
| (the input signal itself) | — | 1566 |

35 dB, and an output discontinuity three times the signal's own largest step.
This is the measurement A1 rests on.

### C. What each source gave

**S2 (DAFx-10).** The delay law and the 1024-stage flanger case (quoted in
Appendix A); "In a chorus, vibrato or flanger circuit, the delay time is
varied automatically by a low-frequency oscillator"; the filters are Sallen-Key — "a third-order filter
for anti-aliasing and a third-order filter followed by a second-order 'corner
correction' filter for reconstruction" — cut "between 1/3 and 1/2 of the
sampling frequency"; "Reticon manufactured the
popular BBD chips SAD512, SAD1024, SAD4096, whose suffix represents the
number of BBD stages"; companders are for long delays, not flangers.

**S3 (DAFx-18).** Names the reference devices — "Well-known BBD-based devices
include the Memory Man delay/echo pedal and **the Electric Mistress flanger
effect from Electro-Harmonix**"; the two-phase clock and the output
combination; the rectangular-pulse convolution and its clock-dependent HF
attenuation; the two aliasing sources and the filters that suppress them.

**S4 (DAFx-05).** "A flanger mixes a slightly delayed signal with the
original, acting as a comb filter … the flanger produces infinitely many
notches that are spaced at constant intervals"; "Flangers often add feedback
from delay output to input to produce a number of peaks to emphasize the
effect"; §5.1 on the reciprocal law, the warping and the absence of
discontinuities; eq. 25, the transit-time average; §5.2, the NE570 compander
model.

**S5 (PCB Guitar Mania, Electric Lover).** "Based on: EHX's Electric
Mistress". Controls: **Feedback 10K B, Range 100K B, Rate 1M C**; trimmers
Bias 100 k, Clock 10 k, T1 10 k, Vol 50 k. ICs: JRC4558 ×2, **MN3007** (the
modern stand-in for the SAD1024), CD4049UBE, 4013N, LM324, LM311N;
transistors 2N3904, 2N5087. Its calibration text: the Bias trimmer feeds the
BBD and without it "you may not hear any flanging"; the Clock trimmer is set
"to the point where you achieve a wide sweep with minimum noise"; "With T1,
we can control the maximum Feedback desired, as this trimmer acts as a
limiter to the maximum allowed". Its schematic page has no text layer and the
two images on it are 612×1-pixel gradients, so the drawing itself was **not**
read.

**S6 (MixWave user guide).** Rate: "Controls the speed of the modulation …
approaching vibrato-like behavior at extreme values." Range: "Sets the depth
and lower limit of the modulation sweep. Lower settings produce a tighter,
more subtle sweep. Higher settings extend the sweep further into the low
frequencies." Color: "Controls the intensity and feedback of the flanger …
Higher settings emphasize the comb-filter peaks, producing the classic
'whoosh.'" Filter Matrix: "Freezes modulation by disconnecting the LFO,
creating a static comb-filter effect where Range and Color remain functional
but Rate has no effect."

**S7 (Effects Freak).** "Three knobs take care of color, range, and rate,
while a bizarre filter matrix switch adds a tiny hint of metallic
ring-modulation when engaged"; the Reticon SAD1024; v1 1976 in a slim silver
chassis on two 9 V batteries, v2 1976-77 with an 18 V jack, a one-battery
version in 1980, the Deluxe in 1978.

**S8 (Audiority).** "This flanger, featuring a Reticon SAD1024 BBD chip …";
"Compared to the classic version, the Deluxe models feature a different LFO
and VCO circuit, leading to a wider range of settings."

**S9 (GroupDIY).** JohnRoberts: "The SAD1024 is an analog shift register …
the 4013 (flip flop) is used as a divide by 2 square wave clock driver"; "To
pass signal the 1024 needs two phases of clock (one hi when other low) coming
from the 4013 (pins 12 and 13)"; "The trim pot in the bottom left corner of
the schematic sets this input bias"; "The other trim pot sets a maximum for
how much output gets fed back into the input, if adjusted too high the
feedback will run away." Gus: "Look at the 4013 outputs on pins 12 and 13 …
look for out of phase waveforms" and, for the clock, "then look at the lm339"
— the same part S12 names in the LFO. StephenGiles, quoting the factory
alignment: adjust the feedback trim "until the unit just oscillates. Then
back off from this point until oscillation just ceases."

**S10 (DatasheetCafe's SAD-1024 page — HTTP 200, read on the page; the
first pass's "403, search-index only" was wrong and both audits confirm it).** "The
SAD1024 is a dual 512-stage Bucket-Brigade Device (BBD). Each 512-stage
section is independent as to input, output, and clock. The sections may be
used independently, may be multiplexed to give an increased effective sample
rate, may be connected in series to give increased delay at a fixed sample
rate, or may be operated in a differential mode." Cross-checked against S2
(which calls the flanger case a "single, 1024-stage delay line") and S11
("SAD1024A is a dual 512-stage bucket brigade device").

**S11 (JonDent).** The chips found in a Deluxe v2: LM78L, 4558, SAD1024A,
LM324, LM311N, 4013BE, 2N5087; "Versions 1 (1978), v2 (1979) & v3 (1981) used
the reticon SAD 1024 delay"; the Deluxe was designed by Howard Davis.

### D. Scripts

`probe_comb.py` (B.1, B.2) and `probe_fd.py` (B.3) were written and run in
this session's scratchpad. Station A re-writes them under
`audiocomponents/tools/` as part of the measurement kit (delay tracking,
notch tracking, the click test, silence-after-burst) so the dossier's numbers
and the evidence pack's come from one piece of arithmetic.

### E. Trait-critic calibration (2026-09-06)

Arithmetic run this session under `audiocomponents/.venv` (numpy); every figure
is reproducible from the statement beside it, and no source is cited here that
this run did not reach.

**E1 — how un-linear a hyperbola is.** With 1/t_d affine in time over a sweep of
ratio R, a least-squares affine fit to t_d itself leaves, as a fraction of
t_d's own span: R = 2 → 4.96 % RMS (13.70 % max); R = 3 → 7.39 % (23.22 %);
**R = 4 → 8.78 % (30.31 %)**; R = 6 → 10.21 % (40.37 %). F1's "at least 5 %" is
therefore cleared by about 1.8× on a correct build at F5's minimum 4:1 span,
while a delay that is a triangle in milliseconds gives exactly 0 % and fails.
The two thresholds are a pair: 2 % on the 1/t_d fit and 5 % on the t_d fit
straddle the real figure from both sides.

**E2 — the sinc figure at both readings of N.** |sinc(π·10 kHz / f_clk)| at a
10 ms delay: N = 1024 → f_clk 51.2 kHz → **−0.55 dB**; N = 512 effective
(S12's parallel reading) → 25.6 kHz → **−2.30 dB**. Both recomputed this run;
they match the figures §3 and Appendix A already carried. The *law* is what F7
tests, so neither number gates the trait — but the second is four times the
first, and a 0.4 dB floor written for the first is nearly free on the second.

**E3 — why F6's old bound could not be met by a correct build.** The output of
an equal-weight comb is x[n] + x[n−D], whose first difference can reach twice
the input's wherever the two copies slope the same way. The seed's own B.3
already shows it: the node's per-sample sine, on a *correct* continuous sweep,
gives max |y[n] − y[n−1]| = **3144** against the input signal's own **1566** —
2.0×. A criterion of "never exceeds the input's" fails on the good case, so it
cannot separate a good build from a bad one, which is what a trait has to do.
The replacement compares the step window against a held-delay window of the
same signal, so the comb's own doubling is in both sides of the comparison.

### G. Palette-verifier probes (2026-09-06)

Run by the palette verifier against the CPython build of audioif under
`audiocomponents/.venv/bin/python`, 48 kHz stereo 16-bit signed. Every claim
in §4 and §5 about what an audioif node can and cannot do was checked against
the C first (`audioif/src/shared/audioif_feedback_delay.c`,
`audioif/src/shared/audioif_echo.c`, `audioif/src/audioecho/FeedbackDelay.c`,
`audioif/src/audiodelays/Echo.c`) and then probed. The CPython wrappers were
read too, to be sure a probe on this interpreter measures the same clamps the
board sees (`audioif/src/cpython/audioecho.py:82-93`, `audioif/src/cpython/audiofilters.py:216-237`).

**G.1 — `FeedbackDelay`'s mix law and its clamps, byte-exactly.** 4096 frames
of noise, `delay_ms=3.0, feedback=0`:

| setting | result |
|---|---|
| `mix=0.0` | output **identical** to the source |
| `mix=1.0` | output − (source + source delayed 144 frames) = **0** over frames 1000–4000 |
| `mix=2.0` | output − (source delayed 144 frames) = **0** over the same window |
| `feedback=-0.6` | byte-identical to `feedback=0.0` — clamped silently (`:90`) |
| `feedback=1.5` | byte-identical to `feedback=0.99` |

So F2's equal weight really is `mix = 1.0`, F7's wet-only really is
`mix = 2.0`, and §8.6's mapping question is settled on the node side; what is
left for Station A is only whether §6's `Mix` macro exposes 2.0.

**G.2 — `audiodelays.Echo`, the alternative in §5(b).** Two findings, both
against the current class as well as against the alternative.

*The mix convention is doubled.* `Echo.c:245` reads
`mix = clamp(mix, 0, 1) * 2.0` before the kernel, so the Python-facing 0–1
range maps onto the kernel's 0–2. Measured with a held 3 ms delay,
`decay=0`: at `mix=0.5` the comb's deepest notch is **−27.8 dB** (equal
weight, a null); at `mix=1.0` the transfer is flat and rms out/in is
**0.9988** — wet alone. §7.4's draft claim of a −6.0 dB notch at `mix=0.5`
is struck.

*The delay is floored at the audio buffer.* `Echo.c:122-131` sizes the echo
buffer from `delay_ms` and then, at `:126-128`, raises it to `buffer_len`
(bytes, `:43`) if it came out smaller. At `_core.pcm()`'s `buffer_size=2048`
(`_core.py:64`), 1.0, 6.0, 12.0 and 21.333 ms render **byte-identically** —
1024 frames, 21.3 ms. At `buffer_size=512` the floor is 5.33 ms and 1.0, 3.0
and 5.0 ms are byte-identical while 5.333 ms matches them exactly. With
`freq_shift=True` the floor is bypassed (`:116-120`) and 1.0 and 6.0 ms do
differ. A 0.4–12 ms flanger sweep is therefore unreachable on `Echo`'s plain
path at any buffer size this library uses.

**G.3 — what block-rate control actually costs, controlled.** B.3 compared a
Python-stepped *triangle in ms* against the node's own *sine*: two different
trajectories, so its 35 dB conflates the trajectory with the control rate. The
controlled form renders an ideal float linear-interpolating delay line in
numpy, per sample, on the trajectory under test, and reports the candidate's
error against it as a level re the carrier (1 kHz, 8 s, 0.5 Hz LFO, 1–6 ms):

| candidate | trajectory | error re carrier |
|---|---|---|
| node, `delay_ms` stepped per 256-frame block | triangle in ms | **−23.3 dB** |
| ideal line, same trajectory, block ZOH | triangle in ms | −23.3 dB |
| node, its own `wow_hz`/`wow_depth_ms` sine | sine | **−66.3 dB** |
| ideal line, same sine trajectory, block ZOH | sine | −23.0 dB |
| node, `delay_ms` stepped per block | reciprocal (F1's law) | −20.0 dB |
| node, warped `wow_hz` (G.4) | reciprocal (F1's law) | −23.7 dB |

The gap between per-sample and per-block control is **43 dB** and it is the
same 43 dB on either trajectory. The raw spurious-energy metric B.3 used does
*not* separate them on the reciprocal trajectory — the ideal per-sample line
reads −17.9 dB there against the block ZOH's −17.6 dB, because the sweep's own
sidebands swamp both — which is why the error-against-ideal form is the one the
kit should carry. Delay discontinuity per block: 7.29 frames for the ZOH,
0.32 for the warp, 0.03 for the ideal.

**G.4 — the warped-oscillator counter-case, in full.** `wow_hz` is changed once
per 256-frame block while `wow_depth_ms` is held, so the delay itself stays
continuous and only the oscillator's rate steps. A planner mirrors the node's
recurrence in float32 (`:209-210`), tracks the phase open-loop, and solves each
block for the `wow_hz` that lands the sine on the reciprocal law's next value;
the depth carries 2 % headroom so the arc never has to reach ±1.

| `wow_hz` cap | achieved span | affine RMS on t_d | affine RMS on 1/t_d | error vs ideal |
|---|---|---|---|---|
| 2 Hz | 0.949–6.050 ms | 26.6 % | 25.2 % | — |
| 5 Hz | 0.948–6.053 ms | 13.5 % | 11.5 % | — |
| **20 Hz** | 0.989–5.983 ms | **8.64 %** | **0.01 %** | **−23.7 dB** |
| 100 Hz | 0.991–5.928 ms | 8.63 % | 0.01 % | — |

(F1's bars: 1/t_d under 2 %, t_d at least 5 %. The ideal target trajectory
scores 0.00 % and 8.59 % on the same fits, so at a 20 Hz cap the warp is
tracking the law to the planner's own resolution.) **The shape is reachable
and the artefact is not.** Two structural reasons, both read from the C:
`wow_step` is recomputed from `wow_hz` at `:113-114` and the magic-circle
recurrence at `:209-210` conserves an ellipse whose shape depends on that
step, so every change perturbs the excursion — planned 1.000–5.921 ms,
achieved 0.942–6.059 ms at the 20 Hz cap — and there is no option to read or
set the oscillator's phase, so Python must integrate open-loop in float64
against C's float32 and the two drift. A shape *table*, which is what A1 asks
for, has neither problem: the trajectory is data, the phase is the node's own
index, and nothing about it changes when Python speaks.

*Scripts:* written and run in this session's scratchpad. Station A folds them
into `audiocomponents/tools/` with B's — the delay tracker, the ideal-line
reference and the error metric are three of the measurement kit's own items.

<!-- author: phaser-flanger unit, effects Phase 0, 2026-09-06. S2-S9 and S11
reached this run; S10 partial (index text only, page 403); the original
schematic not reached by four routes, which is why the grade is literature.
Every measurement in Appendix B was taken this run on the CPython build of
audioif.
Trait-critic pass, same day: Tier 2 rewritten in place (7 rows -> 8), Appendix E
added, SS8 items 6 and 7 added. Palette-verifier pass, same day: every node claim
in SS4 and SS5 checked against the C and probed; SS7.4's Echo mix claim struck as
wrong, the Echo buffer-size delay floor found and added to SS5(b), B.3's
uncontrolled comparison replaced by a controlled one, the warped-oscillator
counter-case built and failed, Appendix G added. Sources re-reached in that pass and not taken
from the draft: the DAFx-05 (S4) and DAFx-18 (S3) PDFs, both fetched and read
again; every other row's citation is left exactly as the audits recorded it. -->

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

*Tail note:* `tail_samples` is not zero — the regeneration loop rings. At
Color c and delay τ the −60 dB tail is τ·60/(−20·log₁₀ c) samples; the class
reports it live from the Color macro, and the burst-then-silence probe checks
it. *Rate note:* F2 and F3 hold at 22.05 kHz; F7 does not — the BBD's
sample-and-hold roll-off is measured at 10 kHz, above Nyquist there, so the
trait is stated at 48 kHz and 44.1 kHz only.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | License call | URL | Reached |
|---|---|---|---|
| S2. Raffel & Smith, DAFx-10, "Practical Modeling of Bucket-Brigade Device Circuits" | No licence statement in the PDF — unverified, **read as a paper** (vision §5) | https://www.dafx.de/paper-archive/2010/DAFx10/RaffelSmith_DAFx10_P42.pdf | yes (PDF, pypdf) |
| S3. Holters & Parker, DAFx-18, "A Combined Model for a Bucket Brigade Device and its Input and Output Filters" | No licence statement in the PDF — unverified, read as a paper | https://www.hsu-hh.de/ant/wp-content/uploads/sites/699/2018/09/Holters-Parker-2018-A-Combined-Model-for-a-Bucket-Brigade-Device-and-its-Input-and-Output-Filters.pdf | yes (PDF, pypdf) |
| S4. Huovilainen, DAFx-05, "Enhanced Digital Models for Analog Modulation Effects" | No licence statement in the PDF — unverified, read as a paper | https://www.dafx.de/paper-archive/2005/P_155.pdf | yes (PDF, pypdf) |
| S5. PCB Guitar Mania, "Electric Lover Flanger" build doc v1.1 — an Electric Mistress-derived clone | **Corrected by the audit.** Its "Licensing and Usage" section is not a bare support note: p.12 grants *"These boards may be used for commercial endeavors in any quantity unless expressly noted. No attribution is necessary"*, restricted only by *"you cannot resell the PCB as part of a kit without prior arrangement with us"* and by not removing their logos. The grant is over **the boards**, not over this document or its drawings, so the document itself is **licence unverified — treated as copyleft**: read as a document, nothing reproduced. The BOM text extracted; **the schematic page is a vector drawing with no text layer and was not read** | https://pcbguitarmania.com/wp-content/uploads/2018/05/Electric-Lover-Flanger-1.1v-Building-Docs.pdf | yes (partly) |
| S6. MixWave, "EHX Electric Mistress User Guide" — **a plug-in vendor's manual, not EHX's** | **Corrected by the audit:** the page does carry a licence line, *"© 2025 MixWave LLC. All Rights Reserved."* — all rights reserved, control descriptions quoted as facts about the emulation. Superseded as the control authority by S13, which is EHX's own | https://support.mixwave.com/help/ehx-electric-mistress-user-guide | yes |
| S7. Effects Freak, "Electric Mistress v2 (1976-1977)" | **Corrected by the audit:** not "no licence seen" — the page states *"© 2026 Effects Freak. All trademarks, photos, graphics, and some content is the property of the respective owner and is posted for reference and research for personal use only."* Personal-use-only, read only. **Second audit:** the page also says its content was "gleaned from various sources on the Internet as well as eBay listings" and its opening paragraph was "edited from Gilmourish.com" — a compilation, not a primary source; what the seed takes from it (three knobs plus the Filter Matrix switch on the 1976 unit, the SAD1024, the version dates) is corroborated by S13, S8 and S11 | https://effectsfreak.com/effect/electric-mistress-v2-1976-1977-w-original-packaging/ | yes |
| S8. Audiority, "Electric Matter" product page | **Corrected by the audit:** carries *"© 2010-2024 Audiority Srl"*; no grant of any kind — read only | https://www.audiority.com/shop/electric-matter/ | yes |
| S9. GroupDIY, "Fixing an electric mistress, help needed" | Forum posts; no copyright line on the thread, and the site-wide "Terms and rules" the footer links (`groupdiy.com/tos`) returns **HTTP 403** to a direct fetch (re-tested twice in the second audit) — **licence unverified**, attributed to the named posters, read only | https://groupdiy.com/threads/fixing-an-electric-mistress-help-needed.21271/ | yes |
| S10. DatasheetCafe's HTML page for the EG&G Reticon SAD-1024 — **an aggregator's description page, not the Reticon datasheet PDF** | **Corrected by the audit:** the host returns **HTTP 200**, not 403, and the sentence quoted in §1 was read on the page, not taken from a search index. Aggregator page, no grant — read only | https://www.datasheetcafe.com/sad1024-pdf-datasheet-14598/ | **yes** (audit; HTTP 200) |
| S11. JonDent, "Electro harmonix Deluxe Electric Mistress - Version 2" | No licence statement found on the page — **licence unverified**, read only | https://djjondent.blogspot.com/2017/10/electro-harmonix-deluxe-electric.html | yes |
| S12. Ralf Metzger, "How the Mistress works" + its BBD and measurement pages *(audit)* | *"© www.metzgerralf.de 2003-2015"*, no grant — **licence unverified, treated as copyleft**; read as a document, nothing reproduced | http://metzgerralf.de/elekt/stomp/mistress/how.shtml (also `bbd.shtml`, `measure.shtml`) | yes — **plain HTTP only**; the https URL fails on a certificate name mismatch, which is what earlier runs recorded, and `WebFetch` cannot reach it because it upgrades to https |
| S13. Electro-Harmonix, "Deluxe Electric Mistress Flanger/Filter Matrix" owner's manual — **the maker's own** *(audit)* | Manufacturer product documentation, no licence line — control descriptions quoted as facts. **Second audit, scope narrowed:** this is the manual for the **current compact reissue** — it carries an FCC Part 15 notice and a True Bypass footswitch, is powered from 9 V DC, and tells the buyer the unit "is quite a bit smaller than every other Deluxe Electric Mistress ever made by Electro-Harmonix" while claiming "The circuit remains true to its roots". So it is EHX's own words about the reissued **Deluxe**, two revisions from the 1976 referent, and S8 says the Deluxe's LFO and VCO differ from the classic's. Every control function the seed takes from it is carried back to the original by S7 (the same three knobs and the switch on the 1976 unit) and S9 (the original's factory alignment) | https://www.ehx.com/wp-content/uploads/2021/01/deluxe-electric-mistress-manual.pdf | yes (HTTP 200, PDF, pypdf) |
| S14. Fractal Audio Systems Forum, "MOAEE - Electric Mistress Flanger", p.5 *(audit)* | Forum posts, no licence — attributed, read only. Recorded **only** to correct the not-reached list; no trait rests on it. **Second audit:** both halves check out — the claim is post #82 quoting DLC86, and the reply from a moderator who says he measured a Deluxe by clicks is "Good catch on the negative feedback" | https://forum.fractalaudio.com/threads/moaee-electric-mistress-flanger.76166/page-5 | yes (HTTP 200) |
| S15. Tonepad (Francisco Peña), "Electric Mistress Flanger, Rev.2.Nov.1.2005" — **a schematic with component values**, redrawn from a schematic credited to Stephen Giles (S9's own poster) *(second audit)* | The licence is printed on the drawing: *"Layout and presentation by Francisco Peña 2001-2005®. All rights reserved. Authorization for personal use only, any commercial use is forbidden. Permission for posting/serving limited to http://www.tonepad.com. Permission refused for posting from other sites."* — **all rights reserved, personal use only**: read as a document (vision §5), nothing reproduced, nothing republished, no value taken into §1 or §3. What it is: tonepad's project page calls it the **9 v (non-deluxe)** Electric Mistress with "the LFO of the Deluxe (including it's controls) and the signal path of the ORIGINAL", `Status UNVERIFIED`, "Schematic only" | http://www.tonepad.com/project.asp?id=54 → `getFileInfo.asp?id=102` → `getFile.asp?id=102` | **yes** (HTTP 200, `application/pdf`, 89 372 bytes, 1 page, text layer readable). The download is session-gated, which is what defeated the first audit: `getFile.asp` alone 302s to `downloadWarning.asp` ("Please visit the relevant project(s) page before downloading"). Fetch the project page and the file-info page first **with a shared cookie jar** (`curl -c jar -b jar`) and the third request returns the PDF |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| F1 | **The delay is the reciprocal of the clock, so a linear ramp in the clock is a hyperbola in delay.** With the class's own ramp LFO (`Shape` 0.5, `Filter Matrix` off), over one monotone half-cycle with the turnarounds excluded: an affine fit to **1/t_d(t)** leaves an RMS residual under **2 % of its span**, while an affine fit to **t_d(t)** leaves at least **5 %**. An exact 4:1 hyperbola gives 8.8 % RMS for the second fit and a delay that is a triangle in milliseconds gives 0 % and fails (E1) | S2 §2.1 (t_d = N/(2·f_cp), stated generally; its worked case is a generic 1024-stage BBD flanger, not this pedal); S4 §5.1, re-read this run: *"if the clock rate is varied linearly, the delay time will be roughly proportional to 1/x"*. **Audit corrections kept:** "S10 (1024 stages in series)" is struck (S10 lists the series cascade as one of four configurations and says nothing about this pedal; S12 says the Mistress runs its two 512-stage sections *in parallel*), and the *triangle* is not sourced either — no reached source states this pedal's LFO shape. The trait rests on the reciprocal law, which is what the two fits test | high for the reciprocal law — two papers state it, the third models it; **N itself is unsettled** (§1) and no number here rests on it | an affine fit to 1/t_d with RMS residual over 2 % of span, or an affine fit to t_d under 5 % | delay tracking: t_d from the **k-th** comb notch, t_d = (2k+1)/(2·f_k), k chosen so f_k ≥ 500 Hz — at 12 ms the first notch is 41.7 Hz, which an STFT frame short enough to track a sweep cannot resolve; per frame over one LFO period; both fits with RMS and max residuals. **Control that must pass:** the same fits on a held delay must give a flat t_d(t) within the tracker's own scatter |
| F2 | **Equal-weight comb: notches at (2k+1)/(2·t_d), spacing 1/t_d, the first a null.** At `Color` 0, the sweep stopped (`Filter Matrix` on), `Mix` at the position the class documents as equal weight: every notch below 8 kHz matches the grid to **0.5 %**, and the deepest is at least **30 dB** below the mean of the same transfer over 100 Hz–8 kHz, read at **2.93 Hz** resolution (16384-point Hann, ≥ 2¹⁶ samples, as B.1) | S4 §1 and §5, both re-read this run: *"the flanger produces infinitely many notches that are spaced at constant intervals"*. **The equal-weight sum is this seed's construction choice, not a sourced circuit fact** (§1): no reached source gives the Mistress's dry/wet ratio, and equal weight is what makes the notches nulls. On the node, dry sits at unity for any `mix` ≤ 1, equal weight is `mix = 1.0` and `mix = 2.0` is wet alone (`audioif_feedback_delay.c:201-202`, read this run) — §4 and §6 must say which class `Mix` position is which, because this null depends on it (§8.6) | high | a grid that is not odd-harmonic; or a floor shallower than 30 dB at `Color` 0 at the stated resolution | notch tracking on a white-noise transfer at three held delays (1, 3, 6 ms): frequencies against the grid, and the depth of the deepest. **Control that must pass:** `Mix` 0 must read 0.0 dB everywhere, so a silent render cannot satisfy the 30 dB |
| F3 | **Color is regeneration — peaks, not depth.** At 3 ms held, the comb's peak gain rises **monotonically** across `Color` 0 / 0.3 / 0.6 / 0.9 and by at least **15 dB** end to end, while the notch floor *fills* by at least **10 dB** over the same span | S6 ("Higher settings emphasize the comb-filter peaks"); S9 (the trim "sets a maximum … if adjusted too high the feedback will run away"); direction confirmed on the node (B.2: peak +6.3 → +23.7 dB, floor −32.4 → −6.7 dB). Unlike the Phaser's P8, **no reached source contradicts the filling here** | high for peaks-not-depth; both thresholds are this seed's and B.2 clears each by about 2× | peaks flat or non-monotonic with `Color`; or a floor that deepens as `Color` rises | comb peak gain and notch floor (dB re the wideband mean, 2.93 Hz resolution) at `Color` 0 / 0.3 / 0.6 / 0.9, sweep stopped, 3 ms |
| F4 | **Filter Matrix stops the sweep and nothing else.** With the mode on: the first notch moves under **5 cents in 10 s**; its position at `Rate` 0.02 Hz and at `Rate` 8 Hz agrees within **5 cents**; `Manual` moves it monotonically across §6's whole 0.4–12 ms span; and `Color` still passes F3's test (≥ 15 dB, monotone) with the mode on | **S13, EHX's own manual — for the reissued Deluxe (§2):** *"the modulation waveform is disconnected from the flanger circuit, freezing the flanger … Turn the RANGE knob to change the filters' position and use COLOR to adjust the depth of filtering. The RATE knob has no affect when set to FILTER MATRIX mode"*; S6 says the same of the emulation; **S7 puts the same switch on the 1976 unit**, which is what carries the behaviour back to the referent | high for the behaviour — EHX's own description is unambiguous and S7 puts the switch on the referent | drift over 5 cents in 10 s; a notch position differing by more than 5 cents between the two `Rate` settings; a non-monotonic `Manual` sweep; or a `Color` peak rise under 15 dB with the mode on | notch tracking over 10 s with the mode on, at three `Manual` positions and two `Rate` settings, plus F3's `Color` run repeated with the mode on |
| F5 | **The sweep spans at least 4:1 in delay, topping out near 10 ms.** At `Range` max, `Filter Matrix` off, over one full LFO period: the longest t_d is **8–12 ms** and max(t_d)/min(t_d) is **≥ 4** — two octaves of notch spacing | S2 (*"a flanger effect typically requires a maximum of a 10 ms delay … 1024-stage delay line, giving a clock frequency of … 51.2 kHz"* — its **generic** BBD-flanger case, not a measurement of this pedal); S6 (Range sets depth *and* the lower limit). **Audit correction kept:** the shortest delay is no longer unsourced for the *chip* — S12's BBD table lists the SAD1024 at 0.34 ms minimum, 340 ms maximum; the *pedal's* shortest swept delay is still unsourced (§8.3) | medium — the maximum is sourced but generically; the 4:1 is this seed's floor | a longest delay outside 8–12 ms at `Range` max, or a ratio under 4 | delay tracking as F1 (k-th notch, so 12 ms stays resolvable) over one period at `Range` max: minimum, maximum and ratio |
| F8 | **The `Color` ceiling rings and does not run away.** At `Color` max and 3 ms held: after a burst the −60 dB tail is **≥ 2 s**, and the envelope over the following 10 s of silence is **monotonically non-increasing** | **A design requirement, not a circuit trait, split out of F3 by the trait critic so it cannot be counted as one.** At the panel's ceiling the pedal does the opposite: S13 (EHX, of the current reissued Deluxe) *"Turning COLOR to its most clockwise setting could cause self-oscillation to occur. This is normal!"*, and S6 says the same of its emulation. What this row follows is the **original's** factory alignment, S9 — set the trimmer *"until the unit just oscillates. Then back off from this point until oscillation just ceases"* — so the class's macro ceiling is the trimmed unit's ceiling and the runaway lives above it | n/a — a design decision, recorded with a measurement so it is checkable, not so it counts toward the trait bar | a tail under 2 s, or an envelope that rises at any point in the 10 s | burst-then-silence at `Color` max, 3 ms: −60 dB decay time and the 10 s envelope. **Control that must pass:** the same probe at `Color` 0 must decay to exact zero within `tail_samples` (Tier 1) |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Looked for and not reached.** No schematic of the **1976 two-battery
original** was read by any of the three passes. Still unreached, each
re-tested in the second audit: `diystompboxes.com` (HTTP 403, third time — the
"schematic comparison" and "how the SAD1024 is used" threads);
`community.element14.com` (a connection failure this time, `HTTP/2 stream …
INTERNAL_ERROR`, after a 403 and a timeout before that). **`ronsound.com` was
read this time and its listing is exactly as claimed:** "Electric Mistress
flanger package schematic … the schematics for the 3 versions of the Electric
Mistress: (2) 18v models and (1) 9v model, alignment instructions, and power…
**$15.00**", with a separate "Deluxe Electric Mistress schematic, Dated:
11/78, Includes alignment instructions, 2 pgs, **$8.00**" — a purchase, not a
fetch, and now a priced one. **Tonepad's PDF is no longer unreached**: it is
S15, and the session-cookie recipe that opens it is in that row. One route
this workspace had written off is also open: `web.archive.org` is blocked for
the *fetch tool* but answers `curl`, so the 403'd threads and any archived
schematic page can be tried through it.

*(from §2)*

**Corrected by the audit — four sources recorded as unreachable were
reached.** (a) `metzgerralf.de/…/how.shtml` — the https URL does fail on a
certificate name mismatch, but the site serves the page over **plain HTTP**;
it was read, and is now S12. (b) `forum.fractalaudio.com` — reachable (HTTP
200); it is now S14. (c) `ehx.com`'s own Deluxe manual PDF — reachable (HTTP
200); it is now S13, and it is a better authority on the controls than S6.
(d) `stompboxschematics.com`'s Tonepad page — reachable (HTTP 200), but what
it hosts is a **PCB photograph** (`markus_mistress.jpg`, 741×464: a Reticon
SAD1024, an LM324N, a 4558, and pots reading 1M / 100K / 10K), not a
schematic, so it does not move the grade.

*(from §2)*

**Unsourced and kept out of the trait table:** every component value in the
original. **No longer unsourced, though no trait was added for either** — S12
gives a measured LFO rate ("1977 Electric Mistress V2 LFO at slowest sweep.
The frequency is 0.067 Hz or 4 sweep cycles per minute") and a minimum delay
for the chip (its BBD comparison table lists the SAD1024 at 0.34 ms minimum,
340 ms maximum); the earlier text calling both unsourced was wrong and Phase 3
should start from S12 on each.

*(from §2)*

**The polarity of the regeneration path** stays out of the trait table, but
for a better reason than before: the claim *is* reachable — S14 carries it
("the electric mistress from what I see has an inverted phase feedback path,
so negative feedback values should be used on the axe fx", with a second
poster agreeing) — and it is a forum member's **reading of a schematic he does
not show** ("I took a look at the schematic of this pedal and at how mine
works"), not a drawing we reached and not a polarity measurement, which
§8.2's own rule excludes. The earlier
statement that "every page carrying that claim was one of the 403s" was
false. The vision's "the Electric Mistress's *inverted feedback*" (§6) is
**still not confirmed**, and no trait and no node ask rests on it.

*(from §2)*

**Audit corrections (2026-09-06), beyond the source rows above.** (1) Five
licence calls were wrong: S5 (a grant exists, over the boards), S6, S7 and S8
(each carries a copyright line the seed said was absent), S10 (reachable, and
the sentence is on the page). (2) The four not-reached claims corrected above.
(3) §1's **N = 1024** is an inference and is contradicted by the one source
that reads this circuit — flagged in §1 and in F1's source column, and F7's
two dB figures, which are the only numbers in §3 that move with N, are marked
provisional. (3a) F5's "the shortest delay is unsourced" was true of the pedal
but not of the chip — S12 gives 0.34 ms. (4) §1's
"an LM311 pair" was not in S5's BOM — corrected. (5) F3's "does **not**
self-oscillate" is contradicted by S6 and by EHX's own manual S13 — flagged in
the row as a design choice, not a circuit trait. (6) F4's source and
confidence now cite S13 rather than resting on a plug-in vendor's paraphrase.
No licence call was found to be too permissive.

*(from §2)*

**Second audit pass (2026-09-06) — licence and citation, independent.** All
thirteen rows above were re-fetched and every quotation in §1, §2 and §3 was
re-read against its source. Seven changes. (1) **A schematic with values was
reached** — S15, tonepad's redraw of the 9 V unit, session-gated behind a
cookie the first audit did not carry; the grade line now says what it is and
what it is not, and no trait was moved. (2) **S13 is the reissue's manual**,
not the referent's, and the rows that lean on it say so. (3) §1's "triangle
LFO" and its "summed … at equal weight" were circuit facts with no source
row; both are now labelled as this seed's construction, and F1 and F2 carry
the same note. (4) One citation pointer was wrong: S2's "preceded and
followed by low-pass filters" is §1.3 (Non-ideal BBD Characteristics), not
§1.2. F2's "S4 §1, §5" was checked and **stands** — §1 carries "A flanger
mixes a slightly delayed signal with the original, acting as a comb filter"
and §5 the "infinitely many notches" sentence. (5) S12's sentence is
quoted verbatim now — the source's own spelling is "in parallal" and "will
imporve performance", and a silently tidied quotation is not a quotation.
(6) `groupdiy.com/tos` was fetched this time and returns 403, so S9's licence
stays unverified for a checked reason; the Central-Semi-style question does
not arise elsewhere. (7) `ronsound.com`'s $15 package was read and is exactly
as described. Everything else held: S2's delay law, its 10 ms/1024-stage
flanger case, its Sallen-Key corners and its compander sentence are all in the
paper (whose text layer is mis-encoded — the letters extract correctly, the
digits do not, so the arithmetic was read from the maths font and checked:
1024/(2·0.010) = 51.2 kHz); S3 names "the Electric Mistress flanger effect
from Electro-Harmonix" in §1 and its rectangular-pulse sentence is §2 as
cited; S4's four quoted sentences are all present; S5's controls, trimmers and
IC list are exactly as tabulated and its p.12 grant is verbatim (its clone is
an MN3007/MN3207 9 V adaptation with a buffered clock, an FX loop and an
output gain stage, so its BOM is a clone's, which §1 already says); S6's,
S7's, S8's and S11's copyright lines are as quoted; S10's SAD1024 description
is on the page word for word; S12's three pages carry the © line, the
0.34 ms/340 ms table row and the 0.067 Hz LFO measurement; S14's two posts are
as quoted. No licence call was found to be too permissive, and no quotation
was found to be wrong beyond item (5). Every local line number in this seed
was re-run under `grep -n` and every one is exact:
`audioif_feedback_delay.c:82-83`, `:90`, `:118`, `:120-122`, `:201-202`,
`:205-262`, `:209-213`, `:226-228`, `:260-261`; `audioif_echo.c:20`, `:22-28`,
`:30`, `:36-37`; `audioecho/FeedbackDelay.c:20-29`.

*(from §3)*

**Trait-critic pass (2026-09-06).** Seven rows in, eight out; **seven are
circuit traits** (F1–F7) and F8 is labelled a design requirement so it cannot be
counted as one. Every row now names the macro settings it is read at and, where
it reads a spectrum, the resolution — without which F2's "30 dB below" is a
statement about an FFT rather than about a comb. F1, F2, F6 and F8 gained a
**control that must pass**, so a silent or frozen render cannot satisfy them
(workspace-craft: a suite of only failures proves a checker always fails). Two
rows were repaired rather than tightened. **F6's bound was one a correct build
fails**: "the output's maximum sample-to-sample step never exceeds the input's"
is already violated in the seed's own B.3 by the node's per-sample sine, because
a comb sums two copies of one signal (E3); the before/after window is the same
no-discontinuity claim with a control under it. **F7's measurement was not
reachable as written** — it asked for a wet-only path the class's `Mix` macro
does not expose — and is now pinned to the node's `mix = 2.0`, verified this
run, with an open question against §6. **F3 was split:** its "does not
self-oscillate" clause carried, in the seed's own words, "no confidence at all",
and it contradicts EHX's own description of the reissue; it is now F8, a
labelled design requirement. Nothing was deleted, and no source is cited here
that this run did not reach.

*(from §3)*

Budget as a fraction of one stereo 256-frame block's deadline (5.333 ms at
48 kHz): **ESP32-P4 0.03, ESP32-S3 0.08** — one `audioecho.FeedbackDelay`:
per frame per lane a shape-table lookup, a linear interpolation, **two**
in-loop one-poles (`damping_hz` `:231-235` and `cut_hz` `:236-240`, both of
which this class uses), the optional soft-clip (`:241-243`) and the feedback
multiply-add (`audioif_feedback_delay.c:205-262`), about a fifth of `Rotary`'s
chain and below `Phaser`'s four all-pass stages. *(Corrected from "one in-loop
one-pole" by the palette verifier, 2026-09-06.)*
RAM: a 12 ms stereo line is 576 frames × 2 × 2 bytes ≈ **2.3 KB**, plus a
1024-entry int16 shape table (2 KB) computed on CPython and shipped as data,
never rebuilt on a board. Lean patch expected: **no**.

*(from §3)*

**Latency: 0 samples, 0 ms at 48 kHz.** The dry path is untouched — the comb's
delay is the effect, on the wet path only (`audioif_feedback_delay.c:260-261`
sums the channel's own dry sample). **One option adds latency and it defaults
off:** a `Through Zero` mode delays the *dry* path by the sweep's maximum so
the two paths can cross — up to **12 ms, 576 samples at 48 kHz**; with it on,
`latency_samples` reports the delay actually applied and the docstring names
it in ms at 48 kHz. Nothing else — not Color, not Range, not Filter Matrix.
Reported `latency_samples = 0` with the mode off is verified by the click
measurement at the class gate.

*(from §4)*

Python's job per macro move: turn `Range` and `Manual` into a clock range,
turn the LFO's triangle into the **delay** by the reciprocal law of F1, and
bake one period of that into a table the node reads. `damping_hz` carries F7
(set from the current clock, so it moves with the delay); `cut_hz` keeps the
loop DC-free; `feedback` is `Color`, clamped by the class below the node's
0.99 (`:90`) at the macro ceiling F3 names.

*(from §4)*

**What the node cannot do.** Its only modulation is a **sine** added to the
delay (`:209-213`); `delay_ms` is not a stream input — the options arrive as
plain floats (`FeedbackDelay.c:20-29`, coerced at `:43`; the CPython build
does the same at `audioif/src/cpython/audioecho.py:87`) — so any other shape must be stepped from
Python once per block. B.3 measured that at **−28.1 dB** spurious against the
node's own sine at −63.3 dB, but those two rows are **different trajectories**
(a triangle in ms against a sine), so part of that 35 dB is the trajectory and
not the control rate. The palette verifier re-ran it controlled (G.3): against
an ideal per-sample interpolating line following the *same* trajectory,
block-rate control costs **−23.3 dB** re the carrier where the node's own
per-sample oscillator costs **−66.3 dB**. **43 dB**, on one trajectory, is the
number this ask rests on. Per-block stepping also jumps the delay by up to
**7.3 frames** at once (G.3) where the per-sample paths move it by 0.03; that
is a click per block, and it fails F1 (wrong shape), F6 (a discontinuity) and
Tier 1 level-honesty in one stroke. Hence §5.

*(from §4)*

**Mono and stereo.** A flanger is mono by nature: a mono source gets the full
comb, a stereo source gets the same comb on both channels. `cross_feed`
(`:120-122`) offers a stereo regeneration spread; it is a macro, defaulting
to 0, and the dossier's traits are all stated at `cross_feed = 0`.

*(from §5)*

*Palette instead, and why it fails, measured.* (a) **Stepping `delay_ms` from
Python** once per block: −23.3 dB of error against an ideal per-sample line on
the same trajectory, where the node's own oscillator costs −66.3 dB (G.3;
B.3's uncontrolled −28.1 / −63.3 pair is superseded as the *comparison*, not
as a reading). (b) **`audiodelays.Echo`** does take a `synthio.LFO` on
`delay_ms` (`Echo.c:67`, re-read per block at `:248`), so an arbitrary
interpolated waveform *can* reach it — but its line is read at a
**whole-sample index** (`audioif_echo.c:20`, `:30`; the `freq_shift` path
writes at a variable rate and still reads whole samples, `:22-28`), and worse:
off the `freq_shift` path **`Echo` floors the delay at `buffer_size` bytes per
channel** (`Echo.c:122-131`, the floor at `:126-128`). At the library's own
`_core.pcm()` buffer of 2048 bytes (`_core.py:64`) that floor is 1024 frames =
**21.3 ms at 48 kHz**, and 1.0, 6.0, 12.0 and 21.33 ms render **byte-identically**
(G.2) — the whole 0.4–12 ms flanger span collapses onto one delay. On the
`freq_shift` path the floor is bypassed (`Echo.c:116-120`) and the delay does
move (G.2), but the read is a resampler on whole samples, not an interpolated
tap. (c) **`synthio.LFO`'s arbitrary waveform cannot reach `FeedbackDelay`**
at all: its options are plain floats (`FeedbackDelay.c:20-29`, `:43`), not
block slots. (d) **A sine on the delay is not the BBD law** and fails F1 by
construction, whatever its resolution.

*(from §5)*

*Refutation record (Phase 0).* Three counter-cases, all failed.
(i) "Sweep the sine slowly enough and nobody hears the difference between a
sine and a hyperbola" — fails on F1 as stated, which is a *shape* measured by
fitting 1/t_d(t), not an audibility claim, and does not touch F6, a step
response. (ii) "Use `Echo` for the shape and accept the integer taps" —
rejected on F2 (whole-sample reads quantise the comb) and, more bluntly, on
F5: the buffer-size floor in (b) makes the span itself unreachable.
(iii) **"Warp the node's own oscillator instead of stepping the delay"**
*(new, palette verifier 2026-09-06)* — the strongest counter-case, and the one
worth recording in full because it nearly works. `wow_hz` may be changed from
Python at block rate while `wow_depth_ms` stays fixed; the delay then never
jumps, because only the oscillator's *rate* steps, and by warping the phase a
class can trace an arbitrary monotone trajectory through the sine's own arc.
Built and run (G.4): with a per-block `wow_hz` schedule planned against a
mirror of the node's magic-circle recurrence, the achieved trajectory
**passes F1** — an affine fit to 1/t_d leaves 0.01 % RMS residual and one to
t_d leaves 8.6 %, against F1's 2 % and 5 % bars. It fails on the artefact it
was proposed to avoid: **−23.7 dB** of error against the ideal per-sample line
on that same trajectory, no better than stepping `delay_ms` (−20.0 dB) and
42 dB worse than the node's own oscillator. The cause is structural, not a
tuning failure — the magic-circle oscillator's amplitude invariant depends on
its step (`audioif_feedback_delay.c:113-114`, `:209-210`), so every `wow_hz`
change perturbs the excursion (planned 1.000–5.921 ms, achieved
0.942–6.059 ms), and the phase cannot be read or reset from Python. The ask
therefore stands, and it stands on the *artefact*, not on the shape.

*(from §7)*

2. **A node with no interpolation.** `audiodelays.Echo` (`:55`) reads its line
   at a whole-sample index (`audioif_echo.c:30`); the `freq_shift=True` path
   (`:57`) writes at a variable rate but still reads whole samples
   (`audioif_echo.c:20-28`). A swept comb built on it steps.

*(from §7)*

3. **The wrong modulation shape.** `synthio.LFO(rate, scale=depth_ms,
   offset=depth_ms+1.0)` (`:53-54`) is a symmetric triangle **in
   milliseconds** — the default LFO waveform is the 4-point triangle at
   `synthio/LFO.c:139`, interpolated — where a BBD's delay is the reciprocal
   of a clock (F1). Shape and law both wrong, and block-rate besides.

*(from §7)*

4. **The delay knob does not mean milliseconds on this node.** *(Rewritten by
   the palette verifier, 2026-09-06: the draft's "the comb is 6 dB shallow
   by default, `mix=0.5` gives a −6.0 dB notch" is **wrong** and is struck.
   `audiodelays.Echo`'s Python-facing `mix` is clamped to 0–1 and **doubled**
   before it reaches the kernel — `Echo.c:245`, `mix = clamp(mix,0,1) * 2.0` —
   so `mix=0.5` is the internal 1.0 that `audioif_echo.c:36-37` sums at equal
   weight, a true null: measured −27.8 dB with a held delay, and `mix=1.0`
   would be **wet alone**, flat |H|, rms out/in 0.9988 — G.2.)* The real
   defect at `:55-57` is the node: on `Echo`'s plain path the delay is floored
   at `buffer_size` bytes per channel (`Echo.c:126-128`), which at
   `_core.pcm()`'s 2048 (`_core.py:64`) is 21.3 ms — 1.0 through 21.33 ms all
   render byte-identically (G.2) — and the class only escapes that by asking
   for `freq_shift=True` (`:57`), which trades the floor for a whole-sample
   resampling read (`audioif_echo.c:20-28`). Either way the millisecond
   numbers at `:53-54` are not the delay the listener gets.

*(from §7)*

6. **Nothing declared** — no `CAPABILITIES`, `LATENCY_SAMPLES` or
   `TAIL_SAMPLES`, so `latency_samples` is 0 by accident (`_core.py:245-248`)
   and `tail_samples` is unset while a 0.6-feedback loop (`:51`) rings for
   seconds. The transport is never read.
