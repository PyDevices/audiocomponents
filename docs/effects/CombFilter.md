# Effects Dossier — `CombFilter` (no historical standout — design grade)

**Class:** `lib/audioeffects/eq.py` — the current implementation is read once,
for §7, and not otherwise consulted.
**Family / phase:** EQ / Filter, roadmap Phase 2
**Standout:** none, per vision §4.2 — **confirmed** (§2).
**Grade:** design
**Portability tier:** **audioif** (`audioecho.FeedbackDelay`) — see §4 for why
the stock `audiodelays.Echo` route cannot carry the class.
**Status:** seed (Phase 0)

## 1. The circuit, in one paragraph

A comb filter is a delay line summed with its own input, and — in the
feedback form this class wants — with its own output. Smith gives it as
`y(n) = x(n) + g·y(n−M)`, transfer function `H(z) = 1/(1 − g·z^(−M))`,
amplitude response `G(ω) = 1/|1 − g·e^(−jωM)|` (S2, verbatim), whose peaks
sit at `ω_k = 2π(k/M)` — that is, at every integer multiple of `F_s/M`,
spaced `F_s/M` apart, which is why tuning the line to `1/f` seconds makes the
filter resonate on the harmonic series of `f`. The gains at the extremes are
`1/(1−g)` at the peaks and `1/(1+g)` at the anti-resonances (**derived**, by
evaluating S2's `G(ω)` at `ωM = 0` and `ωM = π`; the page states `G(ω)`, not
the two extremes), so `g` is a
single knob that runs from a gentle ripple to a ringing pitch, and stability
requires `|g| < 1`: *"For stability, the feedback coefficient a_M must be
less than 1 in magnitude"* (S2). There is no nonlinearity in the ideal
circuit; the loop filters and soft clip an analog delay would add belong to
`AnalogDelay` and `TapeDelay`, not here. The one control a comb has beyond
tuning and feedback is the **sign** of the feedback: S2 puts the peaks of a
positive comb at `ω_k` *"while for g<0, the peaks occur midway between these
values"* —
the odd-harmonic comb, which sounds hollow and square-wave-like where the
positive one sounds pitched. That sign is this class's only node ask (§5).
Panel controls: *frequency*, *feedback*, *mix*.

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S2** J. O. Smith III, *Physical Audio Signal Processing* — "Feedback Comb Filters" and "Feedback Comb Filter Amplitude Response" | `y(n) = x(n) + g·y(n−M)`; `H(z) = 1/(1−g z^(−M))`; `G(ω) = 1/\|1 − g e^(−jωM)\|`; peaks at `ω_k = 2π(k/M)` (the `2π/M` spacing follows, and is derived); extremes `1/(1−g)` and `1/(1+g)` (**derived** from `G(ω)` at `ωM = 0, π` — not stated on the page); *"For stability, the feedback coefficient a_M must be less than 1 in magnitude"*, verbatim; *"while for g<0, the peaks occur midway between these values"*, verbatim | © Julius O. Smith III / CCRMA Stanford; W3K Publishing, ISBN 978-0-9745607-2-4. No license granted. Read as a paper | https://ccrma.stanford.edu/~jos/pasp/Feedback_Comb_Filters.html , …/Feedback_Comb_Filter_Amplitude.html | 2026-09-06 |
| **S2b** same book, "Feedforward Comb Filters" | `y(n) = b₀x(n) + b_M x(n−M)` … (App. S2b) | same | https://ccrma.stanford.edu/~jos/pasp/Feedforward_Comb_Filters.html | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* … (App. S3) | *"After Q periods, the amplitude envelope has decayed … (App. S3) | same | https://ccrma.stanford.edu/~jos/filters/Decay_Time_Q_Periods.html | 2026-09-06 |

**Looked for, not found:** `ccrma.stanford.edu/~jos/filters/Comb_Filters.html`
404s (the PASP pages above are the reachable ones); no DAFx or AES paper was
hunted, because the feedback comb is a two-line result and a paper would add
nothing a textbook page does not already state exactly.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **Peaks on the harmonic series of the tuned frequency**: with the line at `1/f` seconds the resonances sit at f, 2f, 3f …, spaced exactly f, for every f in 20 Hz…4 kHz | S2 (`ω_k = 2π k/M`) | high | any peak or spacing more than 1 % off, anywhere in 20 Hz…4 kHz | swept sine, peak picking … (App. T1) |
| T2 | **The feedback knob is the peak height, to the textbook law**: wet-only gain is `1/(1−g)` at the peaks and `1/(1+g)` at the nulls, within 0.2 dB — g 0.8 gives +13.98 and −5.11 dB | S2's `G(ω)` evaluated at `ωM = 0 … (App. T2) | high | either extreme more than 0.2 dB from the closed form, for g ∈ {0.3, 0.5, 0.8, 0.95} | steady-state sine at f and at 1.5 … (App. T2) |
| T3 | **Fractional tuning**: the comb tunes continuously, not to the nearest whole sample — every request in 20 Hz…4 kHz lands within 5 cents. The test only has teeth where the whole-sample grid is coarser than 5 cents, which at 48 kHz means **above about 300 Hz**: rounding 48 000/f to the nearest integer costs only +1.44 cents at 110 Hz — too small to tell an interpolator from a rounder — but −14.37 cents at 880 Hz, +17.40 at 1760 Hz and **−45.56 at 3520 Hz**, T1's top probe. 4 kHz is the one frequency in that decade that must *not* be the test: 48 000/4 000 = 12.000 samples exactly, so a rounding implementation lands on it too | `audioif_feedback_delay.c:226-229` … (App. T3) | high | a first peak more than 5 cents from the request at any of {880, 1760, 3520} Hz, or more than 5 cents anywhere else in 20 Hz…4 kHz | impulse, first-repeat centroid to … (App. T3) |
| T4 | **Negative feedback puts the peaks on the odd half-multiples** — f/2, 3f/2, 5f/2 … — which is the hollow, square-ish comb, as distinct from the pitched positive one | S2, verbatim: *"while for g<0 … (App. T4) | high | a requested g < 0 whose peaks stay on the integer multiples | the T1 sweep at g = −0.8 … (App. T4) |
| T5 | **Zero feedback is the feedforward comb**: at g = 0, Mix 1, the nulls are total at odd multiples of f/2 and the peaks exactly +6.02 dB at multiples of f | S2b; measured bit-exact zero at 500/1500 Hz … (App. T5) | high | a null above −60 dB or a peak outside +6.02 ± 0.1 dB | steady-state sine at f/2, f … (App. T5) |
| T6 | **The tuning knob is click-free**: a 100 Hz → 1 kHz sweep over one second produces no discontinuity above −60 dBFS relative to the running signal, and no single knob step anywhere in 20 Hz…4 kHz produces one | no external source … (App. T6) | medium — the palette … (App. T6) | any discontinuity above −60 dBFS during the sweep, or on any single step of the size the Tune macro's smallest increment produces | first-difference of the output … (App. T6) |

