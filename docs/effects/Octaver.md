# Effects Dossier — `Octaver` (Boss OC-2 Octave)

**Class:** `lib/audioeffects/pitch.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Pitch, roadmap Phase 6
**Standout:** Boss OC-2 Octave — **confirmed**, and the mechanism question the
vision left open (§4.2, §10.5) is **answered: a divider, not a shifter**, and
more precisely a *synchronous multiplier* clocked by a flip-flop divider, not
a square-wave oscillator. §5 carries the measurement that rules the shifter
out.
**Grade:** circuit — a factory drawing with component values read (S2), plus
the published analysis of the topology it uses (S5) and an analytic
derivation of the two output filters (appendix A1).
**Portability tier:** needs audioif-own nodes (`audioroute.Splitter`,
`audiomath.Multiply`, **and one new node** — §5)
**Status:** seed (Phase 0)

## 1. The circuit, in one paragraph

Three knobs: DIRECT LEVEL, OCTAVE 1, OCTAVE 2 (S1). The input meets a
2SK30ATM-Y JFET buffer through 10 kΩ and 0.022 µF, giving the 1 MΩ input
impedance of the spec sheet, then a preamp (IC1, R6 2.7 kΩ / R7 10 kΩ) that
fans three ways (S2). **Direct** leaves the preamp's output for VR3 100 kB on
the output bus; C24 1 µF couples that same output into the octave legs; and a
third branch leaves the same node downward for the clock leg's low-pass
*(audit correction 1, §2)*. **The clock leg** goes into a multi-pole low-pass
— R8 22 kΩ, R9 330 kΩ, C21 0.01 µF, C5 0.0022 µF, R5 330 kΩ, C4 220 pF, then
R10/R32 33 kΩ, C18 0.01 µF, C20 330 pF, R31 68 kΩ — because, as an OC-2
rebuild describes it, "the high frequency range of the input sound is cut with
a low-pass filter to create a square wave with the pitch (frequency) of the
original sound" (S3); two diode-clamped comparator legs (D6/D7 with R33 10
kΩ/R34 1 kΩ into IC2, D8/D9 with R38/R37 into IC3) square what comes out, and
of the chain as a whole S4 says "IC1/IC2/IC3/IC7/IC6 buffer, boost and 'square
up' the incoming signal then divide the fundamental of the incoming frequency
by 2 and by 4" — the dividing itself being IC7 (µPD4013C dual D-type) and IC6
(BA634 single T-type) *(audit correction 2, §2)*. **The octave legs** are
where the sound actually is. For OCT1, R44 and R45 (47 kΩ each) feed IC5's
inverting (pin 6) and non-inverting (pin 5) inputs with R43 27 kΩ in the
feedback, a 1S-188FM germanium diode D10 **shunts the stage's input node** —
the node C24 lands on, ahead of R44/R45 — to the bias rail, R49 100 kΩ sits on
the non-inverting node, and a 2SK30 JFET Q8 switches that non-inverting node
to the same rail, its gate driven from the flip-flop through R47 1 MΩ with R48
1 MΩ to the rail *(audit correction 3, §2)* — so the stage's gain flips
between its non-inverting and inverting values in step with a square at half
the input's frequency. That is a **multiplication**, and its output is
filtered by a two-pole low-pass (R42 22 kΩ, R41 and R40 330 kΩ, C26 0.0047 µF,
C27 470 pF) before VR1. OCT2 repeats the pattern (R53/R54 47 kΩ, R55 27 kΩ,
germanium D11 on its input node, R52 100 kΩ on the non-inverting node, Q7 with
R50 1 MΩ / R51 1 MΩ, then R56 22 kΩ, R57/R58 330 kΩ, C32 0.047 µF, C34 0.001
µF, VR2) with two differences: its capacitors are ten times larger, putting
its corner about two octaves lower (A1); and **its input is OCT1's output, not
the dry signal** — "IC5a (pins 1/2/3) mixes the signal coming out of OCT1 and
the 1/4 frequency square wave from the flip-flops" (S4), which the drawing
confirms. Stompboxology draws this stage as the second of its two "indirect
divider circuits" — its Fig. 4 circuit 2 carries the same germanium diode on
the input node, the same 2R to the bias rail and the same FET on the 1 M gate
resistor, which is the independent confirmation of the paragraph above — and
says the indirect approaches "track input dynamics and sound much smoother
than squarewaves" (S5, quoted in full in A0). Its sum-and-difference
derivation belongs to the *other* variant, which is where O2's law comes from
*(audit correction 4, §2 and O2)*. The pedal is monophonic in use — S3's
author "actually play[s] single notes through this pedal" and names polyphony
as the digital OC-3's trick, not this circuit's, which is as close to a stated
limit as the source comes — and it is rated down to a "Minimum operating input
level: −60 dBm at 250 Hz" (S4). Its real design problem is tracking: S5's own
text on octave skipping says "Preamp gain, filter type and slope, and
comparator sensitivity all figure in the process", and "one filter won't
render the whole fretboard skip-free."

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 Boss, *OC-2 Octave* owner's manual … (App. S1) | "Controls … Pedal Switch, OCTAVE 1 Knob … (App. S1) | Boss/Roland manual scan … (App. S1) | inside S4's PDF (images `Im59` spec, `Im54` setting examples) | 2026-09-06; **re-extracted and re-read in the audit**. Note the −60 dBm/250 Hz minimum-input figure quoted in §1 is **not** on this spec page: it comes from S4's own article text (see S4) |
| S2 **Factory OC-2 schematic**, one page of S4's PDF, read as an image | Every value quoted in §1 and A1 … (App. S2) | Roland/Boss drawing … (App. S2) | inside S4's PDF (image `Im4`, 1085×673) | 2026-09-06; **re-extracted and re-read in the audit** at 3–9× zoom. Every value quoted in §1 and A1 was confirmed on the drawing; three topology claims were not, and are corrected in §1 (the direct path's coupling cap, D10's node, and Q8's gate resistors) |
| S3 Toshi, "Self-made BOSS Octaver OC-2 MOD using CMOS flip-flop" | The low-pass-then-square account … (App. S3) | "Copyright(c) 2022 Toshi All Rights Reserved" | https://toshi.life.coocan.jp/review/en_diy_analog_octaver.html | 2026-09-06; re-fetched in the audit and read in full; all quotations confirmed verbatim. The page documents the author's **OC-2 MOD** build, so it is a description of the OC-2 circuit, not of a stock unit |
| S4 championleccy.com, "Boss OC-2 Octave guitar pedal schematic diagram" … (App. S4) | The semiconductor list (IC1–IC5 TL022CP, IC6 BA634 … (App. S4) | No licence statement in or on the file … (App. S4) | https://championleccy.com/wp-content/uploads/2018/01/boss_octave_oc2_guitar_effect_pedal_sch.pdf | 2026-09-06; **re-fetched in the audit** (HTTP 200, 16 pages, 20 images), unreadable to WebFetch, text and images extracted locally with `pypdf` + Pillow |
| S5 *Stompboxology* Vol. 13 No. 3 … (App. S5) | The two indirect-divider variants drawn (Fig. 4) … (App. S5) | Copyrighted newsletter page (masthead … (App. S5) | inside S4's PDF (image `Im73`, 2166×3082) | 2026-09-06; **re-extracted and re-read in the audit** in four slices; the Fig. 4 caption and the octave-skipping paragraph confirmed verbatim, and the variant attribution corrected in §1 and O2 |
| S6 mirosol, "Boss OC-2 Octave" | Independent confirmation of the two-flip-flop divider … (App. S6) | "© 2026 killall -9 humans"; no open licence | https://mirosol.kapsi.fi/2014/08/boss-oc-2-octave/ | 2026-09-06; re-fetched in the audit — "We have three knobs which control the levels of clean, buffered signal, one octave down and two octaves down" and "The two octaves down are using two channels of the flip-flops and the one down is using one" confirmed. The unit it examines is a later (2001) revision with "two CD4013 chips" rather than the drawing's BA634 + µPD4013C |

**Reachability, corrected in the audit (2026-09-06).** Two of the three
sources the seed recorded as not reached were reached this run:

- **hobby-hour.com's OC-2 page** …  *(argument in full: App. R)*
- **schematicheaven's OC-2 PDF** …  *(argument in full: App. R)*
- **electrosmash's archive mirror** (https://electrosmash.mas-effects.com/) — …  *(argument in full: App. R)*

1. **C24 is not in the direct path.** R44 and R45 hang on C24's far node, so
   C24 is the octave legs' coupling cap; the direct branch leaves the preamp's
   output ahead of it.
2. **"buffer, boost and 'square up' … divide … by 2 and by 4" names five
   ICs** in S4 — "IC1/IC2/IC3/IC7/IC6" — not IC7 and IC6 alone.
3. **D10 does not sit on the non-inverting node.** It shunts the chopper's …  *(argument in full: App. R)*
4. **The sum-and-difference derivation is Fig. 4 circuit 1's**, the plain …  *(argument in full: App. R)*

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| O1 | The octave is the input **multiplied** by a ±square, not a synthesised tone: its level follows the input's envelope with no attack or release of its own, tracking a 40 dB decay — from the pedal's nominal −20 dBm input down to its stated −60 dBm floor — to within **2 dB**, once the first 20 ms window is discarded for the output filter's own ring-down (≈3/f_corner = 9 ms at A1's OCT1 corner) and with the `Gate` macro at its lowest setting so the divider never holds | S5 ("track input dynamics") … (App. O1) | high | An octave whose level is flat while the input decays; any envelope-follower character (attack or release time) in the octave path; a tracking error that grows monotonically through the decay, which is a follower's release showing | Exponentially decaying 220 Hz … (App. O1) |
| O2 | With the output filter defeated, a steady sine at *f* gives **two dominant product lines, at f/2 and 3f/2**, both phase-locked to the input. The ideal synchronous multiplication of a sine by a ±1 square at f/2 puts 3f/2 exactly **4.44 dB** below f/2 — the same figure whether the square switches on the input's zero crossings (S5's circuit 1) or on its peaks (S5's rule for circuit 2), derived in A4 — and the rebuilt stage must land within **±3 dB** of that, i.e. 3f/2 between 1.4 and 7.4 dB below f/2 | S5 Fig. 4's caption gives the … (App. O2) | medium — the analogy … (App. O2) | No 3f/2 component (a synthesised square, not a product); f/2 dominant even with the filter defeated; a component at f/2 that is not phase-locked to the input; a 3f/2 that is *above* f/2, which no multiplication of this kind gives | 65 536-pt Hann STFT of a steady … (App. O2) |
| O3 | **OCT2 is derived from OCT1's output, not from the dry input**: with OCT1's chopper stalled, OCT2 is silent, and OCT2's timbre carries OCT1's output filter as well as its own | S4 ("IC5a … mixes the signal coming out of … (App. O3) | high | An OCT2 that survives OCT1's stage being stalled; an OCT2 whose spectrum shows none of OCT1's filter | Null OCT1's modulator … (App. O3) |
| O4 | The two output filters are **not the same filter**: OCT2's corner is about two octaves below OCT1's (our arithmetic from S2's values gives ≈ 324 Hz and ≈ 70 Hz, A1), so at the same input note OCT2 is measurably darker than OCT1 transposed | S2 values; A1 arithmetic | medium — which … (App. O4) | Two output filters with the same corner; an OCT2/OCT1 corner ratio outside 2–8× | Swept sine through each octave … (App. O4) |
| O5 | The whole chain is **zero-latency**: comparator, flip-flop and multiplier are all causal per sample, so a click's dry and octave components both arrive at offset 0, and the octave's *pitch* is simply undefined until the divider has seen two zero crossings — one input period, not a buffer | S2 (the topology) … (App. O5) | high | Any offset between the dry and octave arrivals; an octave that is correct from the first sample (which would mean a look-ahead) | Click at 48 kHz and 44.1 kHz: dry … (App. O5) |
| O6 | The output low-pass is what makes f/2 dominant, and its discrimination is **note-dependent and bounded**: it is a two-pole (A1) and 3f/2 is exactly three times f/2, so the most it can ever put between them is 20·log₁₀(3²) = **19.1 dB**, approached only when f/2 sits well above the corner, and it falls toward 0 dB as the played note falls below it. The class states, for its shipped `Tone 1` corner, the note above which the rejection exceeds 12 dB and the note below which it is under 3 dB | A1's two-pole reading of S2's values (R41 = … (App. O6) | medium — the filter's … (App. O6) | A rejection above 19.1 dB at any note, which a two-pole cannot give; a rejection that does not change with the played note; a rejection at the top of the sweep no larger than at the bottom (stated at the endpoints rather than as monotonicity, because a resonant two-pole need not be monotone near its own corner and A1 could not read the Q) | Sweep the input note E1–E5 … (App. O6) |

Characters: none. OCT1 and OCT2 are two outputs of one circuit, not two
characters — O3 is precisely the statement that they are not independent.

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

```
source ─ Splitter A(taps=4) ┬ tap 0 ─────────────────────────────────────────► Mixer.voice[0]  direct
                            ├ tap 1 ─ Filter(LP, Tracking) ─ SubOctave(1) ─┐
                            ├ tap 2 ─ Filter(LP, Tracking) ─ SubOctave(2) ─│─┐
                            └ tap 3 ───────────────────────────────────────┤ │
                                             Multiply(tap 3, ÷2) ─ Filter(LP, Tone 1) ─ Splitter B(taps=2)
                                                                                        ├ tap 0 ─────────► Mixer.voice[1]  OCT 1
                                                                                        └ tap 1 ─ Multiply(·, ÷4) ─ Filter(LP, Tone 2) ─► Mixer.voice[2]  OCT 2
