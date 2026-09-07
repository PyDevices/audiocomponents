# Effects Dossier — `CombFilter` (no historical standout — design grade)

**Class:** `lib/audioeffects/eq.py` — the current implementation is read once,
for §7, and not otherwise consulted.
**Family / phase:** EQ / Filter, roadmap Phase 2
**Standout:** none, per vision §4.2 — **confirmed** (§2).
**Grade:** design
**Portability tier:** **audioif** — `REQUIRES = ("audioecho", "audiobiquad")`;
see §4 for why the stock `audiodelays.Echo` route cannot carry the class.
**Status:** **traits frozen at Station A, 2026-09-07**, branch
`effects/p2-combfilter` — §3's Tier 2 table is the frozen set, §6 the frozen
surface, §8's three questions all settled from runs (A13). The seed's own
text is kept everywhere; what moved out of §§1–8 is in the appendices.

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

| Source | Lead | License as read | URL | Reached |
|---|---|---|---|---|
| **S2** J. O. Smith III, *Physical Audio Signal Processing* — "Feedback Comb Filters" and "…Amplitude Response" | `y(n) = x(n) + g·y(n−M)`, `H(z) = 1/(1−g z^(−M))`, `G(ω)`, the peaks at `ω_k = 2πk/M`, the stability condition and the `g<0` sentence — all verbatim; the extremes `1/(1−g)` and `1/(1+g)` and the `2π/M` spacing are **derived**, not on the page | © J. O. Smith III / CCRMA; W3K, ISBN 978-0-9745607-2-4. No licence granted. Read as a paper | https://ccrma.stanford.edu/~jos/pasp/Feedback_Comb_Filters.html , …/Feedback_Comb_Filter_Amplitude.html | 2026-09-06 |
| **S2b** same book, "Feedforward Comb Filters" | `y(n) = b₀x(n) + b_M x(n−M)` | same | https://ccrma.stanford.edu/~jos/pasp/Feedforward_Comb_Filters.html | 2026-09-06 |
| **S3** *Introduction to Digital Filters*, "Decay Time is Q Periods" | reached and verbatim, but **nothing in §3 rests on it** | same | https://ccrma.stanford.edu/~jos/filters/Decay_Time_Q_Periods.html | 2026-09-06 |

*(the full reading of each row is in **App. S**)*

**Looked for, not found:** `ccrma.stanford.edu/~jos/filters/Comb_Filters.html`
404s (the PASP pages above are the reachable ones); no DAFx or AES paper was
hunted, because the feedback comb is a two-line result and a paper would add
nothing a textbook page does not already state exactly.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

**Frozen at Station A, 2026-09-07**, branch `effects/p2-combfilter`, before a
line of the rebuilt class was written. Two rows carry a criterion *restated*
from the seed's; both restatements come from runs (A13) and both originals
stand verbatim in **App. T**, which also holds every row's source and
confidence prose in full.