No characters: a comb has one behaviour.

~~**T4 is unreachable on today's palette.**~~ **Superseded 2026-09-07:** T4
*is* reachable, as a five-node composition measured to within 0.01 dB of the
closed form — §5, Ask 1, and A12. T6 is the one that remains unreachable.

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Compose first — but the node the class uses today cannot do the job, and
the node beside it can.** `audiodelays.Echo` quantises its line to whole
samples (`audioif_echo.c:30`) *and* floors it at the node's own buffer length
(`Echo.c:124-129`), so at the library's standard 2048-byte buffer
(`_core.py:64`) the shortest line it will build is 1024 frames — **21.3 ms, a
46.9 Hz comb**. Every `CombFilter` frequency from 47 Hz to 880 Hz measured as
that same 46.88 Hz comb (A2), reproduced independently 2026-09-07 (A12), where
the floor also tracked `buffer_size` exactly: 512 bytes → 187.50 Hz, 1024 →
93.75, 2048 → 46.88, 4096 → 23.44. That is not a tuning error, it is the
absence of tuning.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

Two were written; **one survives.** Both were already on the vision §6
candidate list for other classes, so neither is a new node. The palette
verification of 2026-09-07 (A12) refutes the first and confirms the second.

**Ask 1 — signed feedback on `audioecho.FeedbackDelay`. Unblocks T4.**
**REFUTED BY PALETTE: the odd-half-multiple comb composes exactly out of
nodes that already exist, and it was measured on 2026-09-07 (A12).**

- `1 − g·z^(−M)` — `audioroute.Splitter(taps=2)`, one tap dry, the other …  *(argument in full: App. R)*
- `1/(1 − g²·z^(−2M))` — a second `FeedbackDelay` at 2M with feedback g²,
  which is inside the existing clamp.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 20 Hz … 4 kHz, log (line 50 ms … 0.25 ms) | the tuning knob |
