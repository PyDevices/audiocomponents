# Effects Dossier — `Tremolo` (Fender amp tremolos: bias-vary and optical)

**Class:** `lib/audioeffects/modulation.py` — read once, for §7.
**Family / phase:** Modulation, roadmap Phase 3
**Standout:** Fender amp tremolos, per vision §4.2 — **confirmed as the proposed
pair**, with the referents fixed by this run's reading: the *bias-vary* character
follows the **Princeton 6G2** (S1; the 6G16 Vibroverb analysis, S4, is a second
read of the same idea), and the *optical* character follows the **AB763**
blackface circuit (S2, S3). A third Fender type, the brownface "harmonic
vibrato", is real (S6, S12) and is deliberately **not** carried as a character
here — see §8.6.
**Grade:** circuit — both schematics reached and read with values (S1 as page
images, S2 as a layout text layer), the LFO's frequency law is analytic (S5) and
the optical shunt is a resistive divider that solves in closed form. The one gap
is the bias-vary *gain-versus-bias* curve, which needs the SPICE run in §8.1
before B1's number is anything but a bound.
**Portability tier:** needs audioif-own nodes (`audiomath`)
**Status:** seed (Phase 0), rewritten 2026-09-06 from re-reached sources (an
earlier draft of this file existed; every source below was fetched again this
run and two of that draft's claims were corrected — see §8.7). Sections 4 and 5 were re-verified against the C under `audioif/src/shared` and the bindings under `audioif/src/<module>/`, and probed on the CPython build, by the palette verifier on 2026-09-06; the corrections and the node-ask verdicts are marked in place.

## 1. The circuit, in one paragraph

Both characters share one **LFO**: a 12AX7 inverting stage whose plate feeds
three cascaded RC sections back to its own grid — a phase-shift oscillator
running where the three sections total 180° and the stage's gain exceeds about
29, at `fo = 1/(2π√6·RC)` for equal sections (S5). On the 6G2 that stage has a
**220 kΩ** plate load to B+ with the plate itself marked **+200 V** on the
drawing, a **3300 Ω** cathode bypassed by **25 µF**, sections of **.01 / .01 / .02 µF** against **1 MΩ** shunts, a **3 MΩ
reverse-audio SPEED pot in series with 100 kΩ** as one section's shunt, and
**56 kΩ** to the tremolo-pedal jack that kills it (S1). The AB763 is the same
shape — 220 kΩ plate, 2.7 kΩ cathode, 25 µF bypass, sections of .01 / .01 /
.02 µF against 1 MΩ, "Tremolo Speed 3M Rev log" and "Tremolo Intensity 50K Rev
log" with a "Max Speed" resistor (S2; S3 states the three tremolo caps
independently as "Two are .01uF and the other is .02uF"; the forum thread's
recollection of 22 µF and .022 µF is S7b's, and the drawing is preferred) — and
because **one pot moves one section**, frequency and amplitude move
together: in Aiken's single-pot example the swing falls from 204 V at 6.5 Hz to
163 V at 2 Hz (S5). The waveform is a sine with "a 'kink' at the bottom edges"
(S5); the usable span is about 3–10 Hz, and the oscillator drops out past the
ends or with a lower plate load (S7b). **Bias-vary (6G2):** the plate feeds
**220 kΩ** and **0.1 µF** into a **250 kΩ linear-taper INTENSITY** pot — the
drawing marks it **250K-L**, against **1M-A** for Tone and Volume and **3M-RA**
for Speed on the same sheet, so the L is linear and this seed's earlier
"audio-taper" reading was wrong (audit, this run) — and that pot sets
how much swing rides on the **−35 V** fixed-bias line, which reaches both
**6V6GT** grids through **220 kΩ 5 %** resistors (S1). The nonlinearity *is* the
output stage: the swing stays inside class AB so the trough softens rather than
cuts off, "smooth, watery — with a soft edge to its rise and fall even at higher
intensities" (S4 — whose amp is the 6G16 with 6L6s, the same bias-vary idea in a
different output stage, and which says the "negative swings of the bias voltage
are short of forcing the amp into Class B operation or beyond"); shifting the
bias point "will cause clipping and distortion, which might add some pleasing
harmonics as well as modulate the volume" (S7a). On the symmetry S7a is explicit
and says the opposite of what an earlier draft of this seed recorded: the
clipping "would theoretically be symmetrical" *because* the swing is applied to
both sides of the push-pull, and is asymmetric in practice only because "it is
not likely that both sides will saturate at exactly the same grid voltage" — the
audit corrected the draft's "because both tubes move together" against the
source. An amp idling hot in class A makes the tremolo "mostly stop working"
(S7c). **Optical (AB763):** the
oscillator's other triode half is the "Tremolo Driver" (S2), lighting a neon lamp
sealed against a photocell — the "Roach", with its own "Bulb Resistor" (S2). The
neon strikes at a threshold, about 90 V, so the light is a pulse and not a sine
(S6), and the cell falls fast and recovers roughly ten times slower (S8, S9,
S10). The cell shunts the vibrato channel's signal node to ground through a
**50 kΩ reverse-audio INTENSITY** pot (S2, S3), injected **at the vibrato
channel's own 220 kΩ mixing resistor**, ahead of the point where the two
channels' mixing resistors join — which is why only that channel is modulated;
moving the wire *past* that junction is Robinette's "Add Tremolo to Both
Channels" mod, not the stock circuit (S3; an earlier draft of this seed had the
stock and modified positions the wrong way round). So the effect is "a volume
control that moves up and down
at the LFO's frequency" (S7a) — a divider near unity when the cell is dark (about
2 MΩ, S11) and deep when it is lit. Panel on both: **Speed**, which moves
frequency *and* swing, and **Intensity**.

## 2. Sources and license calls

All reached this run, fetched 2026-09-06, none from memory. What each gave, in
full, is Appendix A0.