| # | Trait (falsifiable as stated) | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|
| T1 | **Peaks on the harmonic series of the tuned frequency**: with the line at `1/f` seconds the resonances sit at f, 2f, 3f …, spaced exactly f, for every f in 20 Hz…4 kHz | high | any peak or spacing more than 1 % off, anywhere in 20 Hz…4 kHz | RESPONSE, stepped tones at f/2, f, 3f/2, 2f, 5f/2, 3f for f ∈ {55, 110, 220, 440, 880, 1760, 3520} Hz |
| T2 | **The feedback knob is the peak height, to the textbook law**: wet-only gain is `1/(1−g)` at the peaks and `1/(1+g)` at the nulls — g 0.8 gives +13.98 and −5.11 dB. **Restated at Station A:** within 0.2 dB **at and below 2 kHz**; above that the fractional tap is a one-zero low-pass inside the loop and the peak follows a measured curve (App. T, A13) | high | either extreme more than 0.2 dB from the closed form below 2 kHz, at g ∈ {0.3, 0.5, 0.8, 0.95}; or a reading above 2 kHz more than 0.2 dB off that curve | RESPONSE, steady-state sine at f and 1.5 f, wet-only, four g values |
| T3 | **Fractional tuning**: every request in 20 Hz…4 kHz lands within 5 cents. The row has teeth only where the whole-sample grid is coarser than 5 cents — at 48 kHz, above about 300 Hz; the discriminating probes are **880, 1760 and 3520 Hz** (A11), and **4 kHz must not be the test**, being 12.000 samples exactly | high | a first-repeat centroid more than 5 cents from the request at any of {880, 1760, 3520} Hz, or more than 5 cents anywhere else in the span | TAPS: impulse, first-repeat centroid to sub-sample resolution |
| T4 | **Negative feedback puts the peaks on the odd half-multiples** — f/2, 3f/2, 5f/2 … — the hollow, square-ish comb, as distinct from the pitched positive one | high | a requested g < 0 whose peaks stay on the integer multiples | **Not built** (§4): reachable, re-measured in A13, and seven nodes against a budget written for one. The evidence pack records it `unmeasured` with that reason |
| T5 | **Zero feedback is the feedforward comb**: at g = 0, Mix 1, the nulls are total at odd multiples of f/2 and the peaks exactly +6.02 dB at multiples of f | high | a null above −60 dB or a peak outside +6.02 ± 0.1 dB | RESPONSE, steady-state sine at f/2, f, 3f/2, 2f, g = 0, Mix 1 |
| T6 | **The tuning knob is click-free**: a 100 Hz → 1 kHz sweep over one second, the knob re-set once per block, produces no discontinuity at a block boundary that the running signal's own curvature does not already produce. **Restated at Station A:** the seed's −60 dBFS bar sits *below* the estimator's own floor (A12 measured that floor at −44 dBFS), so no build could ever meet it; the bar is now the same render's off-boundary floor, which is what A12's control was for | high (was medium: Ask 2 was granted and landed — §5) | a boundary step more than 1 dB above the same render's 99.9th-percentile off-boundary second difference | second difference at the block boundaries against the 99.9th percentile off them, on a 100 Hz → 1 kHz sweep and on a 440 → 441 Hz step |

No characters: a comb has one behaviour.

**Two of the seed's own verdicts are superseded** — T4 is reachable but unbuilt, T6 is reachable and built; the record of both is in **App. R**.

### Tier 3 — cost and latency

**Latency: 0 samples, at every setting and every rate.** The node writes
`dry·source + wet_gain·loop` in the frame the input arrives
(`audioif_feedback_delay.c:496`); the impulse comes out where it went in, at
full amplitude (A8). No option adds any. The tuned delay is on the wet path
and is the thing the user asked for — vision §9a's distinction. At Mix 2
there is no dry path and the first sound arrives one line-length late; still
the comb, not latency, and the docstring says so in milliseconds.

**Tail: not finitely bounded — `TAIL_SAMPLES = None`.** Below Feedback 0.5
the line always reaches exact zero. Above it, whether it does **depends on
the tuning, not on the feedback alone**: `to_s16` rounds, so every
|c| ≤ 0.5/(1−g) is a fixed point of the loop, and whether the loop can sit on
one depends on the fractional part of `F_s/f`. Measured (A13 §3): a comb at
**1000 Hz (48 000/f = 48.000 frames, no fraction) parks on 10 LSB at
Feedback 0.95** — the closed-form bound, exactly — and 440 Hz (frac 0.09) on
8, 220 Hz (0.18) on 6; while **438.3 Hz (frac 0.51) reaches exact zero at
every feedback the class offers**, because a half-sample tap averages a lone
LSB with its neighbour and rounds it away. The declared figure is therefore
the bound, not a typical value, and both ends are measured. `reset()` clears
it either way.

**Cost budget: ESP32-P4 ≤ 2 %, ESP32-S3 ≤ 7 %** of one stereo block's real-time deadline — the seed's figures, set for a one-node build; the rebuild is two nodes. Desktop anchor re-taken at Station A, net of the source pump: **98.8 ns/frame = 0.47 %** of the 20 833 ns a stereo frame has at 48 kHz (A13). Lean patch expected: **no**. RAM is the line: 60 ms stereo is 11.5 KB at 48 kHz, allocated once.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Compose first — but the node the class uses today cannot do the job, and the node beside it can.** `audiodelays.Echo` quantises its line to whole samples and floors it at its own buffer length, so every `CombFilter` frequency from 47 to 880 Hz measures as the *same* 46.88 Hz comb (A2, A12); the floor tracks `buffer_size` exactly. That is not a tuning error, it is the absence of tuning — the file citations are in §7 and App. R. `audioecho.FeedbackDelay` reads its line with per-sample linear interpolation (`audioif_feedback_delay.c:327-343`) and reproduces S2's closed form to 0.00 dB and its tuning to 0.002 cents (A13).

