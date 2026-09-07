# Effects Dossier — `AutoPan` (no historical standout — grade *design*)

**Class:** `lib/audioeffects/modulation.py` — read once, for §7.
**Family / phase:** Modulation, roadmap Phase 3
**Standout:** none. Vision §4.2 lists `AutoPan` with a dash and grade *design*,
and this run **confirms that** rather than arguing a swap. Auto-panning is a pan
law under an LFO; the pan law is a textbook object with a published set of
conventions (P1, P2, P3) and no single circuit anyone would point at. Two
candidates were considered and rejected on evidence: the Leslie is `Rotary`'s
standout and is a different mechanism (a rotating horn, not a gain law), and
Fender's optical tremolo is `Tremolo`'s and modulates one channel's level, not a
position. Nothing else in the sources reached names a canonical auto-panner.
**Grade:** design — traits are the textbook properties of intensity panning
(vision §4.1), stated here as falsifiable Tier 2 rows rather than left to Tier 1
and Tier 3 alone, because the palette's own pan law fails two of them (§4) and a
seed that did not say so would hand the rebuild a trap.
**Portability tier:** needs audioif-own nodes (`audiomath`)
**Status:** seed (Phase 0), written 2026-09-06. Sections 4 and 5 were re-verified against the C under `audioif/src/shared` and the bindings under `audioif/src/<module>/`, and probed on the CPython build, by the palette verifier on 2026-09-06; the corrections and the node-ask verdicts are marked in place.

## 1. The mechanism, in one paragraph

There is no circuit, so this paragraph states the textbook object instead. A pan
control distributes one source between two outputs with a pair of gains
`g_L(p)`, `g_R(p)` chosen so that a listener hears the image move without hearing
it change loudness; which invariant is held is the *pan law*, and the choice is a
genuine tradeoff rather than a detail. Holding **power** constant —
`g₁² + g₂² = K`, which P1 grounds on `sin²(θ) + cos²(θ) = 1`, so the pair
`g_L = cos θ`, `g_R = sin θ` satisfies it exactly (that pair is this dossier's
arithmetic from P1's constraint and identity, both of which P1 writes; P1's own
worked constant-power form is the circular pan `g_a = (√2/2)[cos θ + sin θ]`,
`g_b = (√2/2)[cos θ − sin θ]`, the same pair rotated 45°, whose squares also sum
to 1) — keeps the loudness steady over loudspeakers and puts
the centre **3.01 dB** down on each leg. Holding the **mono sum** constant —
`g_L + g_R = K`, the linear law — puts the centre **6.02 dB** down on each leg
and is what a signal that may be folded to mono wants, because two identical
channels summed rise by 6.02 dB (P2, P3). The two cannot both hold: whichever is
flat, the other ripples by exactly 3.01 dB across the sweep (A4, derived in A2).
Consoles pick a point on that line — the 3 dB rule, the 4.5 dB compromise and the
6 dB rule are all in use (P2, P3) — so a pan law is a knob, not a constant.
`AutoPan` is that pair of gains driven by a periodic function of time: a **Rate**,
a **Depth** setting how far toward hard-over the sweep travels, a **Shape**
(triangle sweeps at constant angular velocity, sine dwells at the extremes), a
**Phase** offset, and the **Law**. Everything a musician hears in the effect is
in the law and the shape; nothing in it is nonlinear, has memory, or looks ahead.

## 2. Sources and license calls

All reached this run, fetched 2026-09-06, none from memory.

- **P1.** CCRMA / Planet CCRMA, "Multichannel Intensity Panning", Juan Reyes — …  *(argument in full: App. R)*
- **P2.** Wikipedia, "Panning (audio)" — "If the two output buses are to remain …  *(argument in full: App. R)*
- **P3.** Wikipedia, "Panning law" — a coherent signal in both channels rises "up …  *(argument in full: App. R)*
- **Local:** `audioif/src/audiomixer/Mixer.c`, `src/cpython/audiomixer.py`,
  `src/shared/audioif_multiply.c`, `docs/upstream-diff.md`; the probes in A1.
  **MIT (audioif).**

**Audit record — second pass, 2026-09-06 (license and citation, independent of
the research run and of the first audit).** All three sources were fetched again
from scratch and every claim re-checked at source; **nothing needed correcting
this pass**, which is worth recording as plainly as a correction would be.

- **P1.** Raw HTML pulled directly. The equations are LaTeX-rendered PNGs and …  *(argument in full: App. R)*
- **P2, P3.** Both quotations found verbatim, and the −4.5 dB compromise found …  *(argument in full: App. R)*
- **The three "not reached" URLs still 404** — `davidgriesinger.com/pan_laws.pdf`
  and both `~jos` paths, each re-requested this run.
