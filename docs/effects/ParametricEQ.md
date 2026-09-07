# Effects Dossier — `ParametricEQ` (Pultec EQP-1A shelves, API 550 proportional-Q bells)

**Class:** `lib/audioeffects/rebuilt/parametriceq.py`. The old
`lib/audioeffects/eq.py:ParametricEQ` is left untouched beneath, read once for §7.
**Family / phase:** EQ, roadmap Phase 2
**Standout:** EQP-1A for the shelves and the HF bandwidth control, API 550A's
proportional-Q for the bells — vision §4.2, **confirmed**, control laws only.
No new filter math; RBJ biquads carry all of it.
**Grade:** **literature.** The factory schematics are not public (S1). Reached:
a white-box model validated against LTspice, a lab measurement of the 2019
reissue (S1, S2), a JAES paper defining the Q laws (S3), two panel sources
(S6, S7) and two hobbyist redraws with values (S8, S9) — but no SPICE model
and no drawing attributed to the factory, so **literature** stands (vision
§4.1). The path to a circuit grade is a netlist from the parts S8 and S9
agree on, simulated the way `tools/spice/ts808/` already does.
**Portability tier:** **audioif** — `REQUIRES = ("audiobiquad",)`, eight
sections, nothing else (§5, §8 Q1).
**Status:** Station A closed; **trait table frozen 2026-09-07** on
`effects/p2-parametriceq`, before a line of the rebuild was written.

**The frozen facts, in one screen.** Tier **audioif**, `REQUIRES =
("audiobiquad",)`. **Sixteen macros** (§6), **seven patches** 0–6 with patch 0
a wire. **`capabilities = ()`**. **`latency_samples` 0** at every setting and
rate, and no option adds latency; `tail_samples` measured, not assumed.
**Tier 3 budget: P4 26 %, S3 43 %** of one stereo block, for the eight sections
this class always builds. Five Tier 2 traits, T1–T5, frozen.

## 1. The circuit, in one paragraph

The EQP-1A is a **passive LC network followed by a make-up amplifier** — 16 dB
of insertion loss restored by a 12AX7/12AU7 stage, so flat is unity — carrying
**four independent filters, not two** (S1 §1.3): a *low boost* shelf on a
selectable corner (20/30/60/100 Hz) up to 16 dB; a *low cut* shelf up to 20 dB
sharing that selector but **not** the same corner behaviour; a *high boost*
that is a **resonant RLC section — a bell, not a shelf** — on its own selector
(3/4/5/8/10/12/16 kHz) with a **bandwidth** control setting its Q; and a *high
cut* shelf on a third selector (5/10/20 kHz) up to 20 dB. Two consequences make
the sound. Low boost and low cut are separate networks whose curves "affect
slightly different frequency bands" (S1 §1.3) — S9's drawing shows one ganged
selector switching two different capacitor banks (C12–C17 cut, C18–C23 boost) —
so running both does not cancel: SOS's measurement of the reissue reads *"a
gentle +3dB bass shelf combined with a mid-band cut of −2dB"* with both at 2.5
(S2). And bandwidth is not a constant-gain Q knob: at full boost *"the maximum
gain is 9dB greater when the bandwidth is set to narrow"* (S2). The **bells**
are the other standout: an API 550A is three switched bands with *Proportional
Q* — the skirt stays put and the curve narrows as boost rises (S5) — and Bohn
gives the topology that law falls out of, boost `1 + k·BP` against cut
`1/(1 + k·BP)`, so **cut is the exact reciprocal of boost** (S3 §3.1).

*(S5's own figures, the selector lists' disagreements and the maximum-gain
dispute are in **App. R**.)*

## 2. Sources and license calls

All reached 2026-09-06; nothing from memory. What each gave, its licence text
and its chain-of-quotation caveat: **App. S**. Not reached: **App. D**.
Excerpts: **App. E**.

| Source | Licence | URL | Reached |
|---|---|---|---|
| **S1** Barrera et al., *Modeling the Pultec EQP-1A with WDF*, SMC 2024 | **CC BY 3.0** | https://smcnetwork.org/smc2024/papers/SMC2024_paper_id132.pdf | via `pypdf` |
| **S2** Robjohns, *Pulse Techniques EQP-1A*, SOS, Feb 2019 | © SOS, ARR | https://www.soundonsound.com/reviews/pulse-techniques-eqp-1a | read |
| **S3** Bohn, *Constant-Q Graphic Equalizers*, JAES 34(9), 1986 | unverified, treated copyleft | https://www.ranecommercial.com/legacy/pdf/constanq.pdf | via `pypdf` |
| **S4** Bohn, RaneNote 101/117 | © 2005 Rane, ARR | https://www.ranecommercial.com/legacy/note101.html | read |
| **S5** Sutton, *API 550 Equalizers* | © 2026 M. Sutton | https://ms-tas.com/api-550-equalizers/ | read |
| **S6** ABSounds/EQP-WDF-1A front page | **GPL-3.0** | https://github.com/ABSounds/EQP-WDF-1A | read |
| **S7** Ultimate Preset, *Pultec Equalizer Guide* | © 2026, ARR | https://www.ultimatepreset.com/pultec-equalizer-guide/ | read |
| **S8** Gyraf, *The G-Pultec* + `pultech.gif` | none stated | https://www.gyraf.dk/gy_pd/pultec/pultec.htm | page + drawing read |
| **S9** jbb.ru redraw + `1a-shem-p.gif` | none stated | http://jbb.ru/schematics/1a-shem-p.htm | read over http |

## 3. Traits — fixed before measurement

**Frozen 2026-09-07**, before the rebuild began: five Tier 2 rows, none added,
dropped or reworded since.

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The block and this class's notes on it are **App. I**. The one that matters
here: **silence-to-zero is the invariant this family is known to fail** on the
ported node — §5 records what the rebuild does about it.

### Tier 2 — circuit traits

Full source readings and confidence reasoning per row: **App. T**.

| # | Trait (falsifiable as stated) | Src · conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|
| **T1** | Low boost and low cut are two shelves with **different corners**, so both at once is not cancellation. `Low Freq` 60 Hz, both at ¼ travel ⇒ ≥ +2.0 dB at 30 Hz, a local minimum ≤ −1.0 dB in 100–400 Hz, flat within 0.5 dB above 1 kHz. | S1, S2 · **high** for the mechanism, thresholds **ours** (App. T1) | **any of the three missed** — chiefly a shared corner, which cancels to within 1 dB across 20 Hz–1 kHz and is what the current class builds (App. T1) | swept-sine 20 Hz–2 kHz at 48 and 44.1 kHz; report the level at 30 Hz, the frequency and level of the minimum, and the maximum deviation above 1 kHz |
| **T2** | High boost is a **bell**, high cut a **shelf**, on independent selectors. Boost full at 10 kHz *and* cut full at 5 kHz ⇒ a local maximum within ±⅓ oct of 10 kHz **and** a monotonic fall 3→5 kHz. | S1, S6, S7 · high | **either half missed** — no maximum near 10 kHz (the boost is a shelf), a non-monotonic 3→5 kHz fall (the cut is a bell), or the cut selector moving the boost's peak (App. T2) | swept-sine 1–20 kHz, both engaged; report peak frequency, the 3→5 kHz monotonicity, and the boost peak's frequency at both extremes of the cut selector |
| **T3** | Bandwidth changes **peak gain**, not just width: at full boost, sharp minus broad is **+6…+12 dB** and the −3 dB width at sharp is ≤ half that at broad. | S2 · medium (gain), **low and ours** (width) | **either half missed** — sharp-minus-broad outside **6–12 dB**, chiefly under 3 dB, the shape every constant-gain Q knob has; or the sharp width over **half** the broad one (App. T3) | swept-sine at both bandwidth extremes, boost max; report peak dB and −3 dB octave width at each |
| **T4** | The bells are **proportional-Q**: one bell at 1 kHz at +2/+6/+12 dB has its first +1 dB crossing the same **within 5 %**, while mid-gain bandwidth falls **≥ 3×** across that range. | S5, S3 §2, S4; law App. A · medium | **either half missed** — the crossing moving > 5 %, or the ratio under **3×** (App. A predicts 3.39×, so 3× is a floor with margin; near 1 is constant-Q outright) | swept-sine at three boosts; report the +1 dB crossings and half-gain bandwidth in octaves |
| **T5** | Cut is the **exact reciprocal** of boost: for one bell at 1 kHz at **G = 6, 12 and 16 dB**, the product of the +G and −G responses is unity within **0.1 dB**, 20 Hz–20 kHz, at every one of the three. | S3 §3.1 · high | the product deviating > 0.1 dB anywhere in band at any of the three — chiefly a `Q` law reading **signed** gain rather than its magnitude, which breaks the skirts while the peak still looks right (App. T5) | swept-sine at +G and −G for each of the three; multiply, report max deviation from 0 dB and the frequency it occurs at |

