# Changelog

All notable changes to `audioinstruments` and `audioeffects` are recorded
here. The two packages version and release together, from this repository;
[audioif](https://github.com/PyDevices/audioif) publishes the core only.
Releases up to and including audioif's v0.1.1 shipped both packages from
there, and are recorded in its changelog.

## Unreleased

### Changed

- **Phase 2 round-5 gate audit.** All sixteen classes through and in
  `rebuilt.ADOPTED`. `Limiter` clears G3 (`SlowAttack` at Lookahead 0)
  and G9 (3.01 dB surrender in the same words; +2.22 labelled True Peak
  on / Lookahead 0). Phase 2's class-gate bar is met.
  `docs/effects-phase2-gate-audit-round5.md`.
- **`Limiter` L1's plant at Lookahead 0 is `SlowAttack`**, not the catch
  stage. `NoCatchStage` is silent at the default because the shape stage
  already applies its zero-attack brickwall to the current sample; it
  still guards L2/L3 from 2 ms up. `SlowAttack` fires +12.000 dB at
  Lookahead 0 on the default patch at 48000 / 44100 / 22050 Hz; 108
  surface positions cannot restore a zero-attack envelope. Class DSP
  unchanged. The default's surrendered true-peak overshoot is stated as
  **3.01 dB** (worst-phase f_s/4 into −6 dBFS, those three rates) in the
  L1 row, pack summary, dossier §3/§8, docstring and catalogue; catalogue
  **+2.22 dB TP** is labelled True Peak on / Lookahead 0.
- **Phase 2 round-4 gate audit.** Fifteen classes through and in
  `rebuilt.ADOPTED`. `Limiter` stays parked (new L1's plant silent at
  Lookahead 0; pack silent on the +3.01 dB TP the sample-peak default
  surrenders). `docs/effects-phase2-gate-audit-round4.md`.
- **`GraphicEQ` T2's planted fault is `InvertedQGraphicEQ`**, not macro 13.
  The old plant — Constant Q on — is a shipped toggle
  (`fault_reachability` → `FaultReachable` at grid 64). The replacement
  writes the reciprocal of the proportional-Q factor, fires on all nine
  bells at 48 / 44.1 / 22.05 kHz, and 244 surface positions cannot restore
  the narrowing. Class unchanged.
- **Phase 2 round-3 gate audit.** Thirteen classes through and in
  `rebuilt.ADOPTED`. Three stay parked: `Limiter` (redefinition missing
  the independent pass on re-frozen L1), `GraphicEQ` (T2's fault is
  shipped macro 13), `CombFilter` (TAIL above Feedback 0.5 still a parked
  oscillation). `docs/effects-phase2-gate-audit-round3.md`.
- **`Compressor` F2 is demonstrated at Threshold −8 dB and below**, not
  below −4.2 dB: at −7 dB the 20:1 knee widens (12.0 / 8.5 / 6.5 / 10.5).
  Patch 14 `Compressor - lean` drops the idle slow stage from the pull
  chain and measures **13.6 % P4 / 24.2 % S3** against the frozen 19 % /
  36 % pair (working `@13` is still 22.0 / 40.9).
- **`Limiter` is redefined** (vision §7.2): working *Loud* is two bare
  `Dynamics` stages (sample-peak brickwall, True Peak off). Measured
  13.8 % P4 / 27.6 % S3 against the new 15 % / 29 % pair; rt 4.90 / 2.65.
  The historical ITU Loud setting is patch 5 *Loud (True Peak)*, P4 only
  (S3 rt 0.80).
- **`LadderFilter`'s T4(a) faults now fire**, and its Tier 3 pair is the
  palette OS2 row (17 % / 28 %), not the instruction-count 8 / 14. Working
  patch 4 measures 16.2 % P4 / 26.7 % S3; lean patch 6 is 8.6 / 14.7. T5
  and T1's stopband slope stay disconfirmed.
- **`CombFilter`'s parked residue is named** (17.4 cents sharp at 1760 Hz /
  Feedback 0.8), T3 carries a +6 cent bias that fires at 110 Hz, STATE is
  green on all three interpreters at three rates stereo and mono, and the
  palette pair is 8 % / 13 % (measured 6.9 / 12.0 at patch 0).
- **`DynamicEQ`'s T3 fault is now the idle band voice**, not a threshold
  lift. T2/T5 stay bounded by attack and T4/T6's out-of-band clause by Q.
  The listed-remainder pair is 17 % / 29 % (`Splitter` taps=3 is a palette
  gap); patch 0 measures 14.5 % P4 / 26.0 % S3.
- **Phase 2 fix-round gate audit.** Five classes through
  (`Expander`, `MultibandCompressor`, `LowPass`, `HighPass`, `Notch`) and
  added to `rebuilt.ADOPTED` beside `NoiseGate`. Seven on the branch stay
  parked (Limiter, Compressor, DeEsser, TransientShaper, ParametricEQ,
  GraphicEQ, BandPass) and the three that never started stay parked as the
  first audit left them. `docs/effects-phase2-gate-audit-fixround.md`.
- **`Compressor`'s Phase 2 gate cells worked** (the class gate's fixer pass,
  2026-09-07). The class itself changed in one place — its docstring — and
  now says where it is *not* clean: at 10 dB of gain reduction on a 50 Hz
  tone it reads 3.89 % THD with Release at its fastest against a 0.5 % bar,
  three of its four 1176 patches are over that bar at 50 Hz beside the
  all-buttons-in one, and patch 0's own defaults read 0.83 % there; the
  true-RMS detector is
  level-honest only above about 65 Hz at the shipped 10 ms window. Both
  bounds are in the catalogue row too. Traits F5, V6 and V3 stay
  *disconfirmed* with those numbers, M3 moves from *unmeasured* to
  *disconfirmed* (its two program-dependent Vari-Mu patches read 0.99 and
  0.93 against a bar of 3, at trains up to 12 s), and the tally is 6
  demonstrated / 13 disconfirmed / 2 unmeasured. Tier 1's two open rows are
  measured on all three interpreters — allocation flat inside the kit's
  8192-byte bar in all eighteen cells, `deinit()` 5 of 5 owned nodes
  released — and the three planted faults the gate audit sent back are
  replanted so that they fire and the surface cannot dial them.
  `docs/effects/Compressor-evidence.md`. Two audioif issues came out of it:
  **audioif#58** (`audioroute.Splitter` has no `deinit()`) and
  **audioif#59** (the native builds have no deinitialised guard; pulling a
  released `audiomixer.Mixer` dumps core).