**What the rebuild builds: two nodes.** One
`audioecho.FeedbackDelay` — `max_delay_ms = 60`, `delay_ms = 1000/f`,
`feedback`, `mix` and the in-loop `damping_hz` from macros, `delay_slew` from
the Glide macro — and one `audiobiquad.Biquad` HIGH_SHELF at 5 Hz behind it,
which is the only way a make-up trim above unity exists on this palette
(`MixerVoice.level` clamps to 0..1 and `audiomath.Multiply` only attenuates);
`LowPass` measured that shelf flat to 0.010 dB from 50 Hz to 15 kHz. Nothing
else. Python computes one division per Frequency move and nothing per block.

**Why the negative-feedback composition is not one of them.** §5's identity
holds and A13 reproduced it exactly. But it cannot *be* the class at anything
under **seven nodes, three delay lines and the Splitter's 32 KB ring**: its
IIR factor is only exact at the node's wet-only `mix = 2`, so the comb
arrives 2M late — 0.5 ms at 4 kHz, 100 ms at 20 Hz — and a Mix knob that sums
that against an undelayed dry is a flanger, not a comb blend. That is roughly
4× this class's own Tier 3 budget, to move the peaks onto the half-multiples.
T4 stays frozen in §3 and unbuilt; the docstring and the README row say so.
Count and algebra: App. R.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

Two were written. **Neither is outstanding**: the palette verification of
2026-09-07 (A12) refuted the first, and the second was **granted and shipped**
in the Phase 1 palette work, on this pin.

**Ask 1 — signed feedback on `audioecho.FeedbackDelay`. Unblocks T4.**
**REFUTED BY PALETTE: the odd-half-multiple comb composes exactly out of
nodes that already exist, and it was measured on 2026-09-07 (A12), and again
at Station A (A13).**

`1/(1 + g·z^(−M)) = (1 − g·z^(−M)) · 1/(1 − g²·z^(−2M))`, and both factors are on the palette — a `Splitter`, a pure `FeedbackDelay`, an exact `audiomath.Multiply` inversion and a `Mixer` for the first, a second `FeedbackDelay` at 2M with feedback g² for the second (App. R).

Reachable is not the same as built: §4 has the node count and why the class
declines it.

**Ask 2 — a delay-time slew on `audioecho.FeedbackDelay`. Unblocks T6.
GRANTED, LANDED, AND ON THIS PIN — the ask is closed.** `delay_slew` walks
the read head toward a new `delay_ms` instead of jumping to it, in
delay-seconds per second, so it is the same number at every rate
(`audioif_feedback_delay.c:195-203` clamps it to 0..64, `:397-416` walks it
per sample; the binding is
`.venv/lib/python3.12/site-packages/audioecho.py`'s `_OPTIONS["delay_slew"]`,
slot 10). It defaults to 0 — the jump this node always made — so nothing the seed measured moved. A13 measures what it buys (T6, and App. R): at 0 the worst block boundary reads **−10.0 dBFS** against the same render's off-boundary floor of −15.5; at 0.001, 0.01 and 0.05 the boundary reads the floor itself. The class carries it as the **Glide** macro, default 0.05.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Surface — frozen at Station A, 2026-09-07

Six macros, well inside the sixteen. The sixth is Glide, which exists because
Ask 2 was granted (§5); the seed's BIPOLAR Feedback is now UNIPOLAR, because
the negative half is not built (§4) and a knob that runs into a half the
class does not have is a lie on the panel.

| # | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 20 Hz … 4 kHz, log (line 50 ms … 0.25 ms) | the tuning knob |
| 1 | Feedback | UNIPOLAR | 0 … 0.95 (the node clamps at 0.99) | the resonance / regeneration knob |
| 2 | Mix | UNIPOLAR | 0 … 2 — the node's own convention (`audioif_feedback_delay.c:157-165`): 0 is a wire, 1 is dry plus all of the wet, 2 is the filter alone | the blend knob |
| 3 | Tone | UNIPOLAR | 500 Hz … 24 kHz, log; the top of the travel is **off** | the darkening a resonator gets from its own losses — the node's in-loop `damping_hz`, so each pass loses more top than the last |
| 4 | Trim | BIPOLAR | −12 … +12 dB | make-up, because `1/(1−g)` at g 0.95 is +26 dB |
| 5 | Glide | UNIPOLAR | 0 … 1 delay-seconds per second, default 0.05 | how fast the comb walks to a new pitch. 0 is the jump, and it clicks (§5); 1 is the read head standing still, an octave of bend while it travels |