T5 is stated for the **bells only** — the Pultec's low pair is *not* reciprocal,
which is T1, so a rebuild that makes them reciprocal fails T1 while passing T5.
The tension is deliberate. No characters; the table is stated at the defaults
`Q Law` = proportional and `Bandwidth` = 5. *(App. F: the trait-critic pass.)*

### Tier 3 — cost and latency

**Budget**, as a fraction of one stereo block's deadline (256 frames, 5.33 ms at
48 kHz): **P4 26 %, S3 43 %** — App. C's eight-section pair, and eight is what
this class always builds (§4). Lean patch expected: **no**; a patch cannot
change how many nodes exist.

**What that budget does not cover.** App. C counts the **fixed-point** kernel
(76 instructions/sample on Cortex-M4/M7, `audioif/docs/upstream-diff.md:1172`).
This class runs the **float** kernel, for which no count exists on either port,
and its eight sections are eight nodes with eight block pulls where the
arithmetic assumed one `Filter` holding a cascade. The board run measures it;
the pair above is the ceiling, not a prediction.

**Latency: zero samples** at every setting and rate — every section is a
recursive biquad reading no sample it has not been given, and there is no
lookahead, partition or window anywhere in the class, so **there is no
latency-adding option to default off**. `tail_samples` is measured, not
assumed: the float kernel writes any state word under 1e-20 as exact zero
(`AUDIOIF_FILTER_F32_FLUSH`), so the tail is finite and the evidence pack
reports the longest one this class's span reaches.

## 4. Modeling approach on the palette

**One `audiobiquad.Biquad` per section, eight in a chain, Python computing the
coefficients' *arguments* on a macro move.** `mode`, `frequency`, `Q`,
`gain_db` and `mix` are block slots, so a macro retunes a running section
rather than rebuilding it. Citations and probes: **App. G**, **App. R**.

- **`audiobiquad`, not `synthio.Biquad` in an `audiofilters.Filter`.** The
  ported kernel's Q12 memory has fixed points and this class's useful settings
  park on them — a 20 Hz/+10 dB shelf on ±32 LSB, a 31.25 Hz bell on +7 LSB,
  held for three seconds (App. B). The float kernel decays and flushes, so the
  Tier 1 tail invariant is reachable at all.
- **Eight sections, cutting sections first:** Low Atten · High Atten · Bell 1 ·
  Bell 2 · Bell 3 · Low Boost · High Boost · Output. Each writes int16 and clips
  there (`audioif_filter_f32.c:43-51`), so the chain is **not** linear and order
  matters — +12 dB ahead of −12 dB measured 67 % THD at input peak 12000 where
  the reverse measured 0.14 % (App. G(iii)). Headroom is stated, not hidden: at
  full low boost a full-scale source clips in the Low Boost section, as it would
  in the passive unit's make-up amplifier.
- **A flat section is a wire, not a dropped node.** `mix = 0` makes the kernel
  write `to_s16(x0)`, the input sample unchanged (`:239`), so a band at 0 dB is
  byte-identical to that band absent — **at runtime**, which dropping cannot be:
  `output` is an object the host holds, so a section a macro can bring back has
  to already be in the graph. The cost half of the seed's "flat sections are
  dropped" rule is therefore **not** met; Tier 3 carries it. The floor is
  0.2 dB, because a BIPOLAR macro has no exact centre on the 0–127 grid.
- **Clamping below Nyquist is stability, not politeness.** `self._hz()` clamps
  to 0.98·Nyquist and never raises; `High Freq` and `Atten Freq` both reach
  above Nyquist at 22.05 kHz. **`Output` is a section, not a level** — no
  palette node gives gain above unity, so it is a `HIGH_SHELF` at 5 Hz:
  +12.00 dB from 100 Hz to 10 kHz at all three rates, +11.89 dB at 20 Hz.
  **Mono** gets the same curve on one channel; each node keeps per-channel
  state, so channels do not leak.

## 5. Node asks

**None.** T1–T5 are reachable on the Phase 1 palette as it stands, and the one
Tier 1 matter this dossier inherited is answered.

 audioif#23 — the
fixed-point biquad's held DC — is a Tier 1 failure for this class at its own
useful settings: a 20 Hz/+10 dB shelf holds **−32 LSB**, the +16 dB edge of its
span **−45 LSB**, a 31.25 Hz bell **+7 LSB**, for three seconds of silence.
*(Struck here as App. B's audit asked: this section read −56 LSB for the
+10 dB shelf; −56 is the **+20 dB** figure, outside §6's ±16 dB span. Three
probes reproduced −32/−45/−56 at +10/+16/+20 dB; the magnitude repeats, the
sign does not.)*

**Gate 0 answered with the float node, not the tail gate.** `audiobiquad`
landed in Phase 1 and the pin moved to `2f6cbc3` (`AUDIOIF_PIN`, 2026-09-07):
float state, anything under 1e-20 written as exact zero, so a decaying tail
arrives rather than parks. The seed said what would follow — *"this class's
tier moves to **audioif** and §4's node list changes; nothing else does"* —
and that is what happened. The two compositions it refuted stay refuted and
are not needed (App. G(iv)).

## 6. Surface — macros, patches, units

Sixteen macros, at the ceiling. **The unit is the panel's own:** the EQP-1A's
four gain pots and its bandwidth pot are dials marked 0–10, so those five read a
dial; the API 550A's band gains are switch positions marked in dB, so the bells
read dB. That removes an assumption the seed had to make — T1's "¼ travel" is
now literally S2's "2.5" on the dial.

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Low Freq | UNIPOLAR | 20–200 Hz log | LOW FREQUENCY selector |
| 1 | Low Boost | UNIPOLAR | dial 0–10 → 0…+16 dB as `16·√(d/10)` | BOOST |
| 2 | Low Atten | UNIPOLAR | dial 0–10 → 0…−20 dB, linear | ATTEN |
| 3,5,7 | Bell 1–3 Freq | UNIPOLAR | 20 Hz–20 kHz log | 550A band frequency switches |
| 4,6,8 | Bell 1–3 Gain | BIPOLAR | ±16 dB | 550A band gains |
| 9 | Bandwidth | UNIPOLAR | dial 0–10, broad→sharp | BANDWIDTH — sets the HF bell's Q *and* its peak gain (T3) |
| 10 | High Freq | UNIPOLAR | 3–16 kHz log | HIGH FREQUENCY selector |
| 11 | High Boost | UNIPOLAR | dial 0–10 → 0…+9 dB broad, 0…+18 dB sharp | HF BOOST |
| 12 | Atten Freq | UNIPOLAR | 5–20 kHz log, stepped to 5/10/20 kHz | ATTEN SEL |
| 13 | High Atten | UNIPOLAR | dial 0–10 → 0…−20 dB, linear | HF ATTEN |
| 14 | Q Law | TOGGLE | proportional \| constant (one octave, Q 1.414) | none — the S3/S5 axis, default proportional |
| 15 | Output | BIPOLAR | ±12 dB | the make-up amplifier |

**The two low tapers are ours**, chosen so dial 2.5 on both reproduces S2's
reading rather than cancelling: +8.0 dB against −5.0 dB. A **linear pair cannot
reach T1 at any corner ratio or shelf Q** — searched over 5 ratios × 6 boost Qs
× 7 cut Qs, zero pass. Sourced: that the two pots cannot share a law (S9's 10 k
against 100 k). Not sourced: the exponents (App. R).

**Characters:** none. **Patches:** `0 Flat` · `1 Low Lift And Clear` (T1's pair,
dial 2.5/2.5) · `2 Air Above Ten` · `3 Broad Warm Tilt` · `4 Sharp Presence
Bell` · `5 Rumble Trim And Top Trim` · `6 Wide Gentle Smile`. Patch 0 is the
constructor's defaults on the 0–127 grid, every section of it under the 0.2 dB
floor, so patch 0 is a wire. **`capabilities = ()`:** an equaliser has no
tempo-dependent behaviour and the class never reads `self._transport()`.

## 7. Defects in the current class the rebuild must not repeat

One read of `lib/audioeffects/eq.py`. Full wording of 2, 3, 5 and 6: **App. R**.

1. **No surface at all** — `MACRO_LABELS = ()` (`eq.py:40`), one unnamed patch (`:42`).
2. **Both shelves forced to Q 0.707** (`:54`), both low sections from one
   `low_shelf` argument at one frequency — T1 and T3 are unrepresentable in the
   constructor's shape, not merely unimplemented.
3. **`check_hz()` refuses instead of clamping** (`:48`, `:54`;
   `_core.py:471-474`), against Tier 1's "never refused".
4. **Q is an argument, not a law** (`:47-49`) — constant-Q by omission, so T4 is
   not expressible.
5. **The empty-EQ passthrough returns the source itself** (`:59-60`), and both
   `deinit()` and `reset()` skip when `output is self._source`.
6. **Constructing an effect mutates module-wide state** — `Effect.__new__` calls
   `configure()` (`_core.py:149-152`), so one EQ built at 44.1 kHz re-points
   every class built afterwards.