| 1 | Feedback | BIPOLAR | −0.95 … +0.95, default +0.7; the negative half is built by the composition in §5 (Ask 1 refuted), so it costs four extra nodes when the macro crosses zero — or the class builds the composition once and runs it at every sign | the resonance/regeneration knob, with the sign switch S2 describes |
| 2 | Mix | UNIPOLAR | 0 exactly … 1 (dry plus wet; the node's own convention, `audioif_feedback_delay.c:201-202`) | the blend knob |
| 3 | Tone | UNIPOLAR | in-loop low-pass 1 kHz … off, default off | the darkening a resonator gets from its own losses |
| 4 | Trim | BIPOLAR | −12 … +12 dB, default 0 | make-up, because `1/(1−g)` at g 0.95 is +26 dB |

`capabilities = ()`: a comb's delay is a *pitch*, not a rhythm, so syncing it
to the transport would be meaningless — the class does not read `transport()`
(D10, answered, and this is the one class in the unit where the answer needed
an argument rather than an observation).

Patches: 0 **Metallic** (440 Hz, +0.7, mix 1, tone off — the constructor's
defaults on the grid), 1 **Ringing Pitch** (220 Hz, +0.92, mix 1, −9 dB
trim), 2 **Soft Ripple** (110 Hz, +0.3, mix 0.5), 3 **Hollow** (330 Hz,
−0.8, mix 1 — the negative comb, reachable today by §5's composition), 4 **Single Slap** (55 Hz, 0.0,
mix 1 — the feedforward comb of T5), 5 **Dark Resonator** (150 Hz, +0.85,
mix 1, tone 2 kHz, −6 dB trim).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/eq.py`.

- **The class does not tune. At all.** `delay_ms = 1000.0/float(frequency)` …  *(argument in full: App. R)*
- **Even without the floor, the tuning would quantise.** `audioif_echo.c:30`
  reads a whole-sample tap; at 4 kHz the nearest whole sample is 45 cents
  away, at 5 kHz 111 cents.
- **No guard on `feedback`.** `eq.py:204` passes it straight to `decay`; the …  *(argument in full: App. R)*
- **No surface at all.** `MACRO_LABELS = ()` (`eq.py:200`); frequency,
  feedback and mix are constructor-only and there is no setter for any of
  them.
- **`max_delay_ms=50` is hard-coded** (`eq.py:207`), so the class silently
  clamps below 20 Hz and can never be a longer resonator.
- **No tail is declared** (`TAIL_SAMPLES = None`, `_core.py:141`) for a class
  whose whole point is a feedback loop; `latency_samples` 0 is right and
  measured right (A8).
- **`reset()` and `deinit()` reach one node each** (`_core.py:366-374`, …  *(argument in full: App. R)*

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Ask 1 and Ask 2** (§5) — do they survive Gate 0's refutation, and what
   do they cost on the S3? *Settled by:* Phase 0 Gate and Phase 1.
2. **Whether the top of the Frequency range should be 4 kHz or Nyquist/4.**
   Above ~4 kHz the line is under 12 samples and linear interpolation's own
   low-pass tilt starts to shape the comb; the honest ceiling may be lower.
   *Settled by:* the implementation session, measuring the tilt.
3. **Whether the line should be int16 or float.** The node stores the
   recirculating signal as int16 (`audioif_feedback_delay.c:255-256`), so at
   g 0.95 the ring accumulates quantisation noise over its ~60 000-sample
   tail. Whether that is audible at −90 dBFS, and whether a float line is
   worth the RAM, is a measurement nobody has taken. *Settled by:* the
   implementation session at Phase 2; it becomes a Phase 1 ask only if the
   measurement says so.

---


## Appendix

Run 2026-09-06 on this machine. CPython target:
`audiocomponents/.venv/bin/python`. MicroPython: `cmods/bin/micropython`.
Probes were scratch scripts, not committed; every number is reproducible from
its description. A3 shares its run with `LowPass.md`.

### A2. The measurements this seed rests on

**The shipped class does not tune.** `CombFilter(frequency=f)`, impulse in,
left channel, positions of the repeats:

```
  asked  110.00 Hz -> wanted delay  436.36 samples;  impulses at [0,1024,2048,3072,4096,5120]; first lag 1024 -> 46.88 Hz
  asked  220.00 Hz -> wanted delay  218.18 samples;  impulses at [0,1024,2048,3072,4096,5120]; first lag 1024 -> 46.88 Hz
  asked  440.00 Hz -> wanted delay  109.09 samples;  impulses at [0,1024,2048,3072,4096,5120]; first lag 1024 -> 46.88 Hz
  asked  880.00 Hz -> wanted delay   54.55 samples;  impulses at [0,1024,2048,3072,4096,5120]; first lag 1024 -> 46.88 Hz
  asked   47.00 Hz -> wanted delay 1021.28 samples;  impulses at [0,1024,2048,3072,4096,5120]; first lag 1024 -> 46.88 Hz
  asked   20.50 Hz -> wanted delay 2341.46 samples;  impulses at [0,2341,4682,7023,9364,11705]; first lag 2341 -> 20.50 Hz
```

The floor tracks the node's buffer length exactly, confirming `Echo.c:126-128`
as the cause rather than anything in the Python:

```
  buffer_size=  256 bytes -> first lag 128 samples =  375.00 Hz  (asked 440 Hz = 109.09 samples)
  buffer_size=  512 bytes -> first lag 256 samples =  187.50 Hz
  buffer_size= 1024 bytes -> first lag 512 samples =   93.75 Hz
  buffer_size= 2048 bytes -> first lag 1024 samples =  46.88 Hz
```

**`audioecho.FeedbackDelay` tunes, fractionally.** Same impulse, same
requests:

```
  asked   110.0 Hz ( 436.364 samples)  peaks at [0, 436, 437, 872, 873, 874]
  asked   440.0 Hz ( 109.091 samples)  peaks at [0, 109, 110, 218, 219, 220]
  asked  1000.0 Hz (  48.000 samples)  peaks at [0, 48, 96, 144, 192, 240]
  asked  4000.0 Hz (  12.000 samples)  peaks at [0, 12, 24, 36, 48, 60]
```

The split across two neighbouring samples at 110 and 440 Hz is the
interpolator (`audioif_feedback_delay.c:226-229`) placing a fractional tap;
at 1 kHz and 4 kHz the request lands on whole samples and there is nothing to
split. T3's planted fault: replace the interpolated read with
`lane[near_frame]` alone and the 110 Hz case must collapse onto one sample
and read 110.09 Hz.

**T2, the peak/null law.** Wet-only (`mix=2`), 1 ms line, g = 0.8:

```
   1000.0 Hz ->  +13.98 dB      theory 1/(1-g) = +13.98
   1500.0 Hz ->   -5.11 dB      theory 1/(1+g) =  -5.11
```

Dry summed (`mix=1`), 440 Hz line, g = 0.8: +15.56 dB at 440 and 880 Hz,
−7.04 dB at 220, 660 and 1100 Hz, against the closed form's +15.56 and −7.04.
Two independent derivations agree to the second decimal.

**T5, the feedforward comb.** g = 0, `mix=1`, 1 ms line:

```
    500.0 Hz -> -180.00 dB    (bit-exact zero)
   1000.0 Hz ->   +6.02 dB
   1500.0 Hz -> -180.00 dB
   2000.0 Hz ->   +6.02 dB
```

**T4, and why it is an ask.** Requested feedback ±0.8, 1 ms line, impulse:

```
  requested feedback +0.80: peaks at [0, 48, 96, 144, 192, 240] values [20000, 20000, 16000, 12800, 10240, 8192]
  requested feedback -0.80: peaks at [0, 48]                     values [20000, 20000]
```

The negative request produces one repeat and stops — the clamp at
`audioif_feedback_delay.c:90` has turned it into g = 0. The peaks cannot move
to the midpoints because there is no recirculation to move them.

### A3. Held DC after silence

`CombFilter` at its shipped defaults settles to exact zero on both
interpreters, so audioif#23 does not reach this class. The probe and its
planted fault (pulling past the end of the source makes every filter look
clean, because `Filter.c:202-223` memsets when the source is exhausted) are
described in `LowPass.md` A3.

### A5. Refutation records for the two asks

*Ask 1.* ~~Could the class compose a negative-feedback comb from positive
parts? `1/(1 + g z^(−M))` is the positive comb at half the delay minus the
positive comb at the full delay — two `FeedbackDelay` nodes and a mixer,
doubling cost and RAM, and the cancellation is exact only if both lines are
bit-identical, which they stop being as soon as the interpolator's rounding
differs between a fractional and a whole-sample tap. That is a coincidence
that drifts, not a composition. The ask stands.~~
**Overturned 2026-09-07 by the palette verification pass (A12).** The identity
written here is wrong: `1/(1 + g z^(−M))` is not a difference of two positive
combs, it is the *product* `(1 − g z^(−M)) · 1/(1 − g² z^(−2M))`. Both factors
are on the palette, nothing has to cancel, and the composition measures within
0.01 dB of the closed form at every peak and null. Ask 1 is refuted; §5 carries
the composition and its cost.

*Ask 2.* Could a crossfade between two `FeedbackDelay` nodes hide the step?
Both nodes' outputs are continuous, but the crossfade itself is not: a
`Mixer` voice level is a block slot, ticked once per block
(`audioif/src/audiomixer/Mixer.c:330-332`), so the ramp is a staircase whose
step is `1/N` of full scale for an N-block fade — 9 blocks over 100 ms at
48 kHz is an 11 % amplitude step, about −19 dBFS, which is the same order as
the click it replaces and far above T6's −60 dBFS bar. Reaching −60 dBFS would
need a fade of order a thousand blocks, over ten seconds. `audiomath.Multiply`
*is* per-sample and could carry a ramp table, at the cost of two more nodes and
a table restart per knob move, but it was not built or measured in this run and
is not claimed. The ask stands, and A12 measures the step it removes.

### A7. Desktop cost anchor

```
  FeedbackDelay comb      frames= 256    141.7 ns/frame
  Filter 1 biquad         frames= 512    146.6 ns/frame
  CombFilter (Echo node)  frames= 512    161.7 ns/frame
  real time per stereo frame at 48 kHz = 20833.3 ns
```

### A8. Latency

Impulse at frame 50 through `CombFilter()`: first non-zero output at frame
**50**, peak **20 000** of 20 000 — the dry path is bit-transparent and the
comb's own delay is on the wet path. `latency_samples` reports **0**. Agreed.

### A9. Licence and citation audit, 2026-09-06

This seed's §2 carries the corrections themselves; this is the full
re-verification record behind them. Every source row in §2 and every URL
anywhere in this seed was re-fetched by a second agent that read none of the
first run's notes. Three corrections applied in place. The negative-feedback
sentence was quoted as *"peaks shift to midway positions between these
values"*; the page's actual words are *"while for g<0, the peaks occur midway
between these values"*, and §1, the S2 row and T4 now carry the real quote —
the substance was right, the quotation marks were not. The **peak and null
extremes `1/(1−g)` and `1/(1+g)` are not stated on the page**: they follow
from S2's `G(ω)` evaluated at `ωM = 0` and `ωM = π`, and are now marked
derived in §1, in the S2 row and in T2's source. The `2π/M` spacing is marked
derived for the same reason.

Re-verified exactly as the seed states them: `y(n) = x(n) + g·y(n−M)`,
`H(z) = 1/(1 − g z^(−M))`, `G(ω) = 1/|1 − g e^(−jωM)|`, the peaks at
`ω_k = 2π(k/M)`, and *"For stability, the feedback coefficient a_M must be
less than 1 in magnitude"* — all verbatim on the two PASP pages;
`y(n) = b₀x(n) + b_M x(n−M)` verbatim on the feedforward page; the e^{−π}
decay in Q periods verbatim on the *Decay Time is Q Periods* page; the
footer's *"Physical Audio Signal Processing", by Julius O. Smith III, W3K
Publishing, 2010, ISBN 978-0-9745607-2-4* with **no** licence grant; and
`ccrma.stanford.edu/~jos/filters/Comb_Filters.html` returning **404**, exactly
as recorded. The two repository citations behind T3 and the latency claim were
re-read with `grep -n`: `audioif_feedback_delay.c:226-229` is the per-sample
linear interpolation and `:260-261` is `to_s16(dry * source + wet *
loop[channel])`, both as cited.

**Unsourced, and flagged as such:** the attributes given to the two dropped
candidates (the Electric Mistress's BBD companding, bandwidth and inverted
feedback; a Schroeder comb bank's echo density and RT60) are stated from
general knowledge — no schematic or paper for either was reached in this run.
They carry the scope argument only; nothing in §3 rests on them.

### A10. Second licence and citation audit, 2026-09-06 (the re-fetch pass)

**Second licence-and-citation audit, 2026-09-06** — a third pass, run
independently of the first audit, in which **every URL in this seed was
re-fetched in this run**, including
`ccrma.stanford.edu/~jos/filters/Decay_Time_Q_Periods.html`, which carries
verbatim *"After Q periods, the amplitude envelope has decayed to e^(−π)
≈ 0.043, which is about 96 percent decay"* under the condition *"Q >> 1/2"*.

**One correction from this pass**, applied above: **S3's "what it gave" cell
overstated its use.** The Decay-Time page is genuinely reached and its
sentence is verbatim, but no trait in §3 cites it and this class's
`tail_samples` is derived from the feedback coefficient
(`ceil(−6.91/ln g · F_s/f)`), not from Q periods; the cell now says so. Every
S2 quote was re-fetched and is verbatim on the page named: the difference
equation *"y(n) = x(n) + g·y(n-M)"*, *"H(z) = 1/(1-g·z^(-M))"* and
*"G(ω) = 1/|1 - g·e^(-jωM)|"* on **Feedback Comb Filter Amplitude Response**,
the peaks *"at ω_k = 2πk/M"* and *"for g<0, the peaks occur midway between
these values"* on the same page, and *"For stability, the feedback
coefficient a_M must be less than 1 in magnitude, i.e., |a_M|<1"* on
**Feedback Comb Filters**. Note for a reader checking by eye: the Feedback
Comb Filters page states the direct-form-1 equation as
*"y(n) = b_0 x(n) - a_M y(n-M)"*, so `g = −a_M`; `|g| < 1` and `|a_M| < 1`
are the same condition. **Feedforward Comb Filters** gives
*"y(n) = b_0 x(n) + b_M x(n-M)"*, S2b as cited. The extremes `1/(1−g)` and
`1/(1+g)` are still **not on the page** and remain marked derived; re-derived
here, g = 0.8 gives +13.98 dB and −5.11 dB, matching T2, and the feedforward
peak is +6.02 dB, matching T5. All three CCRMA pages carry only
*"'Physical Audio Signal Processing', by Julius O. Smith III, W3K Publishing,
2010, ISBN 978-0-9745607-2-4. Copyright © 2026-08-21 by Julius O. Smith III"*
— no licence granted, so *read as a paper* stands.
`ccrma.stanford.edu/~jos/filters/Comb_Filters.html` was re-checked and is
still **HTTP 404** — recorded as not reached, never as evidence.

### A11. Trait-critic pass, 2026-09-06 — the tuning-grid derivation

Arithmetic on the sample rate, in float64
(`audiocomponents/.venv/bin/python`). Not a render.

Whole-sample rounding error at T1's own probe frequencies, 48 kHz — i.e. what
a *non*-interpolating comb would deliver, and therefore the size of the gap
T3's 5-cent tolerance has to see across:

| f | 48 000/f (samples) | nearest whole → Hz | rounding error |
|---|---|---|---|
| 55 Hz | 872.727 | 873 → 54.983 | −0.54 cents |
| 110 Hz | 436.364 | 436 → 110.092 | +1.44 cents |
| 220 Hz | 218.182 | 218 → 220.183 | +1.44 cents |
| 440 Hz | 109.091 | 109 → 440.367 | +1.44 cents |
| 880 Hz | 54.545 | 55 → 872.727 | **−14.37 cents** |
| 1760 Hz | 27.273 | 27 → 1777.778 | **+17.40 cents** |
| 3520 Hz | 13.636 | 14 → 3428.571 | **−45.56 cents** |
| 4000 Hz | 12.000 | 12 → 4000.000 | **0.00 cents** |

And the grid's coarseness, as the interval between adjacent whole-sample
tunings (worst-case rounding is half of it): 0.72 cents at 20 Hz, 3.97 at
110 Hz, 15.81 at 440 Hz, 35.70 at 1 kHz, 70.67 at 2 kHz, 138.57 at 4 kHz.
This is why the fractional-tuning claim is a high-frequency claim: below a few
hundred Hz the two mechanisms are indistinguishable at a 5-cent tolerance.


### A12. Palette verification pass, 2026-09-07

Every §4/§5 claim about what an audioif node can and cannot do re-measured
independently. CPython target `audiocomponents/.venv/bin/python`, which runs
the same `src/shared` C the boards do (`src/cpython/_audioif.c:23` includes
`shared/audioif_feedback_delay.h`; `:20-21` the splitter and multiply).
Sources reach the graph through a one-voice `Mixer` pump, so nothing ever
hands a downstream node more than 512 frames in one call. Probes were scratch
scripts, not committed; every number is reproducible from its description.

**`audiodelays.Echo` cannot tune.** Today's class, `mix = 1` so the output is
wet-only, impulse in, peaks out:

```
  request   47.0 Hz -> peaks [1024, 2048, 3072, 4096]  => 46.88 Hz
  request  100.0 Hz -> peaks [1024, 2048, 3072, 4096]  => 46.88 Hz
  request  220.0 Hz -> peaks [1024, 2048, 3072, 4096]  => 46.88 Hz
  request  440.0 Hz -> peaks [1024, 2048, 3072, 4096]  => 46.88 Hz
  request  880.0 Hz -> peaks [1024, 2048, 3072, 4096]  => 46.88 Hz
  request   20.0 Hz -> peaks [2400, 4800, 7200]        => 20.00 Hz
```

and the floor tracks `buffer_size` exactly — 512 bytes → 187.50 Hz, 1024 →
93.75, 2048 → 46.88, 4096 → 23.44. §4's reading of `Echo.c:124-129` is right.

**`audioecho.FeedbackDelay` does tune, to sub-sample resolution.** Impulse,
`feedback = 0`, `mix = 2`; first repeat as an amplitude-weighted centroid:

```
  f =  110.0 Hz  ideal 436.364 frames  taps [(436,12728),(437,7272)]  centroid 436.364
  f =  440.0 Hz  ideal 109.091 frames  taps [(109,18182),(110,1818)]  centroid 109.091
  f =  880.0 Hz  ideal  54.545 frames  taps [(54,9091),(55,10909)]    centroid  54.545
  f = 3520.0 Hz  ideal  13.636 frames  taps [(13,7273),(14,12727)]    centroid  13.636
  f = 1000.0 Hz  ideal  48.000 frames  taps [(48,20000)]              centroid  48.000
  f = 4000.0 Hz  ideal  12.000 frames  taps [(12,20000)]              centroid  12.000
```

T3's warning holds: 1 kHz and 4 kHz land whole, so neither can tell an
interpolator from a rounder. Mono (`channel_count = 1`) and stereo produce the
same taps sample for sample.

**T2's law.** g = 0.8, wet-only, f₀ = 200 Hz: +13.98 dB at every integer
multiple and −5.11 dB at every odd half-multiple, against a closed form of
+13.98 / −5.11.

**Ask 1 — the negative comb composes.** `Splitter(taps=2)` → {dry ,
`FeedbackDelay`(M, fb 0, mix 2) → `Multiply`(× const −32768) } →
`Mixer`(1.0, g) → `FeedbackDelay`(2M, fb g², mix 2). The inverter is exact:
max |y + x| = 0 over 1024 samples. The FIR stage's impulse response is
`+20000 @0, −16000 @240` at f₀ = 200 Hz, g = 0.8. End to end, wet-only:

```
  probe Hz   positive comb   composed negative   ideal negative
    100.0           -5.11              13.98            13.98
    200.0           13.98              -5.10            -5.11
    300.0           -5.11              13.98            13.98
    400.0           13.98              -5.10            -5.11
    500.0           -5.11              13.98            13.98
    600.0           13.98              -5.10            -5.11
    700.0           -5.11              13.98            13.98
```

The peaks move to the odd half-multiples and the heights hold to 0.01 dB.
T4 is reachable; the ask is refuted.

**Ask 2 — the tuning step is audible, and nothing on the palette smooths
it.** 440 Hz sine, `mix = 1`, g = 0.7, `delay_ms` re-set once per 512-frame
block; worst first difference at a step boundary, against the signal's RMS:

```
  100 -> 1000 Hz over 1 s (94 steps)   median |dy| 248   jump 7313    -2.1 dBFS
  440 -> 441  Hz over 1 s (94 steps)   median |dy| 1388  jump 2000   -21.6 dBFS
  no knob move at all (the control)    median |dy| 1385  jump 1996   -21.6 dBFS
```

The control is the point: a 440 → 441 Hz sweep is indistinguishable from not
moving the knob, so the estimator is not simply reporting every boundary as a
click. Sized per step on a 480-frame line, excess over the local slew:

```
  step frames   0.000   0.001   0.010   0.100   0.500   1.000   2.000   5.000  12.000
  excess dBFS   -44.4   -44.4   -46.0   -49.5   -27.8   -21.1   -14.8    -6.6    +0.4
```

−44 dBFS is the estimator's floor (the zero-step control reads it), so
anything at or below that is "no step seen". The palette is silent only for
sub-frame steps; the twelve-frame step T6's sweep needs reads 0 dBFS. Ask 2
stands.

**One thing the run needed that the kit spec must carry.** A bare `RawSample`
hands its whole array over in one `get_buffer` call. Fed straight into a
`Splitter`, a 40 000-frame probe loses everything but the last 8192 frames
(`audioif_splitter.c:35-38`) and an impulse at frame 0 vanishes — measured
here while building the Ask 1 composition, and independently in `DynamicEQ`
A2. Every probe in this appendix is pumped through a one-voice `Mixer` for
that reason.

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

The delay-line invariants are the ones with teeth here. `reset()` must empty
the line — the planted fault the vision names ("a delay line left full") is
this class's — and `audioecho.FeedbackDelay` does **not** reset its source
recursively (roadmap §3), so the rebuild's node list must include the line
explicitly. The residual measurement (A3) shows `CombFilter` at its shipped
defaults reaching exact zero, so audioif#23 does not touch this class.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S2b** same book, "Feedforward Comb Filters" | `y(n) = b₀x(n) + b_M x(n−M)` — the zero-feedback case this class's Mix at unity produces | same | https://ccrma.stanford.edu/~jos/pasp/Feedforward_Comb_Filters.html | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* — "Decay Time is Q Periods" | *"After Q periods, the amplitude envelope has decayed to e^(−π) ≈ 0.043"*, verbatim (the page states it for `Q >> 1/2`) — reached, but **nothing in §3 rests on it**: this class's tail is `ceil(−6.91/ln g · F_s/f)`, derived from the feedback coefficient, not from Q periods | same | https://ccrma.stanford.edu/~jos/filters/Decay_Time_Q_Periods.html | 2026-09-06 |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **Peaks on the harmonic series of the tuned frequency**: with the line at `1/f` seconds the resonances sit at f, 2f, 3f …, spaced exactly f, for every f in 20 Hz…4 kHz | S2 (`ω_k = 2π k/M`) | high | any peak or spacing more than 1 % off, anywhere in 20 Hz…4 kHz | swept sine, peak picking, f ∈ {55, 110, 220, 440, 880, 1760, 3520} Hz |
| T2 | **The feedback knob is the peak height, to the textbook law**: wet-only gain is `1/(1−g)` at the peaks and `1/(1+g)` at the nulls, within 0.2 dB — g 0.8 gives +13.98 and −5.11 dB | S2's `G(ω)` evaluated at `ωM = 0, π` (derived, not stated on the page); measured to 0.00 dB (A2) | high | either extreme more than 0.2 dB from the closed form, for g ∈ {0.3, 0.5, 0.8, 0.95} | steady-state sine at f and at 1.5 f, wet-only, for four g values |
| T3 | **Fractional tuning**: the comb tunes continuously, not to the nearest whole sample — every request in 20 Hz…4 kHz lands within 5 cents. The test only has teeth where the whole-sample grid is coarser than 5 cents, which at 48 kHz means **above about 300 Hz**: rounding 48 000/f to the nearest integer costs only +1.44 cents at 110 Hz — too small to tell an interpolator from a rounder — but −14.37 cents at 880 Hz, +17.40 at 1760 Hz and **−45.56 at 3520 Hz**, T1's top probe. 4 kHz is the one frequency in that decade that must *not* be the test: 48 000/4 000 = 12.000 samples exactly, so a rounding implementation lands on it too | `audioif_feedback_delay.c:226-229` (per-sample linear interpolation); measured — the impulse splits across samples 436/437 at 110 Hz and 109/110 at 440 Hz, and lands whole at 1 kHz and 4 kHz (A2); the cents figures re-derived in A11 | high | a first peak more than 5 cents from the request at any of {880, 1760, 3520} Hz, or more than 5 cents anywhere else in 20 Hz…4 kHz | impulse, first-repeat centroid to sub-sample resolution, at f ∈ {880, 1760, 3520} Hz first because those are the discriminating ones; then T1's full probe set |
| T4 | **Negative feedback puts the peaks on the odd half-multiples** — f/2, 3f/2, 5f/2 … — which is the hollow, square-ish comb, as distinct from the pitched positive one | S2, verbatim: *"while for g<0, the peaks occur midway between these values"* | high | a requested g < 0 whose peaks stay on the integer multiples | the T1 sweep at g = −0.8, peaks compared against `(k+½)·f` |
| T5 | **Zero feedback is the feedforward comb**: at g = 0, Mix 1, the nulls are total at odd multiples of f/2 and the peaks exactly +6.02 dB at multiples of f | S2b; measured bit-exact zero at 500/1500 Hz and +6.02 dB at 1000/2000 Hz on a 1 ms line (A2) | high | a null above −60 dB or a peak outside +6.02 ± 0.1 dB | steady-state sine at f/2, f, 3f/2, 2f, g = 0, Mix 1 |
| T6 | **The tuning knob is click-free**: a 100 Hz → 1 kHz sweep over one second produces no discontinuity above −60 dBFS relative to the running signal, and no single knob step anywhere in 20 Hz…4 kHz produces one | no external source — a knob that clicks is not a knob — but the risk is *located*, not assumed: `audioif_feedback_delay.c:82` writes the requested delay straight into `config->delay_frames` and `:212` reads it unsmoothed into the tap offset, so every step is a hard jump in the read position with nothing between the old and new tap | medium — the palette steps the delay once per block (§5), and §5's slew ask is what would remove the step; until it lands the trait may be disconfirmed, which is a legitimate Phase 0 result | any discontinuity above −60 dBFS during the sweep, or on any single step of the size the Tune macro's smallest increment produces | first-difference of the output over a one-second log sweep, peak against the signal's RMS; and the same on a single 440 → 441 Hz step, which is the worst case per unit of pitch change |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Standout confirmed.** Two candidates were weighed and dropped: a **flanger
with its LFO stopped**, which is literally this circuit but whose
distinguishing traits (BBD companding, bandwidth, inverted feedback) belong
to `Flanger`, which the vision already gives the Electric Mistress; and a
**Schroeder reverberator's comb bank**, whose traits are a reverb's (echo
density, RT60) and belong to `Reverb`. This class is the naked building
block and its traits are the textbook's.

*(from §2)*

**Independent licence and citation audit, 2026-09-06** (a second agent, none
of the first run's notes read; full record in Appendix A9). Three corrections
are applied above. The negative-feedback sentence was quoted as *"peaks shift
to midway positions between these values"*; the page's actual words are *"while
for g<0, the peaks occur midway between these values"* — the substance was
right, the quotation marks were not, and §1, the S2 row and T4 now carry the
real quote. The **extremes `1/(1−g)` and `1/(1+g)` are not stated on the
page**: they follow from S2's `G(ω)` at `ωM = 0` and `π`, and are marked
derived in §1, in the S2 row and in T2's source; the `2π/M` spacing likewise.
The dropped candidates' attributes (the Electric Mistress's companding and
inverted feedback; a Schroeder bank's RT60) are **unsourced** general
knowledge; nothing in §3 rests on them.

*(from §2)*

**Second licence-and-citation audit, 2026-09-06** (a third pass, independent
of the first audit; **every URL in this seed re-fetched in this run**). All
four S2/S2b/S3 quotes are verbatim on the pages named, the CCRMA rights lines
are unchanged, and `…/filters/Comb_Filters.html` is still **HTTP 404**, so it
stays recorded as not reached. **One correction, applied above:** S3's "what
it gave" cell overstated its use — no trait in §3 cites S3, and this class's
tail comes from the feedback coefficient, not from Q periods. Full record in
`A10`.

*(from §3)*

**Trait-critic pass, 2026-09-06.** T3 and T6 rewritten in place. T3 carried a
mis-attributed number: the 45 cents is the whole-sample rounding error at
**3520 Hz**, T1's top probe, not at 4 kHz, where 48 000/4 000 is exactly 12
samples and rounding costs nothing — stated at 4 kHz the row named the one
frequency in its own range at which the test cannot fail. It now names where
the 5-cent tolerance discriminates (880, 1760, 3520 Hz) and where it cannot
(110 Hz, 1.44 cents). T6 still has no external source — none exists for "a knob
should not click" — but now cites the two palette lines that make the click
likely (`audioif_feedback_delay.c:82`, `:212`), so the claim is anchored to a
mechanism. T1, T2, T4, T5 unchanged. Grid arithmetic in A11. **Six Tier 2 rows
after the pass.**

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: **ESP32-P4
≤ 2 %, ESP32-S3 ≤ 7 %**. Lean patch expected: **no** — the loop is one
interpolated read, one multiply-add and one write per sample per channel, and
the optional in-loop filters are one pole each. Desktop anchor (A7): 141.7 ns
per stereo frame against 20 833 ns of real time, 0.68 %, essentially one
biquad. RAM is the line: 50 ms stereo is 9.6 KB at 48 kHz, allocated once.

*(from §3)*

**Latency: zero on the dry path; the comb delay is the effect, not latency.**
`audioif_feedback_delay.c:260-261` writes `dry·source + wet·loop` in the same
frame the input arrives — measured, impulse at frame 50 in, frame 50 out, at
its full 20 000 peak (A8). `latency_samples` is **0** and no option adds any:
the tuned delay (0.25–50 ms) is on the wet path and is the thing the user
asked for, which vision §9a distinguishes from latency. `tail_samples`
follows the feedback, `ceil(−6.91/ln(g) · F_s/f)` for −60 dB — about 60 000
samples at g 0.95 and 110 Hz — reported and recomputed on every knob move.

*(from §4)*

`audioecho.FeedbackDelay` — audioif's own (`upstream-diff.md:770`) — is the
composition that works: it reads the line per sample with linear
interpolation between two neighbours (`audioif_feedback_delay.c:226-228`),
clamps only at 1 frame and `line_frames − 2` (`:82-83`), and sums
`dry·source + wet·loop` per sample (`:260-261`). Measured against S2's closed
form it reproduces the peak and null gains to 0.00 dB and the fractional
tuning to sub-sample resolution (A2), re-measured independently 2026-09-07
(A12): +13.98 / −5.11 dB at g = 0.8 against the closed form's +13.98 / −5.11,
and an impulse whose first-repeat centroid lands on 436.364, 109.091, 54.545
and 13.636 frames for 110, 440, 880 and 3520 Hz — the exact `F_s/f`. So: one
`FeedbackDelay`, `max_delay_ms = 50` (a 20 Hz floor), `delay_ms = 1000/f`,
feedback and mix from macros, the in-loop filters off by default and reachable
only through the Tone macro (§6). Python computes one division per frequency
move and nothing per block. **Mono:** at `channel_count = 1` the node runs one
lane (`:62-71`, `:223-224`) and the cross-feed term is forced to zero
(`:248`), so a mono source gets the identical comb — measured, the mono and
stereo impulse responses are the same sample for sample (A12). The one caveat
is that a non-zero `cross_feed` in mono does not cross anything, it only
scales the feedback by `1 − cross_feed` (`:203-204`, `:249`); this class
leaves it at its default 0.

*(from §4)*

**Portability tier: audioif.** On a stock CircuitPython board the class
imports cleanly and raises a clear `ImportError` at construction, in the
shape `CabinetSim` uses (`drive.py:30-33`, `:331-334`), leaving the other
`eq.py` classes importable. There is no honest stock fallback: `Echo`'s floor
tracks `buffer_size` exactly (A2, A12), so the smallest buffer the library
uses today — 1024 bytes, at `eq.py:250` — floors the comb at **93.75 Hz**, and
even a 512-byte buffer only reaches 187.5 Hz, still short of most of the
20 Hz…4 kHz span. Offering it would ship a class that silently ignores its
main control.

*(from §5)*

The node's own clamp is real: feedback is clamped to `0.0 … 0.99`
(`audioif_feedback_delay.c:90`), and asked for g = −0.8 on a 1 ms line the
node gives a single repeat and no recirculation — `[20000 @48]` wet-only,
against `[20000 @48, 16000 @96, 12800 @144, 10240 @192, 8192 @240 …]` at
g = +0.8 (A2, reproduced A12). But the trait does not need that clamp
widened. `1/(1 + g·z^(−M)) = (1 − g·z^(−M)) · 1/(1 − g²·z^(−2M))`, and both
factors are on the palette:

*(from §5)*

- `1 − g·z^(−M)` — `audioroute.Splitter(taps=2)`, one tap dry, the other
  through a `FeedbackDelay` at M with `feedback = 0`, `mix = 2` (a pure delay),
  through `audiomath.Multiply` against a constant `−32768` modulator, summed by
  an `audiomixer.Mixer` with the inverted voice at level g. The `Multiply`
  inversion is **exact**: max |y + x| over 1024 samples is 0, because
  `(x · −32768) >> 15` is `−x` (`audioif_multiply.c:38`). The stage's impulse
  response is `+20000 @0, −16000 @240` for f = 200 Hz, g = 0.8 — the textbook
  FIR comb.

*(from §5)*

Measured end to end at f₀ = 200 Hz, g = 0.8, wet-only, against the closed form
`1/|1 + g·e^(−jωM)|`: **+13.98 dB at 100, 300, 500 and 700 Hz** and −5.10 dB
at 200, 400 and 600 Hz, against an ideal +13.98 / −5.11 — the peaks are on the
odd half-multiples, which is exactly what T4 asserts, and the heights are
within 0.01 dB. A5's earlier refutation record reasoned from the wrong
identity (it wrote `1/(1+g z^−M)` as a *difference* of two positive combs, and
worried about a cancellation that would drift); the correct factorisation is a
product, and nothing cancels.

*(from §5)*

What it costs, so Gate 0 can weigh reinstating the ask on cost rather than
reachability: five nodes instead of one, two delay lines, the `Splitter`'s
fixed 32 KB ring (`audioif_splitter.h:20`) and a constant modulator sample;
int16 requantisation at every stage; and the wet path arrives 2M samples late,
so wet-only (Mix 1) is exact while a dry/wet blend needs the true dry off a
third `Splitter` tap. Vision §6 still names inverted feedback on this node for
`Flanger` — that is `Flanger`'s ask to make, on `Flanger`'s trait, and this
class no longer seconds it.

*(from §5)*

**Ask 2 — a delay-time slew on `audioecho.FeedbackDelay`. Unblocks T6.**
**STANDS**, and now with the measurement it was owed (A12).
`delay_ms` is a config value set from Python (`audioif_feedback_delay.c:82-83`)
and read unsmoothed by the process loop (`:212`), so a swept tuning knob
steps once per block — at 48 kHz and 512-frame blocks a 100 Hz → 1 kHz sweep
in one second steps the line ~94 times, each a discontinuity in the read
pointer. Measured on a 440 Hz sine (A12): that sweep's worst step reads
**−2.1 dBFS** against the running signal's RMS, and sized per step on a
480-frame line the excess runs −27.8 dBFS at half a frame, −21.1 at one, −6.6
at five and 0.0 at the twelve the sweep needs — against a zero-step control
that reads −44 dBFS, the estimator's floor. So the palette *can* move the
knob silently, but only in sub-frame steps, far slower than T6's sweep.
*What the palette does instead:*
nothing else moves the tap per sample except `wow_hz`/`wow_depth_ms`, which is
a fixed-frequency sine (`:111-118`, `:209-213`) and cannot ramp to a target.
The ask is a per-sample slew toward the target with a time constant the class
sets — the same option vision §6 names (*"the click-free knob every delay
class needs"*), wanted here for tuning rather than tape pitch-bend.
*Refutation record:* A5, extended in A12.

*(from §5)*

T4 is no longer conditional: it is reachable today, at the cost §5 states, and
§3's "T4 is unreachable on today's palette" is superseded by this section. If
Gate 0 declines Ask 2, **T6 becomes a stated stepping figure in dBFS** and the
docstring says so — the numbers above are that figure.

*(from §7)*

- **The class does not tune. At all.** `delay_ms = 1000.0/float(frequency)`
  (`eq.py:205`) goes to `audiodelays.Echo(max_delay_ms=50, ...)`
  (`eq.py:206-208`) with the library's default 2048-byte buffer
  (`_core.py:64`), and `Echo.c:126-128` raises any line shorter than that
  buffer to the buffer's own length. Measured (A2): 110, 220, 440, 880 **and**
  47 Hz all produce the *same* comb, first repeat at 1024 samples —
  **46.88 Hz**. Only below ~47 Hz does the frequency argument do anything.
  This is the defect the rebuild exists to fix.

*(from §7)*

- **No guard on `feedback`.** `eq.py:204` passes it straight to `decay`; the
  kernel multiplies and saturates (`audioif_echo.c:31-33`) rather than
  refusing, so `feedback=1.0` is a non-decaying ring the docstring does not
  mention. S2's stability condition is `|g| < 1`.

*(from §7)*

- **`reset()` and `deinit()` reach one node each** (`_core.py:366-374`,
  `:376-385`), which for a single-node class happens to be enough today; the
  rebuild must not rely on the accident.