`capabilities = ()`: a comb's delay **is a pitch, not a rhythm** — 1/f
seconds, where f is the note you hear — so syncing it to the transport would
be meaningless, and the class never reads `self._transport()` (D10).

**Two grid notes, both arithmetic, both handled in the class:** Mix **snaps to exactly 1.0 within ±0.02** and Trim is a wire below 0.2 dB, because the 0–127 grid has no exact centre and an off-by-0.0079 Mix turns T5's total null into a −42 dB one; and 20 Hz…4 kHz over 127 steps is 72 cents a step, so the *knob* is coarse where the *tuning* is not (App. R).

Patches: 0 **Metallic** (440 Hz, 0.7, Mix 1, tone off, trim 0, glide 0.05 —
the constructor's defaults on the grid), 1 **Ringing Pitch** (220 Hz, 0.92,
Mix 1, −9 dB), 2 **Soft Ripple** (110 Hz, 0.3, Mix 0.5), 3 **Dark Resonator**
(150 Hz, 0.85, Mix 1, tone 2 kHz, −6 dB), 4 **Single Slap** (55 Hz, 0.0,
Mix 1 — the feedforward comb of T5), 5 **Filter Only** (1 kHz, 0.8, Mix 2 —
the comb with no dry at all, which is where T2's law is read).

The seed's patch 3 **Hollow** (330 Hz, −0.8) is **withdrawn** — it is the
negative comb, and §4 does not build it. **Dark Resonator** takes the slot.

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

## 8. Open questions — all three settled at Station A, 2026-09-07

Each answer is one line here; the run behind it, and the reasoning, are in
**App. Q**, with the numbers themselves in **A13**.

1. **Ask 1 and Ask 2** (§5). **SETTLED.** Ask 1 refuted by the palette
   (A12, reproduced A13); Ask 2 **granted and shipped** — `delay_slew` is on
   this pin, costs nothing when it is 0, and A13 measures what it buys. What
   T4 would cost the S3 is a class question, and §4 answers it.
2. **4 kHz or Nyquist/4 at the top of the Frequency range?** **SETTLED:
   4 kHz stays, and T2's tolerance becomes frequency-dependent.** The tilt
   depends on the *fractional part* of `F_s/f`, not on f: measured 0.00 dB
   at 55/110/440 Hz **and at 1000/2000/3000/4000 Hz**, −0.07 at 880, −0.23
   at 1760, −1.02 at 3520, −2.06 at 5000. A ceiling would cost an octave and
   a half of wanted sound to hide a number that belongs in the docstring.
3. **int16 or float line?** **SETTLED, and the answer is sharper than
   "noise": above Feedback 0.5 the int16 line can stop decaying, and whether
   it does is decided by the tuning.** `to_s16` rounds, so any
   |c| ≤ 0.5/(1−g) is a fixed point. Measured (A13 §3): exact zero at every
   tuning below Feedback 0.5; at 0.95, **10 LSB (−70.3 dBFS) at 1 kHz, where
   48 000/f is a whole 48 frames**, 8 at 440 Hz, 6 at 220 — and **exact zero
   at 438.3 Hz**, where the tap sits half a sample out and the interpolator
   averages the last LSB away. So the fractional part that costs T2 its
   0.2 dB above 2 kHz is the same one that buys the tail its exact zero.
   Both fixes are node changes on a frozen pin, so the class **states** it:
   `TAIL_SAMPLES = None`, the bound in the docstring, and `reset()` clears
   it.

*(Nothing else is open. Each answer above came from a run, not an argument.)*

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

### A13. Station A measurement run, 2026-09-07

Every number §§3–8 gained at Station A, with the run behind it. Interpreter
`audiocomponents/.venv/bin/python` (CPython 3.12, audioif at the pin
`2f6cbc3`), 48 000 Hz, stereo, probes pumped through a one-voice `Mixer` so
nothing downstream is handed more than one block at a time (A12's rule).
Probes were scratch scripts; every number is reproducible from its
description, and the ones the class gate needs are re-taken through the kit
in `CombFilter-evidence.md`.

**1. T3 — the first-repeat centroid, `feedback = 0`, `mix = 2`, impulse in.**
Cents are `1200·log2(F_s/f ÷ centroid)`:

```
  f0=   20.0  ideal 2400.0000  centroid 2400.0000   +0.000 cents
  f0=   55.0  ideal  872.7273  centroid  872.7273   +0.000 cents
  f0=  110.0  ideal  436.3636  centroid  436.3636   +0.000 cents
  f0=  440.0  ideal  109.0909  centroid  109.0909   +0.000 cents
  f0=  880.0  ideal   54.5455  centroid   54.5455   +0.000 cents
  f0= 1760.0  ideal   27.2727  centroid   27.2727   -0.001 cents
  f0= 3520.0  ideal   13.6364  centroid   13.6364   +0.002 cents
  f0= 4000.0  ideal   12.0000  centroid   12.0000   +0.000 cents
```

**2. T2 and §8 Q2 — the peak/null law across the range.** g = 0.8, wet-only
(`mix = 2`), steady-state sine at f₀ and at 1.5 f₀, referenced to the same
tone through the same node at `mix = 0`. Probe amplitude 2000 LSB: at 8000
the peak gain clips the int16 output and every row reads a uniform −0.82 dB,
which is a measurement fault, not a filter — it is recorded here because it
is the first thing a re-runner will hit.

```
  f0        M (frames)   peak         err      null        err
    20.0     2400.000   +13.55 dB    -0.43    -5.15 dB    -0.05
    55.0      872.727   +13.98       -0.00    -5.11       -0.00
   110.0      436.364   +13.98       -0.00    -5.11       -0.00
   440.0      109.091   +13.97       -0.01    -5.11       -0.00
   880.0       54.545   +13.91       -0.07    -5.12       -0.02
  1760.0       27.273   +13.75       -0.23    -5.16       -0.06
  2000.0       24.000   +13.98       -0.00    -5.11       -0.00
  2500.0       19.200   +13.61       -0.37    -5.20       -0.09
  3000.0       16.000   +13.98       -0.00    -5.11       -0.00
  3520.0       13.636   +12.95       -1.02    -5.38       -0.27
  4000.0       12.000   +13.98       -0.00    -5.11       -0.00
  5000.0        9.600   +11.92       -2.06    -5.70       -0.59
  6000.0        8.000   +13.98       -0.00    -5.11       -0.00
```

The pattern is the point: **every whole-sample tuning is exact and every
fractional one tilts**, and the tilt grows with f₀ because the interpolator's
one-zero low-pass steepens toward Nyquist. The 20 Hz row is not the
interpolator — its line is 2400 of the 2880 frames a 60 ms line has, and the
render is not long enough for a 0.95-per-pass loop to settle; it is quoted as
measured.

**3. Tier 1's tail — the loop's fixed point.** A 0.1 s 440 Hz burst at 20 000
LSB into silence; `mix = 2`; the largest |y| in the last half-second of a 6 s
render (30 s at g 0.95), worst over f₀ ∈ {20, 110, 440, 1000, 3520} Hz:

```
  feedback 0.30  residue   0 LSB   bound floor(0.5/(1-g)) = 0
  feedback 0.45  residue   0 LSB   bound 0
  feedback 0.49  residue   0 LSB   bound 0
  feedback 0.50  residue   1 LSB   bound 1
  feedback 0.60  residue   1 LSB   bound 1
  feedback 0.70  residue   1 LSB   bound 1
  feedback 0.80  residue   2 LSB   bound 2
  feedback 0.90  residue   5 LSB   bound 5
  feedback 0.95  residue  10 LSB   bound 10      (30 s render)
```

and at g 0.95, per frequency over 30 s — the last non-zero frame is the last
frame of every render, i.e. it never stops:

```
  f0=   20.0  residue 10 LSB    f0=  440.0  residue  8 LSB
  f0=   55.0  residue  4 LSB    f0= 1000.0  residue 10 LSB
  f0=  110.0  residue  3 LSB    f0= 3520.0  residue 10 LSB
                                f0= 4000.0  residue 10 LSB
```

**Re-measured at Station C, through the class, and the first reading was too
broad.** Whether the loop parks is decided by the *fractional part of
`F_s/f`*, not by the feedback alone. Ten-second renders, a 0.2 s burst, the
largest |y| in the last second, and the last non-zero frame (480 000 means
"still running at the end"):

```
  tuned    burst    g      residue   last non-zero frame
   440.0    440.0  0.70      1 LSB   479999      frac 0.09
   440.0   1000.0  0.70      1 LSB   479999
   440.0    440.0  0.95      8 LSB   479999
   440.0   1000.0  0.95      8 LSB   479999
   438.3   1000.0  0.70      0 LSB    17881      frac 0.51
   438.3    438.3  0.70      0 LSB    19904
   438.3   1000.0  0.95      0 LSB    29380
   438.3    438.3  0.95      0 LSB    34360
   220.0    220.0  0.95      6 LSB   479999      frac 0.18
   110.0    110.0  0.70      0 LSB   114465      frac 0.36
   110.0    110.0  0.95      3 LSB   479999
  1000.0   1000.0  0.70      1 LSB   479999      frac 0.00
  1000.0   1000.0  0.95     10 LSB   479999
  3520.0   3520.0  0.70      0 LSB    12078      frac 0.64
  3520.0   3520.0  0.95      3 LSB   479999
```

The burst's frequency does not matter; the *tuning's* does. Where the tap
sits near a whole sample the read is nearly exact and a lone LSB survives its
own round trip; where it sits near half a sample the interpolator averages it
with a zero neighbour and it rounds away. `floor(0.5/(1−g))` is hit exactly
at 1 kHz — 48 000/1000 is 48.000 frames — and is an upper bound everywhere
else.

The residue is a square-ish oscillation at the tuned pitch, not DC: at
110 Hz, g 0.95, the last forty samples run `-3 × 29, -2, -1, 0, 1, 2, 3 × 6`.
`cut_hz` does not remove it — it is a DC blocker and this is not DC. Measured
with `cut_hz` at 5, 10 and 20 Hz the residue stayed (−5 LSB at 10 Hz), and at
f₀ = 20 Hz `cut_hz = 10` made it **worse**: ±80 LSB, growing. Nothing else on
the palette touches it. Cause: `to_s16` rounds
(`audioif_feedback_delay.c:308-316`), so `to_s16(g·c) = c` for every
|c| ≤ 0.5/(1−g).

**4. T6 and Ask 2 — `delay_slew`.** A 440 Hz sine at 8000 LSB through the
comb at `feedback = 0.7`, `mix = 1`; `delay_ms` re-set once per 512-frame
block along a 100 Hz → 1 kHz log sweep over one second (94 steps). The
estimator is the **second difference** `|y[n] − 2y[n−1] + y[n−2]|`, which a
smooth waveform holds to `amplitude·ω²` and a step in the read pointer does
not; the discriminator is the worst value *at* a block boundary against the
99.9th percentile *off* the boundaries in the same render:

```
  delay_slew   worst boundary        off-boundary floor
      0.000    -10.0 dBFS            -15.5 dBFS      <- a step, +5.5 dB
      0.001    -44.4                 -44.2
      0.010    -39.4                 -39.3
      0.050    -38.4                 -37.9
      0.100    -36.9                 -37.3
      0.250    -30.7                 -35.1
      0.500    -24.3                 -30.6
      1.000    -18.1                 -24.6
```

The control — the same estimator with the knob never moved — reads −31.8 at
the boundaries against a −31.0 floor, and a 440 → 441 Hz step reads −31.7
against −30.9 at every slew, which is why that step was never the
discriminating case. Above 0.25 the boundary rises again: the *target* still
jumps once a block, so a fast slew arrives and stops within the block and the
arrival itself is a corner. 0.05 is the default for that reason.

**5. Ask 1 — the negative comb, reproduced.** `Splitter(taps=2)` → {dry,
`FeedbackDelay`(M, fb 0, mix 2) → `Multiply` × a constant −32768} →
`Mixer`(1.0, g) → `FeedbackDelay`(2M, fb g², mix 2), at f₀ = 200 Hz
(M = 240), g = 0.8, impulse in:

```
  positive comb, one node, mix 2:  (240, 20000) (480, 16000) (720, 12800)
                                   (960, 10240) (1200, 8192) (1440, 6554)
  composed negative comb:          (480, 20000) (720, -16000) (960, 12800)
                                   (1200, -10240) (1440, 8192) (1680, -6554)
                                   (1920, 5243) (2160, -4195)
```

The sign alternates, which is the odd-half-multiple comb — and **the first
arrival is at 2M, not M**. That is the measurement §4 declines the
composition on: the whole wet path is a further M late, and M is the tuning
knob.

**6. Desktop cost anchor.** Four seconds of 48 kHz stereo pulled block by
block, best of three, on the same source pump so the pump's own cost
subtracts out:

```
  source alone                    1316.4 ns/frame
  + FeedbackDelay                 1361.1 ns/frame   (+44.7)
  + FeedbackDelay + trim biquad   1415.2 ns/frame   (+98.8 over the source)
  real time per stereo frame at 48 kHz = 20833.3 ns  ->  0.47 %
```

A7's 141.7 ns for one `FeedbackDelay` was taken over 256-frame blocks and is
not comparable frame for frame; both are quoted rather than reconciled.

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

### App. G — the two grid notes, in full

**Two grid notes, both from arithmetic, both handled in the class.** The
0–127 grid has no exact centre, so `macro_of(2.0-span, 1.0)` is 64 and 64/127
is 1.0079, not 1.0 — and at Mix 1.0079 the dry leg is 0.9921 rather than
unity, which turns T5's total null into a −42 dB one. Mix therefore **snaps
to exactly 1.0 within ±0.02**, and Trim to a wire below 0.2 dB, the floor
`LowPass` uses for the same reason. And 20 Hz…4 kHz over 127 steps is 72
cents a step: the *knob* is coarse, the *tuning* is not — `set_macro` takes
floats and the constructor's `frequency=` is seeded unquantized, which is
what T3 measures.

### App. Q — the three Station A settlements, in full

Moved here under the length rule; §8 keeps the answer and the verdict, which are what the gate reads.

1. **Ask 1 and Ask 2** (§5) — do they survive Gate 0's refutation, and what
   do they cost on the S3? **SETTLED.** Ask 1 was refuted by the palette
   (A12, reproduced A13): the odd-half-multiple comb composes exactly, so no
   node change is needed for it. Ask 2 was **granted and shipped**:
   `delay_slew` is on this pin, off by default, and A13 measures what it buys
   (§5). Neither ask is outstanding, and neither costs the S3 anything —
   `delay_slew` is one compare and one add per frame on a path the node
   already walks, branched around entirely when it is 0
   (`audioif_feedback_delay.c:402`). What T4 *would* cost the S3 is a class
   question, not a node one, and §4 answers it: seven nodes against a budget
   written for one.
2. **Whether the top of the Frequency range should be 4 kHz or Nyquist/4.**
   **SETTLED: 4 kHz stays, and T2's tolerance becomes frequency-dependent
   instead.** Measured at Station A (A13), g = 0.8, wet-only, peak against
   the closed form's +13.98 dB: **0.00 dB at 55, 110, 440 Hz; −0.07 at 880;
   −0.23 at 1760; −1.02 at 3520; −2.06 at 5000** — and **exactly 0.00 at
   1000, 2000, 3000, 4000 and 6000 Hz**, every one of which divides 48 000
   into a whole number of samples. So the tilt is not a ceiling, it is the
   fractional tap's own one-zero low-pass inside the loop, and it depends on
   the *fractional part* of `F_s/f`, not on f alone. Clipping the range at
   1.6 kHz — where the worst case (a half-sample tap) first exceeds 0.2 dB —
   would cost the class an octave and a half of real, wanted sound to hide a
   number that belongs in the docstring. The range stays 20 Hz…4 kHz, T2
   carries the curve, and the class states it.
3. **Whether the line should be int16 or float.** **SETTLED, and it is worse
   than "noise": the int16 line does not decay to zero at all above Feedback
   0.5.** `to_s16` rounds (`audioif_feedback_delay.c:308-316`), so any
   |c| ≤ 0.5/(1−g) is a fixed point of `line ← to_s16(g·line)` and the loop
   parks there. Measured (A13), worst over 20 Hz…4 kHz, still present 30 s
   after a 0.1 s burst: **0 LSB below g 0.5, 1 at 0.5–0.7, 2 at 0.8, 5 at
   0.9, 10 LSB (−70.3 dBFS) at 0.95** — the closed-form bound hit exactly.
   A float line would remove it, and so would truncation toward zero in
   `to_s16`, but **both are node changes on a frozen pin**, not class
   choices; nothing the class can build on this palette removes a limit cycle
   at the tuned pitch (`cut_hz` does not — it is a DC blocker and the residue
   is not DC; measured, it made the 20 Hz case *worse*, ±80 LSB). So the
   class **states it**: `TAIL_SAMPLES = None`, the docstring names the
   number, and `reset()` clears it. It becomes an audioif ask only if the
   effects program wants exact silence at high feedback; the evidence pack
   §11 carries it as an issue to file.

*(Nothing else is open. The three above are the seed's three, each answered
from a run in A13, not from an argument.)*


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

*(from §3, the superseded verdicts)*

~~**T4 is unreachable on today's palette.**~~ **Superseded 2026-09-07:** T4
*is* reachable, as a five-node composition measured to within 0.01 dB of the
closed form — §5, Ask 1, and A12. T6 is the one that remains unreachable.
**Superseded again at Station A, 2026-09-07:** T6 *is* reachable —
`delay_slew` landed on this pin in the Phase 1 palette work (§5, A13) — and
T4, though reachable, is not built (§4).

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

*(from §3, Station A)*

**Latency: 0 samples, at every setting and every rate.**
`audioif_feedback_delay.c:496` writes `dry·source + wet_gain·loop` in the
frame the input arrives; the impulse comes out where it went in, at full
amplitude (A8). `latency_samples` is **0** and no option adds any. The tuned
delay is on the wet path and is the thing the user asked for, which vision
§9a distinguishes from latency. At Mix 2 there is no dry path at all and the
first sound arrives one line-length late — still the comb, not latency, and
the class docstring says so in milliseconds.

**Tail: not finitely bounded — `TAIL_SAMPLES = None`.** Measured at Station A
(A13): below Feedback 0.5 the line reaches **exact zero**. At and above it
`to_s16`'s rounding (`audioif_feedback_delay.c:308-316`) makes every
|c| ≤ 0.5/(1−g) a fixed point of the loop, so the line parks on a bounded
limit cycle at the tuned pitch and holds it for as long as the graph runs:
**1 LSB at g 0.7, 2 at 0.8, 5 at 0.9 and 10 LSB (−70.3 dBFS) at the class's
maximum 0.95** — the closed-form bound `floor(0.5/(1−g))`, hit exactly, worst
over 20 Hz…4 kHz, still there 30 s after a 0.1 s burst. `reset()` clears it.
This is the audioif#23 *class* of defect in a different node; it is the
node's arithmetic, not the class's, and the class states it rather than
hiding it.

**Cost budget: ESP32-P4 ≤ 2 %, ESP32-S3 ≤ 7 %** of one stereo block's
real-time deadline — the seed's figures, set for a one-node build, and the
rebuild is two nodes (§4). Desktop anchor re-taken at Station A (A13), net of
the source pump: `FeedbackDelay` **44.7 ns/frame**, the trim biquad
**54.1 ns**, **98.8 ns/frame together = 0.47 %** of the 20 833 ns a stereo
frame has at 48 kHz. Lean patch expected: **no**. RAM is the line: 60 ms
stereo is 11.5 KB at 48 kHz, allocated once, plus the biquad's float state.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

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

*(from §4, the Echo history in full)*

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

*(from §5, Station A — Ask 2's measurement in full)*

It defaults to 0, which is the jump this node always made, so
nothing the seed measured moved. Measured at Station A (A13) on T6's own
sweep: at `delay_slew = 0` the worst block boundary reads **−10.0 dBFS**
against the same render's off-boundary floor of −15.5 — a discontinuity you
can see. At 0.001 it is −44.4 against a floor of −44.2, at 0.01 −39.4 against
−39.3, at 0.05 −38.4 against −37.9: **the boundary stops being findable.**
The class carries it as the Glide macro, default 0.05.

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

*(from §4, Station A — the seven-node count in full)*

**Why the negative-feedback composition is not one of them.** §5's identity
holds and A13 reproduced it — impulse in, peaks at 480, 720, 960, 1200 …
frames with the sign alternating, which is `z^(−2M)/(1 + g·z^(−M))` exactly.
But it cannot be *the class* at anything under seven nodes. The IIR factor
`1/(1 − g²z^(−2M))` is only exact at the node's `mix = 2`, which is wet-only,
so the composed comb comes out **2M samples late** — 0.5 ms at 4 kHz and
100 ms at 20 Hz — and a Mix knob that sums that against an undelayed dry is a
flanger, not a comb blend. Aligning them costs a delayed dry path; keeping
the dry clean costs a Splitter tap and an output Mixer; carrying both signs
costs the inverter. The count is `Splitter(3)` + delay(M) + `Multiply` +
`Mixer(2)` + delay(2M) + `Mixer(2)` + a dry delay = **seven nodes, three
delay lines and the Splitter's fixed 32 KB ring**, against a Tier 3 budget
(§3) written for one node at 0.68 % of real time. The class is the naked
building block; it is not worth 4× its own budget on the S3 to put the peaks
on the half-multiples. T4 stays frozen in §3 and unbuilt, and the class
docstring and README row say so.


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