## 8. Open questions — three settled, one still open

1. **audioif#23's one answer. Settled.** Gate 0 took the float node:
   `audiobiquad` is on the pin (`2f6cbc3`) and this class is built on it, so the
   tier moves from **stock** to **audioif**, exactly as §5 said it would.
2. **The proportional-Q skirt level. Settled at 1 dB, against T4's own
   threshold**, which is how the seed asked for it to be decided. On the node's
   own coefficients at 48 kHz, bell at 1 kHz, +2/+6/+12 dB: at a **0.1 dB**
   skirt the first +1 dB crossing moves **18.0 %** and T4's 5 % bar is missed
   outright; at **0.5 dB**, **11.6 %**, also a miss; at **1 dB** it does not
   move at all (**0.000 %**, 2.2992 × f₀ at all three) while mid-gain bandwidth
   still falls **3.384×**, against T4's floor of 3×. The 0.1 dB skirt reproduces
   S5's prose most closely and cannot pass this class's own trait.
3. **Whether `Bandwidth` drives the bells too. Settled: the HF bell only.**
   S8's drawing puts the `HI BOOST Q` 2K2A pot *inside* the resonant HF-boost
   network (App. E), across that section's own inductor, where it reaches
   nothing else. The seed's words for the alternative were "one knob is cheaper
   and less honest"; the drawing agrees with the honest reading.
4. **Two sources could not be read here** (App. D) — the manual scan needs OCR,
   the API PDF a working certificate chain. **Still open, not a blocker.** T3
   and T4 keep medium confidence because of it, and **T3's width half stays low
   and marked ours**: no source reached here states the EQP-1A's bandwidth in
   octaves at either extreme, so that half is a design target this dossier set,
   not a fact about the pedal.

---

## Appendix

### A. The proportional-Q control law, derived

RBJ's peaking prototype normalised to ω₀ = 1, with `A = 10^(G/40)` so peak gain
is `A²`:

    |H(jω)|² = (u² + (A/Q)²) / (u² + (1/(AQ))²),   u = (1 − ω²)/ω

`u` is a dimensionless detuning — zero at centre, one value naming a
geometrically symmetric pair of frequencies. Setting `|H|² = L²` for a **fixed
absolute level** L (the "skirt"):

    u² = (A² − L²/A²) / (Q² (L² − 1))

Holding the skirt still across boost settings means holding `u` at a constant
`u₀`, i.e.

    **Q(G) = sqrt( (A² − L²/A²) / (u₀² (L² − 1)) ),   A = 10^(G/40)**

with `u₀` fixed by one anchor. Checked numerically at L = 1 dB, anchored at
Q(12 dB) = 2 ⇒ u₀ = 1.8811:

| G (dB) | Q | upper 1 dB edge | mid-gain bandwidth |
|---|---|---|---|
| 2 | 0.532 | 2.3134 × f₀ | 2.420 oct |
| 3 | 0.754 | 2.3134 × f₀ | 1.795 oct |
| 4 | 0.929 | 2.3134 × f₀ | 1.486 oct |
| 6 | 1.220 | 2.3134 × f₀ | 1.151 oct |
| 9 | 1.609 | 2.3134 × f₀ | 0.883 oct |
| 12 | 2.000 | 2.3134 × f₀ | 0.714 oct |
| 18 | 2.915 | 2.3134 × f₀ | 0.493 oct |

The skirt is pinned to five decimals and the width falls 3.4× from +2 to
+12 dB — T4's two halves. Skirt sensitivity at the same anchor: L = 0.5 dB puts
the +2 dB bell's edge at 3.08 × f₀, L = 0.1 dB at 6.48 × f₀, the closest
reproduction of S5's "0.1×f₀ to 10×f₀". Cuts take the same Q at `|G|` with the
reciprocal curve (T5). The asymptotic simplification `Q ∝ A` is **not** used:
it holds only for G ≫ L and is badly wrong at low gain. *(Audit: the "30 %"
figure did not reproduce — at +2 dB with L = 1 dB the exact Q is 0.532 against
the asymptotic 1.172, a factor of 2.2. The direction of the claim stands; the
number is struck as unverified.)*

The octave↔Q closed form used across this unit is `Q = √(2^N)/(2^N − 1)`. It
returns **4.3185** at N = ⅓, matching Bohn's own 4.318 (S3 §4.1) — corroborated,
not asserted — and 1.4142 at N = 1.

### B. Measured: what the palette's biquad does after silence

2026-09-06, CPython build of audioif (`audiocomponents/.venv/bin/python`).
200 Hz tone at 20000 for 0.1 s into one `audiofilters.Filter`, then **three
seconds of digital silence**. Values are the output sample at each mark.

| configuration | +100 ms | +0.5 s | +1 s | +2 s |
|---|---|---|---|---|
| `PEAKING_EQ` 1 kHz, +6 dB, Q 2 | 0 | 0 | 0 | 0 |
| `PEAKING_EQ` 31.25 Hz, +6 dB, Q 1.4 | −82 | **+7** | **+7** | **+7** |
| `PEAKING_EQ` 31.25 Hz, −6 dB, Q 1.4 | −7 | **−7** | **−7** | **−7** |
| `PEAKING_EQ` 62.5 Hz, +6 dB, Q 1.4 | −4 | **+2** | **+2** | **+2** |
| `LOW_SHELF` 80 Hz, +6 dB | 2 | **+2** | **+2** | **+2** |
| `LOW_SHELF` 20 Hz, +10 dB | 68 | **−56** | **−56** | **−56** |
| `LOW_PASS` 100 Hz, Q 0.707 | 1 | **+1** | **+1** | **+1** |
| ten bands 31.25 Hz…16 kHz, all +6 dB | 30 | **+5** | **+5** | **+5** |
| four `LOW_PASS` 1200 Hz (the old ladder) | 0 | 0 | 0 | 0 |

The `LOW_PASS` 100 Hz row reproduces audioif#23's own "+1 LSB" exactly, which is
the corroboration that this probe measures the same defect. New here: **peaking
and shelving sections carry it further down** — −56 LSB is ≈ −55 dBFS of DC in
every rest — and it is a low-frequency property, not a filter-type one. These
numbers belong in audioif#23 beside the existing ones (roadmap Phase 0 gate).

**Audit re-run, 2026-09-06** — an independent probe on the same CPython build
(200 Hz at 20000 for 0.1 s, then silence; `LOW_SHELF` sections at Q 0.707;
`buffer_size` 2048; output sample read at +0.5 / +1 / +2 s). **Seven of the nine
rows reproduced exactly**: 1 kHz bell 0, 31.25 Hz/+6 dB **+7**, 62.5 Hz **+2**,
80 Hz shelf **+2**, `LOW_PASS` 100 Hz **+1**, ten bands **+5**, four `LOW_PASS`
1200 Hz **0**. **Two did not.**

- `LOW_SHELF` 20 Hz **+10 dB** settles on **±32 LSB**, not −56. −56 is what a
  **+20 dB** shelf holds at that corner (+16 dB → −45, +18 dB → −50). The row's
  *gain* is the number that is wrong, not the residue — and +20 dB is outside
  this class's own ±16 dB span (§6), so the headline "−56 LSB ≈ −55 dBFS" in the
  Tier 1 notes and in §5 overstates the worst case a shipped setting can reach.
  §5 still carries the old figure; it is flagged here rather than edited,
  because §5 is outside the audit's edit boundary.
- `PEAKING_EQ` 31.25 Hz **−6 dB** read **+7**, not −7. The **sign** of a held
  residue is not stable: on the 20 Hz shelf it flips with the tone amplitude
  (5000 → +32; 10000 and 20000 → −32) and with the section's Q (0.4/0.5/0.6/1.0/
  2.0 → +; 0.707/0.8/1.4 → −). The magnitude repeats; the sign does not.

Two lessons for the kit spec: a row in this table is only reproducible if it
states the section's **Q** and the excitation level, and the gate's criterion
must be `|residue| > 0` rather than a signed value.