- **`Limiter`'s true-peak ceiling now needs lookahead, and gets it.** The
  Phase 2 gate audit parked the class on a broken promise: at a -6 dBFS
  ceiling with True Peak on, `ramp_fs` escaped by **+2.22 dB TP** and
  `dc_step` by +1.12 (audit §4.1, audiocomponents#38). The cause is the
  node's own detector - a 12-tap polyphase window names an inter-sample peak
  about five and a half samples after it happened, so a gain computed from it
  needs audio behind it to act on. The class now moves the last
  `TRUE_PEAK_RESERVE_SAMPLES` (12) of whatever the Lookahead macro asks for
  from the shape stage to the catch stage whenever True Peak is on; the two
  delays sum to the macro's own number, so `latency_samples` does not move
  and L4 and L5 are untouched. The catch stage's release is stretched with
  the reserve (`_CATCH_SAG_DB`), because a delay in front of a releasing
  detector is a peak that arrives after the gain has begun coming back: at
  the unstretched 5 ms it costs **+0.344 dB** of L3's +0.100 bar on an
  impulse, and at the stretched release +0.039. Measured over the whole committed corpus - 65
  probes at 48 kHz and 44.1 kHz, Lookahead 0.25, 1.5 and 10 ms - the worst
  escape is **+0.22 dB** against a 0.50 bar, with **no red probe**; at
  Lookahead **0** it is unchanged at +2.22 dB and is now stated as a bound in
  the docstring and the catalogue row, because an inter-sample peak cannot be
  caught with no delay to catch it in. Every factory patch that turns True
  Peak on already asks for lookahead. Evidence:
  `docs/effects/Limiter-evidence.md` L1.
- **`Limiter`'s L6 and L7 readings can now fail.** L6's slope clause read
  -0.00000 dB/dB on a build with no compression at all and its knee width
  moved 0.000 -> 7.900 dB with the measurement grid (gate audit §3, G3); it
  is now one CURVE fit of the whole law, judged on the ratio and the knee
  together, which goes red on the class built as a wire (ratio 1.0034), red
  on a finite-ratio build in **both** stages, and red on a knee forced open
  with the macro at 0 - and it does not move between a 0.25 dB and a 0.05 dB
  grid. L7's second clause - "or a docstring that does not name the trade" -
  had no check and no fault; it now re-measures the two figures the docstring
  names and goes red when either drifts by 0.5 %.
- **`tools/measure_effect_cost.py` can name a rebuilt class and a patch**:
  `rebuilt:<Name>` builds the Phase 2 class whether or not it is adopted —
  `effect:<Name>` goes through the registry and serves the *old* class for
  the fifteen parked ones — and `@<patch>` applies a patch, so a board
  figure can be taken in the state its evidence pack names rather than at
  construction defaults. A class whose construction defaults are a bypass -
  four of Phase 2's sixteen - otherwise renders the bare probe's own digest,
  and its board figure checks nothing about its audio
  (`docs/effects-phase2-pattern-revision.md` §1.4).
- **`Expander`'s gate-audit cells closed, and one bounded rather than
  claimed** (`effects/p2b-expander`). G3: both planted faults replaced with
  ones the macro surface cannot dial — the old depth fault *was* macro 2
  `Depth` at grid position 0, and the old ratio multiplier read the identical
  slope 8.0817 (+1.02 %) at the top of the span — and every row re-measured
  over the span it quantifies over rather than at a chosen point. G2: the nine
  Tier 1 cells that carried `n/a` now run on MicroPython and CircuitPython at
  all three rates, stereo and mono, `0 failures` on all three. G6: patch 6
  `Expander - lean` added and measured, and it does **not** close the item —
  the only cost lever the macro surface has is worth 5–8 % where the budget
  needs 26–29 %. **`Expander.PATCHES` gains patch 6** and the class docstring
  and catalogue row gain E1's detector bound: the ratio law is the RMS
  detector's, and at the peak position the slope falls 7.5 % short at ratio 8
  and 29 % at patch 5's own settings (audiocomponents#50). The DSP is
  unchanged. `tools/measure_effect_cost.py` gains two additive target
  suffixes, `#<patch>` and `@rebuilt`, without which a cost run for a parked
  class silently measures the old one.
- **`DeEsser`'s gate-audit cells closed or answered, and the class's DSP not
  touched.** The 22.05 kHz leg G2 named is run: 24 renders — four invariants'
  probes at three rates, stereo and mono, on all three interpreters — and all
  24 agree, with the six WIRE rows equal to their own source digest. Two
  readings that could not fail were rebuilt: D2's corner tracking is now a
  frequency solved out of the detector band's shape (worst −0.86 % over the
  whole Frequency macro, against a 5 % bar) rather than a level read off a
  crossover sum that is flat at every corner, and D4's release rate is
  asserted against the 902's 925 dB/sec instead of printed. Four traits are
  swept over the spans they quantify over, and the sweeps bound two of them
  honestly: level independence holds from −6 to −40 dBFS and not at −55, and
  the 925 dB/sec is the default `Release`'s — the macro dials it from 1643
  down to 20. The refutation record's open question on `Range` is answered by
  measurement: the dry blend alone, with the gain cell muted, reads further
  past the ceiling than the class does, so the excess is int16 truncation.
  On cost, the gate's `" - lean"` escape is exercised rather than left owed —
  all six patches cost the same to the runner's own noise, because a patch
  here is seven macro positions and the cost is the graph — and the leanest
  graph the dossier allows is 2.93× cheaper and still misses both budgets, so
  the class stays parked on G6 for the auditor to rule on the budget.