```

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

### `audiomath.SubOctave` — the flip-flop divider

- **Traits it unblocks:** O1, O2, O3, O5 and O6 — that is, all of them.
  Without a divider there is no octave of the OC-2's kind at all, and with no
  f/2 line there is nothing for O6's filter to discriminate.
- **What the palette does instead, and the measurement that shows it fails.**
  The substitute is `audiodelays.PitchShift` at −12 semitones, which is what
  the class does today (`pitch.py:86`, `:105-106`). Measured (A3): the output
  is a comb spaced 46.9 Hz whose dominant line is **205.08 Hz**, not 220 —
  **−121.6 cents** — and the wet path is delayed by up to **10.7 ms**. That
  fails O5 outright (latency where the circuit has none), fails O2 (a splice
  comb, not a sum-and-difference pair, with no 3f/2 product to filter) and
  fails O1 (the level follows the input but the *content* is a re-read of it,
  so a decaying note's octave decays with the window, not the note). A
  granular shifter is a different effect that happens to land an octave down.
- **Why no composition reaches it — the refutation, rewritten and measured
  (palette verifier, 2026-09-06).** The seed's original argument rested on
  *"no member of the palette is nonlinear **and** stateful"*, and that premise
  is **false**, so it is withdrawn: `audioecho.FeedbackDelay` carries an
  odd-cubic `soft_clip()` **inside** its feedback loop
  (`audioif_feedback_delay.c:177-184`, applied at `:241-243`) with an int16
  saturating write to the line at `:255-256`, and `audiodynamics.Dynamics`
  is a level-dependent gain driven by an attack/release envelope it remembers
  between blocks (`audioif_dynamics.c:124-127`; the coefficients at
  `audioif_dynamics.h:68-69`). Both are nonlinear and stateful. The
  conclusion survives the premise, on measurement rather than on assertion.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | `Direct` | UNIPOLAR | −∞ … 0 dB | DIRECT LEVEL (VR3) |
| 1 | `Octave 1` | UNIPOLAR | −∞ … 0 dB | OCTAVE 1 (VR1) |
| 2 | `Octave 2` | UNIPOLAR | −∞ … 0 dB | OCTAVE 2 (VR2) |
| 3 | `Tracking` | UNIPOLAR | 80 … 800 Hz | the clock leg's low-pass corner — the knob the OC-2 does not have and every player wishes it did (S5: "one filter won't render the whole fretboard skip-free") |
| 4 | `Tone 1` | UNIPOLAR | 100 … 2000 Hz | OCT1's output filter corner (≈324 Hz on the pedal, A1) |
| 5 | `Tone 2` | UNIPOLAR | 40 … 800 Hz | OCT2's output filter corner (≈70 Hz, A1) |
| 6 | `Gate` | UNIPOLAR | −70 … −30 dBFS | the level below which the divider holds; the pedal's own floor is −60 dBm at 250 Hz (S4) |

Characters: none. Patches, named after the OC-2 manual's own four setting
examples (S1) without borrowing its words: 0 *Octave down under the dry*
(constructor defaults) · 1 *Guitar with a bass under it* · 2 *Fat riff, both
octaves* · 3 *Synth-like, direct down* · 4 *For a bass guitar — low tracking* ·
5 *Two octaves only, no direct* · 6 *Wide tracking for high notes*.

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/pitch.py`.