**Audit re-run, 2026-09-06 (third independent probe, `dc2.py`).** Same CPython
build, 200 Hz at 20000 for 0.1 s then three seconds of silence, `buffer_size`
2048, output sample read at +0.1 / +0.5 / +1 / +2 s. **Every row reproduced:**
1 kHz bell **0**; 31.25 Hz/+6 dB **+7**; 31.25 Hz/**−6 dB** **+7** (the sign
correction above holds — a −6 dB bell also settles positive); 62.5 Hz **+2**;
`LOW_SHELF` 80 Hz/+6 dB **+2**; `LOW_SHELF` 20 Hz/**+10 dB** **−32**;
20 Hz/**+16 dB** **−45**; 20 Hz/**+20 dB** **−56**; `LOW_PASS` 100 Hz **+1**
(audioif#23's own figure); ten bands **+5**; four `LOW_PASS` 1200 Hz **0**.

**And one finding the kit spec must carry, because it nearly produced a green
result on a defect that was there.** The audit's *first* probe fed a 0.1 s
`RawSample` and then kept pulling the `Filter` for three seconds, expecting the
node to filter the silence that follows the sample. It does not: once the source
ends, `audiofilters.Filter` returns **exact zeros**, and all eleven rows —
including the `LOW_PASS` 100 Hz row that audioif#23 itself measures at +1 LSB —
read 0. The residue only exists while the node is actually processing samples,
so the silence **must be inside the sample** (tone-then-zeros in one buffer), as
the rows above do. A tail probe built the first way would report every
configuration clean and would have been believed: absence reading as agreement,
in the exact shape `agent-knowledge/workspace-craft.md` names. The Phase 0 kit's
burst-then-silence probe must therefore feed silence *through* the class, and
must carry a **positive control** — a configuration known to hold a residue
(31.25 Hz/+6 dB/Q 1.4, +7 LSB) that has to come back non-zero, or the probe is
not measuring anything.

### C. The cost arithmetic behind Tier 3

audioif's own cross-compiled measurement: `audioif_biquad_process()` is **76
instructions per sample** on Cortex-M4/M7 after the widening
(`docs/upstream-diff.md:1167-1174`). No Xtensa or RISC-V count exists yet, so
this budget assumes **100 instructions per sample per section per channel** —
the M4 figure with a third of headroom for the two ports' multiply paths, which
Station C either meets or corrects.

One stereo block is 256 frames (`SYNTHIO_MAX_DUR`, `src/synthio/__init__.h:126`) = 512 samples =
5.33 ms at 48 kHz: **1,280,000 cycles on a 240 MHz S3**, **2,133,000 on a
400 MHz P4**. One stereo section ≈ 51,200 cycles ⇒ **4.0 % of the S3's block,
2.4 % of the P4's**. Four sections: 16 % / 10 %. The budget adds a third for
the `Filter` node's per-block overhead and the Python that runs on a macro
move, giving **S3 21 % / P4 13 %** at four sections and **S3 43 % / P4 26 %** at
eight (the audit's correction: adding a third to 16 % / 10 % gives 21 % / 13 %,
and doubling that gives the eight-section pair). Ceilings the class gate
measures against, not predictions.

**Audit, 2026-09-06.** The arithmetic reproduces exactly: 51,200 cycles is
4.00 % of the S3's 1,280,000 and 2.40 % of the P4's 2,133,333; four sections
16.0 % / 9.6 %; plus a third, 21.3 % / 12.8 % ⇒ **21 % / 13 %**; eight sections
42.7 % / 25.6 % ⇒ **43 % / 26 %**. Both repo citations check by `grep -n`:
`#define SYNTHIO_MAX_DUR (256)` is `audioif/src/synthio/__init__.h:126`, and the
76-instruction Cortex-M4/M7 figure is `audioif/docs/upstream-diff.md:1172`
(inside the cited `:1167-1174`). The 0.03 dB flatness cited in §4 is
`docs/upstream-diff.md:1123`, inside its cited `:1108-1123`. *(`GraphicEQ.md`'s
Tier 3 did **not** reproduce from this arithmetic and was corrected in the same
audit; see its Tier 3 note.)*

### D. Sources not reached, and what was looked for

**Reached, unreadable:** the EQP-1A user manual scan,
https://www.thehistoryofrecording.com/Manuals/Pultec/Pultec_EQP-1A_Manual.pdf
— 8 pages, **zero extractable text** under `pypdf`: an image-only scan, and this
machine has no OCR. **Not reached:** `help.uaudio.com` Pultec and API manuals
(HTTP 403); `apiaudio.com` 550A product page (TLS handshake failure);
technicalaudio's *API 550 Equalizer Versions* PDF (certificate chain not
verifiable); `jbb.ru` EQP-1A schematic over **https** (certificate name
mismatch) — but **reached over http in the audit run and read**, and now
carried as S9;
`www.electrosmash.com` (does not resolve from this machine — re-confirmed in the
audit run — and its MAS Effects mirror, whose index the audit re-read, lists 29
articles and no equaliser among them). **Looked for and not found:** any
published measurement of an API 550A's actual Q-versus-boost curve family, and
any DAFx or AES paper modelling the 550 — which is why T4's law is derived in
Appendix A rather than read off a curve, and why its confidence is medium.

**Audit, 2026-09-06 — every line above re-tested, with the failure each host
actually returns.** `thehistoryofrecording.com` manual: **HTTP 200**, 424,913 B,
**8 pages, 0 extractable characters** under `pypdf` — reached and unreadable, as
recorded. `help.uaudio.com`: **HTTP 403**. `apiaudio.com`: no HTTP status at all —
`OpenSSL … sslv3 alert handshake failure` at the TLS handshake. `technicalaudio.com`
API 550 versions PDF: `SSL certificate problem: unable to get local issuer
certificate` — the chain is unverifiable, and the audit did **not** bypass
verification to read it, so it stays not reached and T3/T4 keep their medium
confidence. `jbb.ru` over **https**: `no alternative certificate subject name
matches target host name` — over **http**: HTTP 200, and the GIF (3662 × 2579,
130,969 B, `image/gif`) was decoded and read in this run. `www.electrosmash.com`:
`Could not resolve host` (no DNS record at all). Its MAS Effects mirror:
**HTTP 200**, and the index states in its own words that it is "not a complete
backup of the site — just these 29 articles"; the audit counted them — 19 pedals,
4 chips, 6 amps — four of them MXR (Distortion +, Dyna Comp, MicroAmp, Phase 90)
and **no equaliser**.

### E. Audit source notes — the excerpts the §2 rows point to

Read at source in the licence-and-citation audit run, 2026-09-06. Kept here so
§2 stays a table and §1–§8 stay a read.

**S5, and what is S5's own.** Its own words: "boosting 2dB @200Hz in proportional
Q starts to boost near 20Hz and finishes near 2kHz. That's .1 x the center
frequency to 10 x the center frequency", and "as you increase the boost or cut,
the frequency range remains stable, but the shape of the curve narrows — thus
proportional Q." Its model table (API 550 / 550A / 550A-1 / 550B, band counts and
frequency counts, Proportional vs Constant Q) is introduced as a summary of
"an interesting article about API 550 equalizers"; that article was not reached.

**S9's drawing, read.** HF boost bank C1 18nF, C2 15nF, C3 8.2nF, C4 5.6nF,
C5 3.3nF over L1 150mH, L2 82mH, L3 68mH, L4 47mH, L5 33mH, L6 27mH on SW1 at
3/4/5/8/10/12/16 kHz. HF atten bank C6 290nF, C7 220nF, C8 170nF, C9 120nF,
C10 68nF, C11 68nF on SW3 ("ATTEN SEL") at 3/5/6/8/10/20 kHz. Low section: two
banks on one ganged selector at 20/25/30/60/80/100 Hz — SW2a cut C12 56nF,
C13 43nF, C14 27nF, C15 8.2nF, C16 4nF, C17 12nF; SW2b boost C18 1.5µF,
C19 1.2µF, C20 820nF, C21 220nF, C22 100nF, C23 330nF. Pots: Treble Boost R1 10k
Lin 0…+16 dB, Treble Cut R2 1k Lin 0…−16 dB, Bass Boost R9 10k Log 0…+16 dB,
Bass Cut R8 100k Log 0…−16 dB, Bandwidth R6 2k5 Lin Sharp↔Broad; plus R3 75,
R4 1k, R5 10k, R7 1M and a SW4a/SW4b in/out. Read tile by tile from the decoded
GIF, at 1.35× upscale.

**S8's drawing, read.** HI BOOST bank and its own table: 3 kHz 15nF » 175mH,
4 kHz 15nF » 100mH, 5 kHz 10nF » 90mH, 6 kHz 10nF » 65mH, 10 kHz 6,8nF » 35mH,
12 kHz 6,8nF » 23mH, 16 kHz 3,3nF » 19mH, with a "HI BOOST Q" **2K2A pot** —
the Bandwidth control, inside the resonant section. LO FREQ selector 2u2 = 20 Hz,
1u = 30 Hz, 470n = 60 Hz, 330n = 100 Hz, with a second low-frequency bank
(100n / 47n / 22n / 15n) on the other low path. HI-CUT ("HI-CUT F") 47n / 47n /
150n at 5, 10, 20 kHz. Pots: BOOST HI 10KA, CUT HI 1KC (with 75R), BOOST LO 10KB,
CUT LO 100KB — the same four resistances S9 gives as R1 10k, R2 1k, R9 10k and
R8 100k. Tubes ECC83 (V1) and ECC82 (V2), 600:600R input transformer,
10K:10K+10K interstage, output transformer T3, and a "BYPASS" switch on both
low paths. The page's text adds that the amplifier was later changed to an
ECC88/6DJ8/6922 in the author's own build.

**S3/S4, the Rane site's terms.** `ranecommercial.com`'s footer links
`/terms-of-use` (inMusic Brands): site content "is owned, controlled or licensed
by or to inMusic"; "no part of the Site and no Content may be copied, reproduced,
republished … without inMusic's express prior written consent"; viewing is granted
"solely for your own personal purposes and provided that … the Content available
from this Site is used for informational and non-commercial purposes only". That
makes the *site* call verified all-rights-reserved rather than unverified; it does
not change the treatment of either document, and it says nothing about the 1986
JAES paper's own rights, which remain AES's and unread.

### F. Trait-critic pass — what changed in the Tier 2 table

2026-09-07. Five rows, all kept, all five rewritten in
place; none needed marking unmeasured. Three of the five carried a
disconfirmation that was not the complement of the trait — **T3** asked for
6–12 dB and disconfirmed at "under 3 dB", **T4** asked for a 3× bandwidth ratio
and disconfirmed at "under 2", **T1** asked for three thresholds and
disconfirmed on one — so a measurement could miss the stated numbers without
meeting the stated disconfirmation, which leaves a gate with nothing to fail on.
Each is now "any of the N missed", with the old wording kept as the limiting
case that names the mechanism. **T1**'s confidence was "high" over thresholds
scaled from one reviewer's single reading; the mechanism keeps that grade and
the numbers are now marked ours, including the assumption that S2's "2.5" is ¼
of this class's macro travel. **T3**'s width half is marked low and ours: no
source reached here states the EQP-1A's bandwidth in octaves. **T5** named "+G"
without saying what G is — it now measures at 6, 12 and 16 dB, and names the
signed-gain `Q` law as the way a build fails it while still looking right at the
peak. T2's peak-monotonicity half gained the disconfirmation it lacked. Tier 1
block verbatim; Tier 3 carries both boards.

### G. Palette-verifier pass — the probes behind §4 and §5

2026-09-06, CPython build of audioif (`audiocomponents/.venv/bin/python`),
audioif at `v0.2.0-14-g0b640b3`. Every number in §4 and §5 that says "measured"
comes from this run; every line citation in §4 and §5 was re-checked with
`grep -n` against the tree at that commit.

**Cites corrected.** `Biquad.c:45` is the `set_Q` *signature*, so the `Q`
slot's `assign_slot` is `:46`; the per-block slot reads are `:79-83`, not
`:81-83` (`:79` is the `frequency` read the old range omitted); and the change
guard is the three-line `if` at `:87-90`, of which `:88` was the middle line.
**Confirmed as written:** `Biquad.h:21-23` (all seven modes);
`shared/audioif_biquad.c:54-68` and `:118-124` (double coefficients,
per-filter fractional format), `:159-179` and `audioif_biquad.h:14` (the
`int64_t` accumulator and `AUDIOIF_BIQUAD_STATE_SHIFT 12`), `:88-95` (the
peaking-`b2` sign fix); `docs/upstream-diff.md:1108-1123` (the 0.03 dB
flatness, the sentence itself at `:1123`) and `:983-1020` (per-channel biquad
state, the change at `src/audiofilters/Filter.c:109-118` and `:282`).

**(i) T1 on two stock `LOW_SHELF` sections at different corners.** One
`audiofilters.Filter`, 48 kHz mono, boost `LOW_SHELF` 60 Hz A = 10^(7/40), cut
`LOW_SHELF` 300 Hz A = 10^(−4.5/40), steady-state peak of a rendered sine at
each frequency:

| Hz | 20 | 30 | 60 | 100 | 150 | 200 | 400 | 1000 | 5000 |
|---|---|---|---|---|---|---|---|---|---|
| dB | +2.41 | **+2.05** | −0.99 | −3.59 | **−4.04** | −3.68 | −1.10 | **−0.05** | +0.00 |

T1 asks for ≥ +2.0 dB at 30 Hz, a minimum ≤ −1.0 dB inside 100–400 Hz, and
flat within 0.5 dB above 1 kHz. All three, on stock nodes. (The gains and
corners here are one working point, not the class's control law — §6 and
Phase 2 set that.)

**(ii) Unity-plus gain.** `audiomixer.Mixer` accepts `voice[0].level = 2.0`,
reads it back as 2.0, and renders a 4000-peak sine at **4000** — the limit is
`synthio_block_slot_get_limited(&voice->level, 0.0, 1.0)`
(`src/audiomixer/Mixer.c:332`) and it does not raise. `audiomath.Multiply`
cannot exceed unity by construction (`shared/audioif_multiply.c:38-45`). A
`HIGH_SHELF` biquad at a subsonic corner does the job:

| corner | 30 Hz | 100 Hz | 1 kHz | 10 kHz |
|---|---|---|---|---|
| 1 Hz | +12.03 | +12.01 | +12.01 | +12.06 |
| 5 Hz | +11.99 | +12.00 | +12.00 | +12.01 |
| 20 Hz | +9.69 | +11.97 | +12.00 | +12.00 |

5 Hz is the working corner: flat to ±0.01 dB across the band, and its own
20 Hz roll-off is far enough down not to eat a low shelf.

**(iii) Order matters, because the chain is not linear.** +12 dB broadband
shelf-gain and a −12 dB 1 kHz bell, both inside one `Filter`, 1 kHz sine:

| input peak | gain→bank peak | THD | bank→gain peak | THD |
|---|---|---|---|---|
| 2000 | 2003 | 0.09 % | 2009 | 0.26 % |
| 6000 | 6012 | 0.19 % | 6003 | 0.05 % |
| **12000** | 12941 | **67.3 %** | 12017 | **0.14 %** |
| 20000 | 14548 | 82.7 % | 28521 | 9.4 % |

The mechanism is the biquad's own state clamp at ±32767
(`shared/audioif_biquad.c:163-164`, `:174-175`), which bites the *intermediate*
section; the 28521 the last row settles on is that clamp read through the
`Filter`'s ±28000 mix-down knee (`src/audiofilters/Filter.c:288`;
28000 + (32767 − 28000)·7151/65536 = 28520).

**(iv) audioif#23 re-measured, and the two refutations.** Probe shape as
Appendix B (tone-then-zeros **inside one sample**, 200 Hz at 20000 for 0.1 s
then 3 s of silence, `buffer_size` 2048, output read at +0.1/+0.5/+1/+2 s).
Eleven rows, all reproduced: 1 kHz bell **0**; 31.25 Hz/+6 dB **+7**;
31.25 Hz/−6 dB **+7**; 62.5 Hz **+2**; `LOW_SHELF` 80 Hz/+6 dB **+2**;
20 Hz/+10 dB **−32**; 20 Hz/+16 dB **−45**; 20 Hz/+20 dB **−56**; `LOW_PASS`
100 Hz **+1** (audioif#23's own figure, the positive control); ten bands
31.25 Hz–16 kHz all +6 dB **+5**; four `LOW_PASS` 1200 Hz **0**.

Appended `HIGH_PASS` after `LOW_SHELF` 20 Hz/+10 dB: 20 Hz → **+18**,
40 Hz → **+4**, 5 Hz → **−284**. Appended after `PEAKING` 31.25 Hz/+6 dB:
**−18**; placed *before* it: **+25**. `audiodynamics.Dynamics(DYN_GATE,
threshold_db=-70, ratio=4, attack_ms=1, release_ms=50)` downstream of the
`Filter`: **−32** at every mark; at `threshold_db=-50`: **0** at every mark
and a maximum of 0 across the last second.

Probe scripts are scratch (`dc_probe.py`, `dc_compose.py`, `dc_gate.py`,
`pultec.py`, `gain.py`, `commute.py`); every one is reproducible from the
Phase 0 kit's swept-sine and burst-then-silence probes once those exist, and
the burst probe must carry the positive control named in Appendix B.

**One warning the whole survey needs.** `src/synthio/__init__.h` **moved
between the commit vision §6 names (`7455577`) and this one**: `SYNTHIO_MAX_DUR`
was line 119 there and is line 126 here, and the mix-down range/scale pair was
`:126-127` there and is `:133-134` here. Every other file cited in §4 and §5 —
`Biquad.c`, `Biquad.h`, `audiofilters/Filter.c`, `shared/audioif_biquad.c`,
`shared/audioif_multiply.c`, `audiomixer/Mixer.c`, `docs/upstream-diff.md` — is
byte-identical across those seven commits, so their line numbers hold either
way. `LadderFilter.md` §5 and its Appendix C disagreed with each other on this
exact line, which is how the drift was found. **Seeds should state the audioif
commit their citations are against;** these do now.

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

**Notes.** `capabilities = ()`: an EQ has no tempo-dependent behaviour and does
not read the transport (D10). Not stereo-by-definition — mono gets the same
curve on one channel. At 22.05 kHz the 16 kHz shelf and bells above ~10 kHz do
not exist, so spans **clamp** and T2/T3 are stated only below 0.45·Nyquist.
**Silence-to-zero is the invariant this family is known to fail**: measured
here, a 31.25 Hz/+6 dB/Q 1.4 bell settles on **+7 LSB and holds it for three
seconds**, a 20 Hz low shelf on **±32 LSB at +10 dB** (the −56 LSB of the first
run is what a **+20 dB** shelf holds — corrected by the audit re-run in
Appendix B, which also shows the *sign* of a held residue is not stable, so
read these as magnitudes), ten bands at +6 dB on **+5 LSB**; the same bell at
1 kHz reaches exact zero (Appendix B). **A third, independent probe in the
licence-and-citation audit run reproduced every one of those rows exactly**,
including the two controls that must read zero, and added the +16 dB shelf
(−45 LSB) between the +10 and +20 dB rows (Appendix B). **§5 still quotes
−56 LSB for a 20 Hz/+10 dB shelf**: that is the **+20 dB** shelf's figure, the
+10 dB shelf holds 32, and §5's sentence must be struck when §5 is next edited
(§5 is outside the audit's edit boundary). Gate 0 owns the one answer (§5).

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Barrera, Lizarraga-Seijas & Font, *Modeling the Pultec EQP-1A with Wave Digital Filters*, Proc. SMC 2024, 445–452 | the four filter blocks and their kinds; 16 dB insertion loss; the boost/cut different-band statement (fig. 2); that the schematics are not public | **CC BY 3.0** (p. 445) — permissive, attributed | https://smcnetwork.org/smc2024/papers/SMC2024_paper_id132.pdf | fetched; read via `pypdf` (the fetch tool could not) |
| **S2** Robjohns, *Pulse Techniques EQP-1A*, Sound On Sound, Feb 2019 | lab measurements of the 2019 reissue: the 9 dB narrow-vs-broad figure, the +3/−2 dB combined setting | © SOS Publications 1985–2026, all rights reserved — read as a document | https://www.soundonsound.com/reviews/pulse-techniques-eqp-1a | read |
| **S3** Bohn, *Constant-Q Graphic Equalizers*, JAES **34**(9), Sept 1986 | **conventional** vs constant Q (§2 — Bohn's word is *conventional*, and neither this paper nor S4 ever writes *proportional*; that term is S5's and API's); reciprocal `1+k·BP` / `1/(1+k·BP)` (§3.1, stated there for the symmetrical topology); Q = 4.318 at ⅓ octave (§4.1) | **No copyright or licence line in the PDF** (re-read in the audit run); the hosting site does carry a **Terms of Use** — personal, non-commercial, all content reserved (https://www.ranecommercial.com/terms-of-use, Appendix E) — while the paper's own rights are AES's: **license unverified, treated as copyleft**, read as a paper, its mathematics re-derived, no code taken | https://www.ranecommercial.com/legacy/pdf/constanq.pdf | fetched and read via `pypdf` in the audit run |
| **S4** Bohn, RaneNote 101/117 ("written 1982 & 1987; last revised 11/05") | the Q/bandwidth definitions used here (Q = f₀ ÷ bandwidth in Hz; ⅓ octave ⇒ Q 4.31) | "© 2005 Rane" on the page, under the same site-wide Terms of Use as S3 (personal, non-commercial) — **verified all-rights-reserved**, read as a document | https://www.ranecommercial.com/legacy/note101.html | re-read in the audit run |
| **S5** Sutton, *API 550 Equalizers* (31 Jan 2023) | 550A: three bands, five frequencies each, Proportional Q; the law in the author's own words, and the 0.1–10×f₀ figures at 2 dB (quoted in Appendix E). **Chain:** the model/band table is S5's own summary of another article — technicalaudio's *API 550 Equalizer Versions*, **not reached** (Appendix D) — so that half is a quotation at one remove; the proportional-Q prose and the 0.1–10×f₀ figures are S5's own | "© 2026 Matthew Sutton" (Privacy Policy only; no other terms page) | https://ms-tas.com/api-550-equalizers/ | re-read in the audit run |
| **S6** ABSounds/EQP-WDF-1A front page | panel ranges: LF 20/30/60/100 Hz, 13.5/17.5 dB; HF boost 3–16 kHz to 18 dB, variable Q; HF cut 5/10/20 kHz to 16 dB. **Chain:** the README states these in a block quote it attributes to `musictech.com/reviews/pultec-eqp-1a`, which was not fetched — so this is a quotation at one remove, not the repository's own measurement, and its dB figures disagree with S1's | **GPL-3.0 — copyleft.** Front page read as a document; **no source file opened** (vision §5) | https://github.com/ABSounds/EQP-WDF-1A | read |
| **S7** Ultimate Preset, *Pultec Equalizer Guide* | corroborates all three selector lists verbatim: LF 20/30/60/100 Hz, HF peak boost 3/4/5/8/10/12/16 kHz "with adjustable bandwidth (Q)", HF shelving attenuation 5/10/20 kHz | "© 2026 Ultimate Preset. **All rights reserved.**" — verified all-rights-reserved, read as a document | https://www.ultimatepreset.com/pultec-equalizer-guide/ | re-read in the audit run |
| **S8** Gyraf Audio, *The G-Pultec* — the page **and** its linked drawing `gy_pd/pultec/pultech.gif` ("Pultec/ Tubetec PE-1a program equalizer, November 2001"), the diagram S1 lists as one of its four references | **Audit correction: this row read "nothing usable … the schematic is an unrendered GIF". The GIF was fetched and read in the audit run and is a full reverse-engineering *with values*** — it corroborates the **four-position LF selector** (20/30/60/100 Hz), the **three-position HI-CUT** (5/10/20 kHz), the **two separate low-frequency capacitor banks** T1 rests on, and **all four of S9's pot resistances**; it disagrees with S6/S7/S9 on one HF-boost position (6 kHz where they give 8). Values, the cap/inductor table and the caveats are in Appendix E. Its author states it is his own reverse-engineering and that "the transformer data are guesswork" | **No licence and no copyright line on the page, and none on `gyraf.dk`'s home page** (both checked in the audit run); Jakob Erland, signed 03-03-2006 — license unverified, treated as copyleft; read as a document for topology and values (vision §5), nothing reproduced | https://www.gyraf.dk/gy_pd/pultec/pultec.htm (drawing at `/gy_pd/pultec/pultech.gif`, 1024 × 617) | page and drawing both **reached and read in the audit run** |
| **S9** *Schematic Pultec EQP-1A — Program Equalizer Passive*, jbb.ru's own redraw (watermarked `www.jbb.ru`, no attribution to a factory drawing) | a full passive-section drawing **with values**: the HF boost and HF atten banks with their switch positions, **two separate LF capacitor banks on one ganged selector** (SW2a cut C12–C17, SW2b boost C18–C23, at 20/25/30/60/80/100 Hz) — the mechanism T1 rests on — and all four pots marked ±16 dB. Every value, switch position and pot marking was read off the drawing itself in the audit run and is listed in Appendix E; S8's independent drawing agrees on the pot resistances and on the two-bank low section, and disagrees on the selector lists | **No licence and no copyright line on the page, and none on jbb.ru's home page — license unverified, treated as copyleft.** Read as a document for topology and values (vision §5); nothing reproduced | http://jbb.ru/schematics/1a-shem-p.htm (drawing at `/schematics/1a-shem-p.gif`) | **reached over http and read in both audit runs**; https fails on a certificate name mismatch. The GIF is 3662 × 2579 and legible once decoded |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| **T1** | Low boost and low cut are two shelves with **different corners**, so both at once is not cancellation. `Low Freq` 60 Hz, both at ¼ travel ⇒ ≥ +2.0 dB at 30 Hz, a local minimum ≤ −1.0 dB in 100–400 Hz, flat within 0.5 dB above 1 kHz. | S1 §1.3 + fig. 2 (two networks, "slightly different frequency bands"); S2's measurement of the reissue | **high** for the mechanism; the three thresholds are **ours**, scaled from S2's single reading (+3 dB shelf with a −2 dB mid dip, both controls at 2.5) and loosened by a third. That S2's "2.5" is ¼ of the class's macro travel is this seed's mapping, not S2's statement | **any of the three missed.** In particular: the two curves cancelling to within 1 dB everywhere from 20 Hz to 1 kHz (one shared corner — a single reciprocal shelf pair, which is what the current class builds); or the minimum landing **below** 60 Hz instead of above it | swept-sine 20 Hz–2 kHz at 48 and 44.1 kHz; report the level at 30 Hz, the frequency and level of the minimum, and the maximum deviation above 1 kHz |
| **T2** | High boost is a **bell**, high cut a **shelf**, on independent selectors. Boost full at 10 kHz *and* cut full at 5 kHz ⇒ a local maximum within ±⅓ oct of 10 kHz **and** a monotonic fall 3→5 kHz. | S1 §1.3; S6, S7 (three selectors) | high | **either half missed.** No local maximum within ±⅓ oct of 10 kHz (the HF boost is a shelf, not a bell); or the 3→5 kHz fall not monotonic (the HF cut is a bell, not a shelf); or moving the HF-cut selector also moving the boost's peak (one shared selector) | swept-sine 1–20 kHz, both engaged; report peak frequency, the 3→5 kHz monotonicity, and the boost peak's frequency at both extremes of the cut selector |
| **T3** | Bandwidth changes **peak gain**, not just width: at full boost, sharp minus broad is **+6…+12 dB** and the −3 dB width at sharp is ≤ half that at broad. | S2 (the 9 dB figure, quoted in §1) | **medium** for the gain half — one reviewer's reading of one unit, bracketed ±3 dB around S2's 9. **Low, and ours,** for the width half: no source reached here states the EQP-1A's bandwidth range in octaves at either extreme, so the halving is a design target this seed sets, not a fact about the pedal | **either half missed.** Sharp-minus-broad peak gain outside **6–12 dB** — in particular under 3 dB, which is a width-only control and the shape every constant-gain Q knob has; or the sharp setting's −3 dB width more than **half** the broad setting's | swept-sine at both bandwidth extremes, boost max; report peak dB and −3 dB octave width at each |
| **T4** | The bells are **proportional-Q**: one bell at 1 kHz at +2/+6/+12 dB has its first +1 dB crossing the same **within 5 %**, while mid-gain bandwidth falls **≥ 3×** across that range. | S5; S3 §2 and S4 for the definitions; law derived in Appendix A | medium — no measured API curve family reached; the law is ours | **either half missed.** The +1 dB crossing moving > 5 % between the three boosts; or the mid-gain bandwidth ratio from +2 to +12 dB under **3×** — the law of Appendix A predicts **3.39×** at the anchor `Q(12 dB) = 2`, so 3× is a floor with margin rather than the prediction itself, and a ratio near 1 is constant-Q outright | swept-sine at three boosts; report the +1 dB crossings and half-gain bandwidth in octaves |
| **T5** | Cut is the **exact reciprocal** of boost: for one bell at 1 kHz at **G = 6, 12 and 16 dB**, the product of the +G and −G responses is unity within **0.1 dB**, 20 Hz–20 kHz, at every one of the three. | S3 §3.1 | high | the product deviating > 0.1 dB anywhere in band at any of the three gains — in particular a `Q` law that reads **signed** gain rather than its magnitude, which gives the cut a different width from the boost and breaks the product at the skirts while leaving the peak looking right | swept-sine at +G and −G for each of the three; multiply, report max deviation from 0 dB and the frequency it occurs at |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Audit, 2026-09-06.** Every row above was independently re-fetched and re-read by
the licence-and-citation audit, not taken from this seed: S1 and S3 downloaded and
read with `pypdf`; S2, S4–S8 fetched and read as HTML; S6's licence read from the
repository's own `LICENSE` file (GNU GPL v3, 29 June 2007) rather than from GitHub's
label; S9 fetched over **http** and its GIF decoded, upscaled and read tile by tile —
every component value, switch position and pot marking in the S9 row was checked
against the drawing itself. Corrections are marked in place. Nothing in §1 or §3 was
found without a source row.

*(from §3)*

**Two standouts, and each has its own rows.** This class carries a pair (vision
§4.2), and they are not alternative characters a patch switches between — they
occupy different parts of one surface, so both are live at once and both are
measured at once. **T1, T2 and T3 are the EQP-1A's** (the two low networks, the
bell-versus-shelf split at the top, the bandwidth control); **T4 and T5 are the
API 550's** (the proportional-Q law and its reciprocal cut). Neither standout can
hide behind the other: a rebuild that passes T4 and T5 with a single reciprocal
shelf pair at the bottom still fails T1.

*(from §3)*

Budget as a fraction of one stereo block's deadline (256 frames, 5.33 ms at
48 kHz): **P4 13 %, S3 21 %** for the default four sections (two shelves, two
bells); **P4 26 %, S3 43 %** at the full eight. *(Audit correction: this line
first read 6/11 % and 12/22 %, which is Appendix C's own arithmetic shifted a
column — 16 % raw at four sections cannot become 11 % by adding a third to it,
and the old "eight section" pair is in fact the four-section figure.
`GraphicEQ.md`'s Tier 3 already uses the corrected scale.)* Arithmetic in
Appendix C from audioif's own instruction counts. **Lean patch expected: no** — an EQ over
budget drops sections, which is already what a flat band does (§4).

*(from §3)*

**Latency: zero.** Every section is a biquad — recursive, reading no sample it
has not been given — so `latency_samples` is 0 at every macro setting and every
rate, and **no option on this class adds latency**: there is no lookahead, no
partition, no window. `tail_samples` is not zero; the lowest-corner,
highest-Q section's measured 60 dB decay sets it.

*(from §4)*

- All seven RBJ modes are there (`src/synthio/Biquad.h:21-23`), and
  `frequency`, `Q` **and** `A` are block slots (`Biquad.c:46`, `:54`, `:62`)
  read once per block (`:79-83`) behind a change guard (`:87-90`) — so every
  macro can bind to a synthio block and sweep with no Python in the loop. The
  `Filter` drives the tick (`src/audiofilters/Filter.c:281`) and scales
  `frequency` by the **running** rate at tick time (`Biquad.c:80`, the global
  set at `Filter.c:231`), so corners are stated in Hz and never pre-warped.
  *(Cites corrected in the palette-verifier pass, Appendix G.)*

*(from §4)*

- Coefficients build in `double` with a per-filter fractional format
  (`shared/audioif_biquad.c:54-68`, `:118-124`) into an `int64_t` accumulator
  with 12 extra fractional state bits (`:159-179`, `audioif_biquad.h:14`), and
  measure flat to **0.03 dB from 50 Hz to 22 kHz**
  (`docs/upstream-diff.md:1108-1123`); peaking `b2` carries audioif's sign fix
  (`audioif_biquad.c:88-95`). No new filter math is needed or asked for.

*(from §4)*

- **Clamping below Nyquist is a stability requirement, not a politeness.** A
  `synthio.Biquad` whose corner sits above the running Nyquist is **unstable**:
  at 22.05 kHz a 16 kHz section rails into a full-scale ±28521 square wave at
  f_s/4 within ten samples, in `HIGH_SHELF`, `PEAKING_EQ` and `LOW_PASS` alike,
  raising nothing — and it stays silent on silence, so construct-and-catch and
  silence-in-silence-out both pass it (`GraphicEQ.md` Appendix E(iv)). `High
  Freq` (to 16 kHz) and `Atten Freq` (to 20 kHz) both reach there at 22.05 kHz.

*(from §4)*

- **Python computes, per macro move and not per block:** a bell's `Q` from its
  gain by the proportional-Q law (Appendix A, one `sqrt` and two `10**`); and
  the Pultec shelves as **two separate `LOW_SHELF` sections at different
  frequencies**, which is how T1 is reached on stock nodes. Nothing is
  tabulated and nothing is rebuilt on a board. **Measured, not asserted:** one
  such pair renders +2.05 dB at 30 Hz, a −4.04 dB minimum at 150 Hz and ≤0.05 dB
  deviation above 1 kHz — T1's three thresholds, on stock nodes (Appendix G(i)).

*(from §4)*

- **The `Output` macro is a section, not a level.** No palette node gives gain
  above unity: `audiomixer.MixerVoice.level` clamps to 0–1 and does so
  **silently** (`src/audiomixer/Mixer.c:332` — `level = 2.0` reads back as 2.0
  and renders at unity), and `audiomath.Multiply` can only attenuate
  (`shared/audioif_multiply.c:38-45`). The stock ±12 dB is a **`HIGH_SHELF` at
  a subsonic corner** — 5 Hz at A = 10^(12/40) measures +12.00 ± 0.01 dB from
  30 Hz to 10 kHz (Appendix G(ii)) — which is one more biquad for Tier 3 to
  count.

*(from §4)*

- **Cascaded sections have a headroom rule.** Each biquad clamps its own state
  at ±32767 (`shared/audioif_biquad.c:163-164`, `:174-175`) and the `Filter`'s
  output passes a soft knee at ±28000 (`src/audiofilters/Filter.c:288`,
  `src/synthio/__init__.h:133-134`), observed ceiling 28521 — so the cascade is
  **not linear** and section order matters: a +12 dB shelf ahead of a −12 dB
  1 kHz bell measures **67 % THD at input peak 12000** where the reverse order
  measures **0.14 %** (Appendix G(iii)). The rebuild puts cutting sections
  first, or states the headroom it needs.

*(from §4)*

- **Mono:** the same curve, one channel. A stereo `Filter` keeps per-channel
  biquad state (`docs/upstream-diff.md:983-1020`), so channels do not leak.
  **Portability tier: stock.**

*(from §5)*

One **Tier 1** matter is not this dossier's to decide, and the seed states which
answer it inherits. **audioif#23** — the fixed-point biquad's held DC — is a
Tier 1 failure for this class at its own useful settings: a 20 Hz/+10 dB low
shelf holds **−32 LSB** (≈ −60 dBFS of DC) forever, the +16 dB edge of this
class's own span **−45 LSB** (≈ −57 dBFS), and a 31.25 Hz bell **+7 LSB**.
*(Palette-verifier correction, 2026-09-06: this read **−56 LSB (≈ −55 dBFS)**
for the 20 Hz/+10 dB shelf. −56 is what a **+20 dB** shelf holds, and +20 dB is
outside the ±16 dB span §6 offers. Appendix B's second audit caught it and
could not edit here; a third independent probe reproduced −32 / −45 / −56 at
+10 / +16 / +20 dB. The residue's magnitude repeats; its sign does not.)*

*(from §5)*

Gate 0 gives one answer for the whole EQ family and the Phaser. **This seed
recommends the block-rate tail gate first**: compose-first, no node, and the
residues are small enough that zeroing the chain after N blocks of silent
input removes them exactly. If Gate 0 takes a float node instead, this class's
tier moves to **audioif** and §4's node list changes; nothing else does.

*(from §5)*

- **Append a stock `HIGH_PASS`.** The obvious compose-first move, and it makes
  the defect **worse** — the high-pass is the same fixed-point kernel and holds
  its own residue. After a `LOW_SHELF` 20 Hz/+10 dB (−32 LSB alone): a 20 Hz
  high-pass gives **+18**, a 40 Hz one **+4**, a 5 Hz one **−284**.

*(from §5)*

- **Gate with `audiodynamics.Dynamics` in `DYN_GATE`.** Mechanically it works —
  the gate's cut floors at −80 dB (`shared/audioif_dynamics.c:187-192`) — but
  only with its threshold **above** the residue's own −60 dBFS: at
  `threshold_db=-70` the output still reads −32, at `-50` exactly 0. A −50 dBFS
  gate on an equaliser mutes reverb tails, and `Dynamics` is an audioif-own
  node, so the composition also costs the **stock** tier it was protecting.

*(from §7)*

2. **Both shelves forced to Q 0.707** (`eq.py:54`), and low boost and low cut
   built from one `low_shelf` argument at one frequency — T1 and T3 are not
   merely unimplemented, they are unrepresentable in the constructor's shape.

*(from §7)*

3. **`check_hz()` refuses instead of clamping** (`eq.py:48`, `:54`; the raise at
   `_core.py:471-474`). Tier 1 says clamp, "never refused at construction or at
   `set_macro`": at 22.05 kHz a 16 kHz shelf must become a clamped shelf.

*(from §7)*

5. **The empty-EQ passthrough returns the source itself** (`eq.py:59-60`), and
   both `deinit()` (`_core.py:380`) and `reset()` (`_core.py:368`) skip when
   `output is self._source` — so the two paths through this class behave
   differently under the contract's own methods. The rebuild enumerates the
   nodes it built and walks that list (roadmap §3).

*(from §7)*

6. **Constructing an effect mutates module-wide state**: `Effect.__new__` calls
   `configure(source_rate, source_channels)` (`_core.py:149-152`), so building
   one EQ at 44.1 kHz re-points every class built afterwards.

*(from the header, replaced 2026-09-07 — the seed's grade paragraph, verbatim)*

**Grade:** **literature.** S1 states the factory schematics are not public.
What was reached: a peer-reviewed white-box model validated against LTspice and
a lab measurement of the 2019 reissue (S1, S2), a JAES paper defining the Q laws
(S3), two panel sources (S6, S7). *Audit corrections, 2026-09-06:* **two**
hobbyist redraws **with component values** were reached and read — **S9**
(`jbb.ru`, over http, this seed having recorded it as not reached on an https
certificate error) and, in the second audit pass, **S8**'s linked drawing
(Gyraf's own reverse-engineering, which this seed had written off as "nothing
usable" without opening it; S1 cites it as one of its four references). They
agree on all four pot resistances and on the two-capacitor-bank low section, and
disagree on the selector lists (§1). Neither is attributed to a factory drawing
and neither carries a SPICE model or an analytic derivation of the traits, so
the grade stays **literature** under vision §4.1 — and the named path to a
circuit grade is now a netlist written from the parts S8 and S9 agree on,
simulated the way `tools/spice/ts808/` already does.

*(from §1, moved 2026-09-07 — the selector-list and maximum-gain disputes)*

The three selector lists are corroborated by S6, S7 and — added by the audit —
by **S8's drawing**, whose LO FREQ selector carries exactly four positions,
20/30/60/100 Hz, and whose HI-CUT carries exactly three, 5/10/20 kHz; S9's
redraw carries six low-frequency and six high-cut positions instead, so it is
the variant drawing, now two independent sources against it. S8 in turn places
its HF-boost sixth position at 6 kHz where S6, S7 and S9 all give 8 kHz — every
hobbyist redraw of this unit disagrees with the others somewhere, which is why
the selector lists in §1 are stated from the panel descriptions rather than from
any one drawing. The maximum-gain figures do **not** agree across sources
either — S1 gives 16/20/20 dB where S6 gives 13.5/17.5/16 dB and S9 marks every
pot ±16 dB — and this dossier does not resolve it.

*(from §1, moved 2026-09-07 — S5's own proportional-Q figures)*

S5's reading of the API 550A: three switched bands, five frequencies each; "a
2 dB boost at 200 Hz reaching 0.1×f₀ to 10×f₀". Bohn's word for the law is
*conventional*, not *proportional*; the latter is S5's and API's (App. S).

*(from §2, moved 2026-09-07)*

The §2 table's "what it gave" column now lives only in **App. S**, where it was
already carried in full. §2 keeps every source id, its licence call, its URL and
its reached / not-reached call — the gate conditions.

*(from §6, replaced 2026-09-07 — the seed's proposed surface, verbatim)*

Sixteen macros, at the ceiling. Ranges are engineering spans; the host sees
0–127. 0 `Low Freq` UNIPOLAR 20–200 Hz log (LOW FREQUENCY selector) · 1 `Low
Boost` UNIPOLAR 0…+16 dB (BOOST) · 2 `Low Atten` UNIPOLAR 0…−20 dB (ATTEN) ·
3,5,7 `Bell 1–3 Freq` UNIPOLAR 20 Hz–20 kHz log · 4,6,8 `Bell 1–3 Gain` BIPOLAR
±16 dB · 9 `Bandwidth` UNIPOLAR broad…sharp · 10 `High Freq` UNIPOLAR 3–16 kHz
log · 11 `High Boost` UNIPOLAR 0…+18 dB · 12 `Atten Freq` UNIPOLAR 5/10/20 kHz
stepped · 13 `High Atten` UNIPOLAR 0…−20 dB · 14 `Q Law` TOGGLE proportional |
constant · 15 `Output` BIPOLAR ±12 dB. "Constructor options stay as expressive
as today so local code can build an arbitrary section list; the sixteen are the
host-facing surface." The rebuild kept every index, mode and generalization and
changed only the **unit** of macros 1, 2, 9, 11 and 13 — from a decibel span to
the panel's own 0–10 dial — and stated the taper behind each (§6).

*(from §6, moved 2026-09-07 — the taper's arithmetic)*

`16·√(2.5/10)` = 8.0 dB against `20·(2.5/10)` = 5.0 dB, which measures
+2.48 dB at 30 Hz, a −4.47 dB minimum at 144.4 Hz and 0.042 dB of deviation
above 1 kHz — T1's three thresholds, at all three rates. The linear search that
found no passing alternative was over corner ratios 3/4/5/6/8, boost shelf Qs
0.5/0.707/0.9/1.2/1.6/2.0 and cut shelf Qs 0.4/0.5/0.707/0.9/1.2/1.6/2.0 at
+4/−5 dB (dial 2.5 on a linear pair): zero of the 210 combinations reach
≥ +2.0 dB at 30 Hz with a ≤ −1.0 dB minimum inside 100–400 Hz.

*(from §8, replaced 2026-09-07 — the seed's four open questions, verbatim)*

1. **audioif#23's one answer** — tail gate, float node, or recorded
   disconfirmation. *Gate 0*, once, for the whole EQ family and the Phaser; §5
   states this seed's recommendation.
2. **The proportional-Q skirt level**, the law's one design constant
   (Appendix A): 0.1 dB reproduces API's prose most closely, 1 dB behaves better
   when three bells overlap. *Implementation session, Phase 2*, decided against
   T4's threshold rather than argued.
3. **Whether `Bandwidth` drives the bells too or only the HF bell.** One knob is
   cheaper and less honest. *Implementation session.*
4. **Two sources exist and could not be read here** (Appendix D) — the manual
   scan needs OCR, the API PDF a working certificate chain. T3 and T4 carry
   medium confidence because of it, and after the trait-critic pass **T3's width
   half carries low confidence and is marked ours**. Either of the two unread
   sources would settle it. Not a blocker.

Questions 1, 2 and 3 are settled in §8; question 4 is still open.