- The local citations behind §3 and §4 were re-read in the tree: …  *(argument in full: App. R)*

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — the textbook properties, stated so a measurement can fail them

Kit measurements, defined in A3: **ENV** per-channel envelope (RMS in 1 ms
windows across four LFO periods of a full-scale 1 kHz tone, both channels);
**BLOCK** the block-product bands of a 1 kHz tone's spectrum; **WIRE** a byte
compare against the source.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| A1 | At Law = constant power and Depth 1, `L² + R²` taken from the envelopes is flat to within **0.2 dB** over the whole sweep, and the centre of the sweep sits **3.01 ± 0.1 dB** below hard-over on each leg | P1; P2, P3 (the −3 dB rule) | high | a power ripple above 0.2 dB, or a centre attenuation outside 3.01 ± 0.1 dB | ENV |
| A2 | The Law macro reaches all three published conventions: its three calibration points give centre attenuations of **3.01, 4.5 and 6.02 dB** on each leg, each within 0.1 dB, and the centre attenuation increases monotonically with the macro between them | P2 ("a law of −3 dB is desirable" for stereo … (App. A2) | high | any of the three points off by more than 0.1 dB, or a centre attenuation that does not rise monotonically across the eleven positions | ENV at eleven macro positions |
| A3 | The pan is per sample, not per block: with a 1 kHz tone at Rate 0.05, 5 and 20 Hz — the bottom, middle and top of the macro's range — and Depth 1, no component within ±30 Hz of 1000 ± f_s/256 or 1000 ± 2·f_s/256 (187.5 and 375 Hz at 48 kHz, the render block being 256 frames) rises above **−80 dB** re the tone | vision §6 (block-rate nodes) … (App. A3) | high | any product above −80 dB in those bands | BLOCK |
| A4 | The mono-sum ripple is exactly the complement of A1: at Law = constant power the mono sum `(L+R)/2` varies by **3.01 ± 0.2 dB** over the sweep with its maximum at the centre, twice per pan cycle; at Law = 6 dB it varies by **0.0 ± 0.2 dB** | P2; the two-line derivation in A2 | high | either figure outside tolerance, or the constant-power maximum anywhere but the centre | ENV, mono sum |
| A5 | A mono source is a wire: with `channel_count` 1 the output is byte-identical to the source at every Rate, Depth, Shape, Phase and Law setting, and at every patch | this dossier's §3 decision … (App. A5) | high | any differing byte | WIRE |
| A6 | Depth is honest at both ends: at Depth 1 the far channel's minimum over one period is **exactly 0**, not one LSB above it — the period table is built to place the sweep's extremes on table samples, so the zero is exact and not an approximation — and at Depth 0 both channels are byte-identical to the source | the textbook definition of a pan sweep … (App. A6) | high | a far-channel minimum of 1 LSB or more at Depth 1 (a clamp, or extremes that fall between table samples), or a non-wire at Depth 0 | ENV, WIRE |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Topology: `source → audiomath.Multiply(modulator = a stereo period table)`.**
One node, the same one `Tremolo` and `RingMod` use, and the whole design turns on
one measured palette fact: **`Multiply` applies the modulator's left and right
columns independently** (A1/P4 — a modulator of L = 32767, R = 8192 on a DC 16000
source gives L = 15999, R = 4000). A stereo table is therefore a per-sample,
per-channel, arbitrary gain law, which is exactly what a pan law is. `audiomath`
is audioif's own with no ancestor anywhere (`upstream-diff.md:714`), so the tier
is **audioif**.

**The Mixer route is rejected, with the numbers.** Driving
`audiomixer.MixerVoice.panning` from a `synthio.LFO` is the obvious build and it
fails two traits by measurement, not by argument:

- **It is not constant power, and it is not any of the three published laws.** …  *(argument in full: App. R)*
- **It is block-rate, and on CPython it does not move at all.** `Mixer.c:331` …  *(argument in full: App. R)*

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**None required.** Every trait A1–A6 composes on `audiomath.Multiply` with a
stereo table, and the two traits the palette's Mixer cannot reach are reached by
not using the Mixer.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

No characters: there is no standout to have two of, and the Law macro covers the
axis a character would have covered.

Macros (seven; ceiling sixteen), ranges in engineering values:

| # | Label | Mode | Range | What it generalizes |
|---|---|---|---|---|
| 0 | Rate | UNIPOLAR | 0.05–20 Hz, log | the pan speed; no panel anywhere to inherit one from |
| 1 | Depth | UNIPOLAR | 0–1, 0 = the Tier 1 wire | how far toward hard-over the sweep travels |
| 2 | Shape | UNIPOLAR | 0–1: 0 triangle, 1 sine | triangle sweeps at constant angular velocity, sine dwells at the extremes |
| 3 | Law | UNIPOLAR | calibrated at 3.01 / 4.5 / 6.02 dB centre attenuation | the console pan law (P2, P3); default constant power |
| 4 | Centre | BIPOLAR | −1…+1 | the axis the sweep is centred on — a static pan offset |
| 5 | Phase | BIPOLAR | −180…+180° | where in the period the sweep starts; matters when several instances share a transport |
| 6 | Sync | TOGGLE | off/on, default off | Rate quantised to the transport's tempo divisions when a transport is present |

`capabilities = ("tempo_sync",)` (D10): the class reads `transport()` when Sync
is on and holds its previous Rate when there is no transport. An LFO-driven
effect with a free Rate is exactly the case the roadmap names as a candidate, and
a swept pan that drifts against the bar is the one thing a host cannot fix.

Patches (names describe settings, never products): 0 **Slow Sweep** (0.25 Hz,
Depth 1, sine, constant power); 1 **Quarter Note** (Sync on, 1/4, Depth 0.8,
triangle); 2 **Wide Triangle** (0.8 Hz, Depth 1, triangle); 3 **Narrow Drift**
(0.12 Hz, Depth 0.35, sine); 4 **Mono-Safe Sweep** (0.5 Hz, Depth 1, sine,
Law 6.02 dB); 5 **Offset Left** (0.6 Hz, Depth 0.5, Centre −0.4); 6 **Fast
Flutter** (7 Hz, Depth 0.7, triangle); 7 **Half Note Offset** (Sync on, 1/2,
Depth 1, Phase 90°).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/modulation.py` on 2026-09-06.

- `modulation.py:121` with `:82-89`: the pan rides `MixerVoice.panning`, a block …  *(argument in full: App. R)*
- `Mixer.c:335-341`: even where it does move, the law attenuates only the far …  *(argument in full: App. R)*
- `modulation.py:86-89`: a `Mixer` sits at the class output, so on stock …  *(argument in full: App. R)*
- `modulation.py:119`: `synthio.LFO(rate=rate, scale=depth)` — a bare bipolar …  *(argument in full: App. R)*
- `modulation.py:117`: `rate` is unbounded and unlogged; nothing stops a rate
  above the block rate, where the effect becomes aliased amplitude noise.
- `modulation.py:114-116`: `MACRO_LABELS = ()` and one empty patch — no surface
  at all (vision §2.1).
- `tail_samples` reports `None` (measured, A1/P5); a gain law has no tail and the
  honest report is 0.
- Mono behaviour is accidental: `Mixer.c:336` skips the pan branch entirely when …  *(argument in full: App. R)*

Nothing else about the old class is carried forward.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **A2's tolerance wants a published number.** The ±0.1 dB is arithmetic on the
   law, which is fine for a gate but says nothing about how close a console
   actually holds its taper. The AES paper that would have said (Griesinger, P2's
   "looked for and not reached") 404'd. Owner: Station A, one fetch; if it stays
   unreachable the tolerance stands as arithmetic and the dossier says so.
2. **The Law macro's calibration points.** Three named laws on a continuous
   macro: whether the macro should be continuous with three marked positions, or
   a three-position TOGGLE-like enum, is a surface decision for the implementation
   session. The trait is written so either passes.
3. **The rate floor.** Below about 1.5 Hz the period table passes 128 KB (Tier 3).
   Whether the class clamps Rate there on a PSRAM-less board, or accepts the
   allocation, is decided with N1 on the Phase 0 node list — not here.
4. **The CPython Mixer never ticks its block inputs.** Not this class's bug, but
   `src/cpython/audiomixer.py` has no tick where `Mixer.c:331` has one, and every
   shipped class built on `_MixerMod` is therefore frozen on CPython. An audioif
   issue for Arthur to file with the measurement in A1/P5 attached; the rebuild
   routes around it either way.

---


## Appendix

### A1. Probes run this session (venv CPython, `audiocomponents/.venv`, 2026-09-06)

Scripts are throwaway; the numbers are the evidence. P1, P1b, P4, P4b and P5
below are the same runs cited by the `Tremolo` and `RingMod` seeds.

- **P2 — the palette Mixer's pan law, measured.** One voice, `level = 1.0`, a DC
  16000 stereo source, sample 100 of the render, at nine pan positions:

  | pan | L | R | L²+R² | (L+R)/2 |
  |---|---|---|---|---|
  | −1.00 | 0 | 16000 | 256 000 000 | 8000.0 |
  | −0.50 | 7999 | 16000 | 319 984 001 | 11999.5 |
  | 0.00 | 16000 | 16000 | 512 000 000 | 16000.0 |
  | +0.50 | 16000 | 7999 | 319 984 001 | 11999.5 |
  | +1.00 | 16000 | 0 | 256 000 000 | 8000.0 |

  Centre-to-edge power ratio **+3.010 dB**; mono sum centre-to-edge **−6.02 dB**.
  The near channel never leaves unity — the law is "attenuate the far channel",
  which is neither the 3 dB, the 4.5 dB nor the 6 dB convention.
- **P4 — `Multiply` honours per-channel modulator columns.** DC 16000 stereo
  source, modulator (L = 32767, R = 8192) → L = 15999, R = 4000. This is the
  whole of §4's design.
- **P5 — the shipped class on CPython.** `audioeffects.create('AutoPan', …,
  rate=5.0, depth=1.0)` over one second of DC 16000: L min/max 16000/16000, R
  min/max 16000/16000 — no movement at all. `latency_samples = 0`,
  `tail_samples = None`. The same run on `Tremolo` (rate 5, depth 1) gives a
  frozen 8000/7999, i.e. the LFO's value at phase 0, held for a second.
- **P9 — block-held pan products, across the whole Rate range** (trait-critic
  pass, 2026-09-06; numpy in the same venv, a float model of the law rather than a
  render through `Multiply` — what is being measured is the cost of holding a gain
  across a block, which is a property of the holding and not of the node). A 1 kHz
  tone, constant-power sweep, Depth 1, 2^19 frames, Hann FFT, worst of the
  ±30 Hz bands at 1000 ± 187.5 Hz:

  | Rate | per-sample | gain held across each 256-frame block |
  |---|---|---|
  | 0.05 Hz | −189.3 dB | **−65.4 dB** |
  | 1 Hz | −202.1 dB | −52.6 dB |
  | 5 Hz | −201.6 dB | **−38.0 dB** |
  | 10 Hz | −208.1 dB | −32.8 dB |
  | 20 Hz | −155.7 dB | **−25.7 dB** |

  A3's −80 dB bar therefore separates the two builds at every rate the macro
  offers, including the slowest — the row is not passable by a rate at which
  nothing moves. (The `−34 dB` an earlier draft of this seed attributed to the
  Mixer route appears in no probe in this file or in `Tremolo`'s; it is replaced
  by these measured figures.)
- **P16 — how far the old class's LFO actually swings** (palette-verifier pass,
  2026-09-06). `synthio.LFO(rate=r, scale=1.0)` with the default four-point
  triangle, ticked once per 256-frame block for eight periods, maximum value
  taken, then run through the Mixer's own arithmetic
  (`synthio/__init__.c:475-478` then `Mixer.c:338`):

  | Rate | LFO max | `panning` | far-channel scale | far channel |
  |---|---|---|---|---|
  | 0.25 Hz | 0.997303 | 32680 | 87 | −51.5 dB |
  | 0.75 Hz | 0.991970 | 32505 | 262 | −41.9 dB |
  | 0.80 Hz | 0.999436 | 32750 | 17 | −65.7 dB |
  | 5.00 Hz | 0.986637 | 32330 | 437 | −37.5 dB |

  `ALMOST_ONE` is 0.999969: the LFO never reaches it, so the clamp an earlier
  draft blamed never engages. A panning value that *does* reach it gives a far
  channel of exactly 0 — P2's pan +1.00 row, re-run this session.
- **P1 / P1b — `Multiply`'s wire and its LSB.** At `mix = 0` a 1 kHz half-scale
  tone comes back byte-identical over 8192 samples. At `mix = 1` with a modulator
  held at 32767 the error is −1 … 0, never positive, because `(a·b)>>15` is an
  arithmetic shift and floors. Depth 0 must therefore be `mix = 0`, not a table
  of 32767.

### A2. The two-line derivation behind A1 and A4

Constant power, `g_L = cos θ`, `g_R = sin θ`, `θ ∈ [0, π/2]`:
`g_L² + g_R² = 1` for all θ — flat, and at θ = π/4 each leg is
`1/√2` = **−3.01 dB**. The mono sum is
`cos θ + sin θ = √2·sin(θ + π/4)`, which runs from 1 at either extreme to √2 at
the centre — a **+3.01 dB** bump at the centre, reached twice per pan cycle.

Linear (mono-safe), `g_L = 1 − p`, `g_R = p`, `p ∈ [0, 1]`: the mono sum is 1 for
all p — flat — and at p = ½ each leg is ½ = **−6.02 dB**, while
`g_L² + g_R²` runs from 1 at the extremes to ½ at the centre, a **−3.01 dB** dip.

So the ripple is conserved: whichever quantity the law holds flat, the other
ripples by exactly 3.01 dB, and the 4.5 dB convention (P2, P3) splits it. A1 and
A4 are the two halves of this one fact, which is why they are measured from the
same envelope and why a build that passes one and fails the other has a bug
rather than a preference.

### A3. The kit measurements this seed names

- **ENV** — a full-scale 1 kHz tone rendered for four LFO periods; per-channel
  RMS in 1 ms windows; from the two envelope traces the kit reports `L²+R²` in dB
  (its spread across the sweep, and its centre-versus-extreme difference), the
  per-leg centre attenuation, and the mono sum `(L+R)/2` in dB with the position
  of its maximum. A1, A2, A4 and A6 all read this one export.
  *Planted fault that must turn it red:* replace the constant-power table with the
  Mixer's own far-channel-only law, whose measured signature is a centre 3.01 dB
  up rather than flat (A1/P2) — a fault with a known, already-measured answer.
- **BLOCK** — a 1 kHz tone rendered for four seconds; Hann-windowed FFT; the
  maximum in ±30 Hz bands around 1000 ± 187.5 Hz and 1000 ± 375 Hz, reported in
  dB re the tone. A3 reads this. *Planted fault:* hold the table's value constant
  across each 256-frame block, which is what a block input does, and the bands must
  rise from the per-sample build's −190 dB or lower to the −65.4 / −38.0 /
  −25.7 dB that A1/P9 measured at 0.05, 5 and 20 Hz. *The control that must pass:*
  the same probe on the per-sample build at those three rates, so the battery is
  not made only of faults.
- **WIRE** — construct at `channel_count` 1 (A5) or at Depth 0 (A6), render the
  probe set, byte-compare against the source. A5 and A6 read this. *Planted
  fault:* set the modulator to a constant 32767 with `mix = 1` instead of setting
  `mix = 0`; the compare must fail on the −1 LSB that A1/P1b measured.

Every measurement takes the sample rate as a parameter and records it in what it
exports; the evidence pack carries A1–A6 at 48 kHz and 44.1 kHz and the Tier 1
invariants additionally at 22.05 kHz.

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

`AutoPan` is **stereo by definition**, and the last invariant is therefore a real
decision, taken here: **a mono source gets a wire** — byte-identical output at
every macro setting, and `latency_samples`/`tail_samples` still 0. The mono sum
of the stereo behaviour was rejected because at the constant-power law it is a
3 dB tremolo at twice the pan rate (A4) that nobody asked for, and `Tremolo` is
the class for that. This is trait A5 and the kit measures it. No Tier 2 trait
depends on the sample rate: Rate's 20 Hz top and every gain law are rate-free, so
all of A1–A6 hold unchanged at 44.1 and 22.05 kHz.

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| A1 | At Law = constant power and Depth 1, `L² + R²` taken from the envelopes is flat to within **0.2 dB** over the whole sweep, and the centre of the sweep sits **3.01 ± 0.1 dB** below hard-over on each leg | P1; P2, P3 (the −3 dB rule) | high | a power ripple above 0.2 dB, or a centre attenuation outside 3.01 ± 0.1 dB | ENV |
| A2 | The Law macro reaches all three published conventions: its three calibration points give centre attenuations of **3.01, 4.5 and 6.02 dB** on each leg, each within 0.1 dB, and the centre attenuation increases monotonically with the macro between them | P2 ("a law of −3 dB is desirable" for stereo buses, −6 dB where they are recombined to mono, −4.5 dB "a compromise between the two"); P3 | high | any of the three points off by more than 0.1 dB, or a centre attenuation that does not rise monotonically across the eleven positions | ENV at eleven macro positions |
| A3 | The pan is per sample, not per block: with a 1 kHz tone at Rate 0.05, 5 and 20 Hz — the bottom, middle and top of the macro's range — and Depth 1, no component within ±30 Hz of 1000 ± f_s/256 or 1000 ± 2·f_s/256 (187.5 and 375 Hz at 48 kHz, the render block being 256 frames) rises above **−80 dB** re the tone | vision §6 (block-rate nodes); A1/P9, measured this run on the constant-power sweep: holding the gain across each block puts the first band at **−65.4 dB at 0.05 Hz, −38.0 dB at 5 Hz and −25.7 dB at 20 Hz**, so the bar has at least 15 dB of separation at every rate the surface offers and cannot pass by absence anywhere in the range | high | any product above −80 dB in those bands | BLOCK |
| A4 | The mono-sum ripple is exactly the complement of A1: at Law = constant power the mono sum `(L+R)/2` varies by **3.01 ± 0.2 dB** over the sweep with its maximum at the centre, twice per pan cycle; at Law = 6 dB it varies by **0.0 ± 0.2 dB** | P2; the two-line derivation in A2 | high | either figure outside tolerance, or the constant-power maximum anywhere but the centre | ENV, mono sum |
| A5 | A mono source is a wire: with `channel_count` 1 the output is byte-identical to the source at every Rate, Depth, Shape, Phase and Law setting, and at every patch | this dossier's §3 decision, which vision §3's last Tier 1 bullet requires be stated and measured | high | any differing byte | WIRE |
| A6 | Depth is honest at both ends: at Depth 1 the far channel's minimum over one period is **exactly 0**, not one LSB above it — the period table is built to place the sweep's extremes on table samples, so the zero is exact and not an approximation — and at Depth 0 both channels are byte-identical to the source | the textbook definition of a pan sweep; Tier 1's wire rule; the failure it guards is measured in §7 — the old class never quite reaches hard-over, though **not** for the reason an earlier draft of this row gave; see §7 and A1/P16 | high | a far-channel minimum of 1 LSB or more at Depth 1 (a clamp, or extremes that fall between table samples), or a non-wire at Depth 0 | ENV, WIRE |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

- **P1.** CCRMA / Planet CCRMA, "Multichannel Intensity Panning", Juan Reyes —
  constant intensity as `g₁² + g₂² = K`, grounded on `sin²(θ) + cos²(θ) = 1`,
  with a distance-compensated form and a circular-pan form. The equations are
  LaTeX-rendered PNGs, not page text; the auditor downloaded and read them, and
  they are, exactly: `g₁² + g₂² = K`; `sin²(θ) + cos²(θ) = 1`;
  `g₁ = sin²(θ)/d²`, `g₂ = cos²(θ)/d²`; and, for the circular pan,
  `g_a = (√2/2)[cos(θ) + sin(θ)]`, `g_b = (√2/2)[cos(θ) − sin(θ)]`. **Note the
  page's own inconsistency, recorded rather than smoothed over:** its
  distance-compensated pair uses *squared* sine and cosine, so `g₁ + g₂ = 1/d²`
  — a linear law, not the constant-power one the same page derives; only the
  circular pair satisfies `g_a² + g_b² = 1`. Nothing in §3 rests on the
  distance-compensated form. "© Copyright 2001-2022 CCRMA, Stanford University.
  All rights reserved" (footer, read verbatim) — **read only, all rights
  reserved.**
  <https://ccrma.stanford.edu/guides/planetccrma/Multichannel_Intensity_Pann.html>

*(from §2)*

- **P2.** Wikipedia, "Panning (audio)" — "If the two output buses are to remain
  stereo then a law of −3 dB is desirable"; −6 dB "if the two output buses are
  later recombined into a monaural signal"; −4.5 dB as the compromise. **CC
  BY-SA 4.0.** <https://en.wikipedia.org/wiki/Panning_(audio)>

*(from §2)*

- **P3.** Wikipedia, "Panning law" — a coherent signal in both channels rises "up
  to 6.02 dBSPL"; the 3 dB rule and the 4.5 dB rule named with the console
  families that use them. **CC BY-SA 4.0.**
  <https://en.wikipedia.org/wiki/Panning_law>

*(from §2)*

**Looked for and not reached.** `davidgriesinger.com/pan_laws.pdf` (HTTP 404,
re-checked by the audit) — a paper that might have given A2's tolerance a
published number instead of this seed's. **Nothing is known here about its
contents**: an earlier draft described it as "an AES convention paper comparing
sine-cosine against square-root laws for two- and three-channel arrays", which
could only have come from a search result's own words, and the audit struck it —
a 404 is not evidence about what a document says.
`ccrma.stanford.edu/~jos/pasp/Panning_Laws.html` and the `Interpolation/` variant
also 404 (both re-checked; the JOS page has moved or does not exist under those
paths). **Unsourced and kept out of the trait table:** any
claim about which law a listener prefers, and any figure for perceptual image
width against pan position — A2's ±0.1 dB tolerance is arithmetic on the law, not
a psychoacoustic claim. No emulator was read for code.

*(from §2)*

- **P1.** Raw HTML pulled directly. The equations are LaTeX-rendered PNGs and
  their `ALT` attributes carry the LaTeX itself, so the transcription above is
  checkable without reading the images: `$g_1^2+g_2^2=K$`,
  `$sin^2(\theta)+cos^2(\theta)=1$`, `$g_1=\frac{\sin^2(\theta)}{d^2}$`,
  `$g_2=\frac{\cos^2(\theta)}{d^2}$`,
  `$g_a=\frac{\sqrt(2)}{2}[cos(\theta)+sin(\theta)]$` and its `g_b` partner.
  The page's own inconsistency recorded above (squared sine and cosine in the
  distance-compensated pair) is real and is in the source, not in this seed.
  Footer read verbatim: "© Copyright 2001-2022 CCRMA, Stanford University. All
  rights reserved. Created and Mantained by Juan Reyes".

*(from §2)*

- **P2, P3.** Both quotations found verbatim, and the −4.5 dB compromise found
  on both pages in the raw wikitext ("4.5 dB at center is a compromise between
  the two"; "4.5 dB panning rule"). Footer on both: "Text is available under the
  Creative Commons Attribution-ShareAlike 4.0 License". **CC BY-SA 4.0** stands.

*(from §2)*

- The local citations behind §3 and §4 were re-read in the tree:
  `audioif_multiply.c:38-45` is the multiply/blend/clamp and `:28-29` the
  wet/dry pair that makes `mix = 0` bit-exact; `Mixer.c:331` is the block-rate
  `shared_bindings_synthio_lfo_tick`; `Mixer.c:335-341` is the pan law that
  scales only the far channel; `src/cpython/audiomixer.py` contains zero
  occurrences of `tick`; `upstream-diff.md:714` is the `audiomath` heading.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: **ESP32-P4 1 %,
ESP32-S3 2 %** — per sample one Q15 multiply, one blend and one clamp per channel
(`audioif_multiply.c:38-45`), the same node and the same work as `Tremolo` and
`RingMod`. Lean patch expected: **no**. RAM: one stereo period table, 4 bytes per
frame — 19 KB at 10 Hz, 64 KB at 3 Hz, 384 KB at 0.5 Hz — allocated at
construction and on every Rate, Depth, Shape, Phase or Law move, never on pull.
The rate floor is the only place this design is expensive, and it is why §5's
conditional ask exists.

*(from §3)*

**Latency: 0 samples (0.0 ms at 48 kHz); `tail_samples` 0.** A pan law is a gain
pair applied sample-aligned; nothing in the class looks ahead or remembers.
**No option adds latency and none may be added** — a smoothing filter on the gain
would be a filter, not a delay, and any proposal that buys smoothness with
lookahead is refused under vision §9a. The class gate's click measurement
verifies `latency_samples = 0` at 48 kHz and 44.1 kHz.

*(from §4)*

Python computes one whole LFO period at construction: for each frame, the sweep
position from Rate/Shape/Phase, then `g_L` and `g_R` from the Law, scaled by
Depth toward the centre, written as Q15 into the table's two columns. At Depth 0
the class sets `mix = 0`, which `audioif_multiply.c:28-29` makes a bit-exact wire
(A6). Tables are computed on CPython and never rebuilt on a board mid-render (the
ESP32 ports are single-precision). **A mono source gets no node at all** — the
class hands its source straight through, which is the cheapest possible way to
honour A5 and makes the byte compare trivially exact.

*(from §4)*

- **It is not constant power, and it is not any of the three published laws.**
  The pan branch attenuates only the *far* channel and leaves the near one at
  unity (`Mixer.c:335-341`; the CPython path is the same arithmetic at
  `src/cpython/audiomixer.py:151-154`). Measured on a DC 16000 stereo source, the
  centre is 3.01 dB **up** in power on the edges, and the mono sum falls 6.02 dB
  from centre to hard-over (A1/P2). That is A1 and A2 failed at every setting and
  A4 inverted.

*(from §4)*

- **It is block-rate, and on CPython it does not move at all.** `Mixer.c:331`
  ticks the LFO once per pulled chunk; `src/cpython/audiomixer.py` contains no
  tick at all (zero occurrences of the string), so the block input is read at
  whatever value it was constructed with. Measured: the shipped `AutoPan` at
  Rate 5 Hz, Depth 1 renders **16000 / 16000, constant, for a full second** on
  CPython (A1/P5). That is A3 failed and a Tier 1 cross-interpreter failure.

*(from §4)*

A Mixer at the class output is also unusable mid-chain on stock CircuitPython,
where the next node's `play()` silences it permanently
(`upstream-diff.md:887`, and `:929-938` for why audioif's fix is deliberately not
applied to that target) — a third reason, independent of the two above. Note that
this is about a Mixer at the **class output**; a Mixer used only to loop a
modulator table (below) is never reset by `Multiply`, whose `reset_buffer` clears
its own cursors and does not recurse (`Multiply.c:198-209`).

*(from §4)*

**A short table instead of a whole period, measured** (palette-verifier pass,
2026-09-06; shared with `Tremolo` §4). `Mixer(voice.play(table, loop=True)) →
audiospeed.SpeedChanger(rate) → Multiply` plays a **1 KB** table per sample
instead of the whole-period table Tier 3 prices at 384 KB at 0.5 Hz, and its
`rate` changes mid-render with a **measured phase jump of zero** (`Tremolo`
A1/P13). Two things the implementation session must measure before choosing it
for this class rather than `Tremolo`'s: `SpeedChanger` is nearest-neighbour
(`SpeedChanger.c:160`, `:171-173`), so the modulator is a staircase whose
step rate is (table length)·Rate — and at this class's **0.05 Hz floor** that is
13 Hz with a 256-point table, well below A3's 187.5 and 375 Hz bands, where the
staircase's images have to be shown to sit under −80 dB rather than assumed to;
and its phase truncates to zero on every source-buffer fetch
(`SpeedChanger.c:99-100`). A6's "extremes on table samples" is also a stronger
requirement here than in `Tremolo`, and a nearest-neighbour read of a short table
places them only if the table length divides the period. Neither is a reason to
ask for a node (§5); both are numbers Station A owes before it picks a form.

*(from §5)*

**N1 (conditional, shared with `Tremolo`, not asked for here) — a table-driven,
phase-continuous LFO modulator inside `audiomath`.** *Trait ids:* none. It
unblocks no fixed trait; it addresses the RAM floor at slow rates (Tier 3: 384 KB
at 0.5 Hz) and the phase restart on every Rate move, which is a click the class
gate will measure but which no trait in §3 names. *What the palette does instead:*
rebuilds the period table, which works at every rate the surface offers and fits
both boards above about 1.5 Hz. *Refutation record (Phase 0):* since no trait is
blocked, this ask cannot survive a need statement on `AutoPan`'s own account and
is recorded here only so the Phase 0 node list sees the second consumer.

*(from §5)*

**REFUTED BY PALETTE** (palette-verifier pass, 2026-09-06), on the same two
grounds recorded in `Tremolo` §5: the ask names no trait id, and the two things
it addresses instead — the RAM floor at slow rates and the phase restart on a
Rate move — are both reached by `Mixer(voice.play(table, loop=True)) →
audiospeed.SpeedChanger(rate) → Multiply`, which was built and rendered
(`Tremolo` A1/P13): a 1 KB table read per sample, and a mid-render rate change
with a measured phase jump of zero. N1 does not go on the Phase 0 node list from
either class. What remains for this class is a measurement, not a node: the
staircase's step rate at the 0.05 Hz Rate floor (§4).

*(from §7)*

- `modulation.py:121` with `:82-89`: the pan rides `MixerVoice.panning`, a block
  input. On CPython the Mixer never ticks it (`src/cpython/audiomixer.py` has no
  tick), so the shipped class renders a **constant 16000/16000 for a full second**
  at Rate 5 Hz, Depth 1 — measured, A1/P5. The effect simply does not exist on
  one of the three interpreters, and nothing in the tree said so.

*(from §7)*

- `Mixer.c:335-341`: even where it does move, the law attenuates only the far
  channel — centre power 3.01 dB *above* the edges, mono sum 6.02 dB *below*
  (measured, A1/P2). That is not any of the three published pan laws.

*(from §7)*

- `modulation.py:86-89`: a `Mixer` sits at the class output, so on stock
  CircuitPython the class is silenced by the next node's `play()`
  (`upstream-diff.md:887`) and can only ever be last in a chain.

*(from §7)*

- `modulation.py:119`: `synthio.LFO(rate=rate, scale=depth)` — a bare bipolar
  triangle with no law, no shape, no centre and no phase; at Depth 1 hard-over is
  never quite reached (A6). **The mechanism, corrected by measurement**
  (palette-verifier pass, 2026-09-06; an earlier draft of this bullet and of A6
  blamed a clamp to `ALMOST_ONE` at `Mixer.c:333`, and that is wrong): the
  `ALMOST_ONE` bound is not the obstacle, because a panning value that *does*
  reach it scales to exactly 32767 (`synthio/__init__.c:475-478`) and
  `Mixer.c:338` then leaves the far channel at exactly 0 — measured, pan +1.00
  gives R = 0 (A1/P2, re-run this session). What actually stops the old class is
  that the LFO is sampled once per 256-frame block on the default **four-point**
  triangle `{0, 32767, 0, −32767}` (`LFO.c:139`, read and interpolated at
  `:51-68`), so the peak index falls *between* ticks and the LFO's own maximum
  never even reaches the bound: measured **0.999436 at Rate 0.8 Hz** and
  **0.986637 at 5 Hz**, which leave the far channel at **−65.7 dB** and
  **−37.5 dB** instead of at zero (A1/P16). It is the block-rate sampling — A3's
  defect — not a clamp, and the rebuild's per-sample table removes it by placing
  the sweep's extremes on table samples, exactly as A6 requires.

*(from §7)*

- Mono behaviour is accidental: `Mixer.c:336` skips the pan branch entirely when
  `channel_count` is 1, so the class is silently a wire — the right answer,
  arrived at by omission, undocumented and unmeasured.
