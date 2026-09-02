# Phase 1 close-out — the ten drum machines

**Closed 2026-09-02.** Approved by Brad: *"Let's wrap up phase one where it
stands and move on to phase 2."*

## What was actually achieved

All ten drum machines rebuilt against named references, with a dossier each
recording sources, licences and per-voice acceptance criteria. Three defects
found and fixed that the original modules carried:

| | before | after |
|---|---|---|
| cr78 snare | -46.7 LUFS against its own -21.1 kick — no audible backbeat | -23.0, peer field -19..-27 |
| tr808 hats | closed -42.7 / open -34.2, filtered into near-silence | -27.5 / -19.0, reference -26.8 / -15.9 |
| tr808 cymbal | 1.4% of power at 2-4 kHz, reference 31.3% — all sizzle, no clang | 31.3%, exact |

And one defect in the core, found through them: audioif's CPython target baked
a note's envelope in at press time, so any circuit shared by two voices with
different decays swapped them. A closed hat struck after an open one rang for
the open hat's full decay in **eight of ten kits** — tr707 worst at 747 ms
where 64 ms was correct. Fixed in audioif `d84470a`; MicroPython and the
CircuitPython oracle were always right.

## What we did NOT establish

**Whether the kits are accurate.** Brad's verdict: *"I didn't hear anything I
didn't like, but it's difficult for me to say if they are right, particularly
the tonal sounds... Have we hit the bar we were shooting for? I don't know,
but we're not done trying."* That is the honest state of the program, and it
should not be written up as anything stronger.

Three reasons, all recorded rather than argued away:

1. **Tonal voices are unjudgeable by ear in the current material.** A cowbell,
   clave, conga and rimshot in a phrase are four pitched blips with no way to
   tell which fired. This made `linndrum` and `dmx` the *hardest* kits to
   judge despite being among the better ones. Issue #15 is the fix: drive the
   kits from a DAW through micropython-vst3 so hits are visible against the
   piano roll.
2. **The analog machines have no acoustic referent.** For a sampled acoustic
   kit the ear knows what a snare should be. For a TR-808 there is no original
   to compare against, only a record collection.
3. **Coverage is thin where evidence is thin.** cr78 has measured references
   for 2 of its 14 voices, both hats; eleven voices carry the module's own
   prior values forward. That is recorded in its dossier and was never claimed
   otherwise.

## Standing caveats

- **The blessing predates two fixes.** Phase 1 was listened to and approved on
  a floor before the envelope fix and before the cymbal revoicing (#14).
- **The overlap gate measures decay only.** It cannot see a wrong attack or
  sustain level, and three pairs escape it for documented reasons.
- **The gate covers the ten drums.** The 43 melodic instruments are immune by
  construction — verified, every one builds a fresh Note per press — but a
  future instrument adopting the shared-circuit idiom would be ungated.
- **tr808's cymbal now fails its f_early row** (5531 Hz against a 5814 floor).
  Traded deliberately: that number is a marginal argmax that flips on nothing,
  and the 2-4 kHz band share is what actually caught the fault. The dossier
  proposes replacing the criterion.

## Release

Brad's instinct, recorded and **not acted on** — versions are his call:
*"this is what we release in the next patch or maybe even minor release, and
we revisit it again under different test conditions before releasing 1.0. We
have a significant improvement over the originals, so we're making progress."*

## Carried into Phase 2

- #15, the DAW listening rig — **more urgent for Phase 2 than for drums**, since
  the electromechanical pianos are tonal end to end.
- `docs/phase2-listening-guide.md`, written because Brad said plainly he did
  not know what to listen for on these instruments.
- The gate pattern itself: make the fault mechanical wherever it can be
  measured, and spend the ear only on what genuinely needs it.