- `pitch.py:105-106` — the class is **four pitch shifters**. The standout has …  *(argument in full: App. R)*
- `pitch.py:84-85` — the comment "Shorter windows track faster, which matters …  *(argument in full: App. R)*
- `pitch.py:86-87` — two of the four branches shift **up**, which the OC-2 …  *(argument in full: App. R)*
- `pitch.py:79` — `MACRO_LABELS = ()`. Four levels are constructor-only, so a …  *(argument in full: App. R)*
- `pitch.py:89` — the branch is built only if its level is `> 0.0`, so a level …  *(argument in full: App. R)*
- `_core.py:140-141` — `LATENCY_SAMPLES = 0` inherited, which is *accidentally* …  *(argument in full: App. R)*
- `pitch.py:92-96` raises when more octaves are asked for than the Splitter can …  *(argument in full: App. R)*

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **The two output-filter corners.** A1's ≈324 Hz and ≈70 Hz come from our
   arithmetic on a drawing read as an image, and depend on which capacitor
   pair sets each pole. Station A writes the netlist under
   `audiocomponents/tools/spice/oc2/` and settles it the way the TS808 run
   settled the Overdrive's corner — including whether the germanium diode's
   half-wave clamp changes the effective corner the way the TS808's diodes
   changed its plateau gain. *(Phase 6, or earlier if the survey has room.)*
2. **An octave up.** The current class offers one; the standout does not. The
   honest mechanism is a frequency doubler — squaring, which the palette can
   do today with `Multiply` fed two taps of the same source, then a high-pass
   to drop the DC term — and its own standout would be a full-wave-rectifier
   octave-up fuzz, **not researched in this run**. It is deliberately absent
   from §6 rather than shipped with no trait behind it. *(Phase 0 survey to
   decide whether it earns a source hunt; Phase 6 to build or drop it.)*
3. **Tracking on a chord.** The pedal is monophonic (S3) and so is the
   rebuild. The docstring must say it in the player's terms — one note at a
   time, the lower the better — rather than let a user discover it, and the
   evidence pack carries one measured sentence on what the divider does to a
   chord. *(Phase 6.)*
4. **Where `SubOctave` lives.** `audiomath` is proposed because the node's
   output is a modulator for `Multiply` and the two are always used together.
   A reviewer may prefer a new module. *(Gate 0, with the node list.)*
5. **The Splitter's ring is 64 kB of this class.** `AUDIOIF_SPLITTER_RING_FRAMES`
   is a fixed 8192 frames (`audioif_splitter.h:20`), 32 kB stereo per Splitter,
   and §4 needs two — far more than a lockstep fan-out requires, since every
   branch here is pulled in the same block. A constructor-time ring size on
   `audioroute.Splitter` would cut this class's RAM by an order of magnitude
   and would help every parallel class in the library. It is **not raised as
   an ask here**, because no Tier 2 trait is blocked by it and vision §6 says
   asks need a blocked trait; it is recorded so the survey can weigh it across
   all the parallel classes at once, where the case may be stronger.
   *(Phase 0 survey, as a cross-class note.)*


## Appendix

### A0 — what Stompboxology actually says (S5, Fig. 4 caption and text)

On the two indirect divider stages the OC-2 uses: *"Op amp configured as a
synchronous detector whose output equals sum and difference of inputs. If
input is a sinewave of frequency x, and FET is toggled by a squarewave at a
rate equal to 1/2x, then output contains [(x − 1/2x) = 1/2x] — i.e., a signal
an octave below x — and [(x + 1/2x) = 3/2x]; also, many high harmonics of
squarewave, but these are relatively easy to filter. Proper circuit function
calls for squarewave transitions to coincide with sinewave zero-crossing
points."* And of the second variant, the one drawn with the germanium diode
and the FET: *"Strategy is to slice, invert, scale, and apply a DC offset to
the wave, which reassembles into a physical approximation of a tone one octave
below the fundamental. Control transitions must coincide with sinewave peaks.
Both approaches are more complicated than dividing the output of a
sine-to-square converter, but track input dynamics and sound much smoother
than squarewaves."* On tracking: *"This exercise demonstrates that octave
skipping involves interactive variables, and shows why one filter won't render
the whole fretboard skip-free. Preamp gain, filter type and slope, and
comparator sensitivity all figure in the process."* The same page's Fig. 6
block diagram of a "basic direct-divider box for guitar" runs preamp →
lowpass filter → sine-to-square converter → ÷2 → ÷2 → gate or expander (fed by
an audio level detector) → output filter → mixer with the dry signal — the
block-level shape §4 builds, with `SubOctave`'s `gate` standing in for the
gate/expander.

