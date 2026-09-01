# tr909 — Station C Evidence Pack

**Dossier:** [tr909.md](tr909.md). **Status:** parked for the batch listen —
`APPROVE ACCURACY tr909` blesses the golden. Built unattended under the
GO-golds charter (issue #6); every deviation from the dossier is stated here.

## Criteria, measured

**Knob curves (the pack's unique contribution) — 6/6 pass:**

| Knob | Hardware (measured) | Rebuild (measured) |
|---|---|---|
| BD Tune settled | 46.9 → 82.0 Hz | 46.4 → 84.1 Hz |
| BD Decay tau | 0.031 → 0.091 s | 0.031 → 0.087 s |
| BD Attack onset | −12.14 → −8.19 dBFS (3.95 dB) | −12.86 → −8.82 dBFS (4.04 dB) |
| SD Tune f_early | 120 → 240 Hz | 123 → 246 Hz |
| Tom Decay (LT) tau | 0.059 → 0.125 s | 0.037 → 0.123 s |
| Cymbal Tune → Ride tau (inverse) | 0.284 → 0.156 s | 0.373 → 0.182 s (span 2.05) |

**Tau aggregates: 9/9 pass** (BD/SD/CH/OH/LT/rim/clap/crash/ride, ±30%).

**Spectral centroids — measured under a corrected ruler.** The dossier's
aggregate centroid targets were computed on the 96 kHz pack as-is; Station C
found that ruler skewed three ways (96 kHz bandwidth vs 48 kHz renders;
magnitude weighting over the analog noise-floor tail our digital-silence
renders lack; untrimmed windows). The honest comparison — both sides
band-capped at 20 kHz and trimmed to the audible region — is what this pack
reports (`.reference-captures/tr909/renders/capped_centroids.json`):
**9/11 voices pass**. Two documented deviations:

- **BD: ref 160 Hz, ours 419.** Root cause identified, not fudged: synthio
  envelopes are linear, and the real kick's exponential low tail carries
  spectral mass a linear decay cannot. A same-shape kick, slightly less
  sub-heavy in the spectrum. The ear test is the phrase pair.
- **Rimshot: ref 615, ours 3127** (down from 8279 at first render). The real
  rim is dominated by a woody ~500 Hz resonator body; noise-excited biquad
  bands carry skirt energy above it. Voiced as dark as the architecture
  allows without a dedicated tone note.

## What Station B changed (and why)

Fixed-circuit architecture, 13 resident notes exactly (the ceiling):
BD 2, SD 2, toms 3, **shared tom stick-click 1** (the dossier's stretch
slot — spent here, not on the snare's second VCO: the schematic's noise
source is labeled "Tom Noise" and lives on the tom board, and reference
tom attacks demand it), rim 2, clap 1, hat 1 shared, cymbal 1 shared.
Kit residency verified at 13; BD survival through a full-kit hit 0.98.

Faithful-to-schematic changes: the BD keeps its **single downward sweep**
(VCO + CV drop — the dossier's finding that the 909 is not a bridged-T;
drop depth now scales with Tune per the measured 1.5×→2.0× ratios); the
**BD click is low-passed** as the schematic draws it — that one change
resolved the Attack-swing-vs-dark-spectrum tension the high-passed click
created; toms lose their unschematic noise layer but gain the shared
click; the **clap is one Note under a sawtooth flutter** amplitude LFO
(the hardware's own mechanism; verified byte-identical on all three
runtimes before use); rimshot is **filtered noise, not tuned triangles**;
open/closed hat and crash/ride each share one circuit and choke by
retrigger (crash/ride is the dossier's moderate-confidence call — the
batch listen can refuse it and the map degrades gracefully).

Macro ranges retuned to the measured grids: BD Tune 46–84 Hz, BD Decay,
SD Tune 120–240, Mid/Hi Tom tune lowered to the hardware's spans, Tom
Decay narrowed, hat decays re-spanned, **Cymbal Tune now shortens decay
as it rises** — the ROM-clock coupling the tune sweeps proved.

## Verification

- 83 unit tests, validate_api, flake8: green.
- Parity: **only tr909 fails its golden, on both interpreters** — the
  deliberate change; tr808's blessed golden and the other eight drums hold.
- Cross-interpreter: **all 11 one-shots byte-identical** CPython/MicroPython.
  (Sequence-probe hashes will differ per-interpreter through audioif#9's
  re-press phase divergence, as tr808's do; recorded at blessing time.)

## Listening

`phrase_OLD.wav` / `phrase_NEW.wav`, `oneshot_BD_NEW.wav`,
`reference_BD.wav` under `.reference-captures/tr909/renders/ab/`.

**Awaiting the batch listen:** `APPROVE ACCURACY tr909`