- **S1.** Fender "Princeton" schematic, model 6G2 — schematicheaven PDF, …  *(argument in full: App. R)*
- **S2.** Rob Robinette, AB763 Deluxe Reverb layout (DIYLC PDF, text layer via …  *(argument in full: App. R)*
- **S3.** Rob Robinette, "AB763 Mods". No copyright statement in the fetched …  *(argument in full: App. R)*
- **S4.** Amp Books, "Fender Vibroverb 6G16 Tremolo Circuit". "© 2005-2026 Amp
  Books LLC": **read only**. <https://www.ampbooks.com/mobile/classic-circuits/vibroverb/>
- **S5.** Aiken Amplification, "Designing Phase Shift Oscillators for Tremolo …  *(argument in full: App. R)*
- **S6.** Effectrode (Phil Taylor), "Delta-Trem In-depth". Footer verbatim: …  *(argument in full: App. R)*
- **S7a/b/c.** The Amp Garage forum, `t=10265` (how each type works), `t=29561` …  *(argument in full: App. R)*
- **S8.** Wikipedia, "Resistive opto-isolator". **CC BY-SA 4.0.**
  <https://en.wikipedia.org/wiki/Resistive_opto-isolator>
- **S9.** Rich Holmes, "Vactrol information", quoting PerkinElmer's catalogue. …  *(argument in full: App. R)*
- **S10.** PerkinElmer VTL5C3/5C4 datasheet, qsl.net mirror PDF, text extracted.
  No license text; **datasheet facts**. <https://www.qsl.net/wa1ion/vactrol/vactrol.pdf>
- **S11.** Watford Valves, "Fender opto trem/vib" replacement. "© 2026 Watford …  *(argument in full: App. R)*
- **S12.** Carl's Custom Amps, "Types of Tremolo in Tube Amplifiers". No
  copyright seen: **read only**. <http://carlscustomamps.com/types-of-tremolos-in-tube-amps>
- **S13.** Duncan Amps TDSL, 6V6-GT. "copyright 1997-2026 Duncan Amplification
  Limited": **facts**. <http://tdsl.duncanamps.com/show.php?des=6v6gt>
- **Local:** `audioif/src/audiomixer/Mixer.c`, `src/cpython/audiomixer.py`,
  `src/shared/audioif_multiply.c`, `docs/upstream-diff.md`; the probes in A1.
  **MIT (audioif).**

- **The INTENSITY taper was wrong.** §1 read "250 kΩ audio-taper"; the drawing …  *(argument in full: App. R)*
- **The +200 V is the plate, not the supply.** The drawing marks +200 V at the
  12AX7 plate; the 220 kΩ runs from there to the B+ node. §1 and A0 corrected.
- **A0's "1500 screen resistors" are grid resistors.** On the drawing the two …  *(argument in full: App. R)*
- **§8.7's strike against S8 is itself wrong, and this pass could not edit §8.** …  *(argument in full: App. R)*

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

Kit measurements, defined in A3: **ENV** the extracted per-channel envelope of a
full-scale 1 kHz tone over eight LFO periods (peak-track, 1 ms hop) with its
depth, harmonics, slopes and duty reported; **BLOCK** the block-product bands of
a 1 kHz tone's spectrum; **STFT** a time-resolved harmonic spectrum, 10 ms hops.

**Shared LFO** (both characters).

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| L1 | The modulation is per sample, not per block: with a 1 kHz tone at Rate 3, 5 and 10 Hz and Depth 1, no component within ±30 Hz of 1000 ± f_s/256 or 1000 ± 2·f_s/256 — 187.5 and 375 Hz at 48 kHz, the render block being 256 frames — rises above **−80 dB** re the tone | vision §6 on block-rate nodes … (App. L1) | high | any product above −80 dB in those bands | BLOCK |
| L2 | Depth falls with Rate at fixed Intensity, because one pot moves one section of the phase-shift network: with Speed Link on, the envelope depth in dB at 3 Hz is strictly less than at 8 Hz, and the difference lies between **1 and 6 dB** | S5 for the mechanism and its own single-pot … (App. L2) | medium — the … (App. L2) | a difference below 1 dB (depth independent of Rate) or above 6 dB | ENV |
| L3 | The LFO is a near-sine, not a triangle and not a square: the envelope's harmonics of the Rate all sit below **−26 dB** re its fundamental at Depth ≤ 0.5 in the bias character — the kink is a small distortion, not a shape | S5 ("a small amount of harmonic distortion … … (App. L3) | medium — the shape is … (App. L3) | any harmonic above −26 dB; in particular an h3 near −19.1 dB (triangle) or −9.5 dB (square) | ENV |
| L4 | Rate spans at least 3–10 Hz on the amp patches, and the measured envelope fundamental equals the Rate macro's engineering value within **1 %** | S7b only, verbatim: "3Hz to 10Hz is typical … (App. L4) | high for 3 Hz … (App. L4) | Rate error above 1 %, or an amp patch that cannot reach 3 or 10 Hz | ENV |

**Bias-vary character.**

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| B1 | The gain envelope is asymmetric about its mean: at Depth 1, the mean being the arithmetic mean of the **linear** gain envelope over one whole period, the trough sits further below that mean in dB than the crest sits above it, by at least **1 dB**, because the stage's gain follows the pair's transconductance along a curve that flattens toward cutoff | S1; S7a; S13 | low-medium … (App. B1) | a measured trough-versus-crest asymmetry under 1 dB, or §8.1's SPICE gain-versus-bias curve coming back linear over the Intensity swing — in which case B1 is dropped with that record and the envelope is a plain sine | ENV |
| B2 | Depth is bounded and saturating, never a mute: at Depth 1 the trough sits **above −40 dB** re the crest, and the depth in dB added over the last 20 % of Depth travel is **smaller than** the depth added over the first 20 % | S4 ("negative swings of the bias voltage are … (App. B2) | medium — the … (App. B2) | a trough at or below −40 dB at Depth 1 (a mute), or a last 20 % of travel that adds at least as much depth as the first | ENV |
| B3 | Depth depends on the idle bias: between the Bias macro's ends the envelope depth changes by at least **6 dB** at fixed Intensity, shallower toward hot | S7c; S4 | medium — the … (App. B3) | a depth change under 6 dB between the Bias macro's ends — including none at all — or a change that runs the other way, deeper toward hot | ENV |
| B4 | The clipping threshold moves with the bias: with a full-scale 200 Hz tone at Rate 4 Hz and Depth 1, the third-harmonic level over the LFO cycle is not constant — averaged over the tenth of the period centred on the envelope's minimum it is at least **3 dB** higher than over the tenth centred on its maximum — while at Depth 0 it sits at the wire's floor. *Requires the waveshaper node (§5 N2); without it the character omits this trait and says so* | S7a; S6; S1 | medium (mechanism) / … (App. B4) | h3 flat over the cycle at Depth 1 with the node present | STFT |
| B5 | The bias envelope is time-symmetric, where the optical one is not: at Rate 5 Hz and Depth 1 the steepest falling and steepest rising envelope slopes in dB/ms differ by a factor **below 1.5** — a static gain law driven by a near-symmetric LFO has no memory to make a fast edge and a slow one, and L3's kink is the only asymmetry in it | S4 ("a smooth, watery response … (App. B5) | medium — the sourced … (App. B5) | a slope ratio of 1.5 or more in the bias character, which is the signature of an optical-style two-rate tracker having leaked into the bias law | ENV |

**Optical character.**

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| O1 | Gain falls faster than it recovers: the steepest downward slope of the envelope in dB/ms is at least **twice** the steepest upward slope, at Rate 5 Hz and Depth 1 | S8 ("the response to switching the … (App. O1) | high for the … (App. O1) | slopes within a factor of two, or a rise faster than the fall | ENV |
| O2 | The modulation is pulse-shaped, not sinusoidal: at Depth 1 the fraction of the period spent below the mid-depth level is **under 47 %**, and the envelope's second harmonic of the Rate is **above −20 dB** re its fundamental — two readings of one fact, since a rectangular envelope crosses −20 dB of h2 at a duty of about 47 % (0.46 → −18.0 dB, 0.48 → −24.1 dB, computed this run, A1/P8) | S6 (the neon "requires a certain minimum … (App. O2) | medium — the shape is … (App. O2) | a duty at or above 47 %, or an h2 at or below −20 dB — either is the symmetric sine this character is not | ENV |
| O3 | Depth is a resistive divider, not a gate: at Depth 0 the class is a wire; at Depth 1 the trough is a finite attenuation between **−15 and −40 dB**, never silence | S2, S3; S11 (2 MΩ dark); S7a | medium — the lit … (App. O3) | a trough below −40 dB (a gate) or above −15 dB (no bite) at Depth 1 | ENV |
| O4 | The cell's lag smooths fast rates: at Rate 10 Hz the envelope depth is at least **2 dB** less than at 3 Hz for the same Depth and Lag, independently of L2; with Lag at its minimum the loss vanishes | S8, S9, S10 | medium — the lag is … (App. O4) | a loss under 2 dB from 3 to 10 Hz at the default Lag — including none at all — or a loss that survives Lag at its minimum, which would mean the smoothing came from something other than the cell | ENV |

Characters each own their rows; a character that fails its traits cannot hide
behind one that passes (vision §10.7).

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Topology: `source → audiomath.Multiply(modulator = one stereo LFO period)`.**
One node, the same one `AutoPan` and `RingMod` use. The modulator is an
`audiocore.RawSample` holding exactly one period at the output rate, Q15 unipolar
(0…32767 = gain 0…1); `Multiply` loops it because `RawSample` returns its whole
buffer every pull (`upstream-diff.md:714` §), and a whole period makes the loop
point seamless. `mix` is 1 except at Depth 0, where it is 0 (the Tier 1 wire).
`audiomath` is audioif's own with no ancestor anywhere, so the tier is
**audioif**; it applies the modulator's two columns independently (A1/P4), which
is what makes Stereo Phase free — the same law written at two phases.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**N1 — a table-driven, phase-continuous LFO modulator inside `audiomath`
(conditional).** *Trait ids:* **none.** It unblocks no fixed trait: every trait
in §3 is reachable with a period table at the standout's own 3–10 Hz range, where
the table is ≤ 64 KB and fits both boards. What it addresses is the generalized
range (below about 1.5 Hz the table passes 128 KB) and the phase restart on every
Rate move, which is a click the class gate will measure but which no §3 trait
names. *Sketch:* `Multiply.modulate(table, rate_hz)` — a short Q15 table
(1024–4096 points, stereo allowed) read per sample with linear interpolation by a
phase accumulator whose rate changes without a phase jump; a few hundred bytes of
state; additive in audioif's own module. *Refutation record (Phase 0):* an ask
with no trait id is not an ask (vision §6), so this is recorded as a *conditional*
for the node list, not a request. It survives only if Station C's click
measurement on a Rate sweep, or the table-rebuild time on the S3 at 3 Hz, is
shown to fail the class gate. The seed's recommendation is to build on the
palette, measure, and then decide. `AutoPan` makes the same conditional ask and
would share the node.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

**Characters** (constructor option, house style as `Compressor` uses): **`bias`**
and **`optical`**. Each owns its trait rows in §3.

Macros (nine; ceiling sixteen), ranges in engineering values:

| # | Label | Mode | Range | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Rate | UNIPOLAR | 0.5–15 Hz, log; amp patches sit in 3–10 Hz | **Speed** (3M rev-log + 100 kΩ; S1, S2) |
| 1 | Depth | UNIPOLAR | 0–1; 0 is the Tier 1 wire | **Intensity** (250 kΩ log on bias, 50 kΩ rev-log on optical) |
| 2 | Shape | UNIPOLAR | 0–1 | bias: the oscillator's kink (0 pure sine, 1 the sourced kinked sine). optical: the neon strike threshold, i.e. the pulse duty (0 strikes early / wide dip, 1 strikes late / narrow dip) |
| 3 | Lag | UNIPOLAR | 5–100 ms, default 35 ms (optical only) | the photocell's dark recovery (S10's VTL5C3 decay figure) |
| 4 | Bias | UNIPOLAR | cold…hot idle (bias only) | the output stage's bias trimmer; hot shrinks the depth (B3) |
| 5 | Speed Link | TOGGLE | off/on, default on in amp patches | the one-pot oscillator's amplitude-with-speed coupling (L2, S5) |
| 6 | Stereo Phase | BIPOLAR | −180…+180° | none on the amp, which is mono; 180° is an opposed pair |
| 7 | Drive | UNIPOLAR | 0–1 (bias only, with N2) | how hard the signal sits against the moving clipping point (B4); pinned at 0 without the node |
| 8 | Sync | TOGGLE | off/on, default off | none on the amp; Rate quantised to the transport's tempo divisions |

No Mix macro: Depth 0 is the wire, and a tremolo has no wet/dry sense on its
panel. `capabilities = ("tempo_sync",)` (D10): the class reads `transport()` when
Sync is on and holds its previous Rate when there is no transport — the roadmap
names LFO-driven modulation as the candidate case, and a tremolo drifting against
the bar is the one thing a host cannot fix.

Patches (names describe settings, never products): 0 **Bias Wobble** (bias, 5 Hz,
Depth 0.5, Shape 0.5, Speed Link on); 1 **Bias Deep Slow** (bias, 3.5 Hz, Depth
0.9, Bias cold); 2 **Bias Warm Fast** (bias, 8 Hz, Depth 0.4, Bias hot);
3 **Opto Chop** (optical, 6 Hz, Depth 0.9, Shape 0.7, Lag 20 ms); 4 **Opto Soft**
(optical, 4 Hz, Depth 0.5, Shape 0.2, Lag 90 ms); 5 **Opposed Pair** (optical,
5 Hz, Depth 0.8, Stereo Phase 180°); 6 **Helicopter** (optical, 12 Hz, Depth 1.0,
Shape 0.6, Lag 5 ms, Speed Link off); 7 **Slow Swell** (bias, 0.8 Hz, Depth 0.7,
Speed Link off); 8 **Eighth Note Chop** (optical, Sync on, 1/8, Depth 0.9,
Shape 0.7).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/modulation.py` on 2026-09-06.

- `modulation.py:105` with `:82-89`: the modulation rides `MixerVoice.level`, a …  *(argument in full: App. R)*
- On CPython the Mixer never ticks that block input at all …  *(argument in full: App. R)*
- `modulation.py:86-89`: a `Mixer` sits at the class output, so on stock …  *(argument in full: App. R)*
- `modulation.py:103-104`: `scale = depth·0.5`, `offset = 1 − depth·0.5` — a bare …  *(argument in full: App. R)*
- `modulation.py:101`: `rate` is unbounded and unlogged; nothing stops a rate
  above the block rate.
- `modulation.py:98-100`: `MACRO_LABELS = ()` and one empty patch — no surface at
  all (vision §2.1).
- `tail_samples` reports `None` (measured, A1/P5); a gain envelope has no tail and
  the honest report is 0.
- `modulation.py:1-3`: the module docstring claims the block rate "is ample for
  musical sweep rates". The measurement says otherwise.

Nothing else about the old class is carried forward.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **The 6V6 gain-versus-bias curve (B1, B2, B3).** Station A runs the 6G2 output
   stage in ngspice with the bias stepped over the Intensity swing and exports
   gain versus bias. The tube model's parameters must come from a reached source
   — S13 gives operating points, not a model — which is itself part of the task.
   If the curve is linear over the swing, B1 is dropped with that record. Owner:
   Station A, before the rebuild.
2. **The Intensity pot's wiring in the AB763 (O3).** S2's text layer names the pot
   and the roach but not whether the 50 kΩ is in series with the cell or across
   it. Read the AB763 *schematic* drawing at Station A; the divider law in §4
   changes shape but not its bounds.
3. **The lit resistance of the Fender cell (O3).** Unsourced. Station A finds a
   measured figure from a reachable page, or treats it as the character's Depth
   ceiling and says so.
4. **The CPython Mixer never ticks its block inputs.** Not this class's bug, but
   every shipped class built on `_MixerMod` is frozen on CPython because of it.
   An audioif issue for Arthur to file, with A1/P5 attached.
5. **N1's survival** (§5): **settled — refuted**, palette-verifier pass
   2026-09-06. It names no trait, and the compose-first route measured in §4 and
   A1/P13 (`Mixer(loop) → SpeedChanger → Multiply`) reaches both things it
   addressed. What is left for Station C is not N1's survival but the table
   length that keeps the staircase's 256·Rate step rate clear of L1's bands
   across 0.5–15 Hz — 1024 points on the arithmetic, to be measured.
6. **Harmonic vibrato as a third character.** The brownface/blonde harmonic
   vibrato (S6, S12) is a different circuit — a phase-splitting crossover with two
   bias-modulated triodes — and would need its own trait set. A third character is
   a Phase 3 proposal for Arthur, not a seed's call.
7. **Two corrections to the earlier draft of this file**, both from re-reading the
   source this run: the "on/off switching rather than smooth control" phrase
   attributed to S8 is not in what S8 says (its wording is "resulted in a
   nonlinear modulation"), and the NSL-32SR2 "5 ms / 80 ms" figures are not on the
   page S10 mirrors. Both are struck; O1 and O2 now rest on S6, S8's actual
   wording, S9 and S10's VTL5C3 column. The survey audit should treat any other
   claim carried from that draft as unverified until re-fetched.
8. **How few traits the bias character can end with.** Two of its five rows are
   conditional: B1 is dropped if §8.1's SPICE curve comes back linear over the
   Intensity swing, and B4 is omitted if the waveshaper node (§5 N2) does not
   land. If both fall the bias character keeps **three** of its own — B2, B3,
   B5 — plus the four shared LFO rows, and stays at the Phase 0 gate's floor of
   three, not below it. A third drop would put it below that floor and the gate
   would have to record it; nothing is dropped without the written reason
   vision §3 requires. The optical character's four rows are unconditional.
9. **Thump.** The bias-vary LFO leaks to the output when the tubes mismatch
   (S7c). A "Thump" macro would put a sub-audio tone on the output with silence in
   — against Tier 1 — so it is off the surface; the implementation session may
   propose a signal-gated form.

---


## Appendix

### A0. What each source gave, in full

**S1 (Princeton 6G2 drawing).** Header "FENDER 'PRINCETON' SCHEMATIC / MODEL 6G2
/ CIRCUIT PATENT #2817708", margin "Fender Musical Instruments, a division of
Columbia Records Distribution Corp., Santa Ana, California U.S.A.", notes
"voltages read to ground with electronic voltmeter, values shown + or −20%".
Tremolo section, read at 3× and 5× enlargement: a 12AX7 whose plate is marked
**+200 V** with a **220K** plate resistor from it down to the B+ node, cathode
**3300** bypassed by **25/25** (µF/V), the
phase-shift network on the top rail carrying **.01**, **.01** and **.02** against
**1M** shunts, the **3M-RA SPEED** pot in series with **100K** to ground, and
**56K** to the tremolo-pedal jack. From the plate node: **220K** then **.1** into
the **INTENSITY 250K-L** pot, whose far end is the **Y** node marked **−35 V**;
that node carries **.05–200** to ground and feeds two **6V6GT(2)** grids through
**220K 5%** resistors, with a **1500** in series between that bias network and
each grid pin (an earlier draft called these screen resistors; on the drawing
they sit in the control-grid path the −35 V feeds). Bias supply from TR1
through **100K 5%** and **56K 5%** with **25–50** µF. Transformers TR1 125P1A,
TR2 125A10B; rectifier 5Y3GT; preamp 7025 and 12AX7.
**S2 (AB763 layout).** Text layer names "V5 12AX7 — A Tremolo Oscillator, B
Tremolo Driver", "Tremolo Speed **3M Rev log**", "Max Speed", "Tremolo Intensity
**50K Rev log**", "Roach", "Bulb Resistor", "Tremolo Tick Fix", "Bias **−35V**",
and board values including 220K, 100K, 82K, 47Ω and 0.02uF.
**S3 (Robinette, AB763 Mods).** The tremolo is a signal-shunt design; tremolo is
"injected at point Y … using the yellow wire from the Intensity Pot right
terminal" at "the other end of the mixing resistor"; the oscillator has "Two …
.01uF and the other is .02uF" disc caps, slowed by swapping the two .01s for
.02s; Intensity is "50K-RA (reverse audio)"; the max-speed resistor is "100k …
located on the Tremolo Speed pot"; V5 is the driver and its plate wire induces
"tremolo ticking"; "the tremolo intensity pot places a load on the guitar audio
signal".
**S4 (Amp Books, 6G16).** A three-section RC phase-shift LFO reaching 180° at
about 7 Hz, oscillating near 7.4 Hz in their SPICE; a DC-coupled cathode follower
buffers it; C4 blocks DC so the Intensity control combines the LFO's AC with the
**−52 VDC** bias; "When the control is fully clockwise, the −52VDC bias is AC
modulated to its maximum extent", but the negative swings stay short of class B;
the result is "a smooth, watery response — with a soft edge to its rise and fall
even at higher intensities" without "chopping out notes as you play".
**S5 (Aiken).** `fo = 1/(2·Pi·Sqrt(6)·R·C)` for a three-section phase-lead
network; oscillation needs amplifier gain above **29** for three sections, about
**18** for four; a single speed pot gives "an amplitude variation from 204V at
6.5Hz to 163V at 2Hz"; the plot shows "a small amount of harmonic distortion …
as evidenced by the 'kink' at the bottom edges of the sine wave"; design ranges
2–8 Hz (three pots) and 2–6.5 Hz (one pot).
**S6 (Effectrode).** Bias trem: the LFO "wiggles the bias voltage on the grids of
the power tubes"; "a slightly cockeyed, low frequency sinusoidal control
voltage"; the speed range is "typically 4 to 8Hz and at lower speeds the
oscillation collapses and ceases to operate"; it introduces crossover distortion
that is "highly objectionable, especially audible at low volume levels" with a
"thin, 'raspy', 'buzzy' quality", and an intensity-pot failure red-plates the
tubes. Optical: the neon "requires a certain minimum voltage in order to strike"
at about **90V**; at breakdown "there is a sudden jump in light intensity", then
"the light intensity varies relatively linearly", giving the "'choppy' tremolo
effect"; the cell is "a TO-8 (approx 11mm ⌀) CdSe (cadmium selenide) type" with
"a significantly shorter time constant" — about 10 ms against 100 ms for
alternatives. The LFO is an inverting tube stage with "three pairs of resistors
and capacitors" each contributing 60°.
**S7a.** Optical trem "varies a resistance from the signal path to ground at the
input to the phase inverter, effectively acting like a volume control that moves
up and down at the LFO's frequency"; bias trem "superimpos[es] a sinusoidal
variation on the bias voltage supplied to the output tubes"; "shifting the bias
point will cause clipping and distortion, which might add some pleasing harmonics
as well as modulate the volume"; on the symmetry, verbatim: "Since it is applied
to both sides of the push-pull output the clipping would theoretically be
symmetrical, but it is not likely that both sides will saturate at exactly the
same grid voltage, and some asymmetrical clipping will be included."
**S7b.** "3Hz to 10Hz is typical for the AB763 circuit"; stock values 22 µF
cathode bypass, "2 x .01 caps and 1 x .022 cap" against 1M, 220K plate, 2.7K
cathode; a 100K plate "will lower the gain of the circuit and the oscillator may
fail to oscillate altogether, or drop out on the high and low end of the
frequency range".
**S7c.** In push-pull the LFO is applied to opposing grids and the effect is
about twice a single-ended one; an amp idling hot in class A "will mostly stop
working" because the LFO cannot push the tubes toward cutoff; one builder's
"depth pot didn't kick in until about 1/3 of the dial"; one schematic added
"green LED and little caps in the tremolo circuit … to reduce thumping".
**S8.** "The response to switching the illumination on is about 10 times faster"
than off, with turn-off from 2.5 to 1000 ms; CdS about 140 ms at 25 °C, CdSe
"faster, with a time constant of less than 20 ms"; cadmium cells' resistance
"depends on the history of illumination", settling in hours to days. Gibson used
"cheap but slow incandescent lamps"; Fender "replaced them with neon lamps, which
increased the maximum frequency to tens of Hz and reduced controlling currents,
but resulted in a nonlinear modulation."
**S9.** PerkinElmer quoted: on light, resistance "drops very fast, typically
reaching 63% (1-1/e conductance) of its final values in under 10 msec"; off, it
"increases initially at an exponential rate, approximately tripling in a few
milliseconds. The resistance then increases linearly with time." VTL5C2 3.5 ms
rise / 500 ms fall; VTL5C3 2.5 ms / 35 ms.
**S10.** VTL5C3: ON resistance 30 kΩ / 5 Ω / 1.5 Ω at 1 / 10 / 40 mA, OFF
resistance at 10 s ≥ 10 MΩ, dynamic range 75 dB, **turn-on to 63 % final R_ON
2.5 ms typ**, **turn-off (decay) to 100 kΩ 35 ms max**. VTL5C4: 6.0 ms / 1.5 s.
The mirror is four pages: pp. 1–2 are the PerkinElmer VTL5C3/5C4 sheet above,
p. 3 a one-paragraph application note, p. 4 the **Silonex NSL-32SR2** datasheet —
`RON` 40 Ω @ I_F = 20 mA, `ROFF` 5 MΩ typ 10 s after I_F = 0, **`TR` 5 ms** (to
63 % of final conductance @ I_F = 20 mA), **`TF` 80 ms** (to 100 kΩ after removal
of I_F = 20 mA). (The earlier line here, "the mirror's NSL-32SR2 page carries no
rise/fall figures", was wrong and is corrected by the audit.)
**S11.** "2 Meg ohms" dark resistance; "LDR neon bulb opto-coupler assembly".
**S12.** Bias-vary in the power tubes: Princeton and Princeton Reverb, brownface
Vibro-verb and Deluxe, 5G9 Tremolux — "a very rich and soft pulsating sound", at
the cost of "beating sounds that can be very annoying". Bias-vary in a preamp
tube: blackface/silverface Vibro Champs, 5E9 Tremolux. Optical: most
blackface/silverface models except those. Harmonic: brownface and blonde Pro,
Bandmaster, Super, Showman, Twin. Neon optical circuits are "rather choppy
sounding", incandescent ones "much smoother".
**S13.** 6V6-GT class AB1 push-pull: Va 285 V, Vg1 −19.0 V, Ia 70.0 mA for the
pair at zero signal, S = 3.6 mA/V.

### A1. Probes run this session (venv CPython, `audiocomponents/.venv`, 2026-09-06)

Scripts are throwaway; the numbers are the evidence. Shared with the `AutoPan`
and `RingMod` seeds.

- **P1 / P1b — `Multiply`'s wire and its LSB.** At `mix = 0` a 1 kHz half-scale
  tone returns byte-identical over 8192 samples. At `mix = 1` with the modulator
  held at 32767 the error is −1 … 0, never positive, because `(a·b)>>15` is an
  arithmetic shift and floors. Depth 0 must be `mix = 0`.
- **P4 — per-channel modulator columns are honoured.** DC 16000 stereo source,
  modulator (L = 32767, R = 8192) → L = 15999, R = 4000. Stereo Phase is free.
- **P5 — the shipped class on CPython.** `create('Tremolo', …, rate=5.0,
  depth=1.0)` over one second of DC 16000: L min/max **8000/8000**, R min/max
  **7999/7999** — the LFO's value at phase 0, held for a second, no movement.
  `latency_samples = 0`, `tail_samples = None`. `AutoPan` on the same run gives a
  flat 16000/16000.
- **P6 — block stepping versus a period table**, 1 kHz half-scale tone, depth-1
  sine envelope, 65536 frames, Hann FFT, normalised to peak, block 256 frames:

  | build | rate | sideband at 1000 ± rate | product near 1000 + 187.5 | near 1000 + 375 |
  |---|---|---|---|---|
  | gain stepped once per block | 5 Hz | −5.6 dB | **−38.0 dB** | −44.2 dB |
  | gain stepped once per block | 10 Hz | −5.4 dB | **−31.0 dB** | −37.3 dB |
  | period table via `Multiply` | 5 Hz | −5.5 dB | −124.1 dB | −117.2 dB |
  | period table via `Multiply` | 10 Hz | −5.4 dB | −117.0 dB | −125.7 dB |

  Table sizes: 38 400 bytes at 5 Hz, 19 200 at 10 Hz. L1's −80 dB bar separates
  the two builds by more than 40 dB in either direction — it is a bar that can
  actually fail, and the block build is the planted fault that fails it.
- **P8 — envelope-shape signatures, for L3 and O2** (trait-critic pass,
  2026-09-06; numpy in the same venv, one period at 65536 points, harmonics in dB
  re the fundamental). Unit shapes: a sine's h2/h3/h5 sit at the float floor
  (≈ −326 dB); a **triangle's h3 is −19.08 dB** (h5 −27.96); a **square's h3 is
  −9.54 dB** (h5 −13.98). Rectangular envelope, second harmonic against the
  fraction of the period spent low: duty 0.50 → h2 at the float floor, 0.48 →
  **−24.05 dB**, 0.46 → **−18.04 dB**, 0.45 → −16.12 dB, 0.40 → −10.20 dB. These
  are the numbers L3's −26 dB bar and O2's 47 % / −20 dB pair are set against —
  closed-form properties of the shapes, computed rather than recalled.
- **P12 — a `synthio` note's ceiling, measured** (palette-verifier pass,
  2026-09-06). `synthio.Synthesizer(sample_rate=48000, channel_count=2)`, one
  pressed `Note(frequency=5.0, waveform=<table>)`, 24 000 frames pulled: a
  unipolar 0…32767 table returns **0…16382**; a DC 32767 table returns a flat
  **16382**; a bipolar ±32767 table returns **±16382**; `amplitude=1.0` changes
  nothing. The cause is `audioif_sum_with_loudness`'s `>> 16`
  (`audioif_synth_dsp.c:57-68`, the two multiply-and-shift lines at `:61` and
  `:65-66`), not the mix-down knee at `:20-28`, which does not engage until
  ±28000 (`synthio/__init__.h:132-133`). A synthio-note modulator tops out at a
  gain of 0.4999.
- **P13 — a short table under `audiospeed.SpeedChanger`** (palette-verifier pass,
  2026-09-06). A 256-point unipolar stereo table (1 KB).
  (a) `RawSample → SpeedChanger(rate=256/(48000/5)) → Multiply(DC 16000)`:
  movement stops at frame **9604** of 48 128 and the output reverts to the
  source — `RawSample` returns `GET_BUFFER_DONE` (`upstream-diff.md:747-749`) and
  `SpeedChanger.c:162-163` latches it, so the table plays once and stops.
  (b) `RawSample → Mixer(voice.play(loop=True)) → SpeedChanger → Multiply`: runs
  the full 48 128 frames and is still changing at the end (last changing index
  48 096). (c) rate changed mid-render from 5 Hz to 10 Hz: last sample before
  **15759**, first sample after **15759** — a phase jump of **zero** — and the
  largest single-sample step in the 200 frames spanning the change is 59 LSB, the
  staircase's own step. Nearest-neighbour throughout (`SpeedChanger.c:160`,
  `:171-173`); the phase truncates to 0 on every source fetch
  (`SpeedChanger.c:99-100`).
- **P14 — B4 on the palette, attempted** (palette-verifier pass, 2026-09-06).
  `200 Hz full-scale → Multiply(m1) → audiofilters.Distortion(WAVESHAPE, static,
  post_gain 0 dB) → Multiply(m2)`; `m1` 0.05 at the envelope crest and 1.0 at the
  trough, `m2` computed from a first render's sliding 1 ms RMS so the second pass
  delivers the envelope, normalised to `max(m2) = 1`. h3 re fundamental over the
  tenth of the period centred on each extreme, one settled period of the three
  rendered:

  | shaper | drive | h3 at env min | h3 at env max | difference (B4 bar ≥ +3 dB) |
  |---|---|---|---|---|
  | WAVESHAPE | 0.2 | — | — | +1.5 dB |
  | WAVESHAPE | 0.3 | — | — | +2.1 dB |
  | WAVESHAPE | 0.45 | −10.8 dB | −13.5 dB | +2.7 dB |
  | WAVESHAPE | 0.6 | −10.1 dB | −13.2 dB | **+3.1 dB** |
  | WAVESHAPE | 0.7 | −9.7 dB | −12.9 dB | **+3.2 dB** |
  | WAVESHAPE | 0.8 | −9.4 dB | −12.4 dB | **+3.0 dB** |
  | OVERDRIVE | 0.2 / 0.3 / 0.6 | — | — | +1.0 dB at all three |

  (The dashes are levels the sweep printed only as a difference; every row's two
  absolute figures are recoverable by re-running the same script, which is
  throwaway. `CLIP` is absent because its curve is homogeneous and cannot
  respond to a drive change at all.)

  The three rows that clear the bar clear it by 0.0–0.2 dB, and every row's
  delivered crest sits **24.6 dB below unity** (peak RMS 1922 of 32767 at
  drive 0.6) because `Multiply`'s modulator is unipolar Q15 and can only
  attenuate (`audioif_multiply.c:38`). Recorded as an attempt, not a refutation.
- **P15 — `audiofilters.Distortion`'s own harmonics**, full-scale 500 Hz sine,
  32 768-frame render, Hann FFT, h_n re the fundamental (palette-verifier pass,
  2026-09-06): CLIP h3 −25.0 / −16.3 / −10.1 dB at drive 0.2 / 0.5 / 0.9;
  WAVESHAPE h3 −23.1 / −15.4 / −10.1 dB; OVERDRIVE h2 −21.3 and h3 −28.4 dB at
  every drive (its curve ignores `drive`, `audioif_distortion.c:22-29`); LOFI h3
  −100.2 / −76.2 / −26.4 dB. Shared with the `RingMod` seed.
- **P7 — `Multiply` ignores a modulator's declared sample rate.** A ten-frame
  modulator (five at 32767, five at 0) declared `sample_rate=480` against a
  48 kHz DC source renders 5 samples on, 5 off, repeating — one modulator frame
  per output frame, no resampling. A low-rate table is therefore not a cheaper
  route to a slow LFO; the period table must be written at the output rate.

### A3. The kit measurements this seed names

- **ENV** — a full-scale 1 kHz tone rendered for eight LFO periods; per-channel
  envelope by peak-track on a 1 ms hop; the export carries depth peak-to-trough in
  dB, the trough and crest distances from the mean in dB (B1), the envelope's
  harmonics of the Rate in dB re its fundamental (L3, O2), the maximum |dG/dt| on
  the falling and rising halves in dB/ms and their ratio (O1, B5), the fraction
  of the period below the mid-depth level (O2), the trough level in dB (B2, O3), and the fundamental
  frequency (L4). L2, B3 and O4 read the depth figure across two settings.
  *Planted fault that must turn it red:* replace the character's law with a plain
  symmetric sine, which zeroes B1's asymmetry, flattens O2's duty to 50 % and
  makes O1's two slopes equal. *Second planted fault, for B5:* build the bias
  character on the optical character's two-rate tracker, which pushes the bias
  slope ratio past 1.5. *The control that must pass:* the optical law read
  against O1 and the bias law against B5 in the same run — a battery in which
  every configuration fails proves only that the measurement always fails.
- **BLOCK** — a 1 kHz tone for four seconds; Hann FFT; maxima in ±30 Hz bands at
  1000 ± 187.5 Hz and 1000 ± 375 Hz, in dB re the tone (L1). *Planted fault:*
  hold the table's value constant across each 256-frame block; the bands must rise
  to the −38/−31 dB that A1/P6 measured.
- **STFT** — a full-scale 200 Hz tone at Rate 4 Hz, Depth 1; time-resolved
  harmonic spectrum on 10 ms hops; h3 re the fundamental reported against LFO
  phase (B4). *Planted fault:* drive the waveshaper from a constant bias instead
  of the LFO table, which flattens h3 across the cycle.

Every measurement takes the sample rate as a parameter and records it in what it
exports; the evidence pack carries every Tier 2 trait at 48 kHz and 44.1 kHz and
the Tier 1 invariants additionally at 22.05 kHz.

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

For this class "drive at zero" is **Depth at zero**, which must be the `mix = 0`
wire of `audiomath.Multiply` (`audioif_multiply.c:28-29`, `:39`), never a constant
table — a table held at 32767 loses up to one LSB, measured (A1/P1b). `Tremolo`
is **not** stereo by definition: a mono source gets the same envelope on one
channel and the Stereo Phase macro reads inactive, and the kit measures that. No
Tier 2 trait depends on the sample rate — every rate here is a few hertz — so
L1–L4, B1–B5 and O1–O4 all hold unchanged at 44.1 and 22.05 kHz; only L1's
block-product bands move with the rate, and the kit takes the rate as a
parameter.

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| L1 | The modulation is per sample, not per block: with a 1 kHz tone at Rate 3, 5 and 10 Hz and Depth 1, no component within ±30 Hz of 1000 ± f_s/256 or 1000 ± 2·f_s/256 — 187.5 and 375 Hz at 48 kHz, the render block being 256 frames — rises above **−80 dB** re the tone | vision §6 on block-rate nodes; A1/P6, where the block-held build measures −38.0 dB (5 Hz) and −31.0 dB (10 Hz) in the first band, so the bar has more than 40 dB of separation in either direction | high | any product above −80 dB in those bands | BLOCK |
| L2 | Depth falls with Rate at fixed Intensity, because one pot moves one section of the phase-shift network: with Speed Link on, the envelope depth in dB at 3 Hz is strictly less than at 8 Hz, and the difference lies between **1 and 6 dB** | S5 for the mechanism and its own single-pot example — 204 V at 6.5 Hz against 163 V at 2 Hz, which is 1.95 dB of LFO swing across a wider span (this run's arithmetic on S5's two voltages); S6 | medium — the direction is sourced; **the 1–6 dB band is this seed's**, because S5 gives an LFO swing and the kit measures an envelope depth, and the gain law between them is §8.1's open question | a difference below 1 dB (depth independent of Rate) or above 6 dB | ENV |
| L3 | The LFO is a near-sine, not a triangle and not a square: the envelope's harmonics of the Rate all sit below **−26 dB** re its fundamental at Depth ≤ 0.5 in the bias character — the kink is a small distortion, not a shape | S5 ("a small amount of harmonic distortion … the 'kink' at the bottom edges"); S6 ("a slightly cockeyed, low frequency sinusoidal control voltage") | medium — the shape is sourced; **the −26 dB bar is this seed's**, set where it discriminates: a triangle's h3 is −19.08 dB and a square's −9.54 dB (computed this run, A1/P8), so the row rejects either with at least 6.9 dB to spare, where a −20 dB bar would have separated a triangle by 0.9 dB | any harmonic above −26 dB; in particular an h3 near −19.1 dB (triangle) or −9.5 dB (square) | ENV |
| L4 | Rate spans at least 3–10 Hz on the amp patches, and the measured envelope fundamental equals the Rate macro's engineering value within **1 %** | S7b only, verbatim: "3Hz to 10Hz is typical for the AB763 circuit". S5 gives a 2–8 Hz design target and a 2–6.5 Hz worked example; S6 gives a narrower "typically 4 to 8Hz" and disagrees with the top of this span — the trait follows the source closest to the circuit | high for 3 Hz, medium for 10 Hz (one source) | Rate error above 1 %, or an amp patch that cannot reach 3 or 10 Hz | ENV |
| B1 | The gain envelope is asymmetric about its mean: at Depth 1, the mean being the arithmetic mean of the **linear** gain envelope over one whole period, the trough sits further below that mean in dB than the crest sits above it, by at least **1 dB**, because the stage's gain follows the pair's transconductance along a curve that flattens toward cutoff | S1; S7a; S13 | low-medium — the mechanism is sourced, the curvature over the actual swing is not; **the 1 dB bar is this seed's** | a measured trough-versus-crest asymmetry under 1 dB, or §8.1's SPICE gain-versus-bias curve coming back linear over the Intensity swing — in which case B1 is dropped with that record and the envelope is a plain sine | ENV |
| B2 | Depth is bounded and saturating, never a mute: at Depth 1 the trough sits **above −40 dB** re the crest, and the depth in dB added over the last 20 % of Depth travel is **smaller than** the depth added over the first 20 % | S4 ("negative swings of the bias voltage are short of forcing the amp into Class B", "without chopping out notes as you play"); S1 (the fixed −35 V line the swing rides on) | medium — the mechanism is sourced; **the −40 dB floor is this seed's** | a trough at or below −40 dB at Depth 1 (a mute), or a last 20 % of travel that adds at least as much depth as the first | ENV |
| B3 | Depth depends on the idle bias: between the Bias macro's ends the envelope depth changes by at least **6 dB** at fixed Intensity, shallower toward hot | S7c; S4 | medium — the direction is S7c's ("if the bias supply resistors drift so the amp is running a very hot class A, the trem will mostly stop working"); **the 6 dB bar is this seed's**, neither source gives a number | a depth change under 6 dB between the Bias macro's ends — including none at all — or a change that runs the other way, deeper toward hot | ENV |
| B4 | The clipping threshold moves with the bias: with a full-scale 200 Hz tone at Rate 4 Hz and Depth 1, the third-harmonic level over the LFO cycle is not constant — averaged over the tenth of the period centred on the envelope's minimum it is at least **3 dB** higher than over the tenth centred on its maximum — while at Depth 0 it sits at the wire's floor. *Requires the waveshaper node (§5 N2); without it the character omits this trait and says so* | S7a; S6; S1 | medium (mechanism) / low (the 3 dB bar is this seed's) | h3 flat over the cycle at Depth 1 with the node present | STFT |
| B5 | The bias envelope is time-symmetric, where the optical one is not: at Rate 5 Hz and Depth 1 the steepest falling and steepest rising envelope slopes in dB/ms differ by a factor **below 1.5** — a static gain law driven by a near-symmetric LFO has no memory to make a fast edge and a slow one, and L3's kink is the only asymmetry in it | S4 ("a smooth, watery response — with a soft edge to its rise and fall even at higher intensities"); S12 (bias-vary "a very rich and soft pulsating sound" against neon optical circuits being "rather choppy sounding"); the symmetry itself is arithmetic — a static function of a symmetric periodic input is time-symmetric about its extremes | medium — the sourced content is the direction; **the 1.5 bar is this seed's**, set below O1's ≥2 so the two characters cannot both pass | a slope ratio of 1.5 or more in the bias character, which is the signature of an optical-style two-rate tracker having leaked into the bias law | ENV |
| O1 | Gain falls faster than it recovers: the steepest downward slope of the envelope in dB/ms is at least **twice** the steepest upward slope, at Rate 5 Hz and Depth 1 | S8 ("the response to switching the illumination on is about 10 times faster" than off); S9, S10 for figures on named parts — VTL5C3 2.5 ms on / 35 ms off, NSL-32SR2 5 ms / 80 ms | high for the direction; the Fender cell's own constants are unsourced, so the bound is set loosely at 2× where the named parts give 14–16× | slopes within a factor of two, or a rise faster than the fall | ENV |
| O2 | The modulation is pulse-shaped, not sinusoidal: at Depth 1 the fraction of the period spent below the mid-depth level is **under 47 %**, and the envelope's second harmonic of the Rate is **above −20 dB** re its fundamental — two readings of one fact, since a rectangular envelope crosses −20 dB of h2 at a duty of about 47 % (0.46 → −18.0 dB, 0.48 → −24.1 dB, computed this run, A1/P8) | S6 (the neon "requires a certain minimum voltage in order to strike", so the light is a pulse and not a sine); S8; S12 (neon optical circuits "rather choppy sounding") | medium — the shape is sourced; **the 47 % and −20 dB bars are this seed's** | a duty at or above 47 %, or an h2 at or below −20 dB — either is the symmetric sine this character is not | ENV |
| O3 | Depth is a resistive divider, not a gate: at Depth 0 the class is a wire; at Depth 1 the trough is a finite attenuation between **−15 and −40 dB**, never silence | S2, S3; S11 (2 MΩ dark); S7a | medium — the lit resistance is unsourced (§2) | a trough below −40 dB (a gate) or above −15 dB (no bite) at Depth 1 | ENV |
| O4 | The cell's lag smooths fast rates: at Rate 10 Hz the envelope depth is at least **2 dB** less than at 3 Hz for the same Depth and Lag, independently of L2; with Lag at its minimum the loss vanishes | S8, S9, S10 | medium — the lag is the sources'; **the 2 dB bar is this seed's** | a loss under 2 dB from 3 to 10 Hz at the default Lag — including none at all — or a loss that survives Lag at its minimum, which would mean the smoothing came from something other than the cell | ENV |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

- **S1.** Fender "Princeton" schematic, model 6G2 — schematicheaven PDF,
  image-only; both pages extracted with `pypdf` and read at 3× and 5×
  enlargement. No license on the PDF. The site's terms *were* reached this run
  (audit): `schematicheaven.net/copyright.html`, linked only from the homepage
  footer, reads "Any information found here may be freely copied, downloaded, or
  otherwise reposted. But NOTHING on this website may be SOLD or repackaged for
  SALE." That is the host's grant, not Fender's, and the drawing itself carries
  no rights line — so the call stands at **read as a document, nothing
  reproduced** (vision §5), with the site terms now verified rather than
  unfetched.
  <https://schematicheaven.net/fenderamps/princeton_6g2_schem.pdf>

*(from §2)*

- **S2.** Rob Robinette, AB763 Deluxe Reverb layout (DIYLC PDF, text layer via
  `pypdf`). No license text: **unverified, read only**.
  <https://robrobinette.com/images/Guitar/AB763_Models/AB763_Deluxe_Reverb_Layout_DIYLC.pdf>

*(from §2)*

- **S3.** Rob Robinette, "AB763 Mods". No copyright statement in the fetched
  content, and the audit also fetched `robrobinette.com/` itself: no copyright
  line, no terms link, nothing in the footer (the `/terms.php` pattern
  `instrument-sources.md` warns about was looked for and is absent):
  **unverified, read only**. <https://robrobinette.com/AB763_Modifications.htm>

*(from §2)*

- **S5.** Aiken Amplification, "Designing Phase Shift Oscillators for Tremolo
  Circuits". "© 1999-2014 Randall Aiken. May not be reproduced in any form
  without written approval": **read only**.
  <https://www.aikenamps.com/index.php/designing-phase-shift-oscillators-for-tremolo-circuits>

*(from §2)*

- **S6.** Effectrode (Phil Taylor), "Delta-Trem In-depth". Footer verbatim:
  "Copyright © 1963 EFFECTRODE THERMIONIC. All Rights Reserved." (the year is the
  site's, transcribed as it stands): **read only**.
  <https://www.effectrode.com/knowledge-base/delta-trem-in-depth/>

*(from §2)*

- **S7a/b/c.** The Amp Garage forum, `t=10265` (how each type works), `t=29561`
  (AB763 oscillator range and values), `t=19228` (bias trem, push-pull vs
  single-ended). Forum posts, no license: **attributed, read only**.
  <https://ampgarage.com/forum/viewtopic.php?t=10265> ·
  <https://ampgarage.com/forum/viewtopic.php?t=29561> ·
  <https://ampgarage.com/forum/viewtopic.php?t=19228>

*(from §2)*

- **S9.** Rich Holmes, "Vactrol information", quoting PerkinElmer's catalogue.
  "© 2023 Rich Holmes": **read only**.
  <https://richardsholmes.com/topics/synth/vactrol-information/>

*(from §2)*

- **S11.** Watford Valves, "Fender opto trem/vib" replacement. "© 2026 Watford
  Valves Ltd": **product page, read only**.
  <https://www.watfordvalves.com/product_detail.asp?id=1008>

*(from §2)*

**Looked for and not reached.** No DAFx/AES/CCRMA paper on Fender tremolo
modelling was found by search — the audit repeated the search against
`dafx.de`, `aes.org` and `ccrma.stanford.edu` and the nearest hits are Fender
*preamp* and tone-stack papers, none fetched. One lead the audit surfaced and
deliberately did **not** fetch, recorded so §8.1 can chase it rather than
re-find it: an Eichas and Zölzer paper on modelling an optocoupler-based audio
dynamic-range-control circuit (SPIE, 2016) — a compressor, not a tremolo, but
the only optocoupler lag model this program has seen named. It is a search
result and nothing more; nothing in §3 rests on it. `geofex.com` not attempted
(known connection reset); the ElectroSmash mirror's index carries no tremolo
article (re-fetched by the audit: zero occurrences of "tremolo"). **Struck from the earlier draft** because it was
not re-reached this run: a Dexter Amps "how does a tremolo roach work" page.
**Unsourced and kept out of the trait table:** the *lit* resistance of the Fender
cell (only the 2 MΩ dark figure, S11, was read); the 6V6's transfer curve (S13
gives operating points, not a model); the exact wiring of the 50 kΩ Intensity pot
relative to the cell (S3 fixes where the tremolo is injected, not whether the
cell sits in series with the pot or across it).

*(from §2)*

**Restored by the audit, 2026-09-06.** This seed previously listed Silonex
NSL-32SR2 timing as unsourced and struck the earlier draft's "5 ms / 80 ms". That
strike was wrong: S10's mirror PDF is four pages, and its **fourth page is the
Silonex NSL-32SR2 datasheet**, which gives `TR` **5 ms** (time to 63 % of final
conductance @ I_F = 20 mA) and `TF` **80 ms** (time to 100 kΩ after removal of
I_F = 20 mA); S9's vendor table lists the same 5 / 80 for that part. The figures
are sourced and are now cited in O1. Neither figure is the *Fender* cell, which
stays unsourced.

*(from §2)*

**Audit record — second pass, 2026-09-06 (license and citation, independent of
the research run and of the first audit).** All thirteen sources were fetched
again from scratch: S1 and S2 as their PDFs (S1's two page images extracted with
Pillow, the whole sheet read at native size and the oscillator, the plate node
and the 6V6 grid network re-read at 3× and 5×; S2's text layer re-extracted),
S8 as the article's raw wikitext via `Special:Export`, S3, S9 and S12 as raw
HTML, S10 as its four `pypdf`-extracted pages, and S4, S5, S6, S7a/b/c, S11 and
S13 through the fetch tool (`ampgarage.com` answers `curl` with HTTP 406, so
those three threads are fetch-tool reads only). Every license line above was
seen on the page it is
attributed to; two of them were made more precise (S1's site terms, S3's absent
footer). What this pass changed, beyond the license lines:

*(from §2)*

- **The INTENSITY taper was wrong.** §1 read "250 kΩ audio-taper"; the drawing
  says **250K-L**, and the same sheet writes **1M-A** (Tone, Volume) and
  **3M-RA** (Speed), so L is linear. Appendix A0 had already transcribed
  `250K-L` correctly — the seed contradicted itself, and the first audit's claim
  that "every 6G2 value in §1 [was] checked against the drawing" did not hold.
  §6's macro table still says "250 kΩ log on bias" and is out of this pass's
  scope to edit; it needs the same fix.

*(from §2)*

- **A0's "1500 screen resistors" are grid resistors.** On the drawing the two
  1500 Ω sit between the 220 kΩ bias network and each 6V6GT grid pin, which is
  the control-grid path the −35 V feeds. Corrected in A0.

*(from §2)*

- **§8.7's strike against S8 is itself wrong, and this pass could not edit §8.**
  §8.7 says the phrase "on/off switching rather than smooth control" is "not in
  what S8 says". It is: the article's *Applications → guitar amplifiers*
  section reads "in contrast to the continuous modulation by Gibson, Fender used
  the on/off switching mode that resulted in less pleasant sound", alongside the
  "resulted in a nonlinear modulation" wording in *History of applications* that
  §8.7 quotes. Both are S8's. The strike should be withdrawn.

*(from §2)*

Upheld under challenge: S9's "quoting PerkinElmer's catalogue" — the page
carries the quote verbatim ("Quoting from the PerkinElmer catalog: When light is
suddenly applied, the photocells resistance drops very fast, typically reaching
63% (1-1/e conductance) of its final values in under 10 msec."), and its
per-part figures sit in the vendor table beside it (VTL5C3 2.5 / 35,
NSL-32SR2 5 / 80). Upheld too: the NSL-32SR2 restore (S10 page 4 is the Silonex
sheet, `TR` 5 ms, `TF` 80 ms), the VTL5C3 2.5 / 35 ms on S10 page 1, the AB763
cap and bypass values, the reason the bias-vary clipping is asymmetric, and the
stock injection point relative to the mixing resistor — each re-read at source
this run rather than carried.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: **ESP32-P4 1 %,
ESP32-S3 2 %** — per sample one Q15 multiply, one blend and one clamp
(`audioif_multiply.c:38-45`). Lean patch expected: **no** (a lean *rate floor* is
the fallback if §5 N1 fails on a PSRAM-less board). RAM: one stereo period table,
4 bytes per frame — measured at **38 400 bytes at 5 Hz and 19 200 at 10 Hz**
(A1/P6), 64 KB at 3 Hz, 384 KB at 0.5 Hz — allocated at construction and on every
Rate, Depth, Shape, Lag or Bias move, never on pull. With N2 the bias character
adds one shaper call per sample and its oversampling; that budget is stated in the
`Overdrive` and `Distortion` seeds and inherited here.

*(from §3)*

**Latency: 0 samples (0.0 ms at 48 kHz); `tail_samples` 0.** The gain is applied
sample-aligned, and the optical cell's lag is modelled *inside the table* as
envelope shape, not as delay — that is the whole reason the two-rate tracker is
iterated in Python at construction rather than run as a filter on the signal.
**No option adds latency.** In particular the Lag macro (O1, O4) is a shape
parameter, not a delay line, and no proposal to implement it as one is accepted
under vision §9a. The class gate's click measurement verifies
`latency_samples = 0` at 48 kHz and 44.1 kHz.

*(from §4)*

Python computes the chosen character's gain law over one period at construction.
The **LFO shape** is a sine with a small fixed asymmetric distortion for the kink
(L3), its amplitude scaling with Rate when Speed Link is on (L2 — the seed uses a
monotonic fall of about 2 dB across 2–6.5 Hz from S5 until §8.1's SPICE replaces
it). **Bias-vary:** `gain = G(V₀ + A·s(t)) / G(V₀)`, with `s` the shape, `A` the
Intensity swing, `V₀` the idle bias (the Bias macro) and `G` the stage gain versus
grid bias — a concave law flattening toward cutoff; the seed carries a placeholder
of that shape and §8.1's ngspice run supplies the numbers as a gain-versus-bias
table the kit compares against (B1, B2, B3). **Optical:** neon drive is `s(t)`
above a strike threshold (Shape sets the threshold, hence the duty, O2); cell
conductance follows a two-rate first-order tracker, fast toward lit and slow
toward dark with Lag scaling the slow constant (O1, O4), iterated until periodic;
gain is `(R_cell + R_int) / (R_src + R_cell + R_int)`, normalised so dark is unity
(O3). A period at 3 Hz is 16 000 frames; filling it in Python on an S3 is a
construction cost paid once; knob-move behaviour on the S3 is still a Station A
measurement, though it no longer decides a node ask (§5). Tables are computed on CPython, never on a board mid-render (the
ESP32 ports are single-precision).

*(from §4)*

**Rejected on the palette, with the numbers.** Driving
`audiomixer.MixerVoice.level` from a `synthio.LFO` is block-rate by construction
— `Mixer.c:331` ticks the LFO once per pulled chunk — and measured this run at
block products of **−38.0 dB at 5 Hz and −31.0 dB at 10 Hz** against L1's −80 dB
bar (A1/P6). Worse, on the CPython build the Mixer never ticks a block input at
all (`src/cpython/audiomixer.py` contains no tick where `Mixer.c:331` has one), so
the shipped class renders a **constant 8000/7999 for a full second** at Rate 5 Hz,
Depth 1 (A1/P5) — a Tier 1 cross-interpreter failure, not a quality question. A
`synthio.Synthesizer` note playing a gain table is per sample and cheap on RAM,
and **its ceiling is now measured, which rules the route out by number rather
than by a pending Station A task**: a note's per-voice sum shifts right by 16,
not 15 (`audioif_synth_dsp.c:57-68`, the multiply-and-shift at `:61` and
`:65-66`), so a table of 32767 comes back as **16382 — a flat halving, −6.02 dB**
— whatever its shape and whatever `amplitude` is set to (measured this run,
A1/P12: unipolar table, DC table, bipolar table and `amplitude=1.0` all cap at
16382). A modulator that can only reach a gain of 0.4999 cannot be a tremolo's
gain envelope. The mix-down soft-knee this seed's first draft blamed
(`audioif_synth_dsp.c:20-28`) is **not** what does it: that knee starts at
±28000 (`synthio/__init__.h:132-133`) and the halved output never reaches it.
`Multiply` ignores a modulator's
declared sample rate — a table declared at 480 Hz is consumed one frame per
output frame — so there is no cheap low-rate table either.

*(from §4)*

**Considered and not rejected: a short table played by `audiospeed.SpeedChanger`
(new this run, palette-verifier pass).** `Mixer(voice.play(table, loop=True)) →
audiospeed.SpeedChanger(rate) → Multiply` gives a per-sample modulator from a
**1 KB** table instead of a whole period, and it was built and rendered this run
(A1/P13): it runs continuously for a full second and beyond, its `rate` changes
mid-stream with a **measured phase jump of zero** (5 → 10 Hz, last sample before
15759, first after 15759), and its stepping is at 256·Rate Hz — 1280 Hz at
Rate 5 — not at the 187.5 Hz block rate. Three costs, all measured or read:
`SpeedChanger` is **nearest-neighbour, no interpolation** (`SpeedChanger.c:160`,
`:171-173` reads one whole source frame per output frame with no fractional
blend, and `:176` is the only place the phase advances), so the modulator is a
staircase; its phase truncates to zero on **every** source-buffer fetch
(`SpeedChanger.c:99-100`), so a fractional sample is lost at each Mixer chunk
boundary; and `SpeedChanger` over a bare `RawSample` **does not loop at all** —
`RawSample` returns `GET_BUFFER_DONE` (`upstream-diff.md:747-749`) and
`SpeedChanger.c:162-163` latches that into `source_exhausted`, so the table plays
once and stops (measured: movement ended at frame 9604 of 48128, A1/P13). The
`Mixer`'s `loop=True` is what makes the route work at all. The one trait this
route can fail is L1: the staircase's step rate is 256·Rate, which lands **inside**
L1's ±30 Hz bands when it is near 187.5 or 375 Hz — at Rate 0.73 and 1.46 Hz with
a 256-point table. A 1024-point table (4 KB) puts the step rate at or above
512 Hz across this class's whole 0.5–15 Hz Rate range and clears both bands; that
is the form the implementation session should measure first.

*(from §5)*

**REFUTED BY PALETTE** (palette-verifier pass, 2026-09-06). Two grounds, the
second measured this run. First, the ask names no trait id, and vision §6 asks
for a node "only when a fixed trait is shown unreachable, with the measurement
that shows it" — there is no such trait here. Second, the two things N1 addresses
instead of a trait are both reached by composing nodes that already exist:
`Mixer(voice.play(table, loop=True)) → audiospeed.SpeedChanger(rate) → Multiply`
plays a **1 KB** table per sample (so the RAM floor at slow rates goes away) and
its `rate` changes mid-stream with a **measured phase jump of zero** (so the
phase restart goes away) — built and rendered this run, A1/P13 and §4. What that
route costs is a nearest-neighbour staircase at 256·Rate Hz rather than N1's
interpolated read (`SpeedChanger.c:160`, `:171-173`), which no trait in §3
forbids and which a 1024-point table keeps clear of L1's bands across this
class's whole Rate range. N1 therefore does **not** go on the Phase 0 node list.
It may be re-opened only by a Station C measurement that fails a fixed trait —
not by a click or a rebuild time that no trait names.

*(from §5)*

**N2 — the table-driven waveshaper with oversampling (the vision §6 node, the
Drive family's ask), as a second consumer.** *Trait id:* **B4.** *What the
palette does instead:* the bias shift is a moving operating point on a static
curve; `audiofilters.Distortion` offers four fixed curves
(`audioif_distortion.c:16-33`) with no movable operating point, and it is a
CircuitPython-ported node that never changes; the modulated-threshold clipping of
B4 therefore has to be *imitated* by modulating the drive into a static curve
rather than moving the curve, and the paragraph below measures how far that
gets. *The measurement that shows it:* B4's own — h3 flat over
the LFO cycle is exactly what a pure gain envelope gives. *Refutation:* B4 is a
second-order trait of one character, and the character stays honest without it
(the row says so), so this class does **not** justify the node alone; it is a
second consumer of a node Drive needs anyway.

*(from §5)*

**Refutation attempted on the palette and NOT carried** (palette-verifier pass,
2026-09-06). The route tried, because B4 does not say *how* the threshold moves:
`source → Multiply(m1) → audiofilters.Distortion(WAVESHAPE, static) →
Multiply(m2)`, with `m1` a per-sample table that drives the shaper hardest at the
envelope trough and `m2` the table that then delivers the gain envelope — two
`audiomath.Multiply` nodes and one ported `audiofilters.Distortion`, nothing
modified, no block inputs. Rendered at 200 Hz, Rate 4 Hz, one settled period,
h3/h1 read over the tenth of the period centred on the envelope's minimum and its
maximum (A1/P14): **+3.1 dB at drive 0.6, +3.2 dB at 0.7, +3.0 dB at 0.8**
against B4's ≥ 3 dB bar; **+1.5 / +2.1 / +2.7 dB** at `WAVESHAPE` drives 0.2 /
0.3 / 0.45; and **+1.0 dB** in `OVERDRIVE` mode at every drive, whose curve
ignores `drive` altogether (`audioif_distortion.c:22-29`). `CLIP` cannot do it at
all: `pow(|v|, d)` is homogeneous (`audioif_distortion.c:17`), so its harmonic
ratios do not move with level and modulating the drive into it changes nothing. A margin of 0.0–0.2 dB is not a
demonstration, and the build that produced it delivers its crest **24.6 dB below
unity** — `Multiply`'s modulator is unipolar Q15, so `m2` can only attenuate
(`audioif_multiply.c:38`), and the normalisation that keeps `m2 ≤ 1` costs the
level-honesty Tier 1 requires. The ask therefore **stands** for B4, with this
record so nobody re-argues it: the palette route exists, was built, and does not
clear the bar while holding the invariants. If the waveshaper lands, the
bias-vary graph becomes a waveshaper whose bias input is the LFO table, with the
gain law folded into the curve; the implementation session chooses the form.

*(from §7)*

- `modulation.py:105` with `:82-89`: the modulation rides `MixerVoice.level`, a
  block input — block-rate by construction (`Mixer.c:331`), measured at −38.0 dB
  (5 Hz) and −31.0 dB (10 Hz) of stepping products against L1's −80 dB bar
  (A1/P6). The rebuild puts the LFO in the audio path (§4), never on a block
  input.

*(from §7)*

- On CPython the Mixer never ticks that block input at all
  (`src/cpython/audiomixer.py` has no tick): the shipped class renders a
  **constant 8000/7999 for a full second** at Rate 5 Hz, Depth 1 (A1/P5). The
  effect does not exist on one of the three interpreters, and nothing in the tree
  said so.

*(from §7)*

- `modulation.py:86-89`: a `Mixer` sits at the class output, so on stock
  CircuitPython the class is silenced by the next node's `play()`
  (`upstream-diff.md:887`) and can only ever be last in a chain. The rebuild has
  no Mixer.

*(from §7)*

- `modulation.py:103-104`: `scale = depth·0.5`, `offset = 1 − depth·0.5` — a bare
  sine whose Depth 1 swings the gain to exactly zero, i.e. a **mute**, which
  neither character does (B2, O3), and no circuit law of any kind.