### A1 — the two output filters, from S2's values

Both octave stages end in an active two-pole low-pass around a TL022 section
with two 330 kΩ resistors and two capacitors. Treating them as an equal-R
two-pole with f₀ = 1 / (2π·R·√(C₁C₂)):

- **OCT1** — R41 = R40 = 330 kΩ, C26 = 0.0047 µF, C27 = 470 pF:
  √(4.7 nF · 470 pF) = 1.486 nF, f₀ = **324 Hz**.
- **OCT2** — R57 = R58 = 330 kΩ, C32 = 0.047 µF, C34 = 0.001 µF:
  √(47 nF · 1 nF) = 6.856 nF, f₀ = **70.3 Hz**.

Ratio 4.6, i.e. 2.2 octaves — which is why O4 says "about two octaves" and not
a number. **Audit cross-check (2026-09-06):** Stellan Lehrberg's independent
redraw, reached this run inside schematicheaven's PDF (§2), agrees on
330 kΩ/330 kΩ, on OCT1's 4.7 nF and on OCT2's 47 nF/1 nF, but reads OCT1's
small capacitor as **220 pF**, which gives √(4.7 nF · 220 pF) = 1.017 nF and
f₀ = **474 Hz**, and a ratio of 6.7 (2.75 octaves). The factory drawing's
"C27 470p" is legible at 5× and is what this dossier keeps; the disagreement
is one more thing for the netlist to settle. Two further caveats, both real:
the third capacitor in each group (C28 0.022 µF on OCT1, C31 0.01 µF on
OCT2) is read as a coupling cap and is not in
the arithmetic, and the exact topology (Sallen-Key or multiple-feedback) is not
legible at the resolution reached. That is precisely the disagreement the
TS808 proof showed SPICE settling, and §8.1 sends it there. Every value above
was re-read off the drawing at 5× in the audit and confirmed; what is in doubt
is not the reading but the 470 pF/220 pF disagreement between the two
drawings.

### A4 — the 4.44 dB, derived (trait-critic pass, 2026-09-06)

S5's caption for circuit 1 gives the products of a sine at *x* against a square
at *x*/2 as (x − x/2) and (x + x/2), "also, many high harmonics of squarewave".
Writing θ = πft so the input is sin 2θ and the square is the odd series
(4/π)·Σ_{k odd} sin(kθ)/k, and using sin 2θ·sin kθ = ½[cos((2−k)θ) −
cos((2+k)θ)]:

- k = 1 contributes +2/π at θ (= f/2) and −2/π at 3θ (= 3f/2)
- k = 3 contributes +2/(3π) at θ and −2/(3π) at 5θ
- k = 5 contributes +2/(5π) at 3θ and −2/(5π) at 7θ

