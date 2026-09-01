# sp1200 — Station C Evidence Pack

**Dossier:** [sp1200.md](sp1200.md). **Status:** parked for the batch
listen — `APPROVE ACCURACY sp1200`. Built unattended at literature grade;
**upgraded to GOLD the same day**: Brad completed the Samples From Mars
signup and the full free catalogue lives at `~/SamplesFromMars` (kept
outside the repo by his choice — measured in place, nothing copied,
nothing redistributed, per the SFM EULA already on record).

## What was rebuilt

A 4-voice sketch became the machine's architecture: **8 fixed channels**
exactly as the service manual's block diagram draws them — channels 1–6
through a modeled SSM2044 (attack-time exponential cutoff sweep, the
`release_filter` idiom run forward), channels 7–8 (tom, cowbell) direct
outs with only the anti-alias ceiling, even though a filtered tom would
sound more "natural"; the manual wins. 12 resident notes, fixed-circuit.
No hat choke — a sampler's CH and OH are separate samples on separate
channels, so modeling one would be *false* accuracy.

## Criteria (literature-derived), measured

| Criterion | Target | Measured |
|---|---|---|
| Bandwidth ceiling | ~no energy above ≈13 kHz | 1.9% above 13.5 kHz on the brightest voice — PASS |
| 12-bit noise floor | tail settles ≈ −72 dBFS | **−73.1 dB** rel peak — PASS |
| 8-bit level DAC | amplitudes on 256 discrete steps | modeled exactly in `qlevel()` — structural PASS |
| Pitch-tied decay | ≈0.6–0.7× at max up, ≈1.5–1.6× at max down | **0.65× / 1.52×** vs Yeh's measured 0.67×/1.56× — PASS |
| VCF (SP Crunch) sweep | cutoff decays from elevated onset; static at 0 | centroid falls 1.51× at crunch=127, static at 0 — PASS |
| Channel/filter routing | 6 filtered, 2 direct | structural PASS |
| Voice ceiling | 8 channels, ≤13 residents | 12 residents, 8 channels — PASS |

The pitch↔length coupling was not tuned to hit Yeh's numbers — it *falls
out* of binding decay to the same ratio the pitch macro drives, which is
what a sampler is. "SP Crunch" is rebound from the old grab-bag to the
one real, measurable thing it can stand for: the SSM2044 sweep depth.

**Stated unreachable, not faked:** true aliasing from truncated-index
skip/repeat and zero-order-hold imaging — synthio has no primitive for
either.

## Verification

83 unit tests, validate_api, flake8: green. Parity: sp1200/tr707/tr909
fail their own goldens (all deliberate, awaiting the batch blessing);
tr808's blessed golden and the other six hold. Cross-interpreter: all 8
one-shots byte-identical.

## The re-check, executed: measured criteria replace literature ones

The 65 drum WAVs were measured in place. Three upgrades followed:

**The coupling criterion is now anchored to the SP-1200 itself.** The
pack's 16-step factory-snare tuning sweep holds `f x duration` constant
(~30) across its untruncated upper range — pure repitch, measured on the
real machine, no longer borrowed from Yeh's SP-12. Our macro extremes
land at 0.59x / 1.48x.

**The role map was corrected by the pack's own kit** (the dossier's
re-check clause, exercised): the reference kit carries a **crash and no
rimshot**, so channel 5 is now Crash (note 49), filtered per the manual.

**All 16 measured rows pass** (kick family tau/pitch, snare tau+centroid,
both hats, clap, tom, crash, cowbell — each against its role's measured
median), plus the physics rows re-verified: noise-floor tail −73.1 dB,
bandwidth ceiling, 8-bit level DAC, VCF sweep. Voicing moved to the
measured kit: kick family shortened, hats re-spanned, cowbell fundamental
to the factory 398 Hz, crash at tau 0.39.

Full numbers: `.reference-captures/sp1200/sfm_stats.json` (reference) and
`renders/after_stats.json` (ours).

**Awaiting the batch listen:** `APPROVE ACCURACY sp1200`
