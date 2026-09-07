# Effects Dossier — `RingMod` (the Bode four-diode ring, R.A. Moog 6401 / 6402)

**Class:** `lib/audioeffects/modulation.py` — read once, for §7.
**Family / phase:** Modulation, roadmap Phase 3
**Standout:** the four-diode ring — Bode's transformer-coupled diode ring as
built by R.A. Moog Co. as the 6401 (6402 dual), per vision §4.2. **Confirmed on
primary evidence**, not left as a proposal: Bode's own article on this instrument
(S1) and Moog's own schematic of it (S2) were both reached this run. The vision's
warning holds — the Bode 1630 is the *frequency shifter*, not referenced here.
**Grade:** literature — traits fixed from S1 and two DAFx modelling papers (S3,
S4). The schematic *with values* was also read (S2), so the grade rises to
**circuit** once Station A runs the ring in ngspice at the drawing's own levels
(§8.1).
**Portability tier:** needs audioif-own nodes (`audiomath`)
**Status:** seed (Phase 0), written 2026-09-06. Sections 4 and 5 were re-verified against the C under `audioif/src/shared` and the bindings under `audioif/src/<module>/`, and probed on the CPython build, by the palette verifier on 2026-09-06; the corrections and the node-ask verdicts are marked in place.

## 1. The circuit, in one paragraph

Four diodes in a ring (equivalently a lattice) are the only nonlinear elements;
everything else is transformers, resistors and trims (S1). The **carrier** enters
one diagonal *through an input transformer*, the **program** the other *directly,
one side grounded*, because the transformerless path reaches "from DC to very
high frequencies" and the transformer-coupled one does not (S1) — the two inputs
are deliberately asymmetric though Bode writes that "Basically, however, the two
inputs for the ring modulator are equivalent" (S1; an earlier draft of this seed
compressed that sentence into a quoted phrase, "basically equivalent", which is
not on the page — corrected by the audit). The
output leaves through a second transformer. A positive carrier conducts one diode
pair and blocks the other, a negative carrier swaps them, and the carrier current
cancels in the output transformer, leaving the product (S3). What separates
Bode's *multiplier type* from the ordinary *switching type* is the operating
point, not the topology: it uses "specially selected diodes of a type which, at
normal signal levels, operates in the 'square law' region" (S1). Moog's drawing
1113 is that instrument (S2): the four ring devices marked **SELECT DIODES**,
each arm padded with 470 Ω into 1 kΩ terminations, both diagonals carrying a 1 kΩ
balance trim (BALANCE on the carrier side, BAL on the output side), **three**
UTC A-20 transformers — T2 at the carrier input, T1 taking the ring's output and
T3 after the output amplifier (an earlier draft said two, counting only the
ring's own pair; corrected by the audit) — and the working levels written on the
drawing — 1.0 V RMS at each
jack, **0.16 V RMS** of carrier at the input transformer, **0.10 V RMS** of
program at the ring. (An earlier draft added "i.e. driven far below any silicon
knee" here; no diode knee voltage was reached from a source this run, the
DigiKey page gives only a 1 V forward drop at 100 mA, and §2 and §8.2 both say
this seed states levels and not a diode material — so the inference is struck
and the levels stand alone.) The output there
sits below studio level, so an output amplifier is part of the instrument; and
because a residual carrier is audible in the gaps a **gate** sits in the carrier
path ahead of the ring, opened only when the program passes a threshold, through
a preamplifier, rectifier, ripple filter and Schmitt trigger (S1; CR-1…CR-4 and
the threshold board on S2). The panel is therefore small: **Threshold**, a
**Squelch on/off** switch, the balance trims "which normally remain untouched",
and power (S1). There is no carrier oscillator in the box and no depth or mix
control — the carrier is whatever the studio patches in.

## 2. Sources and license calls

All reached this run, fetched 2026-09-06, none from memory. What each gave, in
full, is Appendix A0; the licence call is the bolded verdict.

- **S1.** H. Bode, "The Multiplier-Type Ring Modulator", *Electronic Music …  *(argument in full: App. R)*
- **S2.** R.A. Moog Co., "BODE RING MODULATOR MODELS 6401 & 6402 — SCHEMATIC", …  *(argument in full: App. R)*
- **S3.** R. Hoffmann-Burchardi, DAFx-08 (2008), "Digital Simulation of the Diode …  *(argument in full: App. R)*
- **S4.** J. Parker, DAFx-11 (2011), "A Simple Digital Model of the Diode-Based …  *(argument in full: App. R)*
- **S5.** H. Bode, "History of Electronic Sound Modification", *JAES* 32(10) …  *(argument in full: App. R)*
- **S6.** Synth-Werk SW 6401M entry, ModularGrid. Product listing, no license:
  **corroboration only**. <https://modulargrid.net/d/synth-werk-sw-6401m-bode-ring-modulator>
- **S7.** DigiKey, Microchip 1N485A. Distributor page: **facts**.
  <https://www.digikey.com/en/products/detail/microchip-technology/1N485A/4378292>
- **S8.** GroupDIY, "UTC A-20 blueprint". Forum, no license: **attributed, read
  only**. <https://groupdiy.com/threads/utc-a-20-blueprint.55127/>
- **Local:** `audioif/src/shared/audioif_multiply.c`, `audioif_distortion.c`,
  `docs/upstream-diff.md`, and the probes in A1. **MIT (audioif).**

**Looked for and not reached**, each re-requested by the audit and still out:
`modwiggler.com`'s 6401/6402 thread (**HTTP 403**); `cgs.synth.net` (**DNS
failure — `Could not resolve host`**, both with and without `www.`), Parker's
own reference for the hardware he measured; `web.archive.org` (blocked for this
tool).

**Corrected by the audit, 2026-09-06 — two of this list were reachable after
all**, over plain HTTP where the `https` host fails and the fetch tool's
automatic upgrade defeats it:

- **S9 (new).** Moog Archives, "Bode Ring Modulator 6401 and Dual Ring Modulator …  *(argument in full: App. R)*
- The IRCAM mirror of S4 also answers over plain HTTP — …  *(argument in full: App. R)*

Corrected in place by this pass, on top of the first audit's three:

- **"Basically equivalent" is not a phrase in S1.** The article's sentence is …  *(argument in full: App. R)*
- **The drawing carries three UTC A-20s, not two** — T2, T1 and T3. §1 fixed.
- **S1's host does carry a copyright line** — "© 2026 SYNTH-WERK". §2 fixed;
  the call is unchanged, because that line is the scanner's, not the journal's.
- **The 6402 carrier-bus question was answerable from the drawing** and is out
  of the unsourced list.
- **M4's 12 dB bar is labelled as this seed's**, joining M1's and M5's.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

