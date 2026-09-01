# Phase 1 remainder — Station C Evidence Pack (six instruments)

**Dossiers:** [simmons_sdsv](simmons_sdsv.md) · [cr78](cr78.md) ·
[tr606](tr606.md) · [linndrum](linndrum.md) · [dmx](dmx.md) ·
[drumtraks](drumtraks.md). Built unattended under operating mode v2;
parked for the **phase batch listen** — one phrase per instrument.
All six: fixed-circuit architecture, byte-identical one-shots on
CPython/MicroPython, structural suite green (83 tests, validate_api,
flake8), and only the six own-goldens fail parity — the four blessed
drums held throughout.

## simmons_sdsv (gold)
**7/7 measured rows pass first render** plus CH≪OH choke, the ≥860 Hz
Hi-Tom reach, and 12-resident architecture. BD gained the noise layer
the hardware's uniform module demands; tom pitch ranges retuned onto the
measured 160–860 Hz span (the old ranges topped at 220 with two of three
reference toms above them entirely); ride/pedal-cymbal/fallback dispatch
dropped (no circuits behind them). Deviation: the shared tom noise+click
voice is the dossier's flagged budget trade, kept.

## cr78 (literature; 2-voice capture leg)
The centerpiece: 13 single-Note circuits **plus the hardware's own
4-voice arbiter** — verified live: six distinct triggers settle at
exactly 4 sounding, and same-circuit retriggers never steal
(`MAX_VOICES=5` per the dossier's hand-traced off-by-one). Measured
CH/OH rows all pass after the band-pass fix (the tr909 hat lesson).
Guiro's five staggered notes became one RATCHET-LFO voice; snare is one
resonant-noise voice with Snappy as Q (both flagged trades, fallbacks
stated in the dossier).

## tr606 (literature)
The sourced circuit map, built: BD is two oscillators summed; **the toms
now choke** (one shared ENV/VCA circuit — the schematic said so, the old
code let them ring together: verified, HT truncates LT at 3500× band
dominance); cymbal is two parallel chains at the fixed 7100/3440 Hz
bridged-T centers; 8 residents on the hardware's 5 circuit-groups —
the lightest build of the family. Macro surface: "Cym Tone" (a fixed
bridged-T on hardware, not a knob) swapped for the panel's missing
**Tom Level**; OH-decay-follows-tempo recorded as a stated divergence.

## linndrum (literature; strong-provenance 1996 capture measured)
15-circuit machine rebuilt at the 13 ceiling: **Crash and Ride are
separate circuits again** (the old file conflated them), congas and
cabasa/tambourine share as flagged budget folds, hats share by the
hardware's own one-loop-two-envelopes design. The macro surface was
rebalanced to the real panel: level knobs for every voice, tune only
where the hardware had tune pots; the mislabeled "Cowbell" pitch macro
became a real level control with pitch fixed at the measured 506 Hz;
BD decay corrected from 350 ms to the measured ~26 ms tau. 23/26
naive rows pass; BD and Ride pass under the fair (trimmed) ruler;
**clap parks at 1.42× bright — named residual, single-biquad skirt
floor.**

## dmx (literature)
The 8-voice-card architecture, built: sounds sharing a card choke
(cymbal's Ride/Crash Dual share is manual-quoted; tom and perc pairings
are the dossier's flagged low-confidence groupings). 11 residents; the
existing crush-noise DMX character preserved; the clap's three staggered
notes became one flutter-LFO voice on its shared card; cowbell's pair
lives in one two-partial table. Macros unchanged per the dossier.

## drumtraks (literature; one measured clap)
Macro surface grew 8→16 onto the machine's defining feature (per-voice
programmable tune AND level, as Tune/Level pairs per family); five new
voices (rim, clap, tambourine, cowbell, cabasa, plus the Crash/Ride
split) with repitch coupling on every tuned voice; "Crunch" rebound to a
bandwidth ceiling. 13 residents — **the dossier's own table summed to 13
though it claimed 12; 13 is at the ceiling and stands, correction
noted.** Clap tau passes its measured row; **clap centroid parks at
1.44× — the same named single-biquad residual as linndrum's.**

## Listening
`.reference-captures/phase1-ab/<name>_{OLD,NEW}.wav` — the same two-bar
phrase either side, all six. Reference originals live under each
instrument's `.reference-captures/` dir and `~/SamplesFromMars`.

**Awaiting the phase batch listen:**
`APPROVE ACCURACY simmons_sdsv` · `cr78` · `tr606` · `linndrum` ·
`dmx` · `drumtraks`