- **A parked class can be rendered and costed by name.** `create()` serves the
  old class for every name outside `rebuilt.ADOPTED`, so
  `render_effect.py DeEsser` and `measure_effect_cost.py effect:DeEsser`
  measured `dynamics.DeEsser` and printed the rebuilt one's name over the
  figure. The renderer takes `--rebuilt` and the cost runner takes
  `rebuilt:<Name>`, which resolve through `rebuilt.module_class()`; the cost
  runner also takes `@<patch index>`, because the gate's escape from an
  overrun budget is a patch and it could only measure construction defaults.
- **`TransientShaper`'s gate-audit fix round** (effects program, Phase 2).
  The class's DSP is unchanged — it is parked for coverage and budget, not
  for a defect at a reachable setting. Its whole Tier 1 block, including the
  four STATE rows that had run on CPython at 48 kHz only, now runs on all
  three interpreters at 48 / 44.1 / 22.05 kHz, stereo and mono, with five
  planted faults riding along
  (`tools/phase2_probes/transientshaper_tier1_portable.py`, 0 failures on
  each). The board digest it had was the bare probe's, so the desktop digest
  at a patch where the class works is recorded instead
  (`a7f7c4de0042a7cd`, patch 1 `Snap`, all three interpreters) and
  `tools/measure_effect_cost.py` gained `effect:<Name>@<patch>`,
  `rebuilt:<Name>[@<patch>]` and a `BYPASS` line so a figure taken on a wire
  says so. **No `" - lean"` patch can fit and that is now measured**: every
  shipped patch costs 102–106 % of patch 0, the only cheaper configuration
  that still processes is 89 %, and a node of this kind doing nothing at all
  still costs 75 %, against a budget needing 66–68 % off. The docstring and
  the catalogue row carry T1's and T3's bounded claims and T4's unmeasured
  peak-hold clause. Evidence:
  `docs/effects/TransientShaper-evidence.md`.
- **`MultibandCompressor`'s Phase 2 gate audit answered** (branch
  `effects/p2b-multibandcompressor`). Its M3 depth and evenness clauses were
  measured on a tone window an octave inside each band's corners — 1.3 of the
  mid band's 3.3 octaves — and the auditor widened it to the band's own
  passband and broke them. The class is **not changed**; the claim is bounded
  instead, which is what the audit offered. Read out to each band's own −6 dB
  corners at 200/2000 Hz and ratio 4, the reduction tilts **1.82 / 1.31 /
  1.42 dB** (low / mid / high) against a 0.5 dB bar and lands **0.09 / 0.73 /
  0.36 dB** short of the 12 dB dialled; swept over each band's Ratio macro it
  reaches **2.30 / 1.67 / 1.80 dB** at ratio 20, the macro's own top stop. It
  is the band's own LR4 skirt against a fixed threshold — `(1 − 1/ratio)`
  times the shortfall, exact to two decimals on the mid band — plus, on the
  low band alone, 0.24 dB from the RMS detector's 10 ms window below 50 Hz.
  Both numbers are now in the module docstring, the class docstring and the
  README catalogue row. `multiband_traits.py` measures the wide window and
  keeps the narrow one beside it as a control.
- **No `" - lean"` patch for `MultibandCompressor`, and the reason is
  measured rather than argued.** The class gate's G6 escape is a patch that
  fits the budget; `tools/phase2_probes/multiband_cost.py` walks all 243
  macro positions and shipped patches and finds the same **18 owned nodes and
  72 node pulls per eight blocks** at every one, so no patch can drop work
  from a block — with a planted fault (`MutingMix`, whose Mix 0 stops the
  voices) shown moving it. Measured on process CPU time, the class **fully
  bypassed at Mix 0 costs 102 % of what patch 0 costs**. `bands=2` is the
  only lever, a constructor option at 12 nodes and 48 pulls and 75–79 % of
  the three-band desktop cost, and it is unmeasured on either board. The
  class stays over budget on both.
- **`MultibandCompressor`'s Tier 1 and digest probes name the rebuilt
  class.** Both went through `audioeffects.create()`, which since the
  registry's adoption gate serves the *old* `dynamics.py` class for a parked
  rebuild: the Tier 1 run died on `TypeError: unexpected keyword argument
  'bands'` and the digest run would have hashed the wrong class. Re-run on
  all three interpreters: `0 failing invariants`, and the four probe digests
  unchanged. The same trap in `tools/measure_effect_cost.py` is
  audiocomponents#52.
- **`tools/phase2_probes/multiband_gate.py`** is new: the pattern revision's
  patch sweep, its macro sweeps, `kit_faults.null_build_red` on all five Tier
  2 measurements and `kit_faults.fault_reachability` on all five planted
  faults. Three of this class's five rows — flat sum, zero latency,
  byte-stable render — were green on a piece of wire and now carry the clause
  that says the render is not the source's bytes.
- **`ParametricEQ`'s gate-fix pass** (Phase 2 class gate, audit section 4.2).
  The class's DSP is unchanged; its docstring and its catalogue row now carry
  the bound the audit put on two traits — every section writes int16, so a
  +16 dB bell delivers +16.00 dB at −20 dBFS and +8.37 dB at −6 dBFS while
  the matching cut is untouched, and T3 and T5 are **disconfirmed above
  −16 dBFS**. The evidence pack is rewritten to the revised template: the
  shipped-patch sweep first, *Held fixed* and *Quantified over* per row, the
  independent refutation record inside section 1. T2's measurement, which the
  refutation pass showed green on a byte-flat wire, is replaced by one that
  is red there — a strict maximum with a 1.0 dB prominence bar and an
  interpolated peak — and T2's third clause and T4 get planted faults that
  the class's macro grid cannot dial. `tools/measure_effect_cost.py` and
  `tools/render_effect.py` take `rebuilt:<Name>` and a patch, and the cost
  runner now **refuses a render whose digest is the bare source's**, which is
  what four of Phase 2's sixteen board figures were. Evidence:
  `docs/effects/ParametricEQ-evidence.md`.