**Multiplier character** — the standout's own, the class default.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement |
|---|---|---|---|---|---|
| M1 | On the test material, multiplier character at Depth 1, Mix 1, Balance 0, Program Bal 0: 1000 and 2000 Hz within 0.5 dB of each other, and each of 500, 1500, 4000, 5000, 7000, 8000 Hz at or below −60 dB re those two | S1 for the structure … (App. M1) | high for the … (App. M1) | any named component above −60 dB | SB |
| M2 | Unity level law, not a bare product: a 500 Hz sine program at **−6 dBFS peak** against a full-scale 1500 Hz carrier, multiplier character at Depth 1 and Mix 1, gives output RMS within **0.5 dB** of the program's own RMS, with no sample within 1 LSB of the rails. The named level is part of the trait: a bare product of two sines is exactly −3.010 dB on RMS, so Bode's law implies a **+3.01 dB makeup on the wet path** — declared, wet path only — and at a full-scale program that makeup would peak at 1.414× full scale (both A1/P10). An earlier draft asked for unity at a full-scale program, which no build can meet | S1 Ex. 1 verbatim: "If the magnitudes of the … (App. M2) | high | RMS off by more than 0.5 dB — in particular −3.0 dB, which is the makeup missing — or any sample at the rails | LVL |
| M3 | Bandwidth doubles: a program band-limited 0–100 Hz with a 900 Hz carrier gives −20 dB edges at 800 ± 10 and 1000 ± 10 Hz, energy outside 780–1020 Hz below −40 dB. The probe's own band-limiting filter is measured first and its −20 dB edge recorded, because the sharpness of the output edge is the probe's and only the *position* is the class's | S1 Ex. 3 ("the bandwidth of the output is … (App. M3) | high | an edge outside ±10 Hz of where the probe's own edge predicts it, or skirts above −40 dB | BW |
| M4 | The inputs are not interchangeable: at Carrier Low's **5 Hz default** a 2 Hz carrier gives sidebands **8.6 ± 1.5 dB** below a 200 Hz carrier's at equal level, while a 2 Hz program passes within **0.5 dB** of a 200 Hz program | S1 (the program enters directly … (App. M4) | medium — the … (App. M4) | a difference outside 8.6 ± 1.5 dB, including a carrier path flat at 2 Hz (under 1 dB); or a program path down by more than 0.5 dB at 2 Hz | SWEEP |
| M5 | The quiescent carrier is gated, not merely balanced: Squelch on + full-scale carrier + silent program + Balance detuned 0.2 → every sample exactly zero; Squelch off, same detune → a carrier-frequency component above −60 dBFS | S1 (the gate, the squelch switch … (App. M5) | high for the … (App. M5) | a non-zero sample with Squelch on, or no residual with it off | GATE |

**Switching character** — Bode's other type, carried as a character (§6). Its
traits are its own; it cannot hide behind the multiplier.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement |
|---|---|---|---|---|---|
| W1 | On the same material, switching character at **Shape 1** (the full chopper), Depth 1, Mix 1: 4000 and 5000 Hz (3f₂±f₁) sit at **−9.5 ± 3 dB** and 7000 and 8000 Hz (5f₂±f₁) at **−14.0 ± 3 dB** re the first pair, falling monotonically with order, while 2500 and 3500 Hz (2f₂±f₁) stay below **−40 dB** | S1 verbatim on the switching type: "The … (App. W1) | high for the … (App. W1) | 3f₂±f₁ outside −9.5 ± 3 dB — the multiplier's own build puts them at −101 dB, the Q15 floor (A1/P5) — or an even product above −40 dB, which is a duty that has drifted off 50 % | SB |
| W2 | Band-limited, not aliased: at 48 kHz, on **523 Hz program × 1481 Hz carrier** (not SB's material — see the source column), every bin above **−60 dBFS** lies within 2 Hz of the set { \|±f₁ ± m·f₂\| : m odd, m·f₂ < f_s/2 }, which is the whole spectrum a program times a band-limited odd-harmonic carrier can produce | S4 for the mechanism (the harmonics "fall-off at a rate of around 20db per octave", ×8–×16 oversampling sufficient). The frequencies are measured, not chosen by taste: **on 500 × 1500 this sieve cannot fail** — 48000/500 and 48000/1500 are whole numbers, so every alias folds exactly onto a line the sieve accepts, and an un-band-limited 1× chopper measures zero off-set bins, the same 16-line spectrum as a correct build. At 523 × 1481 the same fault reads −24.6 dB and the correct build still reads zero (A1/P11) | medium — the falloff is Parker's; **the −60 dBFS bar and the probe frequencies are this seed's** | any bin above −60 dBFS off that set | SIEVE |
| W3 | *(No longer conditional on a node — the palette reaches it; see §5's refutation.)* The program passes the diode curve too, not only the carrier: switching character, Shape 1, carrier held at DC (Frequency 0), full-scale 500 Hz program, spectrum normalised to its own peak → third harmonic **above −30 dB** re the fundamental | S3 (the ring's own bias point and its diode … (App. W3) | medium-low … (App. W3) | h3 at or below −30 dB, and in particular at the Q15 floor (≈ −100 dB), which is what any build whose shaping is baked into a carrier-phase table gives — see §5 | DC-H |
| W4 | This character carries **no** makeup, where the multiplier carries M2's +3.01 dB: the same −6 dBFS program at Shape 1, Depth 1, Mix 1 gives output RMS within **0.5 dB** of the program's own, because a chopper leaves \|carrier\| = 1 at every sample and the product's RMS is the program's untouched | S1 (the switching type passes the program through the ring as a switch, not as a multiplier — its own sideband list is the switch's, W1); the arithmetic is this run's (A1/P10) | high — arithmetic on a ±1 carrier, not a claim about the hardware's absolute level | RMS off by more than 0.5 dB; +3.0 dB in particular, which is the multiplier's makeup applied to a chopper, and which clips at any program above −3 dBFS | LVL |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Topology, both characters: `source → audiomath.Multiply(modulator = carrier
table)`.** One node — not a compromise but the standout's own mechanism, and the
palette already reaches the headline trait: the shipped class measures program
and carrier feedthrough at −162 and −158 dB and the switching products at
−100 dB, the Q15 floor (A1/P5) — M1 met with room to spare. **Re-measured this
run** (palette-verifier pass, 2026-09-06, A1/P17): the same configuration through
`audioeffects.create('RingMod', …)` gives 1000 Hz −0.0 dB, 2000 Hz 0.0 dB,
program 500 Hz **−140.6 dB**, carrier 1500 Hz **−138.0 dB**, 4000 Hz −106.8 dB,
5000 Hz **−93.0 dB**, 7000 Hz −96.6 dB — M1's −60 dB bar met with **33 dB** of
margin on its worst named component. P5's exact figures did not reproduce (its
probe setup is not recorded closely enough to repeat), so the margin claim is now
the re-measured one; the conclusion is unchanged. `audiomath` is
audioif's own with no ancestor anywhere (`upstream-diff.md:714`), so the tier is
**audioif**; `Multiply` applies the modulator's left and right columns
independently (A1/P4), which makes the stereo-phase macro free.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**N1 — the table-driven waveshaper with oversampling (the vision §6 node, the
Drive family's ask), as a second consumer.** *Trait id:* **W3**, and W2's floor
at high drive. *What the palette does instead:* bakes the shaping into the
carrier table (§4) — exact for W1, and better than a runtime shaper for W2 — but
a table indexed by carrier phase is a function of the carrier alone, so **nothing
in it can depend on the program**. W3 is unreachable *by that table*, which the
first draft of this ask read as unreachable altogether — see the refutation
below, which reaches it with a different palette node. *The measurement that shows it:* W3's own — with the carrier at DC a
baked-table build applies a constant gain and its third harmonic sits at the Q15
floor (≈ −100 dB) against W3's −30 dB bar, and no table changes that.
*Refutation record (Phase 0):* the standout's own character is fully reachable
without the node — M1–M5 all compose — so this class does **not** justify the
node alone; the ask is recorded as a second consumer of a node the Drive family
needs anyway.

If the waveshaper lands anyway for the Drive family, `RingMod` may still build
Parker's four-path structure on it (S4, A3) as a better model of the same trait;
it is no longer a reason to build the node. **No other ask.**

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

**Characters** (constructor option, house style as `Compressor` uses):
**`multiplier`** (default — the standout) and **`switching`**. This departs from
vision §4.2's note suggesting "carrier bleed and diode asymmetry as characters":
both are *trims on the standout's own panel* (S2's BALANCE and BAL) and belong on
the macro surface, while the pair Bode himself separates — multiplier versus
switching, different sideband structures (S1) — earns its own trait sets.

Macros (eleven; ceiling sixteen), ranges in engineering values:

| # | Label | Mode | Range | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 0.1–8000 Hz log, clamped < 0.45·f_s | none — the 6401 has no oscillator; generalizes the studio's carrier source |
| 1 | Depth | UNIPOLAR | 0–1: 1 ring, 0.5 textbook AM, 0 the Tier 1 wire | none on the standout (D2) |
| 2 | Mix | UNIPOLAR | 0–1 | none on the standout; a modern insert wants it (D2) |
| 3 | Shape | UNIPOLAR | 0–1: 0 square-law, 1 full chopper | the diode operating point; pinned at 0 in `multiplier` |
| 4 | Balance | BIPOLAR | −1…+1, 0 nulled | the 1 kΩ **BALANCE** trim (S2) — carrier feedthrough |
| 5 | Program Bal | BIPOLAR | −1…+1, 0 nulled | the 1 kΩ **BAL** trim (S2) — program feedthrough |
| 6 | Squelch | TOGGLE | on/off, default **on** | the **SQUELCH ON-OFF** switch (S1) |
| 7 | Threshold | UNIPOLAR | −72…0 dBFS | the **THRESHOLD** control (S1, S2) |
| 8 | Release | UNIPOLAR | 5–500 ms | the gate's ripple filter (S1); no panel control |
| 9 | Carrier Low | UNIPOLAR | 2–200 Hz log, default 5 Hz | the carrier transformer's bottom end (S1, S8) |
| 10 | Stereo Phase | BIPOLAR | −180…+180° | none on the 6401; the 6402 is two channels (S2) |

`capabilities = ()` (D10): the carrier is an audio-rate input on the standout and
the instrument has no transport; the sub-audio corner Bode names as a modulation
effect (S1 Ex. 6) belongs to `Tremolo`, which declares `"tempo_sync"`.

Patches (names describe settings, never products): 0 **Clean Ring** (multiplier,
220 Hz, Depth 1, Mix 1, Squelch on, Threshold −60 dBFS); 1 **Textbook AM**
(multiplier, 6 Hz, Depth 0.5); 2 **Clangour** (multiplier, 1500 Hz, Depth 1);
3 **Bell Strike** (multiplier, 3200 Hz, Depth 1, Mix 0.7); 4 **Chopper**
(switching, 1500 Hz, Depth 1, Shape 0.9); 5 **Soft Chopper** (switching, 400 Hz,
Shape 0.35, Mix 0.8); 6 **Detuned Ring** (multiplier, 220 Hz, Balance +0.15,
Squelch off); 7 **Wide Ring** (multiplier, 90 Hz, Stereo Phase 90°); 8 **Growl**
(multiplier, 18 Hz, Depth 0.6).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/modulation.py` on 2026-09-06.

- `modulation.py:189-191`: at Depth 0 the table is a constant 32767 and `mix` …  *(argument in full: App. R)*
- `modulation.py:191`: `int(32767.0 * shape)` truncates toward zero, so the
  table's negative half is up to an LSB shorter than its positive half. Round.
- `modulation.py:192-193`: the table writes the same sample to every channel —
  no stereo carrier phase, and `channel_count` buys nothing.
- `modulation.py:255-262`: a Frequency or Depth move rebuilds the table and
  restarts the carrier at phase zero — a click on every knob tick.
- `tail_samples` reports `None` (measured, A1/P5). The ring is memoryless; the
  honest report is 0.
- No squelch, no balance trims, no carrier band-limit, no switching character —
  none of M4, M5, W1, W2 or W3 exists, and the docstring stops at the multiplier.
- Checked and **cleared**, not a defect: the whole-cycle table rounding …  *(argument in full: App. R)*

Nothing else about the old class is carried forward.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **The ngspice run that raises the grade.** One deck from S2's values and
   levels — four diodes, 470 Ω arms, 1 kΩ terminations, the A-20 as an ideal 1:1
   with S3's magnetising inductance, at 0.16 V RMS carrier and 0.10 V RMS program
   — settles whether the ring is square-law there and fixes Shape's endpoints
   from the circuit instead of Parker's fitted parameters. Owner: Station A.
2. **Silicon in a multiplier-type box.** S5 credits multiplier behaviour to
   *germanium* and names silicon as chopper-type; S2's note and S6's replica both
   say **1N485A**, which S7's 25 nA leakage marks as silicon. The likely
   resolution is the operating level, but "likely" is not sourced and question 1
   decides it. Until then this seed states levels, not a material.
3. **The ring diodes' actual part number** — S2 marks them only "SELECT DIODES";
   whether the general note covers them is a reading a second pair of eyes should
   make. Owner: the survey audit.
4. **Carrier suppression in dB.** M1's and M5's −60 dB bar is this seed's, not
   Moog's; a reachable specification or measurement moves it, recorded.
5. **Squelch on by default?** Bode's panel has the switch and says the balance
   trims "normally remain untouched" (S1), implying the gate is the working
   state; the surface follows that, and the session may argue back.
6. **N1's survival** (§5) is **settled — refuted on this class's account**
   (palette-verifier pass, 2026-09-06): a ported `audiofilters.Distortion` in the
   program path reaches W3's number with 8.8 dB of margin (A1/P18) while still
   passing W1 (A1/P19). The Drive family's own ask is unaffected; what this class
   owes the node list is a *restated* W3 if Station A wants the carrier-dependent
   mechanism rather than the number (§5).
7. **W2's sieve set has to be widened, or W3 dropped** — new this run, measured
   (A1/P18). Any build that satisfies W3 puts |±3f₁ ± m·f₂| terms into the
   spectrum, and W2's set admits only k = 1 on the program. Recommended:
   { |±k·f₁ ± m·f₂| : k odd, m odd }. Owner: Station A, before the rebuild;
   nothing here changes W2's purpose, which is to catch broadband aliasing.
8. **How few traits the switching character can end with.** W3 is no longer
   conditional — the palette reaches it (§5) — so the character keeps **four**
   of its own, W1–W4, above the Phase 0 gate's floor of three. What is still open
   is question 7's wording of W2, and whether a restated, carrier-dependent W3
   would put the character back to three until the waveshaper lands. The
   multiplier character's five rows are all unconditional.

---


## Appendix

### A0. What each source gave, in full

**S1 (Bode 1967).** Two types: switching-type, "widely used in industrial control
applications", whose sidebands are "f2−f1, f2+f1, 3f2−f1, 3f2+f1, 5f2−f1, 5f2+f1,
and the further odd harmonics of f2, minus and plus f1", and which "sounds
scratchy and unpleasant"; multiplier-type, using "specially selected diodes of a
type which, at normal signal levels, operates in the 'square law' region",
producing only f2−f1 and f2+f1 with "an extremely small amount of unwanted
modulation products". All rings are "four diodes arranged in a ring
configuration, or when redrawn, in a lattice configuration"; the carrier enters
"through the input transformer" and the program "directly, one of which is
grounded", the transformerless input being used for program "because of its
extended frequency-handling capability from DC to very high frequencies", the
range then "limited only by … the output transformer". Fig. 1 bottom shows
"potentiometers to improve balance". Because the output "is appreciably below the
standard voltage levels … when the diodes are operating in their optimum range"
an output amplifier is required, and because "a low level carrier feed-through
may become audible" in pauses, a gate in the carrier path is "activated to pass
the carrier signal only when the program level exceeds a predetermined threshold
voltage", set by a preamplifier gain control, then "a rectifier, a ripple filter,
and a Schmitt-trigger circuit". Panel: threshold, "the squelch on-off switch for
activating or de-activating the carrier suppression circuit", "the ring modulator
balancing adjustments (which normally remain untouched)", pilot light and power
switch. Fig. 4 is captioned "Single channel Bode multiplier-type ring modulator
built by the R. A. Moog Co." Ex. 1: 1000 Hz program, 900 Hz carrier → 100 Hz and
1900 Hz, "If the magnitudes of the inputs are both 1.0 volt RMS, the magnitude of
the total output of the described standard model will also be 1.0 volt RMS."
Ex. 3: 0–100 Hz noise with a 900 Hz carrier → 800–1000 Hz, "the bandwidth of the
output is twice the bandwidth of the program input". Ex. 6: program material into
the *carrier* input and a 6 Hz sine into the program input gives "a kind of
spatial amplitude-phase modulation".

**S2 (drawing 1113).** See A2.

**S3 (Hoffmann-Burchardi).** Four diodes and two centre-tapped transformers;
positive carrier conducts D1/D2 and blocks D3/D4, and "the carrier currents …
cancel out each other at the second transformer". Substitute circuit: ideal
transformers with C and L in parallel, diodes as voltage-controlled resistors,
five first-order ODEs, with C = 10 nF, C_p = 10 nF, L = 0.8 H, R_A = 600 Ω,
R_i = 50 Ω, R_M = 80 Ω. Germanium 1N270 at low voltage: `g(x) = 0.17x⁴` for
x > 0, else 0. "Using silicon diode models will not work. Since the bias point of
the diodes is at 0 V, this causes the carrier waveform to 'squash' the modulator
waveform near its zero crossings, creating harsh distortions at the output" —
unless the bias is shifted 300 mV, giving
`g(x) = 40.67286402e−9(e^{17.7493332(x+0.3)} − 1)` for a 1N4448. "The inductances
L affect the frequency response of the circuit, acting like a level-dependent
high-pass filter", with the response plotted for 100 mV and 200 mV of DC carrier;
removing the two inductor equations leaves a linear response and only three
nonlinear ODEs. Inputs should stay within ±200 mV; Forward Euler at ×128
oversampling. The real device measured used four 1N270 germanium diodes and two
Mouser TM018 transformers. "Real ring modulators show an asymmetric behavior
(diodes and transformer coils never match exactly, causing a fraction of the
carrier and modulator signals to appear at the output)".

**S4 (Parker).** Silicon gives "hard clipping or 'chopping' … extremely bright
extra harmonics", germanium "a softer non-linearity and a 'warmer' sound".
Transformers couple voltage between ring nodes and can make three diodes conduct
at once, so he replaces them: two sources at V_C + V_in/2 and V_C − V_in/2,
output across two high-value R_out. Four parallel paths, each a nonlinearity plus
inversions (his Fig. 4). The nonlinearity is a Shockley solve expanded by Taylor
series, then approximated piecewise (A3), with n = 2.19, V_T = 26 mV, I_S = 1e-12,
R_in = 80 Ω, R_out = 1e6 Ω, "chosen to be consistent with an average germanium
diode such as the 1N34". Spectrum for 50 Hz program × 1500 Hz carrier: sum and
difference at 1550 and 1450 Hz "along with further integer multiples of the
modulator frequency above and below the carrier frequency. Also visible are odd
harmonics of the modulated spectrum." Cost: "10 operations per sample, along with
4 calls to the diode-shaping function. The diode-shaping function requires 14
operations each time it is called", halvable where `abs()` is cheap. "Examination
of the harmonics generated by the system reveals that they fall-off at a rate of
around 20db per octave. An oversampling factor of around ×32 would therefore be
necessary … In these applications, an oversampling factor of ×16 or ×8 is
sufficient". On natural sources the result "is harsher and brasher than that of
simple digital multiplication".

**S5 (Bode 1984).** "It was only after ring modulators were built with diodes
(Fig. 8), which operate in the square law region of their transfer function (as
was the case with certain germanium diodes), that they started to perform as
four-quadrant multipliers and became musically interesting." Fig. 8 distinguishes
chopper-type operation with silicon diodes from multiplier-type with germanium.

**S6.** "based on the original design of Harald Bode from 1967"; "a ring of
diodes and transformers forming a four quadrant multiplier"; smaller vintage UTC
SO 15P transformers in place of the originals, with "original NOS 1N485A" diodes.
**S7.** 180 V reverse, 100 mA, V_F 1 V @ 100 mA, reverse leakage 25 nA @ 180 V,
DO-7 — three orders below a germanium part's leakage. **S8.** "500:500
transformer", multiply tapped, rated 15 dBm ("inflated"), saturating at the low
end at 2 V, "craps out at 5 Hz", older units rolling off sooner.

### A1. Probes run this session (venv CPython, `audiocomponents/.venv`, 2026-09-06)

Scripts are throwaway; the numbers are the evidence.

- **P1 — `Multiply` at `mix=0` is a bit-exact wire.** A 1 kHz half-scale stereo
  tone with `mix=0.0`: all 8192 samples identical to the source. Confirms
  `audioif_multiply.c:28-29`, `:39`.
- **P1b — a "unity" table is not a wire.** The same tone at `mix=1.0` with a
  modulator held at 32767: sample error against the source ranges −1 … 0, never
  positive, because `(a·b)>>15` is an arithmetic shift and floors.
- **P4 — per-channel modulator columns are honoured.** DC 16000 stereo source,
  modulator (L = 32767, R = 8192) → L = 15999, R = 4000.
- **P4b — the carrier table's cycle rounding.** `_carrier`'s
  `cycles = round(f·2048/f_s)`, `length = round(cycles·f_s/f)`
  (`modulation.py:185-186`) at 48 kHz: 20 Hz +0.00 ¢, 55 Hz +0.45 ¢, 220 Hz
  −0.32 ¢, 440 Hz −0.23 ¢, 1000 Hz +0.00 ¢, 1234.5 Hz −0.21 ¢, 4000 Hz +0.00 ¢.
- **P5 — the shipped class's sideband spectrum.** 500 Hz half-scale program,
  1500 Hz carrier, Depth 1, Mix 1, 32768-frame render, Hann window, normalised to
  peak: f₂−f₁ (1000 Hz) −0.0 dB, f₂+f₁ (2000 Hz) 0.0 dB, program (500 Hz)
  −162.4 dB, carrier (1500 Hz) −158.1 dB, 3f₂−f₁ (4000 Hz) −101.1 dB, 3f₂+f₁
  (5000 Hz) −100.0 dB, 5f₂−f₁ (7000 Hz) −103.3 dB. The palette already meets M1
  with 40 dB to spare. Same render: `latency_samples = 0`, `tail_samples = None`.

- **P10 — the arithmetic behind M2, M4, W1 and W4** (trait-critic pass,
  2026-09-06; numpy in the same venv, 48 kHz, one second, rectangular window on
  bin-centred frequencies so there is no leakage to read as signal).
  *Level.* A full-scale 500 Hz sine has RMS 0.70712; its product with a
  full-scale 1500 Hz sine has RMS 0.50001 — **−3.010 dB**, the two half-amplitude
  sidebands. Restoring unity costs ×√2, and the product's peak is 1.0, so the
  makeup puts it at **1.4142× full scale**; a program peak of −3 dBFS lands at
  1.0012 and −6 dBFS at 0.7088. Hence M2's −6 dBFS. A ±1 chopper carrier instead
  leaves the product's RMS equal to the program's exactly, which is W4.
  *The carrier corner.* A first-order high-pass, |H| = f/√(f²+f_c²): at
  f_c = 5 Hz, 2 Hz is **−8.60 dB** and 200 Hz **−0.00 dB** — 8.60 dB apart. The
  same pair of points is 3.01 dB apart at f_c = 2 Hz and 14.14 dB at f_c = 10 Hz,
  so an earlier draft's ≥12 dB needs a corner near 8 Hz, above anything S8
  supports. Hence M4's 8.6 ± 1.5 dB at the 5 Hz default.
  *Chopper sidebands.* A 50 %-duty carrier band-limited below Nyquist, times a
  500 Hz sine: 3f₂±f₁ at **−9.54 dB**, 5f₂±f₁ at **−13.98 dB**, 7f₂±f₁ at
  −16.90 dB, every even product at the float floor (≈ −286 dB). Hence W1's
  two-sided windows.
- **P11 — the sieve that could not fail** (trait-critic pass, 2026-09-06). The
  fault is a 1× hard chopper with no band-limit, built from integer phase so no
  float jitter is mistaken for aliasing; the control is the same program times an
  odd-harmonic carrier truncated below Nyquist — the build §4 proposes. The sieve
  accepts { |±f₁ ± m·f₂| : m odd, m·f₂ < f_s/2 }, ±2 Hz, floor −60 dBFS:

  | material | 1× hard chopper (the fault) | band-limited table (the control) |
  |---|---|---|
  | **500 × 1500 Hz** (SB's own) | 16 bins live, **0 off-set** | 16 bins live, 0 off-set |
  | 523 × 1481 Hz | 1146 live, **1130 off-set**, strongest −24.6 dB | 16 live, 0 off-set |
  | 517 × 1493 Hz | 1043 live, **1027 off-set**, strongest −24.6 dB | 16 live, 0 off-set |

  On 500 × 1500 the fault and the control produce **the same spectrum**: 48000/500
  and 48000/1500 are whole numbers, so every alias folds exactly onto a line the
  sieve accepts and no aliasing can ever show. That is the absence-reads-as-
  agreement shape `agent-knowledge/workspace-craft.md` names, and it is why W2
  now runs on its own material and the kit spec (A4) carries the fault and the
  control as a pair.

- **P17 — the shipped class, re-measured** (palette-verifier pass, 2026-09-06).
  `audioeffects.create('RingMod', src, 48000, frequency=1500, depth=1.0,
  mix=1.0)` over a 500 Hz half-scale stereo tone, 32 768-frame render, Hann
  window, normalised to peak: 1000 Hz −0.0 dB, 2000 Hz 0.0 dB, 500 Hz
  −140.6 dB, 1500 Hz −138.0 dB, 4000 Hz −106.8 dB, 5000 Hz −93.0 dB, 7000 Hz
  −96.6 dB; `latency_samples` 0, `tail_samples` `None`. M1's −60 dB bar met with
  33 dB of margin. P5's figures (−162 / −158 / −101 / −100 / −103) did not
  reproduce, so §4 now quotes these.
- **P18 — W3 on the palette, and what it does to W2** (palette-verifier pass,
  2026-09-06). Chain: `RawSample(500 Hz, 32700 peak) →
  audiofilters.Distortion(CLIP, drive 0.3, pre/post gain 0 dB, soft_clip off) →
  audiomath.Multiply(carrier)`.
  *W3 configuration* (carrier a constant 32767 table, i.e. Frequency 0):
  h3 re fundamental **−21.2 dB** with the `Distortion` in place, **−99.3 dB**
  without it. W3's bar is "above −30 dB".
  *W2 configuration* (523 Hz program × a 1481 Hz odd-harmonic carrier truncated
  below Nyquist, whole cycles, sieve ±2 Hz at a −60 dBFS floor): with a linear
  program the strongest off-set bins are all above 19 kHz and are the table's own
  frequency-rounding drift at high harmonic order, not aliasing; with the
  distorted program two new low bins appear at **88 Hz and 3050 Hz, both
  −21.9 dBFS**, which are |3f₁ − f₂| and |3f₁ + f₂|. The sieve as written rejects
  them.
- **P19 — the refuting build against the character's other rows**
  (palette-verifier pass, 2026-09-06), on SB's own material, 500 Hz at −6 dBFS ×
  a band-limited 1500 Hz odd-harmonic carrier, levels re the 1000/2000 pair:

  | | 3f₂±f₁ (4000/5000) | 5f₂±f₁ (7000/8000) | 2f₂±f₁ (2500/3500) | output RMS vs program |
  |---|---|---|---|---|
  | linear program | −10.1 / −10.1 dB | −15.0 / −15.0 dB | −142.2 / −141.9 dB | −0.53 dB |
  | distorted program (W3 met) | −10.9 / −10.3 dB | −15.9 / −15.2 dB | −144.7 / −144.6 dB | +1.86 dB |

  W1's windows are −9.5 ± 3 and −14.0 ± 3 with an even-product floor of −40 dB:
  both builds pass. W4's ±0.5 dB is missed by both — the band-limited table is
  not exactly a ±1 chopper — and is a static `post_gain` trim, not a structural
  failure.

### A2. Reading the drawing (S2)

The four ring devices are drawn as a lattice labelled **SELECT DIODES**,
CR-5…CR-8, with 470 Ω in series with each arm (R14, R15, R17, R19) and 470 Ω
again on the four bridge legs (R16, R18, R20, R21), terminated by 1 kΩ at each
corner (R12, R13, R22, R23). T2 (UTC A-20) brings the carrier in from the carrier
board through C4 80 µF; its secondary sits across one diagonal with the 1 kΩ
**BALANCE** pot. T1 (UTC A-20) takes the output from the other diagonal, the
1 kΩ **BAL** pot beside it, into C6 10 µF and Q8. The program arrives on the top
rail through **R11 1 kΩ** — no transformer, exactly as S1 describes. The carrier
board is a 27 kΩ/10 µF input into Q1, the CR-1…CR-4 gate (bypassed by the SQUELCH
ON-OFF switch), then Q2 into T2, annotated 0.16 V RMS; the program reaches the
ring at 0.10 V RMS, and both front-panel jacks are annotated "1.0 V RMS APPLIED".
The program input and squelch trigger board carries the THRESHOLD pot and Q3–Q7.
Title block: "BODE RING MODULATOR / MODELS 6401 & 6402 / SCHEMATIC / DRAWN BY
B.S. / 10-21-66 / DRAWING NUMBER 1113 / R.A. MOOG CO. TRUMANSBURG, N.Y." Notes:
"ALL CIRCUITRY IS DOUBLE IN #6402 EXCEPT FOR POWER SUPPLY", "ALL TRANSISTORS
2N2925 UNLESS NOTED", "ALL DIODES 1N485A UNLESS NOTED".

### A3. Parker's structure, for the implementation session

If N1 lands: `V_C` and `V_in` combine to `V_C + V_in/2` and `V_C − V_in/2`; each
passes the diode shaper twice with the appropriate inversions, and the four
results sum (S4, Fig. 4). The shaper is `f(v) = 0` for `v ≤ v_b`;
`h(v−v_b)²/(2v_L−2v_b)` for `v_b < v ≤ v_L`;
`hv − hv_L + h(v_L−v_b)²/(2v_L−2v_b)` for `v > v_L` — three parameters, which is
what Shape moves. Where `abs()` is cheap, both paths share one nonlinearity.

### A4. The kit measurements this seed names

Written by the trait-critic pass, 2026-09-06: §3 named these seven and defined
none of them. Every measurement takes the sample rate as a parameter and records
it in what it exports; the evidence pack carries every Tier 2 trait at 48 kHz and
44.1 kHz and the Tier 1 invariants additionally at 22.05 kHz. Unless a row says
otherwise each runs at Balance 0, Program Bal 0, Mix 1.

- **SB — sideband spectrum.** 500 Hz sine program × 1500 Hz sine carrier, Depth 1,
  32768 frames, Hann FFT, peaks read in ±4-bin windows at the named frequencies,
  reported in dB re the stronger of 1000/2000 Hz. M1 and W1 read it.
  *Planted fault for M1:* swap the multiplier's sine table for the switching
  character's chopper, which lifts 4000/5000 Hz from the −101 dB the shipped
  class measures (A1/P5) to about −9.5 dB (A1/P10), leaving them 50 dB above
  M1's −60 dB bar. *Planted fault for W1:* the reverse swap, which drops 3f₂±f₁ to the Q15
  floor; and, for W1's even-product half, a carrier duty moved off 50 %, which
  raises 2500/3500 Hz through the −40 dB floor. *The control that must pass:*
  each character measured against its own row in the same run.
- **LVL — level law.** The M2/W4 material rendered at the stated program level;
  RMS and peak per channel, and the peak as a fraction of full scale. M2 and W4
  read it. *Planted fault:* remove the multiplier's +3.01 dB wet-path makeup —
  M2 must read −3.0 dB — and apply that same makeup to the switching character,
  where W4 must read +3.0 dB. *The control that must pass:* the dry path at
  Mix 0, which Tier 1 holds byte-identical.
- **BW — bandwidth.** A 0–100 Hz band-limited noise program with a 900 Hz
  carrier, averaged spectrum over at least 16 blocks; the probe's own band edge
  measured first, then the output's −20 dB edges and the energy outside
  780–1020 Hz. M3 reads it. *Planted fault:* a carrier with any harmonic content
  (a chopper at Shape > 0), which puts sidebands around 2700 Hz and lifts the
  out-of-band figure through −40 dB.
- **SWEEP — input asymmetry.** Sideband amplitude against carrier frequency over
  1–200 Hz at fixed program, then against program frequency over the same span at
  fixed carrier, both at equal input level, exported as two curves. M4 reads the
  2 Hz and 200 Hz points of each. *Planted fault:* bypass the Carrier Low
  high-pass, which collapses the carrier curve onto the program curve and puts
  the difference under 1 dB. *The control that must pass:* the program curve
  itself, which must stay flat within 0.5 dB across the same span in both runs —
  without it a broken renderer that returns silence would read as agreement.
- **GATE — squelch.** Full-scale carrier, silent program, Balance detuned to 0.2:
  with Squelch on, every sample compared against exact zero; with Squelch off,
  the carrier-bin level in dBFS. Then a burst-then-silence probe for the release
  and for the Tier 1 tail. M5 reads it. *Planted fault:* implement the gate as a
  modulator held at 0 instead of `mix = 0`, which leaves the −1 LSB that A1/P1b
  measured and must fail the exact-zero half; and a second fault, the gate wired
  permanently open, which must fail the Squelch-on half while leaving the
  Squelch-off half untouched. *The control that must pass:* Squelch off with
  Balance nulled, where the carrier bin must sit at the Q15 floor.
- **SIEVE — aliasing.** 523 Hz program × 1481 Hz carrier — **never SB's 500 ×
  1500, on which the sieve provably cannot fail (A1/P11)** — one second at the
  running rate, rectangular window on bin-centred frequencies, every bin above
  −60 dBFS tested against { |±f₁ ± m·f₂| : m odd, m·f₂ < f_s/2 } to ±2 Hz. W2
  reads it. *Planted fault:* a 1× hard chopper with no band-limit, measured at
  1130 off-set bins and −24.6 dB at its strongest. *The control that must pass:*
  the band-limited table on the same material, measured at zero off-set bins.
  Both halves are required: the fault alone would not distinguish this sieve from
  one that fails everything.
- **DC-H — the program through the curve.** Carrier held at DC, full-scale 500 Hz
  program, spectrum normalised to its own peak, h3 in dB re the fundamental. W3
  reads it. *Planted fault:* drive the shaper from the carrier table alone, so the
  program sees a constant gain and h3 falls to the Q15 floor — which is also
  exactly what the palette-only build does, so this measurement is the one that
  decides whether W3 is carried or recorded as not carried (§5).

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

Frequency's 8 kHz top clamps to 0.45·f_s, so at 22.05 kHz it stops at 9.9 kHz;
no trait is lost. Depth 0 must be the `mix=0` wire of `audiomath.Multiply`
(`audioif_multiply.c:28-29`, `:39`), never a constant table — a table at 32767
loses up to one LSB, measured (A1/P1b).

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement |
|---|---|---|---|---|---|
| M1 | On the test material, multiplier character at Depth 1, Mix 1, Balance 0, Program Bal 0: 1000 and 2000 Hz within 0.5 dB of each other, and each of 500, 1500, 4000, 5000, 7000, 8000 Hz at or below −60 dB re those two | S1 for the structure — a multiplier's output is the sum and difference alone, and S1's Ex. 1 shows 1000 Hz × 900 Hz giving "two frequencies, 100 Hz and 1900 Hz" | high for the structure; **the −60 dB number is this seed's**, no 6401 suppression specification was reached (§8.4) | any named component above −60 dB | SB |
| M2 | Unity level law, not a bare product: a 500 Hz sine program at **−6 dBFS peak** against a full-scale 1500 Hz carrier, multiplier character at Depth 1 and Mix 1, gives output RMS within **0.5 dB** of the program's own RMS, with no sample within 1 LSB of the rails. The named level is part of the trait: a bare product of two sines is exactly −3.010 dB on RMS, so Bode's law implies a **+3.01 dB makeup on the wet path** — declared, wet path only — and at a full-scale program that makeup would peak at 1.414× full scale (both A1/P10). An earlier draft asked for unity at a full-scale program, which no build can meet | S1 Ex. 1 verbatim: "If the magnitudes of the inputs are both 1.0 volt RMS, the magnitude of the total output of the described standard model will also be 1.0 volt RMS"; the two figures are this run's arithmetic | high | RMS off by more than 0.5 dB — in particular −3.0 dB, which is the makeup missing — or any sample at the rails | LVL |
| M3 | Bandwidth doubles: a program band-limited 0–100 Hz with a 900 Hz carrier gives −20 dB edges at 800 ± 10 and 1000 ± 10 Hz, energy outside 780–1020 Hz below −40 dB. The probe's own band-limiting filter is measured first and its −20 dB edge recorded, because the sharpness of the output edge is the probe's and only the *position* is the class's | S1 Ex. 3 ("the bandwidth of the output is twice the bandwidth of the program input") | high | an edge outside ±10 Hz of where the probe's own edge predicts it, or skirts above −40 dB | BW |
| M4 | The inputs are not interchangeable: at Carrier Low's **5 Hz default** a 2 Hz carrier gives sidebands **8.6 ± 1.5 dB** below a 200 Hz carrier's at equal level, while a 2 Hz program passes within **0.5 dB** of a 200 Hz program | S1 (the program enters directly, "from DC to very high frequencies", the carrier through the input transformer) and S2 (T2 on the carrier diagonal, the program on the top rail through R11 1 kΩ) for the asymmetry; S8 for the corner (the A-20 "craps out at 5 Hz"). The 8.6 dB is arithmetic on §4's own first-order high-pass at that corner, 20·log₁₀(2/√(2²+5²)), A1/P10. **An earlier draft asked for ≥12 dB, which §4's model cannot reach** — that needs a corner near 8 Hz, above anything S8 supports | medium — the asymmetry is Bode's and the corner is S8's; **the ±1.5 dB window is this seed's** | a difference outside 8.6 ± 1.5 dB, including a carrier path flat at 2 Hz (under 1 dB); or a program path down by more than 0.5 dB at 2 Hz | SWEEP |
| M5 | The quiescent carrier is gated, not merely balanced: Squelch on + full-scale carrier + silent program + Balance detuned 0.2 → every sample exactly zero; Squelch off, same detune → a carrier-frequency component above −60 dBFS | S1 (the gate, the squelch switch, and "the ring modulator balancing adjustments (which normally remain untouched)"); S2 (CR-1…CR-4 in the carrier path, the THRESHOLD pot, the two 1 kΩ balance trims) | high for the mechanism; **the −60 dBFS residual bar is this seed's**, not Moog's (§8.4) | a non-zero sample with Squelch on, or no residual with it off | GATE |
| W1 | On the same material, switching character at **Shape 1** (the full chopper), Depth 1, Mix 1: 4000 and 5000 Hz (3f₂±f₁) sit at **−9.5 ± 3 dB** and 7000 and 8000 Hz (5f₂±f₁) at **−14.0 ± 3 dB** re the first pair, falling monotonically with order, while 2500 and 3500 Hz (2f₂±f₁) stay below **−40 dB** | S1 verbatim on the switching type: "The resulting sidebands are comprised of the frequencies f2−f1, f2+f1, 3f2−f1, 3f2+f1, 5f2−f1, 5f2+f1, and the further odd harmonics of f2, minus and plus f1". The two centre values are the ideal 50 %-duty chopper's 1/3 and 1/5 — **−9.54 and −13.98 dB**, computed this run (A1/P10) — so the row is two-sided rather than a floor | high for the structure (odd orders of the carrier, no even ones); **the ±3 dB windows and the −40 dB floor are this seed's** | 3f₂±f₁ outside −9.5 ± 3 dB — the multiplier's own build puts them at −101 dB, the Q15 floor (A1/P5) — or an even product above −40 dB, which is a duty that has drifted off 50 % | SB |
| W3 | *(No longer conditional on a node — the palette reaches it; see §5's refutation.)* The program passes the diode curve too, not only the carrier: switching character, Shape 1, carrier held at DC (Frequency 0), full-scale 500 Hz program, spectrum normalised to its own peak → third harmonic **above −30 dB** re the fundamental | S3 (the ring's own bias point and its diode conduction law); S4 (the four-path structure, each path a diode nonlinearity the program passes through) | medium-low — the mechanism is sourced; **the −30 dB bar is this seed's** | h3 at or below −30 dB, and in particular at the Q15 floor (≈ −100 dB), which is what any build whose shaping is baked into a carrier-phase table gives — see §5 | DC-H |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

- **S1.** H. Bode, "The Multiplier-Type Ring Modulator", *Electronic Music
  Review* No. 1, Jan. 1967, pp. 9–15, intro. R.A. Moog — Synth-Werk scan, text
  layer via `pypdf`. No license on the scan; the host's own footer, fetched by
  the audit, reads "© 2026 SYNTH-WERK" with Legal Notice and Terms links — which
  is the scanning site's line, not the 1967 journal's, and neither licenses the
  article: **unverified, read as a paper** (vision §5).
  <https://www.synth-werk.com/sites/default/files/pdf/electronic%20music%20review%20No1.%201967.pdf>

*(from §2)*

- **S2.** R.A. Moog Co., "BODE RING MODULATOR MODELS 6401 & 6402 — SCHEMATIC",
  drawing 1113, 10-21-66 — Bob Moog Foundation JPEG, read at 3–6× enlargement.
  The attachment URL redirects to a bare JPEG carrying no license; the site's own
  footer, checked separately, reads "© 2026 The Bob Moog Foundation" with no
  terms page found — so this is **verified site copyright, no stated terms; read
  as a document**; nothing reproduced, no netlist transcribed.
  <https://moogfoundation.org/schematics/attachment/470/> (it redirects to
  `https://moogfoundation.org/wp-content/uploads/470.jpg`; the audit reached it
  both with `curl` and with the fetch tool, so an earlier note here saying the
  fetch tool refuses this host is struck. What the host serves is a 1000 × 747
  rendering of a 6686 × 5138 original, per the file's own EXIF — legible when
  cropped and enlarged, and the ceiling on how much of the drawing can be read)

*(from §2)*

- **S3.** R. Hoffmann-Burchardi, DAFx-08 (2008), "Digital Simulation of the Diode
  Ring Modulator for Musical Applications". No license line: **read as a paper**.
  <https://www.dafx.de/paper-archive/2008/papers/dafx08_29.pdf>

*(from §2)*

- **S4.** J. Parker, DAFx-11 (2011), "A Simple Digital Model of the Diode-Based
  Ring-Modulator". No license line: **read as a paper**.
  <https://www.dafx.de/paper-archive/2011/Papers/66_e.pdf>

*(from §2)*

- **S5.** H. Bode, "History of Electronic Sound Modification", *JAES* 32(10)
  1984, repr. *eContact!* 13.4. No explicit license found: **read as a paper**.
  <http://www.econtact.ca/13_4/bode_history.html>

*(from §2)*

- **S9 (new).** Moog Archives, "Bode Ring Modulator 6401 and Dual Ring Modulator
  6402", `http://moogarchives.com/bode640x.htm` — HTTP 200 with `curl`. It is a
  **serial-number and sales ledger** ("Manufactured by the R.A. Moog Company,
  Trumansburg, New York"; 6401 s/n 1001 to Jan Nordmark, 21 Aug 1967; 6402 s/n
  1004 to Motown Records; and so on), not a circuit document, so it adds
  provenance and nothing to the trait table. No copyright statement on the page:
  **unverified, read only.**

*(from §2)*

- The IRCAM mirror of S4 also answers over plain HTTP —
  `http://recherche.ircam.fr/pub/dafx11/Papers/66_e.pdf`, HTTP 200, re-checked
  by the second audit pass (the URL was split across a line break here and is
  now written whole). The dafx.de copy was used and stands; the mirror is
  recorded only so the next run does not repeat the "unreachable" call.
**Unsourced, kept out of the trait table:** the ring diodes' part number (S2's
general note says 1N485A; the four are marked only "SELECT DIODES"); the A-20's
ratio as the diodes see it *inside this instrument* — S8 does give the part as a
500:500 Ω 1:1 line transformer, measured, with saturation dominating below about
5 Hz, which is what M4 leans on; the 6401's own carrier-suppression figure. No
emulator was read for code. **Struck from this list by the audit:** whether the
6402's channels share a carrier bus — the drawing's own general note answers it,
"ALL CIRCUITRY IS DOUBLE IN #6402 EXCEPT FOR POWER SUPPLY" (S2).

*(from §2)*

**Audit record — second pass, 2026-09-06 (license and citation, independent of
the research run and of the first audit).** Every source was fetched again from
scratch: S1, S3 and S4 as their PDFs (text re-extracted; S1's pagination
re-checked — the running heads run `JANUARY 1967 9`, `10 ELECTRONIC MUSIC
REVIEW`, `JANUARY 1967 11`, `12 …`, `13`, `15`, so pp. 9–15 holds), S2 as its
JPEG (the Foundation serves a 1000 × 747 rendering of a 6686 × 5138 original,
read at 2×, which is legible across the whole sheet), S9 as raw HTML over plain
HTTP, and S5, S6, S7 and S8 through the fetch tool.

*(from §2)*

Confirmed on the drawing (S2), each item read this run: `SELECT DIODES` at
CR-5…CR-8, R16–R19 at 470 Ω, R12/R13/R22/R23 at 1 kΩ, the 1 kΩ `BALANCE` and
`BAL` trims, `1.0 V RMS APPLIED` and `1.0 RMS APPLIED` at the two jacks,
`0.16 RMS` at the carrier transformer, `0-10 RMS` on the program line,
`SQUELCH ON-OFF`, `THRESHOLD`, CR-1…CR-4 on the carrier input board, the
`PROGRAM INPUT AND SQUELCH TRIGGER BOARD`, the general notes `ALL DIODES 1N485A
UNLESS NOTED` / `ALL TRANSISTORS 2N2925 UNLESS NOTED` / `ALL CIRCUITRY IS DOUBLE
IN #6402 EXCEPT FOR POWER SUPPLY`, and the title block `BODE RING MODULATOR
MODELS 6401 & 6402 — SCHEMATIC`, `DATE 10-21-66`, `DRAWING NUMBER 1113`,
`R. A. MOOG CO. TRUMANSBURG, N.Y.`

*(from §2)*

Confirmed verbatim in S1: the "square law" sentence, "from DC to very high
frequencies", the Fig. 4 caption, Ex. 1 (including "If the magnitudes of the
inputs are both 1.0 volt RMS, the magnitude of the total output … will also be
1.0 volt RMS", which is what M2 rests on), Ex. 3 (800–1000 Hz out of a 0–100 Hz
band on a 900 Hz carrier, "the bandwidth of the output is twice the bandwidth of
the input"), the gate chain ("preamplifier … rectifier, a ripple filter, and a
Schmitt-trigger circuit"), and "the ring modulator balancing adjustments (which
normally remain untouched)". Confirmed in S4: "The structure itself requires 10
operations per sample, along with 4 calls to the diode-shaping function. The
diode-shaping function requires 14 operations each time it is called" — the
arithmetic behind Tier 3's 66 — and "harsher and brasher than that of simple
digital multiplication". Confirmed in S3: the D1/D2-conduct, D3/D4-block
description and the carrier currents cancelling at the second transformer.
Confirmed in S9 over `http`: the ledger lines this seed quotes.

*(from §2)*

- **"Basically equivalent" is not a phrase in S1.** The article's sentence is
  "Basically, however, the two inputs for the ring modulator are equivalent."
  §1 now quotes the sentence.

*(from §2)*

One caveat on a quotation this pass would not leave silent: W1's sideband list
is presented as S1 verbatim, and it is a *corrected* transcription of a 1967
scan — the OCR of the page reads "f2-k f2+fr, 3f2-f1, 3f2+fr, 5f2-f1, 5f2+f1,
and the further odd harmonics of f2, minus and plus fl". The structure (odd
orders of f₂, no even ones) is unambiguous in the source; the clean subscripts
are this dossier's rendering of a damaged scan, not the page's own characters.

*(from §3)*

Kit measurements, named here and defined in A4: **SB** sideband spectrum (500 Hz
sine program × 1500 Hz sine carrier, full depth, 32768 frames, Hann FFT, peaks in
±4-bin windows); **LVL** RMS and peak per channel; **BW** band edges of an
averaged noise-render spectrum; **SWEEP** sideband amplitude vs carrier frequency
then vs program frequency over 1–200 Hz; **GATE** silence-after-burst plus a
carrier-bin spectrum; **SIEVE** an aliasing sieve on its **own** material —
523 Hz program × 1481 Hz carrier, never SB's 500 × 1500, for the reason measured
in A1/P11; **DC-H** harmonic spectrum with the carrier held at DC. Unless a row
says otherwise every measurement runs at Balance 0, Program Bal 0 and Mix 1, so
that a trim the surface offers cannot be mistaken for the trait.

*(from §3)*

**W2 and W3 cannot both be met as they are written** (palette-verifier pass,
2026-09-06, measured — A1/P18). W2's sieve accepts only
{ |±f₁ ± m·f₂| : m odd }, i.e. the **first** harmonic of the program and odd
harmonics of the carrier. W3 requires the program to pass a curve, which puts
odd harmonics of the program into the ring, and their products with the carrier
land outside that set. Rendered: the same chain that meets W3 puts **88 Hz and
3050 Hz at −21.9 dBFS** on W2's own 523 × 1481 material — these are
`|3f₁ − f₂|` and `|3f₁ + f₂|` — and W2's sieve rejects both. That is not an artefact
of the refuting build: Parker's four-path structure (A3), the very structure the
node ask would buy, produces the same terms. Two ways out, and Station A picks
one before the rebuild: widen the sieve set to
{ |±k·f₁ ± m·f₂| : k odd, m odd } so it still catches aliasing but not the
program's own harmonics, or drop W3's requirement from the character. Widening is
the recommendation, because the aliasing W2 exists to catch is *broadband* — the
1× chopper fault A1/P11 measured put 1130 bins off-set at −24.6 dB, where a
program third harmonic adds two lines.

*(from §3)*

**Multiplier character, and the switching character on the palette (baked table):
P4 1 %, S3 2 %** of one stereo block's deadline — per sample one Q15 multiply,
one blend, one clamp (`audioif_multiply.c:38-45`); the shaping happens once in
Python at construction. **Switching character with a program-path
`audiofilters.Distortion` — the §5 refutation's build, which is what W3 now
costs:** the baked table plus one `Distortion` pass, a double `pow` per sample
with no oversampling (`audioif_distortion.c:14`, `:17`). Station A prices that on
both boards; it is the number that decides whether W3 ships or the character
stays at three traits. **Switching character through the waveshaper node, if it
lands for the Drive family (§5):** 10 operations plus four shaper calls of 14
(S4) ≈ 66 per sample before oversampling; at ×8, P4 **10 %**, S3 **30 %**. Lean
patch expected: **no** for the first two, **yes** for the last two — the lean
patch drops back to the baked table alone and records W3 as not carried. RAM: one carrier table, 4 bytes per frame; 2048 frames
is 8 KB stereo, rebuilt on a Frequency/Depth/Shape/Balance move, never on pull.

*(from §3)*

**Latency: 0 samples (0.0 ms at 48 kHz); `tail_samples` 0** — the ring is
memoryless and so is the model. **No option adds latency**, and one is
deliberately refused: the Squelch gate (M5) is a level follower with an attack
ramp, not a lookahead gate, because vision §9a puts the effects' share at zero.
If N1 lands its oversampling uses polyphase filters, which cost but do not delay;
a linear-phase decimator is refused for the same reason. The gate's click
measurement verifies `latency_samples = 0` at 48 kHz and 44.1 kHz.

*(from §4)*

Python computes, at construction and on a macro move, one `audiocore.RawSample`
holding a whole number of carrier cycles — looping is free because `RawSample`
returns its whole buffer every pull (`upstream-diff.md:714` §). Into it go, in
order: the carrier waveform; the **Shape** law of the character; the **Depth**
blend between a constant and full swing; the **Carrier Low** first-order
high-pass (analytic, one line, no node — M4); and the **Balance** offset, since a
DC term in the table *is* carrier feedthrough (Program Bal is the matching DC
term on the signal side). The switching character bakes its shaping here, which
is the part worth noticing: computed in Python from a closed form, the table's
harmonic series is **truncated below Nyquist before it is written**, so W2 is met
by construction rather than by oversampling — cheaper *and* cleaner than a
runtime shaper. Tables are computed on CPython, never on a board mid-render (the
ESP32 ports are single-precision). **The squelch (M5)** is a block-rate
program-level follower driving `mix`: below threshold `mix = 0`, a bit-exact wire
(`audioif_multiply.c:28-29`). Block rate is honest — Bode's gate is a rectifier
into a ripple filter into a Schmitt trigger (S1), slower than a block. **Mono
sources:** not stereo by definition; a mono source gets the same ring on one
channel, the stereo-phase macro reads inactive, and the kit measures that.
**Rejected as *the ring's* shaper:** `audiofilters.Distortion` — four curves that
are a `pow`, an `exp` pair, a rational waveshaper and a bit-mask
(`audioif_distortion.c:16-33`), none a diode-ring transfer, and a ported node
that never changes. Three of the four run in double per sample
(`audioif_distortion.c:14`); the bit-mask (`LOFI`) is integer-only when
`soft_clip` is off, because the double block is guarded at
`audioif_distortion.c:13` — a small correction to this seed's first draft, which
said all four were double. Rejected as the *ring*, but **not** rejected as a
program-path nonlinearity: a `Distortion` in the program path is what refutes
this seed's node ask (§5). **Also rejected:** `synthio`'s ring modulation
reaches a *note* and nothing else (`upstream-diff.md:727-729`, inside the section
opening at `:714`).

*(from §5)*

**REFUTED BY PALETTE** (palette-verifier pass, 2026-09-06). W3 as it is written
does not say the program's nonlinearity has to live *inside* the ring, only that
the program passes a curve; and the palette has a per-sample static shaper for a
signal stream that is not a table indexed by carrier phase —
`audiofilters.Distortion`, a ported node used as it stands, placed in the program
path *before* `Multiply`. Measured this run (A1/P18): `RawSample(500 Hz,
full scale) → audiofilters.Distortion(CLIP, drive 0.3) → Multiply(carrier held at
DC)` gives **h3 = −21.2 dB** re the fundamental against W3's −30 dB bar, 8.8 dB
of margin; the same chain with the `Distortion` removed gives **−99.3 dB**, the
Q15 floor this ask predicts. The refuting build was also checked against the
character's other rows so the refutation is not hollow (A1/P19): on SB's own
500 × 1500 material it still passes W1 — 3f₂±f₁ at −10.9 / −10.3 dB inside
−9.5 ± 3, 5f₂±f₁ at −15.9 / −15.2 inside −14.0 ± 3, 2f₂±f₁ at −145 dB, far under
−40 — and its RMS sits +1.86 dB high against W4, which one static `post_gain`
trim removes (the un-distorted control is already −0.53 dB off, so the table, not
the shaper, is what W4 has to be trimmed against). The node is therefore **not
asked for on this class's account**. It costs a double `pow` per sample with no
oversampling (`audioif_distortion.c:14`, `:17`), which is a Tier 3 question for
Station A, not a reason to add a node.

*(from §5)*

**What would re-open it.** W3's source column describes a mechanism the refuting
build does *not* have: in the ring the program's operating point is set by the
carrier, so its distortion varies with carrier level, where a fixed `Distortion`
in the program path is carrier-independent. If Station A wants the mechanism
rather than the number, W3 must be **restated** so that the palette route fails
it — the natural form is "h3 with the carrier at DC changes by at least *n* dB
between two carrier amplitudes", which no static program-path shaper can produce
— and the ask re-opened with that measurement attached. Restating a trait to make
a node necessary is only legitimate before any code exists, which is now; it is
recorded here so the change is visible rather than quiet.

*(from §7)*

- `modulation.py:189-191`: at Depth 0 the table is a constant 32767 and `mix`
  stays at 1, so "no effect" is one LSB down, not a wire — measured at −1 LSB and
  never +1, because the Q15 shift floors (A1/P1b). Depth 0 must set `mix = 0`.

*(from §7)*

- Checked and **cleared**, not a defect: the whole-cycle table rounding
  (`modulation.py:185-186`) detunes the carrier by under half a cent from 20 Hz
  to 4 kHz (A1/P4b) — worth measuring rather than asserting.
