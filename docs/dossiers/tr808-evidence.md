# tr808 — Station C Evidence Pack

**Dossier:** [tr808.md](tr808.md) (Gate A approved 2026-09-01).
**Status:** presented for **Gate B** — `APPROVE ACCURACY tr808`.
**Method:** every number below computed by `tools/measure_hits.py` and
`tools/render_component.py` — the same code that proposed the criteria.
Reference numbers are the MusicRadar cross-check pack (219 hits), per the
dossier's acquisition note; the Splice oracle's WAVs still await the
account download and would re-verify, not re-derive, these targets.

## The criteria, measured

All 13 quantitative rows pass, plus both halves of the qualitative BD
pitch-trace row:

| Criterion | Target band | Before | After |
|---|---|---|---|
| BD settled fundamental | 40–66 Hz | 50.0 | **50.0** |
| BD pitch trace | jump ≥2× settled, then sigh | no jump (fall only) | **108.6 → 82.5 → 58.7 → 52.6 Hz: 2.07×, sighs home** |
| BD decay macro span (τ at 0/127) | ~0.02 … ~0.90 s | 0.03–0.6 | **0.014 – 1.042 s** |
| SD τ / centroid | 0.029–0.055 s / 3595–5393 Hz | 0.0385 / 5384 | **0.0357 / 4979** |
| CH τ / centroid | 0.017–0.031 / 7750–11624 | pass | **0.0177 / 8827** |
| OH τ | 0.121–0.225 | pass | **0.133** |
| Cymbal τ / f_early | 0.543–1.008 / 5814–9690 | **0.264 / 2695 (both MISS)** | **0.671 / 8098** |
| Cowbell f_early | 508–762 | **1184 (MISS)** | **621** |
| Toms pooled f_early | 90–168 | pass | **140.6** |
| Congas f_early | 181–335 | *(voice absent)* | **257.8** |
| Maracas τ / centroid | 0.023–0.043 / 6126–9190 | *(voice absent)* | **0.0302 / 9065** |

## What Station B found under the dossier

The dossier flagged "verify stealing under a dense pattern." Verification
found three stacked facts, each proven by probe:

1. **The synthio core caps at 14 simultaneous notes and silently retires
   the oldest** — identical on CPython, MicroPython, and the
   CircuitPython oracle (`s.pressed` = 14 on all three after 21 presses).
   Floor behavior, designed within.
2. **Releasing notes keep their core slots through the release tail**, and
   at the cap new presses evict *held* notes while tails occupy slots —
   so choke-by-release can never survive a same-block burst.
3. **The CPython extension mishandles an at-cap re-press**: it evicts a
   bystander and leaks a slot (count 14 → 13). CircuitPython and
   MicroPython retrigger in place. A core divergence from the oracle —
   filed as [audioif#8](https://github.com/PyDevices/audioif/issues/8);
   the design below no longer depends on it.

Under the old architecture the consequence was measurable: the bass drum's
40–60 Hz energy was **0.77** of total in a solo hit and **0.0006** in a
full-kit hit — the BD was stolen outright.

## The resolution: the hardware's own architecture

The rebuilt voice layer is **fixed circuits** — every voice a permanent
set of `synthio.Note` objects retriggered in place, exactly as the real
machine's 12 voltage-triggered circuits worked. Nothing allocates at
strike time; nothing is ever released during play; no tail ever occupies
a slot. The hardware's circuit sharing is modeled as itself: tom/conga,
claves/rimshot, maracas/clap, and open/closed hat each ride one circuit
and choke by retrigger. The whole kit resides at **13 notes** —
deliberately one below the core cap, so a retrigger stays below it on
every runtime.

Kit-survival probe after: **0.99** (BD band energy, kit vs solo).

## Deviations from the dossier, stated

- The dossier proposed congas/maracas as *dedicated branches*; they landed
  as *faces of shared circuits* (tom lines and the clap circuit), which is
  strictly closer to the hardware. The dossier's structure-freedom clause
  covers both.
- The cowbell's two oscillators now live in one wavetable (harmonics 2+3
  of a half-frequency fundamental), rounding the hardware's 1.48 ratio to
  1.50 — the price of the 13-note residency. Criterion passes at 621 Hz;
  the beat character is a hair cleaner than the real pair.
- The snare lost its second body partial (one core channel was not worth
  it); τ and centroid criteria still pass after rebalancing.
- The BD jump renders at control-rate resolution: synthio LFOs tick once
  per 256-sample block, advanced before sampling, so a literal 4 ms jump
  is unrenderable — `rate=45/scale=1.65` is the block-honest translation
  whose *audio* clears the octave (2.07× measured by zero-crossing trace).

## Cross-interpreter and parity

- All 16 one-shots render **byte-identical** on CPython and MicroPython
  (streamed sha256 per voice, `render_component.py` on both).
- Structural suite green: 83 unit tests, `validate_api` (53+46),
  effects smoke, flake8.
- Instrument parity: **tr808 fails its golden on both interpreters — the
  deliberate sound change this program exists to make — and the other
  nine drums hold theirs** (20 comparisons, only tr808's 2 fail). The
  golden is *not* re-captured here: that re-blessing is Gate B itself.

## Listening material (delivered with the gate ask)

`phrase_OLD.wav` / `phrase_NEW.wav` — the same two-bar groove either side
of the rebuild; `oneshot_BD_NEW.wav` — the rebuilt kick alone;
`reference_BD_long.wav` — a reference hit from the cross-check pack.
Local copies under `.reference-captures/tr808/renders/`.

**Awaiting Gate B:** `APPROVE ACCURACY tr808`