- **`LowPass`'s gate cells closed where they could be, and named where they
  could not** (effects program, Phase 2 fix round, branch
  `effects/p2b-lowpass`). The class is **not** changed. Four Tier 1 rows the
  pack carried as `n/a` on the native builds now run there as integers on all
  three interpreters at 48 / 44.1 / 22.05 kHz, stereo and mono, each with a
  planted fault that fires
  (`tools/phase2_probes/lowpass_tier1_portable.py`); one row is marked `n/a`
  with its cause instead of passed, because `audiobiquad.Biquad` has no
  `deinit()` on the native builds and the clean run and its fault read alike
  (audioif#63). The four disconfirmed traits are now stated in the class
  docstring and the README catalogue row, as a disconfirmed trait must be.
  **No `" - lean"` patch is possible** and the measurement says so: every
  section runs whatever its `mix` is, so the spread across every setting the
  surface can reach (0.0128 ms/block) is smaller than the run-to-run spread
  of one setting (`tools/phase2_probes/lowpass_cost.py`); the class stays
  parked on its budget, which is not moved. `tools/render_effect.py` and
  `tools/measure_effect_cost.py` take a `rebuilt:` target — without it a
  parked class's own digests do not reproduce — and the cost runner takes an
  `@<patch>` suffix, so a board run can be given the state a class's cost is
  about. `tools/phase2_probes/refute_harness/` had two defects of its own
  (audiocomponents#52), both fixed.

- **`HighPass`'s gate-audit fixes** (effects program, Phase 2). One number in
  the class moved: `TAIL_SAMPLES` 305 152 → **632 832**. The first
  declaration was taken from a 200 ms burst, and a high-pass's tail is its
  resonant pole ringing *down*, so the ceiling belongs to the state a
  full-scale tone **at** the corner drives it to — 627 267 samples at 10 Hz,
  Resonance 16, 24 dB/oct, +12 dB, the worst of 54 swept cells and at every
  span's own stop. The audit's own DC-step reproduction is green on it. The
  docstring and the README row now also carry two disconfirmations the audit
  and the patch sweep found and the class cannot fix: **the corner gain and
  the curve read true only above ω₀ = 5.2e-3** (40 Hz at 48 kHz) — below it
  `audiobiquad`'s `float` coefficient store loses `1 + a₁ + a₂ ≈ ω₀²`, 0.6 dB
  at a 10 Hz corner and 0.21 dB of shape at patch 0's own default — and **the
  corner rings 1.85× longer at 24 dB/oct** than `Resonance` says, which is the
  price of reading the same gain at both slopes. Nothing about the cut, the
  skirt or the exact zero at DC moves, and the class's rendered bytes are
  unchanged (`chord` at 48 kHz, patch 2: `8712fd99` before and after). Two
  Tier 1 rows that had never run now do, on all three interpreters at three
  rates and both channel counts: the tail against its declaration, and the
  no-allocation row (`gc.mem_alloc()` on the native builds). T3's Nyquist leg
  was green on a wire and is re-stated so a wire fails it. **No `" - lean"`
  patch exists** — `mix` 0 does not stop a biquad's recursion running
  (`audioif_filter_f32.c:216-241`), so the class stays parked on G6.
  Evidence: `docs/effects/HighPass-evidence.md`; new probes
  `tools/phase2_probes/highpass_sweep.py` and `highpass_cost.py`.
- **`BandPass`'s gate-audit fix round.** T1's "0 dB peak at every Q" is
  **bounded, not fixed**: it holds at every width above f0 100 Hz and at every
  centre up to Q 2, and misses in 11 of 56 measured cells below that, worst
  **-0.50 dB at the Frequency knob's bottom stop against the Width knob's
  top**. The cause is measured and is not this class - `audiobiquad`'s
  direct-form I recursion carries `float` state, and at w0 = 0.0026 rad its
  two feedback coefficients cancel to seven parts in a million; the same five
  coefficients through a `float64` recursion read -0.003 dB
  (PyDevices/audioif#64). The bound is in the class docstring and the README
  catalogue row, with what it sounds like. Two measurements that could not
  fail were replaced: T1's and T5's readings were both **green on a wire**,
  and T1's planted fault built an `audiobiquad.Biquad` outside the class so
  its red never passed through `BandPass`. New: the Tier 2 rows measured at
  all six shipped patches (T1, T3 and T5 green at every one; seven cells miss
  a T2 or T4 bar and all seven land within 0.005 dB of RBJ's closed form, so
  they are the prototype's), and a working-patch digest anchor for the board
  leg. `tools/render_effect.py` gains `--rebuilt`, without which it renders
  the *old* class for any rebuild the auditor has parked.

- **Phase 2's sixteen rebuilt classes measured on both boards** (ESP32-P4 on
  COM4, ESP32-S3 on COM49, firmware `v1.28.0-dirty on 2026-09-07`), with
  `tools/measure_effect_cost.py` at construction defaults, 256-frame stereo
  blocks at 48 kHz. Every class renders in real time on both boards
  (`MultibandCompressor` on the S3 is the edge, 4.910 ms of a 5.333 ms block)
  and **all sixteen render byte-identical audio on the two boards**. Twelve of
  the sixteen exceed their dossier's ESP32-S3 budget and are recorded as owing
  a `" - lean"` patch; none was invented. Nine differ from the desktop digest,
  and the cause is below the class — the integer-path nodes agree host to
  board, every float-path node differs. Figures in
  `docs/effects-cost-table.md` ("Phase 2 classes") and in §4 of each
  `docs/effects/<Class>-evidence.md`. `rebuilt/ladderfilter.py`'s docstring
  no longer says its cost is unmeasured on either board.
- **`Compressor` rebuilt from scratch** (effects program, Phase 2), against
  `docs/effects/Compressor.md`'s frozen trait table and on the Phase 2
  construction module. The four characters now differ in detector law,
  release law, ratio law and side-chain weighting rather than in three time
  constants: `fet` has both time knobs live and faster clockwise with the
  threshold rising with ratio, `optical` — the default — has **no working
  time knobs at all**, `vca` runs a true-RMS detector and a level-dependent
  attack, and `varimu`'s slope climbs with level with the six factory time
  constants as patches. Two `audiodynamics.Dynamics` in series carry the
  two-stage release with a memory; the surface is fourteen macros and
  fourteen patches; latency is zero at every setting. Portability tier
  **audioif**, `REQUIRES = ("audiodynamics", "audioroute")`. Evidence:
  `docs/effects/Compressor-evidence.md`.
- The kit's CURVE and paired-build fixtures name `character="fet"`
  explicitly: their subject is the textbook single-stage law, and
  `Compressor`'s default character is now the LA-2A.
- **`audioeffects.Limiter` rebuilt** on `_component.Component`, the first of
  the effects program's Phase 2 classes. It is two `audiodynamics.Dynamics` in
  series now: a shaping stage carrying the Knee, the Lookahead and a **4x
  polyphase true-peak detector**, and a catch stage that is the reason
  lookahead no longer overshoots — a 1 ms burst into a −12 dBFS ceiling used
  to come out **1.45 dB over** at 10 ms of lookahead and now sits on the
  ceiling at every setting. `latency_samples` finally reports the lookahead
  instead of a hardcoded zero; three of the old class's five patches were
  delaying the audio by up to 484 samples while claiming none. The surface
  gains **Gain** (drive into the ceiling) and **Knee**, and its Release
  default moves to 149 ms so the class's own THD bound is met. Its dossier is
  `docs/effects/Limiter.md` and its evidence pack is
  `docs/effects/Limiter-evidence.md`.
- **`Expander` rebuilt** on the effects program's construction module, as
  `lib/audioeffects/rebuilt/expander.py`; the old class stands untouched in
  `dynamics.py` until Phase 6 retires `_core`. It had no macros and no patch
  at all; it has nine macros and six patches now — Threshold, Ratio, Depth,
  Attack, Release, Key Low, Key High, Key Listen, Detector — a true-RMS
  detector, a two-ended 12 dB/octave key band, an external key input, and a
  Depth floor that reaches −80 dB where the old class was stuck at the node's
  −60 dB literal without saying so. Portability tier **audioif**
  (`audiodynamics`); `latency_samples` 0 with no look-ahead option at all.
  The dossier's Hold macro is deliberately absent: `hold_ms` does nothing in
  `DYN_EXPAND` and the reason is measured, not assumed
  (`docs/effects/Expander.md` §8.1, `docs/effects/Expander-evidence.md`).
- `NoiseGate` is rebuilt from scratch on the construction module, after the
  Drawmer DS201 (effects program, Phase 2). It gains the eight controls the
  DS201 has and the shipped class had none of: Threshold, Attack, **Hold**,
  Release, **Range**, a two-ended **key band** and **Key Listen**, with six
  named patches. Its closed state is now the Range you set - -15 dB, say,
  where the old class could only slam to -80 - and its law is a depth rather
  than the 8 dB-per-dB slope it inherited from the node's memoryless gain
  computer. `duck=True` builds the ducking version for voice-overs;
  `lookahead_ms` is off by default and is the class's only latency. The old
  class stands untouched in `lib/audioeffects/dynamics.py` beneath the
  registry.
  Evidence: `docs/effects/NoiseGate-evidence.md`.
- `tools/render_effect.py` takes `--option name=value`, so a render can
  reach a class's construction options - a duck graph and a look-ahead are
  build choices, not knobs.
- `DeEsser` is rebuilt on the effects program's Phase 1 palette and served
  from `lib/audioeffects/rebuilt/deesser.py`; the old class stands untouched
  beneath it. It is the dbx 902's mechanism now — the sibilant band's level
  compared with the programme's rather than with a threshold knob — so one
  setting works on a whisper and a belt: measured across the kit's four
  sibilant probes from -6 to -55 dBFS, the reduction spreads 0.772 dB where
  the class it replaces spent its whole range inside 14 dB. Seven macros
  (Frequency, Range, Sensitivity, Mode, Release, Attack, Listen) and six
  patches, where there were none; a broadband and an HF-only mode, where
  there was only broadband; and Range is a real maximum, where `ratio` was
  not. Portability tier **audioif** (`audiobiquad`, `audiodynamics`,
  `audioroute`), latency zero, and no option that adds any. Three traits the
  palette cannot reach are stated in its docstring rather than hidden: the
  release curves where the 902's is a straight line in dB, Range is an
  asymptote rather than a clamp, and the program-dependent attack does not
  reach the 902's ratio. Evidence:
  [`docs/effects/DeEsser.md`](docs/effects/DeEsser.md) and
  [`docs/effects/DeEsser-evidence.md`](docs/effects/DeEsser-evidence.md).
### Added

- `TransientShaper` rebuilt from scratch on the Phase 2 construction module
  (`lib/audioeffects/rebuilt/transientshaper.py`), the effects programme's
  first rebuilt class. SPL Transient Designer: Attack ±15 dB and Sustain
  ±24 dB acting **at the same time** on one `audiodynamics.Dynamics` node
  through Phase 1's `transient_dual`, a peak-hold sustain envelope through
  `slow_hold_ms`, an Output trim, an Attack Speed scaler and a Sustain Hold
  time — five macros and seven patches where the old class had none, and
  latency 0 samples at every setting. `docs/effects/TransientShaper.md`
  (traits frozen at Station A) and
  `docs/effects/TransientShaper-evidence.md` (the class gate's record) land
  with it. T6, the adaptive time constants both sources assert, is
  **disconfirmed** and said so in the docstring.
- **`audioeffects.MultibandCompressor` rebuilt** on `_component.Component`,
  one of the effects program's Phase 2 classes. The old class had **no macros
  and one empty patch**: crossovers, thresholds and ratios were
  constructor-only, attack and release were hardcoded, and there was no
  make-up, no output gain and no mix. It has **fourteen macros and five
  patches** now, and `Mix` at 0 is a **true bypass** — byte-identical to the
  source, which the summed bands can never be, because a Linkwitz-Riley
  network at unity is an all-pass and not a wire.
  Three changes under the surface. The crossover moved to
  **`audiobiquad.Biquad`**: on the ported `synthio.Biquad` cascade the old
  class held **2 LSB of DC for ever at a 100 Hz corner and 8 LSB at 40 Hz**,
  which is audioif#23 sitting in the one node a multiband cannot do without.
  The Splitter is fed through a **block-sized guard**, so a source that hands
  back more than 8192 frames in one call no longer loses the head of every
  buffer — the old class rendered **exact silence** from 16384-, 20000- and
  32768-frame sources on burst material. And the detectors are **RMS**, which
  is what RaneNote 155's Fig. 7 draws and what the node grew this cycle.
  Two bands or three is `bands=`, a **constructor option** rather than a knob:
  the Mixer pulls a voice at level 0 exactly as hard as one at unity, so a
  muted band is not a cheaper build. `bands=2` is four biquads and two
  detectors against three bands' eight and three.
  Measured: the bands sum flat to **+0.001 / −0.119 dB** from 30 Hz to 20 kHz
  at three bands and **±0.000 dB** at two; each crossover is **−6.06 dB at its
  corner on a 23.7 dB/octave skirt**; driving any band to 12 dB of reduction
  moves the others by **0.00 dB**; latency is **0 samples** at every setting.
  One dossier claim did not survive: the **low** band's own reduction tilts
  **0.73 dB across 30–100 Hz** against a 0.5 dB bar, which is its LR4 skirt
  near its corner plus the RMS detector's 10 ms window, and the class
  docstring carries the arithmetic. Its dossier is
  `docs/effects/MultibandCompressor.md` and its evidence pack is
  `docs/effects/MultibandCompressor-evidence.md`.
- `ParametricEQ` is rebuilt from scratch on `_component.Component` for the
  effects program's Phase 2 (`lib/audioeffects/rebuilt/parametriceq.py`;
  dossier `docs/effects/ParametricEQ.md`, evidence
  `docs/effects/ParametricEQ-evidence.md`). It is a Pultec EQP-1A bottom and
  resonant top with three API 550A proportional-Q bells between: sixteen
  macros in the panel's own units, seven patches, `capabilities = ()`, zero
  latency at every setting and rate. **Its portability tier is `audioif`** -
  eight `audiobiquad.Biquad` sections, whose float state lets a decaying tail
  reach exact zero where the ported `synthio.Biquad` parks on DC (audioif#23).
  The old class stays in `eq.py`, untouched, beneath the registry; its
  old-surface trait test in `tests/test_cpython_effects_dynamics_eq.py` is
  retired in the same commit and replaced by
  `tests/test_cpython_effects_parametriceq.py`.
- **`audioeffects.GraphicEQ` rebuilt from scratch** on the Phase 2
  construction module (`lib/audioeffects/rebuilt/graphiceq.py`), after the
  MXR M-108 Ten Band. Ten octave bands on the pedal's own centres from
  **31.25 Hz** (not the ISO series), a **shelf** on top rather than a tenth
  bell, and GAIN and VOLUME around the bank — fourteen macros and six named
  patches where the old class had **no surface at all**. Its bands now
  **widen as you back off**, measured at 1.780 octaves at +3 dB against
  0.716 at +12, where the old class was constant-Q by omission at Q 1.4; a
  `Constant Q` toggle makes the studio-graphic behaviour a choice instead of
  an accident. A band at its centre detent is a **wire byte for byte**, and
  patch 0 is byte-identical to the source. Bands above Nyquist **clamp and
  say so** (`clamped`, `built_centres`) instead of vanishing silently.
- **`GraphicEQ` moves to the `audioif` portability tier** (`audiobiquad`).
  On the ported `synthio.Biquad` it held **+7 LSB** after silence at
  31.25 Hz/+6 dB and +5 LSB with all ten bands engaged, for ever
  (audioif#23); on `audiobiquad`'s float sections the same settings reach
  exact zero. Twelve sections, `latency_samples` 0, `tail_samples` 465 ms.
  Costs about two thirds of an ESP32-S3's stereo block by arithmetic — not
  yet measured on a board.
- `GraphicEQ` can now be built with no `gains_db` at all (flat, and flat is a
  wire), so its entry in the test and renderer `EXTRA_ARGUMENTS` tables is
  gone. A short `gains_db` still sets the bottom of the bank, as before.
- `LowPass` is rebuilt from scratch on `_component.Component` for the effects
  program's Phase 2 (`lib/audioeffects/rebuilt/lowpass.py`; dossier
  `docs/effects/LowPass.md`, evidence `docs/effects/LowPass-evidence.md`).
  Where the old class had no macros at all, a frozen `q`, a hidden `mix` and
  a `set_frequency` that raised above Nyquist, this one has five macros -
  Frequency, Resonance, Slope, Mix, Trim - six patches, `capabilities = ()`,
  zero latency at every setting and rate, and a declared `tail_samples`.
  **Its portability tier is `audioif`** - three `audiobiquad.Biquad`
  sections, whose float state lets a decaying tail reach exact zero where the
  ported `synthio.Biquad` parks on 1 to 4 LSB of DC at exactly the corners a
  low-pass is for (audioif#23). The old class stays in `eq.py`, untouched,
  beneath the registry; its two old-surface trait tests in
  `tests/test_cpython_effects_dynamics_eq.py` are retired in the same commit
  and replaced by `tests/test_cpython_effects_lowpass.py`.
- `AirSpace` drives its tone filter's Frequency macro instead of calling
  `LowPass.set_frequency()`, which the rebuilt class does not have: hertz
  reach a component through its macro grid, which is what the contract has.
- **`audioeffects.HighPass` is rebuilt from scratch** for the effects
  program's Phase 2, against `docs/effects/HighPass.md`, as
  `lib/audioeffects/rebuilt/highpass.py` on the `_component` construction
  module. It gains the five-macro surface the old class did not have
  (Frequency 10 Hz - 20 kHz, Resonance Q 0.5 - 16, a 12/24 dB/oct Slope
  switch, Mix and a +/-12 dB Trim), six named patches, a declared
  `tail_samples` of 305 152 measured rather than assumed, and a `frequency`
  that clamps below Nyquist instead of raising.
- **`HighPass`'s portability tier moves to audioif** (`REQUIRES =
  ("audiobiquad",)`). Its three sections are `audiobiquad.Biquad`, whose
  float state reaches exact zero; the ported `synthio.Biquad` holds up to
  71 LSB of DC at a 10 Hz corner for ever (audioif#23), which is the Tier 1
  invariant failing at exactly the corners a low-cut is for. A stock
  CircuitPython board can no longer construct this class, where the old one
  ran there and quietly failed that invariant.
- `tests/test_rebuilt_registry.py` no longer asserts that every one of the 46
  names misses: it asserts that a name either misses and keeps its old class
  or resolves to a `Component` of that `NAME`, so no rebuild has to edit it.
- The `HighPass` leg of
  `test_cpython_effects_dynamics_eq.py::test_a_filter_sits_at_its_corner_across_the_whole_band`
  is retired above 20 kHz - outside the frozen span. Its replacement,
  `tests/test_cpython_effects_highpass.py::CornerTest`, walks the whole span
  at both slopes and at three rates.
- Phase 2 of the effects program: **`BandPass` rebuilt from scratch** on the
  component contract (`lib/audioeffects/rebuilt/bandpass.py`). It gains a
  four-macro surface where it had none — Frequency, Width, Slope and Mix —
  six patches, and a `tail_samples` computed from the build rather than left
  `None`, which for a resonator is 301 ms at the Sub Window patch and 3 ms at
  the default. Its portability tier moves from stock to **audioif**
  (`REQUIRES = ("audiobiquad",)`): on the ported Q15 biquad a low centre
  holds DC for ever (audioif#23), and on audioif's float-state node every
  setting the surface reaches settles to bit-exact zero. The old class stays
  in `eq.py` untouched; the registry adopts the rebuild by `NAME`. Dossier
  `docs/effects/BandPass.md`, evidence `docs/effects/BandPass-evidence.md` —
  the board leg is not taken and one trait, T4's `|H(f0/100)|` clause, is
  disconfirmed above about 2.5 kHz for a reason that is RBJ's closed form and
  not this class.
- `Notch` is rebuilt from scratch on `_component.Component` for the effects
  program's Phase 2 (`lib/audioeffects/rebuilt/notch.py`; dossier
  `docs/effects/Notch.md`, evidence `docs/effects/Notch-evidence.md`).
  Where the old class had no macros at all, no width knob, a hidden `mix`,
  no declared tail and a `set_frequency` that raised above Nyquist, this one
  has five macros — Frequency, Width, Harmonics, Depth, Trim — six patches,
  `capabilities = ()`, zero latency at every setting and rate, and a
  declared `tail_samples` measured at its own worst corner.
  **Its portability tier is `audioif`** — three `audiobiquad.Biquad`
  sections, whose float state lets a decaying tail reach exact zero where
  the ported `synthio.Biquad` parks on 2 LSB of DC at `Notch(60 Hz, q=8)`
  and 18 at `Notch(20 Hz, q=32)`, which are the settings a notch is most
  used at (audioif#23).
  **The trade that move costs, stated because a caller has to know it:** a
  `float` coefficient set cannot hold the notch's zeros exactly on the unit
  circle, so the rejection at the centre is a true null from 500 Hz up at
  Q ≤ 12 but −35.65 dB at 60 Hz Q 12 and −11.21 dB at 20 Hz Q 32, against
  −78.87 and −40.04 dB on the integer kernel it replaces. The dossier's T1 is
  recorded disconfirmed below about 250 Hz with that cause, and its §5
  carries the audioif node ask that would recover 17–36 dB of it.
  The old class stays in `eq.py`, untouched, beneath the registry.
- `LadderFilter` rebuilt on the component contract, as
  `lib/audioeffects/rebuilt/ladderfilter.py` — one `audioladder.Ladder`, so
  the class is **audioif tier** (`REQUIRES = ("audioladder",)`) and does not
  run on a stock CircuitPython board. It is a ladder now rather than four
  low-passes in a row: the passband droops as `Resonance` rises, it
  self-oscillates at the top of the knob at the cutoff, and `Drive` is the
  only warmth control, all three of which the old class could not do. Seven
  macros where it had none, seven patches where it had one, and
  `latency_samples` 0 at every setting with no latency-adding option.
  Evidence: `docs/effects/LadderFilter-evidence.md` — five traits
  demonstrated, five Tier 1 invariants green on three interpreters at three
  rates, nine planted faults all red, 48 renders byte-identical across
  CPython, MicroPython and the patched CircuitPython. **Cost is unmeasured on
  both boards.**
- `CombFilter` is rebuilt from scratch on `_component.Component` for the
  effects program's Phase 2 (`lib/audioeffects/rebuilt/combfilter.py`;
  dossier `docs/effects/CombFilter.md`, evidence
  `docs/effects/CombFilter-evidence.md`). **The old class did not tune.** It
  sat on `audiodelays.Echo`, which floors its line at the node's own buffer
  length, so every frequency from 47 to 880 Hz came out as the same 46.88 Hz
  comb - the frequency argument did nothing over almost the whole of its
  range. The rebuild sits on `audioecho.FeedbackDelay`, which reads its line
  with per-sample interpolation and tunes to 0.002 cents, and adds the
  surface the old class had none of: six macros - Frequency, Feedback, Mix,
  Tone, Trim, Glide - six patches, `capabilities = ()`, and zero latency at
  every setting and every rate. **Its portability tier is `audioif`**
  (`audioecho`, `audiobiquad`); there is no honest stock fallback, because
  even a 512-byte buffer floors the comb at 187.5 Hz.
  - Trim is **input** headroom, not make-up, and it runs to -18 dB: a comb's
    peak gain is `1/(1-Feedback)`, +26 dB at the top of the knob, and a trim
    behind the comb attenuates a signal that has already hit the rail.
  - Two things stated rather than hidden. The **negative comb** - peaks on
    the odd half-multiples, the hollow one - is not built: it composes out of
    nodes that exist, but only at seven nodes, three delay lines and a
    tuning-dependent 2M pre-delay, about four times the class's cost budget.
    And **above Feedback 0.5 the tail may never reach zero**: the node's line
    is int16 and `to_s16` rounds, so the loop can park on a limit cycle
    bounded by `floor(0.5/(1-g))`. Whether it does is decided by the tuning -
    at 1 kHz, where 48 000/f is a whole 48 frames, it parks on exactly that
    bound (10 LSB, -70.3 dBFS, at Feedback 0.95); at 438.3 Hz, half a sample
    off the grid, it reaches exact zero at every setting. `TAIL_SAMPLES` is
    `None` and `reset()` clears it.
  The old class stays in `eq.py`, untouched, beneath the registry; it had no
  macro surface and so no old-surface trait tests to retire, and
  `tests/test_cpython_effects_combfilter.py` is new.
- **`audioeffects.DynamicEQ` rebuilt** on `_component.Component`, one of the
  effects program's Phase 2 classes. The old class had **no macros at all**
  on the processor with the most to expose: frequency, Q, threshold and ratio
  were constructor-only, attack and release were hardcoded at 2 ms and 80 ms,
  and there was no range, no direction and no way to move the band once it was
  built. It has **eight macros and six patches** now, every one of them live.
  Three changes under the surface. The split moved to **`audiobiquad.Biquad`**,
  which takes the idle reconstruction from 0.015 dB to **0.0000 dB** from
  100 Hz to 12 kHz and takes a low band's held DC to **0 LSB** at 60, 80, 120,
  400 and 3000 Hz - on the Q12 ported biquad the same 60 Hz section holds
  2 LSB for ever, which is audioif#23. The Splitter is fed through a
  **block-sized guard**, so an impulse inside a 40000-frame source no longer
  vanishes (measured: guarded peak 20000, unguarded peak 0), and renders are
  byte-identical at 256, 8192, 16384, 20000 and 32768 frames. And the class
  **does not end in its Mixer**: upstream CircuitPython's `Mixer.reset_buffer`
  stops every voice permanently, and anything upstream resets what it is
  handed - so an `audioroute.MidSide` identity carries the output, without
  which every kit render on `cmods/bin/circuitpython-effects` came back
  silent.
  **`Mix` is the Range control**, and that is arithmetic rather than a saving:
  with `H_notch + H_bandpass` identically 1 the whole class is
  `1 + m*B*(g - 1)`, so a dry/wet blend and a ceiling on how far the band may
  move are the same number. Measured against that closed form at six blends,
  worst **0.0035 dB**, with a tone two octaves away moving **0.0006 dB**
  across the sweep. `Mix` 0 is a byte-identical bypass; `range_db` reports
  `-20 log10(1 - Mix)`.
  `expand=True` is a **constructor option** rather than a knob, because
  `audiodynamics` fixes its mode at construction and a second, idle detector
  would cost a full block every block. Neither direction boosts.
  **It costs more than the class it replaces**: about 45 % more per 256-frame
  block on the desktop (1.46-1.56 ms against 1.10-1.15, five interleaved
  repeats of each), which is the price of the guard, the dry tap and the
  identity tail. No board figure has been taken.
  Measured: the composite follows the node's gain law within **0.42 dB** over
  five levels; the bell matches the closed form built from the band-pass's own
  response within **0.03 dB** everywhere but the centre; a tone two octaves
  out moves **0.055 dB** between idle and 19 dB of reduction; latency is
  **0 samples** at 48 kHz and 44.1 kHz and no option can add any. One seed
  claim did not survive: the 0.42 dB by which the centre sits above the law is
  **not** the notch branch leaking - that branch measures exactly zero at f0 -
  it is the detector's finite attack, and it moves with attack time and with
  frequency. Its dossier is `docs/effects/DynamicEQ.md` and its evidence pack
  is `docs/effects/DynamicEQ-evidence.md`.

### Fixed

- `tests/parity/effects_library_smoke.py` walked one instance through all of
  a class's patches on a **4096-frame** probe and pulled eight output blocks
  per patch, so a class whose output block is the contract's own 256 frames
  used the whole probe on its first two patches and read as **silent** for the
  rest. The probe is 8000 frames now - under `audioroute.Splitter`'s
  8192-frame ring, so no unguarded Splitter class in the catalogue changes -
  and one patch may pull at most 1024 frames off it, which leaves room for
  seven patches and puts every class on the same budget.

## v0.2.0 (2026-09-03)

The first release from this repository. These packages continue a version
history begun in audioif, which published them up to 0.1.1 — that is why
the first release from this repository is 0.2.0.

### Added

- Publishing. `pydevices-audioinstruments` and `pydevices-audioeffects` build,
  publish to TestPyPI and request their MIP index entries from here
  (`prepare-release.yml`, `tag-release.yml`, `publish-release-packages.yml`),
  with `project.urls` pointing here. The two MIP entries ride on one call
  (`mip-profile: audioinstruments,audioeffects`).
- Seeded from audioif at `v0.1.1` (`eefc673`) with the components' own commit
  history preserved: `lib/audioinstruments/`, `lib/audioeffects/`, their
  tests, the two validators, the component API and metadata documents, and
  the instrument parity harness with its goldens.
- `AUDIOIF_PIN`, naming the audioif release every gate runs against.

### Changed

- Phase 1 of the accuracy program: the ten drum machines — `cr78`, `dmx`,
  `drumtraks`, `linndrum`, `simmons_sdsv`, `sp1200`, `tr606`, `tr707`,
  `tr808`, `tr909` — rebuilt as fixed circuits against named references, each
  with a dossier, and blessed at the phase batch listen on 2026-09-02. They
  sound different from audioif's v0.1.1 copies on purpose: the cr78 snare had
  no audible backbeat, the tr808 hats were filtered into near-silence and its
  cymbal was all sizzle and no clang. `docs/phase1-closeout.md` records what
  was and was not established.
- `pydevices-audioif>=0.1.1` is a real dependency floor in both
  `pyproject.toml`s (it was unbounded). The gates still run against the exact
  commit in `AUDIOIF_PIN`, which may sit ahead of the floor.
