# tr707 — Station C Evidence Pack

**Dossier:** [tr707.md](tr707.md). **Status:** parked for the batch listen —
`APPROVE ACCURACY tr707`. Built unattended under the GO-golds charter.

## The grade came back

The dossier honestly downgraded tr707 to literature: ELPHNT's pack is gone
(four dead ends) and the BØLT pack sat one JavaScript step from reach. That
step fell to a Playwright session (the workspace's own examples venv): the
free-purchase claim flow completed headlessly and the **BØLT clean TR-707
pack downloaded whole** — all fifteen ROM sounds, one clean capture each,
recorded provenance in the pack's own naming. **The rebuild is measured
against clean hardware captures after all.** License: claimed through the
store's own $0 purchase flow; no license file ships in the zip, so recorded
as license-unverified-beyond-purchase — analyzed, never redistributed.

## What was rebuilt

The old module was 8 of 15 sounds, level-only macros, no MAX_VOICES, no
chokes. Now: **all fifteen ROM sounds on the hardware's ten channels**,
fixed-circuit architecture (11 residents, under the 13 ceiling), the
hardware's channel sharing modeled as itself — rimshot/cowbell one channel
(waveform swapped in place, assignability verified on all runtimes),
clap/tambourine one channel, open/closed hat one channel choking by
retrigger. Macros grew 8 → 13, every new one a real per-channel level
fader; `Overall Decay` and `Master Tune` stay as calibration globals.
New NOTE_MAP entries follow sibling conventions (rim 37, clap 39, cowbell
56, ride 51) and GM's 54 for tambourine.

## Criteria

**26/26 rows pass** against the BØLT clean captures (tau ±30%, centroid
±25%, tonal f_early ±15%) — every voice's decay constant, spectral center,
and settled pitch measured within tolerance of its reference file,
including both kick variants and both snares. The 6-bit/low-rate ROM
texture itself is unmodeled, as the dossier stated.

## Verification

83 unit tests, validate_api (NOTE_MAP and macro growth included), flake8:
green. Parity: tr707 and tr909 fail their own goldens (both deliberate,
awaiting the batch blessing); tr808's blessed golden and the other seven
hold. Cross-interpreter: all 15 one-shots byte-identical CPython/
MicroPython. Kit residency: 11.

## Listening

`phrase_OLD.wav` / `phrase_NEW.wav` under
`.reference-captures/tr707/renders/ab/`, plus the BØLT originals beside
them in `.reference-captures/tr707/bolt/`.

**Awaiting the batch listen:** `APPROVE ACCURACY tr707`