so |f/2| = (2/π)(1 + 1/3) = 0.8488 and |3f/2| = (2/π)(1 − 1/5) = 0.5093 — a
ratio of 5/3, **4.44 dB**. Switching on the peaks instead of the zero
crossings (S5's rule for circuit 2) replaces the sine series with the cosine
one and changes only signs, so the ratio is identical. Confirmed numerically
as well as analytically on this machine with
`audiocomponents/.venv/bin/python`: a 220 Hz sine multiplied by a ±1 square at
110 Hz, 4 s at 192 kHz, Hann-windowed FFT, reads **4.44 dB** for both
switching phases and puts 5f/2 at −16.9 dB re f/2.

This is the *ideal* multiplication only. The OC-2's own stage half-wave clamps
the input through a germanium diode first (S5 circuit 2; S2's D10), which this
derivation does not model — which is why O2 carries a ±3 dB window and calls a
value outside it a disconfirmation rather than a failure, and why §8.1 sends
the question to the netlist.

The same arithmetic bounds the filter's job (O6): 3f/2 is three times f/2, so
a two-pole low-pass whose corner sits below both lines separates them by at
most 20·log₁₀(3²) = 19.1 dB, and a one-pole by 20·log₁₀(3) = 9.5 dB. Neither
figure depends on the filter's Q, which A1 could not read off the drawing.

### A2 — the current class, rendered

`Octaver()` with its constructor defaults (`down=0.5`, everything else 0),
one full-scale click at frame 64 of an 8000-frame stereo source, 48 kHz:

```
L: (64, 20000)   (192, 10000)   (193, 10000)
```

The dry click is at 64 at full scale; the "octave" is two samples at half
scale at **192**, i.e. 128 frames (2.67 ms) later, and it is not an octave of
anything — it is the click re-read through the shifter's window. `Octaver`
reports `latency_samples` 0 while doing that (`_core.py:140`).

### A3 — the substitute measured (the numbers §5 rests on)

`audiodelays.PitchShift(semitones=−12, mix=1, window=2048, overlap=128)`,
440 Hz sine at 48 kHz, 32 768-point Hann STFT:

| quantity | measured | ideal |
|---|---|---|
| dominant line | 205.08 Hz | 220.00 Hz |
| error | **−121.6 cents** | 0 |
| sideband spacing | 46.9 Hz | none |
| wet-path delay | 32 … 512 frames (0.67 … 10.7 ms) | 0 |

The comb spacing matches f_s·|r−1|/W = 48000 × 0.5 / 512 exactly. The −121.6
cents is the splice-quantisation effect characterised in `PitchShifter.md` T4
and A2, and it is not a tuning bug to be fixed — it is what a fixed-window
splicing shifter does. Which is the whole argument for a divider.

### A5 — seven compositions asked for f/2, and none produced one

Palette verifier, 2026-09-06, `audiocomponents/.venv/bin/python`, 48 kHz
16-bit stereo, `buffer_size` 2048. Probe: 220 Hz sine at 20 000 peak, 32 768
frames, first 4 096 frames discarded. Levels are the Goertzel magnitude at
110 Hz on the settled left channel, in dB relative to the input's 20 000.

| Composition | f/2 (110 Hz) |
|---|---|
| `Distortion` CLIP, drive 0.9, pre-gain +12 dB | −47.0 dB |
| `Distortion` WAVESHAPE, drive 0.99, pre-gain +24 dB | −43.5 dB |
| `FeedbackDelay`, delay 2/f, feedback 0.99, `loop_drive` 1.0 | −47.7 dB |
| `FeedbackDelay`, delay 1/f, same | −47.5 dB |
| `FeedbackDelay`, delay 3/f, same | −47.5 dB |
| `Dynamics` compress 20:1, attack 0.1 ms, release 1 ms | −82.7 dB |
| `Multiply(x, x delayed one input period)` | −47.5 dB |
| the same `Multiply` fed a hard-clipped square instead of the sine | −42.5 dB |

The −42 to −48 dB band is the analyser's leakage floor on this probe (220 Hz
is not bin-aligned in the window), not a signal: the `Dynamics` row, whose
output is quiet enough that leakage falls with it, reads −82.7 dB. Every node
was confirmed to be doing something — output peaks ran 439 to 32 767 — so
these are not silent-render passes, the failure mode `workspace-craft.md`
names. Nothing in the palette halves a frequency, and the three `FeedbackDelay`
rows are the specific test that its in-loop cubic does not period-double even
when the line is tuned to the period that would be needed.

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

Rate note: every corner in this class is a Hz value clamped below Nyquist, and
the divider is a zero-crossing counter, so nothing here is rate-limited. At
22.05 kHz the output filters' corners (A1) are far below Nyquist and O2's
harmonic products fold less, not more.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 Boss, *OC-2 Octave* owner's manual, SPECIFICATIONS and SETTING EXAMPLES pages (scanned into S4) | "Controls … Pedal Switch, OCTAVE 1 Knob, OCTAVE 2 Knob, DIRECT LEVEL Knob"; Nominal Input **and** Output Level −20 dBm; Input Impedance 1 MΩ; "Equivalent Input Noise Level … −100 dBm (IHF-A Weighted, Typ.)"; Current Draw 4 mA; four named setting examples ("To simulate unison play of guitar and bass", "For fat guitar riffs", "To simulate a guitar synthesizer", "For bass guitar") | Boss/Roland manual scan; no licence statement in the file — treated as all rights reserved. Read as a document | inside S4's PDF (images `Im59` spec, `Im54` setting examples) | 2026-09-06; **re-extracted and re-read in the audit**. Note the −60 dBm/250 Hz minimum-input figure quoted in §1 is **not** on this spec page: it comes from S4's own article text (see S4) |
| S2 **Factory OC-2 schematic**, one page of S4's PDF, read as an image | Every value quoted in §1 and A1; the three-way fan-out; the JFET choppers with germanium diodes; the two output filters; OCT2 fed from OCT1 | Roland/Boss drawing; no licence statement. A schematic is a document (vision §5): read for topology and values, nothing reproduced | inside S4's PDF (image `Im4`, 1085×673) | 2026-09-06; **re-extracted and re-read in the audit** at 3–9× zoom. Every value quoted in §1 and A1 was confirmed on the drawing; three topology claims were not, and are corrected in §1 (the direct path's coupling cap, D10's node, and Q8's gate resistors) |
| S3 Toshi, "Self-made BOSS Octaver OC-2 MOD using CMOS flip-flop" | The low-pass-then-square account; "divided into 1/2 and 1/4 using a CMOS flip-flop"; "the input tones half-wave rectified by the germanium diode are multiplied by the op amp's circuit … the half-wave rectified tone is inverted every other wave and converted into a signal with twice the wavelength". **Not** a stated monophony limit: the page contrasts the digital OC-3, which "can be used with chords with multiple notes", with this analog build, and its author "actually play[s] single notes through this pedal" | "Copyright(c) 2022 Toshi All Rights Reserved" | https://toshi.life.coocan.jp/review/en_diy_analog_octaver.html | 2026-09-06; re-fetched in the audit and read in full; all quotations confirmed verbatim. The page documents the author's **OC-2 MOD** build, so it is a description of the OC-2 circuit, not of a stock unit |
| S4 championleccy.com, "Boss OC-2 Octave guitar pedal schematic diagram" (PDF compilation) | The semiconductor list (IC1–IC5 TL022CP, IC6 BA634, IC7 µPD4013C, D10/D11 1S-188FM germanium); the spec table; the stage-by-stage text, including OCT2 fed from OCT1; the manual scans; the factory drawing | No licence statement in or on the file, and championleccy.com's own Terms and Conditions page (checked in the audit) carries none either — a compilation of third-party scans, treated as all rights reserved. Read as a document. **Chain chased (audit):** the PDF's page-1 spec list and semiconductor list are word-for-word the text of hobby-hour.com's OC-2 article, including its "−60dBm al 250Hz" typo, so that article — not the owner's manual — is the origin of the minimum-input figure | https://championleccy.com/wp-content/uploads/2018/01/boss_octave_oc2_guitar_effect_pedal_sch.pdf | 2026-09-06; **re-fetched in the audit** (HTTP 200, 16 pages, 20 images), unreadable to WebFetch, text and images extracted locally with `pypdf` + Pillow |
| S5 *Stompboxology* Vol. 13 No. 3, "indirect divider circuits" page (Figs. 4–7), scanned into S4 | The two indirect-divider variants drawn (Fig. 4), with the sum-and-difference derivation given for **variant 1** and the "slice, invert, scale, DC offset" account for **variant 2**, which is the OC-2's; Fig. 6's direct-divider block diagram; Fig. 7 and the octave-skipping discussion (quoted in A0) | Copyrighted newsletter page (masthead "Stompboxology Vol. 13, No. 3", p. 3), no licence statement — treated as all rights reserved. Read as a document | inside S4's PDF (image `Im73`, 2166×3082) | 2026-09-06; **re-extracted and re-read in the audit** in four slices; the Fig. 4 caption and the octave-skipping paragraph confirmed verbatim, and the variant attribution corrected in §1 and O2 |
| S6 mirosol, "Boss OC-2 Octave" | Independent confirmation of the two-flip-flop divider and the three level knobs | "© 2026 killall -9 humans"; no open licence | https://mirosol.kapsi.fi/2014/08/boss-oc-2-octave/ | 2026-09-06; re-fetched in the audit — "We have three knobs which control the levels of clean, buffered signal, one octave down and two octaves down" and "The two octaves down are using two channels of the flip-flops and the one down is using one" confirmed. The unit it examines is a later (2001) revision with "two CD4013 chips" rather than the drawing's BA634 + µPD4013C |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| O1 | The octave is the input **multiplied** by a ±square, not a synthesised tone: its level follows the input's envelope with no attack or release of its own, tracking a 40 dB decay — from the pedal's nominal −20 dBm input down to its stated −60 dBm floor — to within **2 dB**, once the first 20 ms window is discarded for the output filter's own ring-down (≈3/f_corner = 9 ms at A1's OCT1 corner) and with the `Gate` macro at its lowest setting so the divider never holds | S5 ("track input dynamics"); S3 ("multiplied by the op amp's circuit"); S2 (the JFET chopper); S1/S4 for the −20 dBm nominal and −60 dBm floor that fix the 40 dB span; **the 2 dB window and the 20 ms discard are this seed's** | high | An octave whose level is flat while the input decays; any envelope-follower character (attack or release time) in the octave path; a tracking error that grows monotonically through the decay, which is a follower's release showing | Exponentially decaying 220 Hz sine over 40 dB; RMS envelope of the OCT1 output against the input's, in 20 ms windows, first window discarded. **Planted fault:** put a 100 ms-release envelope follower on the octave path's gain — the error must exceed 2 dB before the decay ends and the check go red |
| O2 | With the output filter defeated, a steady sine at *f* gives **two dominant product lines, at f/2 and 3f/2**, both phase-locked to the input. The ideal synchronous multiplication of a sine by a ±1 square at f/2 puts 3f/2 exactly **4.44 dB** below f/2 — the same figure whether the square switches on the input's zero crossings (S5's circuit 1) or on its peaks (S5's rule for circuit 2), derived in A4 — and the rebuilt stage must land within **±3 dB** of that, i.e. 3f/2 between 1.4 and 7.4 dB below f/2 | S5 Fig. 4's caption gives the sum-and-difference law for its circuit **1**, not the OC-2's circuit 2 (audit correction): "[(x − 1/2x) = 1/2x] … and [(x + 1/2x) = 3/2x]; also, many high harmonics of squarewave, but these are relatively easy to filter", where of circuit 2 it says only "slice, invert, scale, and apply a DC offset … a physical approximation of a tone one octave below the fundamental". The law is carried across by analogy (both are the same multiplication, differing in the diode and the DC offset); the **4.44 dB is arithmetic on that caption's own formula plus the square's Fourier series (A4), not a number any source states**, and the **±3 dB window is this seed's** | medium — the analogy is ours, and circuit 2's germanium half-wave clamp is expected to move the figure inside the window; a value outside it is a legitimate disconfirmation and an interesting result, not a build failure | No 3f/2 component (a synthesised square, not a product); f/2 dominant even with the filter defeated; a component at f/2 that is not phase-locked to the input; a 3f/2 that is *above* f/2, which no multiplication of this kind gives | 65 536-pt Hann STFT of a steady 220 Hz sine with the filter defeated; levels of the 110 Hz and 330 Hz lines. Phase lock is its own check: move the input to 221 Hz and the lower line must move to 110.5 Hz, not stay put. The strongest line at an *even* multiple of f/2 is reported as the stage's duty/offset asymmetry rather than assumed to be zero — unsourced for the OC-2, and the netlist (§8.1) settles what it should be. **Planted fault:** replace the chopper with a free-running ±1 oscillator at the same nominal frequency — the 3f/2 line goes and the 221 Hz test goes red |
| O3 | **OCT2 is derived from OCT1's output, not from the dry input**: with OCT1's chopper stalled, OCT2 is silent, and OCT2's timbre carries OCT1's output filter as well as its own | S4 ("IC5a … mixes the signal coming out of OCT1 and the 1/4 frequency square wave"); S2 confirms on the drawing | high | An OCT2 that survives OCT1's stage being stalled; an OCT2 whose spectrum shows none of OCT1's filter | Null OCT1's modulator; OCT2 must fall below −80 dBFS. **Planted fault:** re-wire OCT2 from the dry tap — the null test must go red |
| O4 | The two output filters are **not the same filter**: OCT2's corner is about two octaves below OCT1's (our arithmetic from S2's values gives ≈ 324 Hz and ≈ 70 Hz, A1), so at the same input note OCT2 is measurably darker than OCT1 transposed | S2 values; A1 arithmetic | medium — which capacitor pair sets each pole is read from a low-resolution drawing and is settled by the netlist; and the audit's cross-check against Lehrberg's independent redraw (§2) reads OCT1's small cap as 220 pF, which would put that corner at ≈474 Hz instead of ≈324 Hz. The *ratio* claim survives either reading (4.6× or 6.7×) | Two output filters with the same corner; an OCT2/OCT1 corner ratio outside 2–8× | Swept sine through each octave path with its chopper forced to a fixed state, so the path is linear; −3 dB corner of each. Station A writes the netlist and SPICE settles the disagreement, TS808-style |
| O5 | The whole chain is **zero-latency**: comparator, flip-flop and multiplier are all causal per sample, so a click's dry and octave components both arrive at offset 0, and the octave's *pitch* is simply undefined until the divider has seen two zero crossings — one input period, not a buffer | S2 (the topology); S5 Fig. 6 (block diagram, no delay element anywhere) | high | Any offset between the dry and octave arrivals; an octave that is correct from the first sample (which would mean a look-ahead) | Click at 48 kHz and 44.1 kHz: dry and octave onsets both at offset 0. Onset test: gated 110 Hz sine; the octave's first full cycle begins no earlier than 9.1 ms (one input period) after onset |
| O6 | The output low-pass is what makes f/2 dominant, and its discrimination is **note-dependent and bounded**: it is a two-pole (A1) and 3f/2 is exactly three times f/2, so the most it can ever put between them is 20·log₁₀(3²) = **19.1 dB**, approached only when f/2 sits well above the corner, and it falls toward 0 dB as the played note falls below it. The class states, for its shipped `Tone 1` corner, the note above which the rejection exceeds 12 dB and the note below which it is under 3 dB | A1's two-pole reading of S2's values (R41 = R40 = 330 kΩ, C26/C27) and the 3× line spacing O2 fixes; the 19.1 dB ceiling is arithmetic (A4). **The 12 dB and 3 dB reporting points are this seed's** | medium — the filter's order is legible on the drawing but its Q is not (A1 leaves Sallen-Key vs multiple-feedback undetermined), so only the two-pole asymptote is claimed here, never a per-note dB | A rejection above 19.1 dB at any note, which a two-pole cannot give; a rejection that does not change with the played note; a rejection at the top of the sweep no larger than at the bottom (stated at the endpoints rather than as monotonicity, because a resonant two-pole need not be monotone near its own corner and A1 could not read the Q) | Sweep the input note E1–E5 (41.2–659 Hz) with the filter engaged — wide enough to cross both reporting points at the shipped corner; at each note take level(f/2) − level(3f/2) in dB off O2's STFT, plot against note, and compare with the netlist's AC sweep (§8.1). **Planted fault:** build the output filter as one pole instead of two — the ceiling must drop to 20·log₁₀(3) = 9.5 dB and every note above the corner must go red |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

- **hobby-hour.com's OC-2 page**
  (https://www.hobby-hour.com/electronics/s/oc2-octave.php) — HTTP 403 to the
  fetch tool, but **HTTP 200 to `curl` with a browser user-agent**. Read in
  full; no licence statement on the page. It is the origin of S4's page-1
  text (above), and adds nothing S4 does not already carry.

*(from §2)*

- **schematicheaven's OC-2 PDF**
  (https://schematicheaven.net/effects/boss_oc2_octave.pdf) — fetched
  (HTTP 200, no licence statement) and its single image **does** decode with
  `pypdf` + Pillow: it is Stellan Lehrberg's redraw of the OC-2,
  byte-identical to image `Im26` inside S4's own PDF. It
  independently corroborates the topology corrected in §1 — germanium diode on
  the chopper's input node, 100 kΩ from the non-inverting node to the rail,
  2SK30A with a 1 MΩ gate resistor — and OCT2's 47 nF/1 nF pair, but it reads
  OCT1's small capacitor as **220 pF where the factory drawing reads 470 pF**,
  which moves A1's OCT1 corner from ≈324 Hz to ≈474 Hz. Recorded as a
  cross-check disagreement for the netlist to settle (§8.1, O4), not as a
  value taken into the dossier.

*(from §2)*

- **electrosmash's archive mirror** (https://electrosmash.mas-effects.com/) —
  index re-read in full in the audit and it still has **no** octave or pitch
  article; its footer states it is "An unofficial, non-commercial backup of
  ElectroSmash.com … All content and images belong to their original
  authors/owners."

*(from §2)*

**A caution recorded on purpose:** S4's PDF also contains a 1999 hobbyist
redraw titled "BOSS OCTAVE OC2 **MODIFIED**" (B. Busser, drawn in Cadence,
dated 23.09.1999 — all confirmed on the drawing in the audit), with
substituted parts (MC14013 + MC14027BCD, TL074s, a 4053B for bypass). It was
read for orientation and **no value in this dossier comes from it**; every
value in §1 and A1 is from S2, the factory drawing — and the audit re-read
that drawing rather than trusting the seed's
reading of it. Nothing was read for code (vision §5).

*(from §2)*

**Audit, 2026-09-06 (licence and citation pass).** Every source above was
re-fetched or re-extracted and every quotation re-read at source. The licence
calls stand, with two sharpened: S4 now records that championleccy's own terms
page carries no IP statement and that its article text is hobby-hour.com's,
and S1 records that the −60 dBm figure comes from that article rather than
from the owner's manual. Four claims in §1 were corrected against the factory
drawing (S2, re-read at 3–9× zoom) and the Stompboxology page (S5):

*(from §2)*

3. **D10 does not sit on the non-inverting node.** It shunts the chopper's
   *input* node (where C24 lands, ahead of R44/R45) to the bias rail; R49
   100 kΩ is what sits on the non-inverting node, and Q8's gate is driven
   through R47 1 MΩ with R48 1 MΩ to the rail, not "R48 1 MΩ, R59 100 kΩ".
   S5's Fig. 4 circuit 2 draws the same three parts in the same places, and
   Lehrberg's redraw (below) agrees, so this is three sources against the
   seed's reading.

*(from §2)*

4. **The sum-and-difference derivation is Fig. 4 circuit 1's**, the plain
   synchronous detector. Of circuit 2 — the OC-2's, the one with the
   germanium diode — S5 says only that its "function … is less obvious", that
   the strategy is "to slice, invert, scale, and apply a DC offset to the
   wave, which reassembles into a physical approximation of a tone one octave
   below the fundamental", and that its "Control transitions must coincide
   with sinewave peaks" rather than zero crossings. O2 carries the law across
   by analogy now, and says so; its 3 dB and 20 dB thresholds are marked as
   the class's own numbers. **This is the one correction that touches the
   build**: §5's `SubOctave` sketch clocks the divider from zero crossings,
   which is variant 1's rule, and Gate 0 should decide against S5's text
   whether the OC-2's stage wants peak-synchronous switching instead.

*(from §3)*

**Trait-critic pass, 2026-09-06.** O2's two numeric thresholds were rewritten
and the second was split out as O6. Both were marked unsourced in the seed and
both were also wrong. *"3f/2 within 3 dB of f/2 with the filter defeated"* is
falsified by the ideal case itself — the arithmetic in A4 puts the ideal at
**4.44 dB**, so a faithful build would have failed the trait as written, which
is the shape `workspace-craft.md` warns about from the other side: a check that
cannot pass. *"With it engaged 3f/2 is at least 20 dB down"* is unreachable at
all: across a 3× frequency ratio a two-pole's asymptotic rejection is 19.1 dB,
and at a 220 Hz input against A1's ≈324 Hz corner the two lines straddle the
corner and sit a few dB apart. O6 states what the filter can actually do and
names the one-pole planted fault that proves the measurement can fail.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: ESP32-P4
**0.03**, ESP32-S3 **0.07**. Lean patch expected: **no** for CPU — the
per-sample work is four biquads, four compares with a branch and two Q15
multiplies — but **yes for RAM on the S3**, where a `" - lean"` patch drops
OCT2 and with it Splitter B and two biquads. RAM: two Splitters at a fixed
8192-frame stereo ring each (`audioif_splitter.h:20`) is **64 kB**, which
dwarfs everything else the class holds and is the one number worth watching
(§8.5).

*(from §3)*

Latency (vision §9a). **Zero samples, on every path**, and this is the class's
defining property rather than a footnote: it is the reason the mechanism
decision went to the divider (§5). No option adds latency; there is no
lookahead, no window and no delay line anywhere in the topology. Reported
`latency_samples` = 0 and the click measurement at the class gate must find
the dry and both octaves at offset 0. `tail_samples` is the output filters'
ring-down, of order 3 / f_corner — about 45 ms for OCT2's ≈70 Hz corner (A1) —
measured, not asserted.

*(from §4)*

Everything in that diagram exists today except `SubOctave`. The tracking
low-passes and the two output low-passes are `audiofilters.Filter` biquads —
built as `synthio.Biquad(mode, frequency, Q)`, which is the **only**
constructor the palette offers: there is no raw-coefficient form, and the RBJ
coefficients are computed **in C**, not in Python
(`audioif_biquad.c:70-125`, `audioif_biquad_configure_w0()`, from mode, W0, Q
and A). Python therefore chooses the mode and writes a corner in hertz; it
never computes or ships a coefficient set. *(Palette-verifier correction,
2026-09-06: the seed said "coefficients computed in Python at construction",
which the palette cannot do.)*
The choppers are `audiomath.Multiply`, which multiplies one stream by another
per sample in Q15 (`audioif_multiply.c:38`) and takes any source as the
modulator, not only a looping table (audioif `docs/upstream-diff.md`,
`audiomath` section) — that is exactly the OC-2's synchronous detector, and it
is why this class is *audioif* tier no matter what else happens. **Splitter B
is there because O3 is true**: OCT1's filtered output has to reach both the
mixer and OCT2's chopper, and a node's output can only be pulled by one
consumer. And the tracking filter is built **twice**, once per divider, for
the same reason — two biquads is far cheaper than a third Splitter's ring. The
two `SubOctave` instances stay phase-locked without any wiring between them
because they see the same samples through two taps of one Splitter and count
the same crossings. Levels are Mixer voice levels, which are exact: one voice
at 1.0 is byte-identical to the source and voices sum without normalisation
(`PitchShifter.md` A5 for the wire, `Harmonizer.md` A3 for the summation —
both re-measured 2026-09-06), so the direct path is a
true wire and the Tier 1 invariant is reachable.

*(from §4)*

Python computes at construction: four `synthio.Biquad` mode/frequency/Q
triples from the corner macros, and the divider's hysteresis and gate
thresholds in LSB. On a macro move it writes one biquad's `frequency` or one
voice level — the C recomputes that section's coefficients.
Nothing per sample, no table. **Mono** is the ordinary case and needs nothing
special: the divider, the multiply and the filters are all per-channel — but
note that Tier 3's 64 kB of Splitter ring does **not** shrink with it, since
the ring is declared stereo whatever the source is (`int16_t ring[8192 * 2]`,
`audioif_splitter.h:29`; a mono frame is duplicated into both lanes at
`audioif_splitter.c:30-31`). That makes §8.5's constructor-time ring size
worth more to this class than to any other in the unit.
`capabilities` = `()` (D10) — nothing in the OC-2 reads a clock.

*(from §4)*

**Palette verification, 2026-09-06 (pitch-stereo unit).** Re-read and
re-measured on this machine: `audiomath.Multiply` is `(a·b) >> 15` blended
`(dry·a + wet·product) >> 15` and clamped, per sample, stateless
(`audioif_multiply.c:32-46`); its `modulator` is any audiosample, checked
with `audiosample_check()` at `audiomath/Multiply.c:55-62` and **exercised
here with a live node as the modulator**, not only a looping `RawSample`
(upstream-diff's `audiomath` section says a table is merely the usual case) —
with one constraint the `SubOctave` sketch must honour: the same lines raise
"modulator channel_count does not match Multiply" (`Multiply.c:58-61`), so on
a stereo source `SubOctave` has to render **two identical lanes**, not one.
The "one consumer per node" fact Splitter B rests on was measured rather than
assumed: one live `audiofilters.Filter` handed to two `Mixer` voices at level
1.0 renders peak **10000** on a 10 000-peak sine — the two voices divide the
stream instead of doubling it — where two independent sources at the same
levels render **20000**.

*(from §5)*

  What actually blocks a subharmonic here is that period doubling needs
  either a clocked bistable or a *regenerative* loop in which the output is
  multiplied back against the input — and the palette's graph is a **pull
  graph with no cycles**: a node's source is fixed at construction, so the
  only feedback paths are internal to one node, and neither internal loop
  contains a multiplier fed by that node's own input. `Dynamics`'s
  nonlinearity is an envelope-rate gain, which can only put sidebands around
  the partials already present.

*(from §5)*

  Measured, 2026-09-06, `audiocomponents/.venv/bin/python`, 220 Hz sine at
  20 000 peak, 48 kHz stereo, Goertzel at f/2 = 110 Hz over the settled tail
  (A5): `Distortion` CLIP at +12 dB pre-gain, `Distortion` WAVESHAPE at
  +24 dB, `FeedbackDelay` with `feedback 0.99` and `loop_drive 1.0` at delays
  of 1/f, 2/f and 3/f (the tunings a period-doubling loop would need),
  `Dynamics` compressing 20:1 at 0.1 ms attack / 1 ms release, and
  `Multiply(x, x delayed one period)` both on the sine and on a hard-clipped
  square. **Every one leaves the 110 Hz line 42.5 dB or more below the input,
  at the same level as the analyser's own leakage floor** — no f/2 line
  exists to filter. The two attempts the seed reasoned about are in that set
  and behaved as it said.
- **Design sketch.** `audiomath.SubOctave(source, order=1, hysteresis=…,
  gate=…)` renders **one** full-scale ±square stream at f_in / 2^order — one
  stream, because that is what every node in this palette has, and at the
  source's channel count with both lanes identical, because `Multiply` raises
  on a modulator whose channel count differs (`Multiply.c:58-61`). Per sample:
  compare against a Schmitt pair (±`hysteresis` of full scale, defaulting to
  about 1 % — the comparator sensitivity S5 names as one of the three things
  that decide skipping); on a rising crossing advance a counter and toggle the
  output every **2^(order − 1)** rising crossings — so `order=1` toggles on
  every rising crossing and gives f/2, `order=2` toggles on every second and
  gives f/4 *(palette-verifier correction, 2026-09-06: the seed said "every
  2^order crossings", which makes `order=1` a divide-by-four and leaves §4's
  OCT1 an octave too low)*; while the input's tracked peak is below
  `gate`, hold the last state and let the output decay to zero rather than
  chatter on noise. Two instances (order 1 and 2) fed from two taps of one
  Splitter see the same samples and count the same crossings, so they are
  phase-locked without any wiring between them — §4's topology depends on
  that, and the class gate measures it. Additive, in an audioif-own module,
  per D1; the ported nodes are untouched.
- **Cost estimate.** Two compares, a branch and a store per frame — the same
  order as `Multiply` (`audioif_multiply.c:32-45`), so well under 1 % of a
  stereo block on the S3. Zero RAM beyond a few words of state, zero latency.
- **Refutation record for Gate 0.** The seed's original bar — "the ask
  survives if the reviewer cannot name a palette composition that is nonlinear
  and stateful" — was a bar the palette clears trivially and it is withdrawn
  with the premise. The bar is now the right one: **the ask falls if a
  reviewer renders a palette composition that puts a line at f_in/2,
  phase-locked to the input, within 20 dB of the fundamental.** Eight
  compositions were rendered and none came within 42.5 dB (above, A5). It
  also falls if the class is content to be a shifter — which the −121.6 cents
  and 10.7 ms above say it should not be.
- **Palette-verifier judgement, 2026-09-06: the ask SURVIVES.** The palette
  does not reach O1, O2, O3, O5 or O6 by composition; the refutation attempt
  is recorded in full above and in A5, with the incorrect premise struck.

*(from §7)*

- `pitch.py:105-106` — the class is **four pitch shifters**. The standout has
  no shifter in it, and the substitution costs 121.6 cents of tuning error and
  10.7 ms of latency (§5). This is the defect; everything else is detail.

*(from §7)*

- `pitch.py:84-85` — the comment "Shorter windows track faster, which matters
  more the further up the shift goes" is wrong about the mechanism it is
  justifying. A shorter window does not track faster; it raises the splice
  rate, which raises the artefact and *worsens* the pitch error
  (`PitchShifter.md` A2: 256 frames gives −132.5 cents where 2048 frames gives
  +10.8). The rebuild does not inherit a comment that reasons from a wrong
  model.

*(from §7)*

- `pitch.py:86-87` — two of the four branches shift **up**, which the OC-2
  cannot do at all; a divider only divides. Whether an up octave belongs in
  this class is §8.2, but if it stays it is a different circuit and needs its
  own source.

*(from §7)*

- `pitch.py:79` — `MACRO_LABELS = ()`. Four levels are constructor-only, so a
  host cannot balance the octaves against the dry — the one thing all three of
  the pedal's knobs do.

*(from §7)*

- `pitch.py:89` — the branch is built only if its level is `> 0.0`, so a level
  of zero is not "silent" but "absent", and a host could never turn it back on
  even if it had a macro to turn.

*(from §7)*

- `_core.py:140-141` — `LATENCY_SAMPLES = 0` inherited, which is *accidentally*
  right for the rebuild and *wrong today*: measured, the current class's
  octave branch puts a click 128 frames (2.67 ms) after the dry (A2).

*(from §7)*

- `pitch.py:92-96` raises when more octaves are asked for than the Splitter can
  carry, where `Harmonizer` silently truncates (`pitch.py:47`). Raising is the
  right behaviour; the rebuild makes both classes agree.
