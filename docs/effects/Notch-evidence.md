# Evidence Pack — `Notch` (no historical standout — design grade)

Written from `tools/phase2_probes/notch_evidence.py`, which prints every
number below, and `tools/phase2_probes/notch_bench.py`, which printed
Station A's own runs (the dossier's A16). Nothing here is from memory; where
a figure has no run behind it, the row says `unmeasured` and §11 says why.

**Read §1 first, and read it as a result rather than as a score.** One Tier 2
trait of six is demonstrated and five are disconfirmed. Four of those five
are one finding wearing four hats: the traits were frozen as statements about
an infinite-precision analog band-stop, and the class is a `float32`
coefficient set. The class matches *its own shipped coefficients* to 0.003 dB
everywhere it was checked. Where it does not match S1's double-precision
closed form, the pack says by how much and why, and never moves a bar.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `Notch` |
| Dossier | [`Notch.md`](Notch.md), traits frozen 2026-09-07 at `3ccab9e` |
| Module | `lib/audioeffects/rebuilt/notch.py` |
| Base | `_component.Component` |
| Family / phase | EQ / Filter, roadmap Phase 2 |
| Standout | none, per vision §4.2 — the Twin-T was weighed and dropped on scope (dossier §2) |
| Grade | design |
| Portability tier | **audioif** (`REQUIRES = ("audiobiquad",)`) |
| Landed in commit | `98e624b` (the class, the README row and the CHANGELOG line), `STATION_C_SHA` (this file, its probe and the class's own tests) |
| audioif pin | `AUDIOIF_PIN` = `2f6cbc3`; every C citation checked against the tree at that pin |
| Interpreters | `audiocomponents/.venv/bin/python` 3.12.3; `cmods/bin/micropython` 1.28.0; `cmods/bin/circuitpython-effects` 10.2.1 |
| Boards | **not run** — see §4 and §11 |

**Dossier trait set frozen before the rebuild began: yes.** Station A landed
in `3ccab9e` with the Tier 2 table unchanged from the seed — no row added,
dropped, renumbered or re-thresholded — and the first line of the class was
written after it. Station A's own runs (A16) already predicted T1's
disconfirmation and are recorded there, against the frozen row rather than
over it.

---

## 1. Traits

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation: argument, and the answer |
|---|---|---|---|---|---|
| **T1** | Total rejection at the centre: a commensurate sine at f₀ renders **bit-exact zero**; a sine at f₀·1.0005 reads −53.96 ± 0.5 dB at Q 2 | **disconfirmed** (first clause) / demonstrated (second) | RESPONSE + peak read, 48 kHz, cpython, level 6000. **Bit-exact zero at 1 kHz (Q 0.707/2/12) and at 4 kHz (all four Q).** Not zero at 60 Hz — **99 LSB at Q 12 (−35.65 dB)**, 150 at Q 32 — nor at 250 Hz Q 12 (5 LSB). Second clause: f₀·1.0005 at Q 2 reads **−53.976 dB** against a closed form of −53.957 (dev −0.020) | the zero pair moved 0.1 % off the probe → at 1 kHz Q 2 peak |y| **0 → 24**, at 4 kHz Q 12 **0 → 151**: RED, clean run green | *"You measured a transient."* Held to 40 s at 20 Hz Q 32 and 16 s at 60 Hz Q 12 — the value does not move by one LSB (dossier A16). *"Then the class is broken."* The rejection predicted from the section's **own shipped `float` coefficients** is −35.54 dB where the measurement reads −35.65: the class is its arithmetic. The cause is `b₀` and `b₁` rounded to `float` independently, so the numerator's cancellation at ω₀ survives only while `2α·sin ω₀` is large — dossier §5's node ask |
| **T2** | Unity outside the band: 0.00 ± 0.1 dB at DC and at 0.48·F_s, at every f₀ and Q | **disconfirmed** (2 of 9 grid corners) | 48 kHz, cpython. On the probes the trait's own Measurement cell names — a **DC step** and a **±FS alternating sequence** — every setting is inside ±0.008 dB (60 Hz Q 12 reads +0.0079 dB at DC, −0.0003 at Nyquist). On *tones* at 10 Hz and 0.48·F_s, 7 of 9 (f₀, Q) corners are inside ±0.1 dB; **f₀ 60 Hz Q 0.5 reads −0.4834 dB at 10 Hz** and **f₀ 16 kHz Q 0.5 reads −0.2068 dB at 0.48·F_s** | the numerator rebuilt as `BAND_PASS`, so it stops summing like the denominator at z = ±1 → **10 Hz −46.03 dB, 0.48·F_s −53.74 dB: RED**; clean run −0.000 / −0.000, green | *"Two failures out of nine is a broken filter."* Both are at **Q 0.5**, where the band is 2·f₀ wide: the 60 Hz notch's lower −3 dB point is **24.853 Hz**, so a 10 Hz probe is on its skirt, and the 16 kHz notch's upper one is **38 627 Hz**, past Nyquist, so 0.48·F_s is inside it. The closed form agrees with both measurements to 0.001 dB — **−0.2063 predicted against −0.2068 measured** at 16 kHz, **−0.4827 against −0.4834** at 60 Hz — so this is the notch's own skirt and not a leak. **The bar is not moved and the span is not narrowed to fit** — dossier A16 shows the span top that would have made it pass (0.2796·F_s) and says why it was not taken |
| **T3** | Width is f₀/Q: the −3 dB points sit at `f₀·(√(1+1/4Q²) ∓ 1/2Q)`, within −3.0 ± 0.15 dB for any Q in 0.5…32 | **disconfirmed** (one corner) | RESPONSE, 48 kHz, cpython. 1 kHz Q 2 → **−3.000 / −2.993 dB**; 1 kHz Q 8 → −2.999 / −2.997; 250 Hz Q 0.5 → −3.010 / −3.007. **4 kHz Q 32 → −2.817 / −2.812**, 0.19 dB outside the bar | the section's Q set to 1.5× the reported Width → edges read **−1.591 / −1.586 dB: RED**; clean −3.000 / −2.993, green | *"The class widened the notch."* It did not: S1's own closed form at those two frequencies reads **−2.818 / −2.812**, so the class is on its own curve to 0.006 dB and it is the **analog** edge formula that stops landing on −3 dB as f₀ climbs — the bilinear transform warps the axis, which is the same effect T6 is written against. The row fails as stated, and it fails on the prediction, not on the filter |
| **T4** | Notch + band-pass = 1 exactly: the two summed reconstruct the input within 0.05 dB from 20 Hz to 0.4·F_s | **demonstrated** | 48 kHz, cpython, f₀ 3 kHz Q 2, seven probes 20 Hz … 12 kHz, summed in float64. **Every probe ±0.0000 dB; worst +0.0000 dB** | the band-pass branch detuned by 1 % → worst near f₀ **+0.1787 dB: RED** (bar 0.05); clean +0.0000, green | *"You summed in float, so you measured algebra."* Deliberately, and it is stated: an int16 sum would measure the mixer's rounding, and the trait is about the two numerators. The two branches are separate renders of separate nodes at the same settings — nothing shares state — and the fault shows the sum is not trivially satisfied |
| **T5** | Depth is not a knob: rejection at f₀ is total for **all** Q in 0.5…32, and the off-centre reading moves 36 dB across that Q range, each point within 0.5 dB of its own closed form | **disconfirmed** (first clause) / demonstrated (second) | 48 kHz, cpython, f₀ 1 kHz. On-centre commensurate: bit-exact zero at Q 0.5, 2 and 8; **1 LSB at Q 32**. Off-centre f₀·1.0005: **−65.920 / −53.976 / −41.917 / −29.862 dB** against closed forms of −65.998 / −53.957 / −41.916 / −29.879 — worst dev 0.078 dB — a **36.06 dB spread on one fixed probe**. Depth law: gain at f₀ is `1 − mix`, measured **0.000 / −2.499 / −6.021 / −53.976 dB** at depth 0 / 0.25 / 0.5 / 1 | Depth implemented as a Q change rather than a mix — the design error the trait forbids → worst deviation from the `1 − mix` prediction **66.154 dB: RED**; clean 0.261 dB, green | *"One LSB at Q 32 is noise."* It is a reading, not noise: the same probe at Q 0.5, 2 and 8 renders **exactly** zero, so the measurement can express zero and this configuration does not reach it. It is T1's law again — at Q 32 the coefficient floor is −84 dB predicted, which rounds to 1 LSB against a 6000 level |
| **T6** | Rate-honest: centre within 0.1 % and the response within 0.1 dB of S1's closed form **at the running rate**, up to 0.45·F_s | **disconfirmed** (curve clause at two rates) / demonstrated (centre clause) | cpython. Centre of the 1 kHz Q 8 notch, located from its two −3 dB crossings: **999.9337 Hz at 48 kHz (0.0066 % out)**, 1000.0737 at 44.1 kHz (0.0074 %), 999.9640 at 22.05 kHz (0.0036 %) — all inside 0.1 %. Curve: worst |measured − closed form| **0.124 dB at 48 kHz** and **0.114 dB at 44.1 kHz**, both at f₀ 60 Hz Q 12 probe 57.6 Hz; **0.017 dB at 22.05 kHz** | coefficients derived as if the graph always ran at 48 kHz → at 22.05 kHz the rejection at the 1002.273 Hz it was asked for reads **−0.02 dB against −240.00: RED**. At 48 kHz the faulted class *is* the shipped one and both read −240.00, which is the control — a rate bug that fired at every rate would not be a rate bug | *"The class drifts with rate."* The centre does not — 0.007 % at the worst rate. What misses is the 0.1 dB curve clause at one probe: the −3 dB edge of a 60 Hz Q 12 notch, 2.4 Hz from the centre on the steepest part of the skirt. The same point computed from the **shipped float coefficients** reads −2.883 dB against a measurement of −2.886, **0.003 dB apart**, so the 0.124 dB is the coefficient set and not the rate handling. It is T1's finding at a third setting |

### 1a. The one finding behind four of the five disconfirmations

T1, T3, T5 and T6 all fail on the same mechanism, and it is worth stating once
rather than four times. The rejection at the centre of an `audiobiquad`
`NOTCH` is

```
|H(w0)| = |2*b0*cos(w0) + b1| * (1 + alpha) / (2 * alpha * sin(w0))
```

`b0` and `b1` are computed in `double` and stored as `float`
(`audioif/src/shared/audioif_filter_f32.c:194-198`), independently, so the
exact cancellation `2*b0*cos(w0) + b1 = 0` survives only to about one ulp of
2 — 1.2e-7 — while the denominator `2*alpha*sin(w0)` shrinks as f₀ falls and
Q rises. At 60 Hz Q 12 that denominator is 5.14e-6, and 1.2e-7 / 5.14e-6 is
−35 dB. At 1 kHz Q 2 it is 8.5e-3, and the same numerator error is −109 dB —
under a third of an LSB, which is the bit-exact zero T1 claims.

Everything else follows: T5's "total at every Q" is T1's clause repeated
across Q; T6's worst curve point is the −3 dB edge of a 60 Hz Q 12 notch,
where the skirt is steepest and the same perturbation shows; T3's 4 kHz Q 32
row is the *other* half of the same family of edge cases, and there the class
is on its own closed form and the analog formula is what misses.

**What was not done about it, and why.** Two builds that would recover most
of it are weighed and refused in the dossier's §5 and App. R — a parallel
`Splitter → BAND_PASS → invert → Mixer` (four extra nodes and an int16 sum on
the dry path, which T2 and LEVEL are stated against) and a four-pole cascade
(which would disconfirm T4 by construction). The remaining route is audioif's
own, and it is the node ask: a `NOTCH` numerator derived from the stored
denominator rather than rounded beside it, worth **17 to 36 dB** at the hum
settings, measured from the shipped coefficients (dossier A16). Filed in §11.

### Refutation pass

Run by this session against its own results, 2026-09-07, after every number
was in hand. What it went after and what it changed:

- **T1's "you measured a transient"** — it forced the 40 s and 16 s holds
  (dossier A16, D12) and the coefficient-side prediction, which is what turned
  a suspicious reading into a law.
- **T2's planted fault** — it **broke the first one**. The first plant was
  "remove the 0.4·F_s centre ceiling", and at 48 kHz that changes nothing at
  all, because the Frequency span's own top (16 kHz) already sits below
  0.4·F_s (19.2 kHz) — a fault that cannot fire. Moved to 22.05 kHz it fires
  only at Q 0.5 — clean (8820 Hz) **−0.6614 dB** against faulted
  (10804.5 Hz) **−4.4319 dB** — and there the **clean** build already misses
  T2's ±0.1 dB bar, so its control is not green. Both are recorded, and the
  fault T2 is cited against is the `BAND_PASS` numerator, whose control
  reads −0.000 / −0.000 dB.
- **T3's failing row** — it demanded the closed form beside the measurement,
  which is what separates "the class widened the notch" from "the analog
  formula stopped predicting the digital filter".
- **LEVEL's probe** — it **broke the first reading**. Broadband noise through
  the class at Depth 1 reads −0.065 dB, which the first draft recorded as a
  Tier 1 failure; it is the 267 Hz the notch removed from a 24 kHz spectrum.
  The measurement's subject moved to a tone outside the band; the noise
  reading is kept beside it, with its cause.
- **TAIL's and the class test's pull loop** — it **broke a green**. Counting
  blocks rather than frames walked the ported-kernel fault past the end of its
  probe, and a `Filter` whose source is exhausted memsets its output without
  running the biquads at all (dossier A3), so audioif#23 read *clean*. Both
  now pull a stated number of frames from a probe sized to outlast them.
- What it could not break: T4's identity, the WIRE/CLICK/STATE rows, the
  three-interpreter byte identity, and the block-size ladder.

---

## 2. Tier 1 invariants

`cp` = `.venv/bin/python`, `mp` = `cmods/bin/micropython`, `cpy` =
`cmods/bin/circuitpython-effects`.

**How the `mp` and `cpy` columns are earned.** Every measurement below reads
PCM. §3 shows the three interpreters rendering **byte-identical PCM** on 18
probe/rate/channel/patch combinations, so a number computed from those bytes
on CPython is the number on all three. The columns say `= cp` for that reason
and not because the analysis was re-run under MicroPython, which has no numpy
and which the kit spec says never to ask for an FFT.

| Invariant | Kit | 48 k cp | 48 k mp/cpy | 44.1 k cp | 44.1 k mp/cpy | 22.05 k cp | 22.05 k mp/cpy |
|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass — residual **0 LSB**, dc_step residual **0 LSB**, at patch 0, at hum 60 with two notches, and at 20 Hz Q 32 with two notches | = cp | pass, 0 / 0 LSB | = cp | pass, 0 / 0 LSB | = cp |
| Depth 0 is a wire, byte-identical to the source | WIRE | pass — **0 of 16384 samples differ**, `ramp_fs`, both at patch 0's settings and at hum 60 with the trim asked for +12 dB (fnv `4af4e8b5` both sides) | = cp | pass, 0 of 16384 | = cp | pass, 0 of 16384 | = cp |
| Level-honest: unity through the dry path, no hidden gain | LEVEL | pass — Depth 0 on `noise_det` **+0.0000 dB**; Depth 1 on a 1 kHz tone with the notch at 8 kHz Q 30 **−0.0000 dB** | = cp | +0.0000 / −0.0001 dB | = cp | +0.0000 / −0.0000 dB | = cp |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass — CLICK measured **[0.0, 0.0]** against a reported 0 at all six patches (§5); longest tail **140 406** samples against a declared 143 360 | = cp | pass, tail 128 480 | = cp | pass, tail 64 783 | = cp |
| `reset()` leaves every node silent and stateless, the source untouched | STATE | pass — **residual 0 LSB** after `reset()` with a silent source, and `resumed` is `True` with a different digest when the probe is handed back | = cp | pass | = cp | pass | = cp |
| `deinit()` releases every node and leaves the source rendering | STATE | pass — **0 of 3 nodes live** after `deinit()` | = cp | pass | = cp | pass | = cp |
| `capabilities` names exactly what is honoured | STATE | pass, `()` | = cp | pass | = cp | pass | = cp |
| Pulling `output` allocates nothing | STATE | pass — **601 bytes over 200 single-block pulls** (bar 8192), on a render whose digest is not silence | = cp | 361 bytes | = cp | 225 bytes | = cp |
| Rate-honest: Hz spans clamp below Nyquist, never refuse | RESPONSE | pass — 100 kHz asked for lands at **19 200 Hz** (0.4·F_s) and the class still filters; no `ValueError` at any rate (`test_cpython_effects_notch.py::TheClassIsRateHonest`) | = cp | pass, 17 640 Hz | = cp | pass, **8 820 Hz** — the clamp that actually bites | = cp |
| Every invariant also holds at `channel_count` 1 | (all) | pass, all rows | = cp | pass | = cp | pass | = cp |

**Mono.** The dossier's §4 says a mono source gets the same filter on one
channel — not a wire and not a sum. Measured: at `channel_count` 1 every row
above is green at all three rates, and the f₀·1.0005 reading at Q 8 is
**identical to the stereo one to 0.0000 dB** at 48 000, 44 100 and 22 050 Hz.

**Planted faults for this block**, each with its clean control:

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | the dry path scaled by 32767/32768, on `ramp_fs` | 0 of 16384 differ | **RED, 8192 of 16384 differ** |
| WIRE (the fault's own control) | the same fault on `quiet_chord`, which peaks below −6.02 dBFS | — | **green, 0 of 16320** — the material cannot reach the mechanism, which is why WIRE names `ramp_fs` |
| TAIL | the same 60 Hz Q 8 filter on the ported integer kernel (`audiofilters.Filter` over `synthio.Biquad`) — audioif#23 itself | residual 0 LSB, tail 33 259 | **RED, residual 2 LSB, tail 283 680** at 48 kHz and 44.1 kHz |
| TAIL (where the fault does not fire) | the same plant at **22.05 kHz** | residual 0 LSB | **green, residual 0 LSB** — audioif#23's fixed points are rate-dependent, and 60 Hz Q 8 is not one at that rate. Recorded rather than hidden |
| LEVEL | +0.1 dB hidden gain on the path | +0.0000 dB | **RED, +0.1000 dB** (bar 0.05) |
| CLICK | `latency_samples` reported 256 short, DSP untouched | measured [0.0, 0.0] against 0 | **RED**, measured [0.0, 0.0] against 256 — and the audio digest is `3b0e4089` in **both** runs, so nothing else fires |
| STATE | — | the control *is* the reading: `resumed` is `True` and `resumed_fnv1a` differs from `reset_residual_fnv1a`, so the walk is not passing because nothing was pulled | |
| `tail_samples` | a subclass declaring 1024 samples | 140 406 ≤ 143 360 | **RED** (`test_cpython_effects_notch.py::TheTailReachesExactZero::test_a_declaration_short_of_the_measurement_is_red`) |

`reset()` and `deinit()` walk the list `_component` requires the class to
enumerate with `self._own()`. **Nodes enumerated by this class, in build
order:** `_fundamental` (`audiobiquad.Biquad`, `NOTCH`), `_harmonic`
(`NOTCH` at 2 f₀), `_trim` (`HIGH_SHELF` at 5 Hz) — three nodes.
`kit.enumerate_nodes` walks *public* attributes and finds none of them, which
is correct: the construction module's whole point is that a class enumerates
its own nodes, so the pack hands the three to STATE by name.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes (`effects_component_probe.py:15`), per probe, per
rate, per channel count, per patch, at block 256. `sum(data)` is never the
comparison.

Command (one row; the other seventeen differ only in the flags):

```
$ PYTHONPATH=lib .venv/bin/python tools/render_effect.py Notch chord OUT/cp \
      --rate 48000 --channels 2 --patch 0
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      tools/render_effect.py Notch chord OUT/mp --rate 48000 --channels 2 --patch 0
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      -X heapsize=256M tools/render_effect.py Notch chord OUT/cpy --rate 48000 --channels 2 --patch 0
```

| Probe | Rate | Ch | Patch | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 2 | 0 | `36089a2d` | `36089a2d` | `36089a2d` | *(board run)* | *(board run)* |
| `chord` | 48000 | 2 | 2 | `d5699325` | `d5699325` | `d5699325` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 2 | 0 | `bb7b1d0d` | `bb7b1d0d` | `bb7b1d0d` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 2 | 2 | `f5caaa81` | `f5caaa81` | `f5caaa81` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 2 | 0 | `50c54011` | `50c54011` | `50c54011` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 2 | 2 | `bf409e69` | `bf409e69` | `bf409e69` | *(board run)* | *(board run)* |
| `chord` | 44100 | 2 | 0 | `fe9cd335` | `fe9cd335` | `fe9cd335` | *(board run)* | *(board run)* |
| `chord` | 44100 | 2 | 2 | `7eff3775` | `7eff3775` | `7eff3775` | *(board run)* | *(board run)* |
| `burst_silence` | 22050 | 2 | 0 | `3a0b5845` | `3a0b5845` | `3a0b5845` | *(board run)* | *(board run)* |
| `burst_silence` | 22050 | 2 | 2 | `32520fbd` | `32520fbd` | `32520fbd` | *(board run)* | *(board run)* |
| `chord` | 48000 | 1 | 0 | `0bc985d0` | `0bc985d0` | `0bc985d0` | *(board run)* | *(board run)* |
| `chord` | 48000 | 1 | 2 | `8444f4b7` | `8444f4b7` | `8444f4b7` | *(board run)* | *(board run)* |

**Desktop agreement: yes**, on all twelve, and none of them is silent (the
renderer refuses to report a silent render as audio and prints `audio` for
each).

**Board agreement:** *(board run — §11)*. Float width / FMA contraction is
the accepted cause of a board/desktop difference (the anchor repo's
`docs/accuracy-roadmap.md:612-616`), never the class.

**The dossier's D4, settled here.** The seed's A9 recorded a cross-target
divergence: `audiofilters.Filter` bypasses its cascade at `mix <= 0.01` on
MicroPython while the CPython target blends, so the Depth macro was to snap
anything in `(0, 0.01]` to zero. This class builds no `Filter`, and
`audiobiquad`'s per-section `mix` is the same C on all three interpreters.
Rendered `sine_1k_-6` with the notch at 983 Hz, one row per Depth:

| Depth | cpython | micropython | circuitpython-effects | agree |
|---|---|---|---|---|
| 0.000 | `58c55925` | `58c55925` | `58c55925` | yes |
| 0.005 | `bd85553d` | `bd85553d` | `bd85553d` | yes |
| 0.010 | `40b79795` | `40b79795` | `40b79795` | yes |
| 0.020 | `7781f65d` | `7781f65d` | `7781f65d` | yes |
| 0.500 | `e570b0dd` | `e570b0dd` | `e570b0dd` | yes |
| 1.000 | `686284f9` | `686284f9` | `686284f9` | yes |

Six distinct digests, so the low Depths are not being bypassed, and the three
interpreters agree at each. **The snap is dropped**, and this table is why.

**Block-size ladder.** The same class and settings (patch 2, `noise_det`,
32768 frames) at five source block sizes:

```
    block 256      fnv 294d8861  sum 16680382
    block 8192     fnv 294d8861  sum 16680382
    block 16384    fnv 294d8861  sum 16680382
    block 20000    fnv 294d8861  sum 16680382
    block 32768    fnv 294d8861  sum 16680382
    identical across the ladder: yes
```

**DIGEST's planted fault**, computed rather than recalled: one sample raised
by 256 LSB and another in the same block lowered by 1 LSB.

```
    planted fault (+256 LSB at byte 0 and -1 LSB at byte 2): fnv 866439e7
    against 294d8861 -> RED;  byte sum 16680382 against 16680382, moves by 0
```

The unsigned-byte sum moves by **exactly zero** and FNV-1a goes red, which is
why the digest is FNV and never `sum(data)`.

---

## 4. Tier 3 — cost on the boards

*(Left for the board run. Fill from `tools/measure_effect_cost.py`; do not
copy a figure from the Phase 1 node table and call it this class's.)*

Dossier budget: ESP32-P4 ≤ 1.5 % of one stereo block's real-time deadline
with one notch and ≤ 2.5 % with two; ESP32-S3 ≤ 5 % and ≤ 9 %. Lean patch
expected: no.

| Board | Patch | Settings the figure was taken at | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | *(board run)* | | | | | |
| S3 | 0 | *(board run)* | | | | | |
| S3 | 2 | *(board run)* | | | | | |

**The dossier's split budget cannot be met one half at a time**, and the
reason is the C rather than a stopwatch. `audioif_biquad_f32_process_s16`
runs the recursion for every frame and *then* blends — `out[index] =
to_s16(dry * x0 + mix * y0)` at
`audioif/src/shared/audioif_filter_f32.c:216-241`, the blend at `:239` — with **no branch on
`mix`**, and the CPython target reaches the same shared function through
`src/cpython/_audioif.c:1205-1224`. All three sections are built at every
setting, because a node cannot be added to a running graph and Harmonics is
a live macro. **So `mix` 0 costs what `mix` 1 costs, one notch costs what two
cost, and the class costs three sections everywhere.** The budget that
governs on the board is therefore the higher pair (P4 ≤ 2.5 %, S3 ≤ 9 %) and
the Harmonics toggle buys nothing back.

**The desktop anchor is `unmeasured`, and the spread is why.** The protocol
in `cost_anchor()` — `gc.collect()`, `time.perf_counter` around 180 blocks,
best of nine, on `noise_det` at 48 kHz stereo — does not produce a repeatable
number on this machine:

```
    patch 0, one notch             min   725.0  median  1015.8  max  1177.3 ns/frame
    patch 2, two notches           min   546.8  median   772.4  max  1030.6 ns/frame
    patch 2 at Depth 0 (a wire)    min   418.8  median   704.9  max  1009.5 ns/frame
    bare source                         6.5 ns/frame
```

and an earlier invocation of the *same* function, same arguments, read 112.9
/ 107.2 / 110.5 ns/frame for the same three rows. A five-fold spread across
invocations is not an anchor, and most of what it times is the CPython twin's
per-chunk Python work rather than the kernel a board runs. **No number above
is quoted as this class's cost.** The board run is the measurement; §11 says
it was not taken.

**The expensive path is reachable and was reached** in the renders §3 cites:
patch 2 at Depth 1 renders `f5caaa81` on `noise_det`, which is not the digest
of silence, so a board runner would rank it rather than refuse it.

---

## 5. Latency

Reported `latency_samples` = **0**. Measured click delay against the dry
path, integer onset, per channel, per patch:

| Rate | Patch | Reported | Measured | Δ | ms |
|---|---|---|---|---|---|
| 48000 | 0–5, all six | 0 | [0.0, 0.0] | 0 | 0.0000 |
| 44100 | 0–5, all six | 0 | [0.0, 0.0] | 0 | 0.0000 |

Dossier latency budget: **0 samples, 0.000 ms**. Met: **yes**.

**Every latency-adding option, each defaulting off or to its shortest:**

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| *(none)* | — | 0 | — | The docstring says so explicitly: every section is a recursive biquad reading no sample it has not been given, and no option adds a lookahead, a partition or a window |

Planted fault: `latency_samples` reported 256 short with the DSP unchanged →
**CLICK red at both rates**, audio digest unchanged (`3b0e4089` at 48 kHz in
both the clean and the faulted run; `28977bad` at 44.1 kHz in both).

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 20 … 16 000 Hz, log; clamped live to `min(16 kHz, 0.4·F_s)` | the tuning knob |
| 1 | Width | UNIPOLAR | Q 0.5 … 32, log; the bandwidth is f₀/Q | the Q / bandwidth knob |
| 2 | Harmonics | TOGGLE | 0 = one notch, 1 = two (f₀ and 2 f₀, the second's Q doubled) | a hum eliminator's harmonic switch |
| 3 | Depth | UNIPOLAR | 0 exactly … 1, the section's own `mix` | the depth control T5 says must be a mix |
| 4 | Trim | BIPOLAR | −12 … +12 dB, default 0; under 0.2 dB the section is a wire | output make-up |

Five of the sixteen the contract allows.

| Patch | Name | What it is for |
|---|---|---|
| 0 | Wide Notch | the constructor's defaults on the 0-127 grid — 983 Hz, Q 0.72, one notch, full depth |
| 1 | Hum 50 | 48.9 Hz at Q 12 with the 97.9 Hz harmonic, for 50 Hz mains |
| 2 | Hum 60 | 60.4 Hz at Q 12 with the 120.8 Hz harmonic, for 60 Hz mains |
| 3 | Feedback Tamer | 2535 Hz at Q 23.8 — narrow enough to take a ringing room mode out of a live mix |
| 4 | Mud Scoop | 293 Hz at Q 1.21 at 60 % depth, a broad partial cut rather than a null |
| 5 | Whistle Kill | 8072 Hz at Q 30, for a single high tone |

Every patch was checked to notch where its comment says and to leave an
octave above it alone
(`test_cpython_effects_notch.py::TheSurface::test_every_patch_notches_where_its_comment_says`).

`patch_index` is 0 on a fresh instance, `None` after any macro move, and the
patch's index after `program_change`: shown by
`tests/test_cpython_effects_notch.py::TheSurface::test_patch_index_follows_the_contract`.

**`capabilities` = `()`.** The class never calls `self._transport()`; the
dossier's one-line reason, quoted: *"nothing in a notch is measured in beats
— its controls are hertz and a dimensionless Q."*

---

## 7. Portability tier

**Tier: audioif.** `REQUIRES = ("audiobiquad",)`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `Biquad` (`NOTCH`) × 2 | `audiobiquad` | Tier 1's exact-zero tail, at every setting in the span | `synthio.Biquad`'s recursion keeps its memory in Q12 sample units and rounds to nearest with no dither and no leak, so it lands on fixed points: `Notch(60 Hz, q=8)` holds **2 LSB** and `Notch(20 Hz, q=32)` **18 LSB**, for ever (audioif#23; measured again in §2's planted fault, residual 2 LSB against 0) |
| `Biquad` (`HIGH_SHELF`) | `audiobiquad` | the make-up Trim, and the same tail invariant through it | the same kernel, and there is no route from Python to a biquad's `b` coefficients on either node, so a subsonic shelf is the palette's only gain above unity |

Test:

```
$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
----------------------------------------------------------------------
Ran 7 tests in 0.004s

OK
```

The class appears in that battery automatically — it walks
`audioeffects.ALL` and `rebuilt.known()` — so a tier claim here that the
class's `TIER` does not match is a test failure, not a wrong sentence in a
document.

**What that test does not prove**, and every pack must repeat it: blocking a
module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace, so a stock-tier class has
*not* been shown rendering on a stock CircuitPython build of the ported C.
That is a gap in the method, not in this class. **And for this class there is
a second thing no interpreter here can show:** what a stock CircuitPython
10.2.1 board actually does with a `synthio.Biquad`, whose single interleaved
biquad state puts every frequency an octave high and couples the two channels
(`audioif/docs/upstream-diff.md:1215-1229`). The dossier's §8 D9 strikes the
seed's claim about that board on those grounds.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began, and §1 lists
      every trait as demonstrated, disconfirmed (with cause) or unmeasured
      (with why no number exists). **1 demonstrated, 5 disconfirmed, 0
      unmeasured.**
- [x] Every Tier 1 invariant is green on CPython and MicroPython at 48 kHz,
      44.1 kHz and 22.05 kHz, and on the patched CircuitPython build where
      its nodes exist; every Tier 2 measurement names the rate it ran at.
- [x] Every demonstrated Tier 2 trait has a measurement, and that measurement
      was shown red on a planted fault of the same kind. **Every
      disconfirmed one carries its fault too**, so the disconfirmations are
      readings and not silence.
- [x] Every demonstrated trait survived an independent refutation attempt,
      recorded with the refuter's argument and the answer (§1, and the
      refutation pass's own summary).
- [x] CPython and desktop MicroPython render identical bytes on the probe
      material — twelve combinations plus six Depth rows, all three
      interpreters. **The P4 and S3 legs are not taken** (§11).
- [ ] Tier 3 cost is measured on the P4 and the S3. **Not done**, and the
      desktop anchor is `unmeasured` too — its spread is five-fold across
      invocations (§4, §11).
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz
      and 44.1 kHz; the dossier's latency budget is met; there is no
      latency-adding option to default off, and the docstring says so.
- [x] The class declares a macro surface (five of sixteen) and five named
      patches beyond patch 0.
- [x] `validate_api`, `validate_metadata`, the CPython tests, the
      portability-tier test, the three-interpreter smoke and flake8 all pass
      (§9). No old-surface trait test was retired, and §10 says why there was
      none to retire.
- [x] The README catalogue row and the docstring describe the standout, the
      portability tier, the cost **and the disconfirmed trait**, in a
      musician's terms.
- [x] The class's code, the README row and the CHANGELOG line landed in
      `98e624b`; this file, its probe and the class's own tests in
      `STATION_C_SHA`.

---

## 9. Commands, verbatim

```
$ PYTHONPATH=lib .venv/bin/python -m flake8
(no output, exit 0)

$ PYTHONPATH=lib .venv/bin/python -m unittest discover -s tests -p "test_*.py"
----------------------------------------------------------------------
Ran 246 tests in 23.395s

OK (skipped=1)

$ PYTHONPATH=lib .venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=lib .venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
----------------------------------------------------------------------
Ran 7 tests in 0.004s

OK

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_cpython_effects_notch
----------------------------------------------------------------------
Ran 19 tests in 0.103s

OK

$ PYTHONPATH=lib .venv/bin/python tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
    tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
    tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ PYTHONPATH=lib .venv/bin/python tools/measure_effect_cost.py --subject Notch --port COMn
not run - no board leg this session (section 11)
```

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

| The old defect | What the rebuild does instead |
|---|---|
| **No surface at all** — `MACRO_LABELS = ()` (`eq.py:156`) | five macros and six patches, §6 |
| **The width knob does not exist and cannot be made to exist** — `q` is a bare float into `synthio.Biquad` (`eq.py:104`) while `frequency` gets a block | Width is macro 1 and a live slot on the section; T3 measures it |
| **No depth control** — `mix` taken at `eq.py:101`, forwarded at `:105`, unreachable after | Depth is macro 3 and is the section's own `mix`; 0 is a byte-exact wire (§2, WIRE) |
| **`set_frequency` is off-contract and it raises** — `_core.check_hz` raises at or above Nyquist (`_core.py:471-474`) | there is no `set_frequency`; hertz reach the class through its macro grid, and the centre **clamps** at `min(16 kHz, 0.4·F_s)` (§2, rate-honest row) |
| **No tail is declared** — `TAIL_SAMPLES = None` (`_core.py:141`) | `TAIL_SAMPLES = 143360`, measured at the class's own worst corner (140 406) and shown red against a short declaration |
| **Held DC at the hum setting** | the tier moved to `audiobiquad`; residual 0 LSB at every setting measured, with the ported kernel as the planted fault |
| **`reset()` reaches one node** (`_core.py:366-374`) and the `Filter` it reaches resets its source | `reset()` walks the three nodes the class enumerated with `self._own()`, and the borrowed source is never named |

**No old-surface trait test was retired**, because there was none:
`test_cpython_effects_dynamics_eq.py` walks `LowPass` and `HighPass` for its
filter rows and names `Notch` nowhere. Said here rather than left as a silent
gap in the gate's own checklist item.

---

## 11. What is not done

- **The board leg is not taken, on either board.** No ESP32-P4 or ESP32-S3
  run happened this session, so §4's cost table is empty and §3's board
  columns are empty. What it would take: `tools/measure_effect_cost.py
  --subject Notch` over mpftp on each board, per
  `docs/agent-knowledge/device-debugging.md`.
- **The desktop cost anchor is `unmeasured`.** §4 has the runs; they spread
  five-fold across invocations of the same protocol, so there is no figure to
  quote. What it would take: a quiet machine, a pinned CPU governor, and a
  protocol that amortises the twin's per-chunk Python work — or, better, the
  board run, which is what Tier 3 actually asks for.
- **The audioif node ask is not filed as an issue.** §1a and the dossier's §5
  carry it with its arithmetic — a `NOTCH` numerator derived from the stored
  denominator, worth 17 to 36 dB at the hum settings. It needs an audioif
  issue; nobody has opened one.
- **`tools/measure_effect_cost.py --subject` was not exercised at all**, not
  even to see it refuse a silent render, because it is a board-side runner
  and there was no board.
- **T2's `0.48·F_s` clause was measured with a tone, and the trait's own
  measurement cell also names a swept sine's endpoints.** The stepped-tone
  excitation is what `effect_measurements.response` implements; the swept and
  STFT excitations are not built (kit spec §5), so the endpoint reading is a
  tone at 0.48·F_s and not a sweep's last point. The numbers agree with the
  closed form to 0.0005 dB, so nothing is hidden by it, but it is a different
  probe from the one the cell names.
- **No listening.** Per the program's mechanical-gate rule for the effects
  phases, this class was not auditioned; every claim above is a number.
