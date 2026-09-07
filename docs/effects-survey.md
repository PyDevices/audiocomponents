# Effects Program — Phase 0 Survey (M0)

**Program:** the effects program (**`GO effects` GIVEN** — Brad, 2026-09-07 04:15 CDT) — [vision](https://github.com/PyDevices/workspace/blob/main/docs/effects-vision.md) and [roadmap](https://github.com/PyDevices/workspace/blob/main/docs/effects-roadmap.md) live in the anchor repo's `docs/`.
**Method:** 16 unit researchers writing one dossier seed per class; a licence-and-citation audit re-fetching every URL; a trait critic re-cutting every Tier 2 row; a palette verifier re-measuring every §4/§5 claim against the C and the CPython build; then a node pass that merged 51 raw asks into 28 candidates and gave **every candidate two independent refuters**. Every cited source was reached during the run; a failed fetch is recorded as not reached, never as evidence.
**Gate:** this document is Phase 0's deliverable (M0). There is no approval phrase to wait for: roadmap §2b says in terms that `GO effects` is this program's only phrase and that a phase closes when every item in its Gate is true and recorded. Phase 0 closes on that condition; Brad is told, not asked.
**Run date:** 2026-09-06 (research, audit, trait-critic and palette passes); the node-refutation, SPICE-transcription and kit-refutation passes carry 2026-09-07 where they say so. Assembled 2026-09-07.

---

## The headline numbers

| Grade | Count | Meaning (vision §4.1) |
|---|---|---|
| **circuit** | **10** | a schematic with values reached and read, plus a SPICE model or an analytic derivation of the traits from it |
| **literature** | **22** | no usable schematic, but a published model sufficient to fix the traits |
| **proxy** | **0** | no class ended up resting on an emulator's output |
| **design** | **14** | no historical standout; traits from the textbook definition |

Coverage: **46 of 46** classes seeded. **46 of 46 standouts confirmed, none swapped** — two of them (`ShimmerHall`, `AirSpace`) proposed with evidence where vision §4.2 left a dash.

| Traits | Count |
|---|---|
| Tier 2 traits fixed, all classes | **327** |
| Median per class | 6 |
| Range | 5 (`ParametricEQ`, `GraphicEQ`, `LadderFilter`, `Harmonizer`, `DigitalDelay`, `SlapbackDelay`, `PingPongDelay`, `MultiTapDelay`, `MultibandCompressor`, `LowPass`, `DynamicEQ`) — 21 (`Compressor`) |
| Non-design seeds fixing ≥ 3 Tier 2 traits (the gate's bar) | **32 of 32** |
| Design seeds carrying Tier 2 rows anyway (§4.1 asks only Tier 1 + Tier 3) | **14 of 14**, min 5 rows |

The 327 reconciles exactly against all sixteen units' own tallies, counted independently here by parsing each seed's Tier 2 table. **It also reconciles against the kit refuter's 332**, which was the count of *non-header table lines* rather than of traits. The five-line gap is exactly: **four character sub-header rows in `Reverb.md`** (`| **Plate** — … | | | | | |` and its `Spring`, `Hall / room / chamber` and `All tank characters` siblings), which carried a trait row's shape with five empty cells; and **one line that was not a table row at all** — a prose line in `RingMod.md` §5 that began with the absolute-value bar of `|3f₁ − f₂|`, which Markdown rendered as a stray row. Both are now fixed at the source: `Reverb`'s sub-headers are bold paragraphs between separate tables, and the `RingMod` line's maths is in backticks, so a parse of the corpus returns **327 in both counts**, with `Reverb` returning 10.

| Sources | Count |
|---|---|
| Reached (the run's own per-class tally, summed) | **200** |
| Recorded as **not reached** (dead link, 403, unreadable scan, TLS failure) | **109** |
| Labelled source rows carried in the seeds' §2, counted mechanically | **288** |

The per-class "reached" figure caps at five in the run's record, and **28 of 46 classes report exactly five** — `Compressor`'s §2 alone runs to S10, `Distortion`, `Flanger` and `Rotary` to S14. So **200 is a floor**, and 288 is the better measure of what the seeds actually carry.

| Node asks | Count |
|---|---|
| Raw asks written in the seeds' §5 | **51** |
| Merged into candidates for the refutation pass | **28** |
| **Survivors** | **23** |
| Refuted | **5** |
| **Unsettled** | **0** — candidate 7, the oversampled waveshaper, is ruled a **survivor** (Arthur, 2026-09-07); `Tremolo` B4 stays struck and the 7a re-file is absorbed back into it |
| Unrefuted (no refuter reached) | **0** — every candidate carried two votes; the drive-family claims the original pass never reached are carried on candidate 7 by the ruling, not as a candidate of their own |
| Distinct design sketches written (they are per-module, not per-candidate) | **10** |
| Asks killed inside the seeds by the palette-verification pass, before the node list | **25** |

---

## What Phase 0 did NOT close

Four items, each stated on its own line rather than inside a paragraph that ends "nothing else is pending".

1. ~~**The oversampled table waveshaper is UNSETTLED.**~~ **Ruled a SURVIVOR 2026-09-07 (Arthur).** Both refuters explicitly scoped their refutation to `Tremolo` B4 alone and said in terms that the drive family's claims are untouched: *"this refutes only the Tremolo B4 line ... Overdrive T7, Distortion A1/F3/SC2, Fuzz A4 and Saturation A4 are alias-floor claims that oversampling still owns"* and *"It says nothing about the Drive family's own claims."* They refute `Tremolo`'s **use** of the node, not the node: B4 stays struck, and candidate 7 survives on Overdrive T7, Distortion A1/F3/SC2, Fuzz A4 and Saturation A4. Its design sketch and cost estimate are now written ([`audioshaper.Waveshaper`](#audioshaperwaveshaper--oversampled-table-waveshaper-candidate-7)), candidate 8 is unblocked, and the 7a re-file is absorbed. **What is still open, on its own line: the audioif issue for candidates 7 and 8 is owed and unfiled**, because the ruling came after the eight issues went up; and the ×2/×4/×8 alias-floor table remains Phase 1's (§10.3). See [The waveshaper problem](#the-waveshaper-problem).
2. ~~**`docs/effects-survey-audit.md` does not exist.**~~ **Written 2026-09-07: [effects-survey-audit.md](effects-survey-audit.md).** The audit *work* was always done — 160 licence corrections, 160 trait rewrites and 158 palette corrections — and the report now assembles and lists them by class and by kind, without fetching anything. What stays open, and the report says so on its own line: **those three counts are floors and their true values are unrecoverable**, because the record caps each unit's list at ten and passes 1 and 2 hit 16 × 10 exactly. A genuinely independent re-audit is not scheduled and is not proposed.
3. **The length rule is applied but not met: 42 of 46 seeds are still over 12 KB.** Vision §7 says a dossier is "a five-minute read" and the Phase 0 brief fixes §§1–8 at 8–12 KB. Every seed's derivations, source excerpts, measurement notes, pass records and per-row prose have now been moved under its existing `## Appendix` heading, behind cell-level `App. <id>` references — nothing was deleted, and the corpus's §§1–8 fell from **1474 KB to 812 KB**, median **29.8 KB → 16.2 KB**, range **11.3 KB (`Notch`) to 29.7 KB (`Rotary`)**. Four are now inside the rule (`Notch`, `BandPass`, `LowPass`, `HighPass`); 16 sit at 12–16 KB, 13 at 16–20 KB, 13 above 20 KB. Each section that lost material carries a one-line pointer to `App. R`, so a reader of §§1–8 is never silently short of an argument. **The remainder cannot be moved without moving what the gate reads.** What is left in §§1–8 of a median seed is: the six header fields (~1.2 KB), §1's one paragraph (~2.2 KB), the Tier 2 table's trait statements, disconfirmations and measurement ids (~5.2 KB), §2's source ids, leads, URLs and reached / not-reached calls (~1.9 KB), and §6's macro table and patches (~1.5 KB) — about 12 KB before a single sentence of argument. A `Compressor` with 21 traits across four characters, or a `Rotary` whose Tier 2 table alone is 12.6 KB, cannot reach 12 KB while its traits stay where the gate looks for them. **Open, and owned by the implementation session:** either the rule's number moves for trait-dense classes, or trait statements move to the appendix too and §3 becomes an index. Phase 0 did not take that decision.
4. **Vision §10.3 (oversampling) and §10.8 (the latency target) are open.** Both are deferred to Phase 1 by four seeds each; see [Vision §10](#vision-10--the-open-questions).

---

## The map — all 46

Standout column: **C** = vision §4.2's proposal confirmed; **C+** = confirmed and pinned or sharpened beyond what §4.2 said; **P** = proposed with evidence where §4.2 left a dash. No class argued a swap.

Tier column: **stock** and **audioif** are roadmap §3's portability tiers; **cond.** means the tier follows a Gate 0 decision, stated both ways in the seed.

| Class | Standout | Grade | Best source reached | T2 | Surviving node asks | Tier | Seed |
|---|---|---|---|---|---|---|---|
| `Phaser` | MXR Phase 90 — **C** | circuit | [ElectroSmash, "MXR Phase 90 Analysis" (MAS mirror)](https://electrosmash.mas-effects.com/mxr-phase90.html) | 10 | DC-clean biquad + all-pass | **cond.** | [Phaser.md](effects/Phaser.md) |
| `Chorus` | EHX Small Clone (MN3007) — **C** | circuit | [Aion FX *Lithium Analog Chorus* build doc](https://aionfx.com/project/lithium-analog-chorus/) | 6 | `wow_shape` | audioif | [Chorus.md](effects/Chorus.md) |
| `Flanger` | EHX Electric Mistress, 1976 unit — **C+** | literature | [Raffel & Smith, DAFx-10, BBD modelling](https://www.dafx.de/paper-archive/2010/DAFx10/RaffelSmith_DAFx10_P42.pdf) | 8 | `wow_shape` | audioif | [Flanger.md](effects/Flanger.md) |
| `Tremolo` | Fender bias-vary (6G2) + optical (AB763) — **C+** | circuit | [Fender Princeton 6G2 schematic](https://schematicheaven.net/fenderamps/princeton_6g2_schem.pdf) | 13 | *(waveshaper — see item 1)* | audioif | [Tremolo.md](effects/Tremolo.md) |
| `Vibrato` | Boss VB-2 — **C** | circuit | [Boss VB-2 factory service schematic](https://www.synthxl.com/wp-content/uploads/2020/04/Boss-VB-2-Schematic.pdf) | 7 | `wow_shape` | audioif | [Vibrato.md](effects/Vibrato.md) |
| `Rotary` | Leslie 122 — **C** | literature | [Leslie 122 Installation Instructions Manual](https://www.manualslib.com/manual/4079586/Leslie-122.html) | 10 | delay slew; `wow_am_depth` | audioif | [Rotary.md](effects/Rotary.md) |
| `AutoPan` | — (design) — **C** | design | [CCRMA, "Multichannel Intensity Panning"](https://ccrma.stanford.edu/guides/planetccrma/Multichannel_Intensity_Pann.html) | 6 | none, by measurement | audioif | [AutoPan.md](effects/AutoPan.md) |
| `RingMod` | Bode / R.A. Moog 6401 diode ring — **C+** | literature | [Bode, "The Multiplier-Type Ring Modulator", EMR 1, 1967](https://www.synth-werk.com/sites/default/files/pdf/electronic%20music%20review%20No1.%201967.pdf) | 9 | none (N1 refuted) | audioif | [RingMod.md](effects/RingMod.md) |
| `Overdrive` | Ibanez TS808 — **C** | circuit | [ElectroSmash, "Tube Screamer Circuit Analysis" (MAS mirror)](https://electrosmash.mas-effects.com/tube-screamer-analysis.html) | 7 | *(waveshaper — see item 1)* | audioif | [Overdrive.md](effects/Overdrive.md) |
| `Distortion` | ProCo Rat + Boss DS-1 as 2nd character — **C** | circuit | [ElectroSmash, "ProCo Rat Analysis" (MAS mirror)](https://electrosmash.mas-effects.com/proco-rat.html) | 11 | DC-clean biquad; *(waveshaper)* | audioif | [Distortion.md](effects/Distortion.md) |
| `Fuzz` | Dallas Arbiter Fuzz Face + Big Muff `cascade` — **C** | circuit | [ElectroSmash, "Fuzz Face Analysis" (MAS mirror)](https://electrosmash.mas-effects.com/fuzz-face.html) | 9 | *(waveshaper — see item 1)* | audioif | [Fuzz.md](effects/Fuzz.md) |
| `Saturation` | triode / tape / console iron, three characters — **C+** | literature | [Yeh, IEEE TASLP 18(3), 2011](https://ccrma.stanford.edu/~dtyeh/papers/yeh12_taslp.pdf) | 10 | hysteresis state; *(waveshaper)* | audioif | [Saturation.md](effects/Saturation.md) |
| `Bitcrusher` | E-mu SP-1200 — **C** | literature | [SP-1200 Service Manual (1987), OCR](https://archive.org/stream/emu-sp-1200-service-manual-1987/Emu-SP-1200-Service-Manual-1987_djvu.txt) | 6 | none (both refuted) | **stock** | [Bitcrusher.md](effects/Bitcrusher.md) |
| `Exciter` | Aphex Aural Exciter — **C** | literature | [US 4,150,253 A (Aphex)](https://patents.google.com/patent/US4150253A/en) | 7 | `DYN_TRANSIENT` time constants | audioif | [Exciter.md](effects/Exciter.md) |
| `CabinetSim` | 4×12 V30 + 1×12 G12M, two characters — **C+** | literature | [Celestion Vintage 30 datasheet](https://celestion.com/productpdf.php?id=888) | 6 | DC-clean biquad | **stock** | [CabinetSim.md](effects/CabinetSim.md) |
| `Compressor` | 1176 / LA-2A / dbx 160 / Fairchild 670 — **C** | literature | [UA 1176LN manual](https://media.uaudio.com/assetlibrary/1/1/1176ln_manual.pdf) | **21** | RMS detector; feedback topology | audioif | [Compressor.md](effects/Compressor.md) |
| `Limiter` | — (design) — **C** | design | [ITU-R BS.1770-5](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I!!PDF-E.pdf) | 7 | BS.1770 true-peak detector | audioif | [Limiter.md](effects/Limiter.md) |
| `Expander` | Drawmer DS201 — **C+** | literature | [Drawmer DS201 operator's manual](http://www.drawmer.com/op201.htm) | 6 | RMS detector; side-chain band; `depth_db`; gate envelope | audioif | [Expander.md](effects/Expander.md) |
| `NoiseGate` | Drawmer DS201 — **C** | literature | [Drawmer DS201 operator's manual](http://www.drawmer.com/op201.htm) | 7 | side-chain band; `depth_db`; gate envelope | audioif | [NoiseGate.md](effects/NoiseGate.md) |
| `DeEsser` | dbx 902 — **C** | literature | [dbx 902 owner's manual](https://adn.harmanpro.com/product_documents/documents/502_1323992524/902%20Owners%20Manual_original.pdf) | 8 | relative threshold; RMS detector; side-chain band; program-dependent attack | audioif | [DeEsser.md](effects/DeEsser.md) |
| `TransientShaper` | SPL Transient Designer — **C** | literature | [SPL RackPack 2715 manual](https://spl.audio/wp-content/uploads/RackPack_2715_TD_BA_E.pdf) | 6 | simultaneous A+S gains; peak-hold sustain | audioif | [TransientShaper.md](effects/TransientShaper.md) |
| `MultibandCompressor` | — (design) — **C** | design | [RaneNote 155, *Dynamics Processors*](https://www.ranecommercial.com/legacy/pdf/ranenotes/Dynamics_Processors.pdf) | 5 | none (N-MB-1 refuted) | audioif | [MultibandCompressor.md](effects/MultibandCompressor.md) |
| `ParametricEQ` | Pultec EQP-1A + API 550A — **C** | literature | [Barrera et al., *Modeling the Pultec EQP-1A with WDF*, SMC 2024](https://smcnetwork.org/smc2024/papers/SMC2024_paper_id132.pdf) | 5 | DC-clean biquad | **stock** | [ParametricEQ.md](effects/ParametricEQ.md) |
| `GraphicEQ` | MXR M-108 / M108S ten-band — **C** | literature | [Dunlop M108S instructions](https://www.jimdunlop.com/content/manuals/M108S.pdf) | 5 | DC-clean biquad | **stock** | [GraphicEQ.md](effects/GraphicEQ.md) |
| `LowPass` | — (design) — **C** | design | [RBJ, *Audio EQ Cookbook*](https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt) | 5 | DC-clean biquad | **stock** | [LowPass.md](effects/LowPass.md) |
| `HighPass` | — (design) — **C** | design | [RBJ, *Audio EQ Cookbook*](https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt) | 6 | DC-clean biquad | **stock** | [HighPass.md](effects/HighPass.md) |
| `BandPass` | — (design) — **C** | design | [RBJ, *Audio EQ Cookbook*](https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt) | 6 | DC-clean biquad | **stock** | [BandPass.md](effects/BandPass.md) |
| `Notch` | — (design) — **C** | design | [RBJ, *Audio EQ Cookbook*](https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt) | 6 | DC-clean biquad | **stock** | [Notch.md](effects/Notch.md) |
| `CombFilter` | — (design) — **C** | design | [J. O. Smith, *PASP*, "Feedback Comb Filters"](https://ccrma.stanford.edu/~jos/pasp/Feedback_Comb_Filters.html) | 6 | delay slew (Ask 1 refuted) | audioif | [CombFilter.md](effects/CombFilter.md) |
| `DynamicEQ` | — (design) — **C** | design | [RBJ, *Audio EQ Cookbook*](https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt) | 5 | none (both refuted) | audioif | [DynamicEQ.md](effects/DynamicEQ.md) |
| `LadderFilter` | Moog transistor ladder — **C** | circuit | [Stinchcombe, *Analysis of the Moog Transistor Ladder*](https://www.timstinchcombe.co.uk/synth/Moog_ladder_tf.pdf) | 5 | `audioladder.Ladder` | audioif | [LadderFilter.md](effects/LadderFilter.md) |
| `TapeDelay` | Echoplex EP-3 + RE-201, two characters — **C+** | literature | [Roland RE-201/101 Service Notes, 1978](https://archive.org/download/Roland_RE-101_RE-201_Service_Manual/Roland_RE-101__RE-201_Service_Manual_djvu.txt) | 6 | delay slew; `wow_shape` | audioif | [TapeDelay.md](effects/TapeDelay.md) |
| `AnalogDelay` | Boss DM-2 + Deluxe Memory Man, two characters — **C+** | circuit | [EHX Deluxe Memory Man schematic](https://experimentalistsanonymous.com/diy/Schematics/Delay%20Echo%20and%20Samplers/Deluxe%20memory%20man.pdf) | 7 | delay slew | audioif | [AnalogDelay.md](effects/AnalogDelay.md) |
| `MultiTapDelay` | RE-201 multi-head modes (+ Binson Echorec) — **C+** | literature | [Roland RE-202 Reference Manual](https://static.roland.com/manuals/re-202_reference/eng/25633275.html) | 5 | delay slew (N1 refuted) | **cond.** | [MultiTapDelay.md](effects/MultiTapDelay.md) |
| `DigitalDelay` | Boss DD-2 — **C** | literature | [Boss DD-2/DD-3 Service Notes, OCR](https://archive.org/stream/boss_DD-2_DD-3_SERVICE_NOTES/DD-2_DD-3_SERVICE_NOTES_djvu.txt) | 5 | delay slew | audioif | [DigitalDelay.md](effects/DigitalDelay.md) |
| `SlapbackDelay` | Sun Studio tape slap — **C+** | literature | [Halmrast, ARP 2019, "Sam Phillips' Slap Back Echo"](https://www.arpjournal.com/asarpwp/wp-content/uploads/2021/12/Tor-Halmrast_ARP2019.pdf) | 5 | delay slew (inherited) | audioif | [SlapbackDelay.md](effects/SlapbackDelay.md) |
| `PingPongDelay` | — (design) — **C** | design | [Tone.js `PingPongDelay` docs](https://tonejs.github.io/docs/15.1.22/classes/PingPongDelay.html) | 5 | delay slew (inherited) | audioif | [PingPongDelay.md](effects/PingPongDelay.md) |
| `Reverb` | EMT 140 plate, 6G15 spring, Dattorro hall/room/chamber — **C+** | literature | [Dattorro, *Effect Design Part 1*, JAES 45(9), 1997](https://ccrma.stanford.edu/~dattorro/EffectDesignPart1.pdf) | 10 | `audioverb.Tank` | audioif | [Reverb.md](effects/Reverb.md) |
| `ConvolutionReverb` | — (design) — **C** | design | [Gardner, JAES 43(3), 1995](https://people.montefiore.uliege.be/josmalskyj/files/Gardner1995Efficient.pdf) | 6 | none (Gardner deferred) | audioif | [ConvolutionReverb.md](effects/ConvolutionReverb.md) |
| `PitchShifter` | Eventide H910 — **C** | literature | [Eventide H910 manual](https://media.uaudio.com/support/manuals/dd/Eventide%20H910%20Harmonizer%20Manual.pdf) | 6 | none | audioif | [PitchShifter.md](effects/PitchShifter.md) |
| `Harmonizer` | Eventide H910 ×3 + keyboard — **C+** | literature | [Eventide H910 manual](https://media.uaudio.com/support/manuals/dd/Eventide%20H910%20Harmonizer%20Manual.pdf) | 5 | none | audioif | [Harmonizer.md](effects/Harmonizer.md) |
| `Octaver` | Boss OC-2 — **C**, mechanism answered | circuit | [Factory OC-2 schematic (championleccy PDF)](https://championleccy.com/wp-content/uploads/2018/01/boss_octave_oc2_guitar_effect_pedal_sch.pdf) | 6 | `audiomath.SubOctave` | audioif | [Octaver.md](effects/Octaver.md) |
| `StereoWidener` | — (design), two characters — **C** | design | [Wikipedia, "Precedence effect"](https://en.wikipedia.org/wiki/Precedence_effect) | 6 | `audioroute.MidSide` | audioif | [StereoWidener.md](effects/StereoWidener.md) |
| `Rack` | — (mechanism) — **C** | design | [Steinberg VST 3 `IAudioProcessor`](https://steinbergmedia.github.io/vst3_doc/vstinterfaces/classSteinberg_1_1Vst_1_1IAudioProcessor.html) | 7 | none | **stock** (mechanism) | [Rack.md](effects/Rack.md) |
| `ShimmerHall` | Eno/Lanois shimmer via Eventide — **P** | literature | [Zhang, CCRMA MUSIC 421A, "Shimmer Audio Effect"](https://ccrma.stanford.edu/~jingjiez/portfolio/echoing-harmonics/pdfs/Shimmer%20Audio%20Effect%20-%20A%20Harmonic%20Reverberator.pdf) | 6 | in-loop pitch shift | audioif | [ShimmerHall.md](effects/ShimmerHall.md) |
| `AirSpace` | Abbey Road S.T.E.E.D. send chain — **P** | design | [Waves *Abbey Road Chambers* user guide](https://assets.wavescdn.com/pdf/plugins/abbey-road-chambers.pdf) | 8 | delay slew | audioif | [AirSpace.md](effects/AirSpace.md) |

**Two conditional tiers, and what decides them.**
`Phaser` is **stock** if Gate 0 keeps the CircuitPython-ported `audiofilters.Phaser`, **audioif** if it takes the DC-clean all-pass. `MultiTapDelay` is **audioif** for the full trait set (T5 reached by composing `audioecho.FeedbackDelay` with the ported `audiodelays.MultiTapDelay`) and **stock** on the ported node alone, minus T5.

**Tier totals:** stock 9, audioif 35, conditional 2.

**One tier moved during the run, on measurement.** `CabinetSim` was written as audioif (the convolver) and is proposed as **stock**: the response is a designed biquad cascade, `audiofilters.Filter` takes a serial `synthio.Biquad` list (probed to twelve stages under CPython), and that delivers it at **zero latency** against the convolver's 256 frames (5.33 ms). `Bitcrusher` moved the same way — bit depth is `audiofilters.Distortion` in `LOFI`, round-to-nearest is an `audiomixer.Mixer` DC offset, and the sample-rate hold is two `audiospeed.SpeedChanger` nodes in series. Its caveat for a board reader: `CIRCUITPY_AUDIOSPEED` is gated per port and only `ports/raspberrypi` sets it upstream, so "stock" there means a stock build *that compiles `audiospeed`*.

---

## The node list

51 raw asks written across the seeds' §5, merged into **28 candidates**. Every candidate was given **two independent refuters** — one working the composition lens (can existing nodes be arranged to reach the trait?), one the measurement-and-cost lens (does the named measurement distinguish node from palette, is the trait falsifiable, is there a cheaper form, does it fit the S3?). **No candidate is unrefuted.** **Five** were refuted; **twenty-three** survive — the twenty-third being the oversampled waveshaper (7), whose two refutations both scope themselves to `Tremolo` B4 and disclaim the drive family, and which Arthur ruled a survivor on 2026-09-07. One of the survivors (Gardner partitioning) survives with **no need**, recorded and deliberately deferred; another (8, hysteresis) is an option on 7 and lands with it.

### Summary

| # | Candidate | Merged from | Verdict | Unblocks |
|---|---|---|---|---|
| 1 | `audioecho.FeedbackDelay` — `wow_shape` table | 4 asks | **survives** | Flanger F1/F6, Chorus T2/T6, Vibrato T7, TapeDelay T4 |
| 2 | `audioecho.FeedbackDelay` — delay-time slew / glide | 6 asks | **survives** | Rotary T6, CombFilter T6, TapeDelay T1a/T1b, AnalogDelay T3, DigitalDelay T2, AirSpace AS7 (+ PingPong, Slapback, MultiTap inherit) |
| 3 | `audioecho.FeedbackDelay` — `wow_am_depth` | 1 ask | **survives** | Rotary T4 (post-cycle clause), T6 |
| 4 | `audioecho.FeedbackDelay` — signed (negative) feedback | 1 ask | **refuted** | — (no fixed trait needs it) |
| 5 | `audioecho.FeedbackDelay` — pitch shift inside the loop | 1 ask | **survives** | ShimmerHall SH4, SH5, SH6 |
| 6 | `audioecho.FeedbackDelay` — multiple read heads | 1 ask | **refuted** | — |
| 7 | **Oversampled table waveshaper** (new own module `audioshaper`) | 6 asks | **survives** — Arthur's ruling, 2026-09-07: both refutations scope themselves to `Tremolo` B4 and disclaim the drive family | Overdrive T7; Distortion A1/F3/SC2; Fuzz G1/G2/C1/A4; Saturation TU1–TU3/TP2/A4 — **`Tremolo` B4 struck**, refuted on both votes (see [The waveshaper problem](#the-waveshaper-problem)) |
| 7a | **Oversampled table waveshaper — the drive-family claims** (re-filed from 7) | the 5 unrefuted claimants of 7 | **absorbed back into 7** by the ruling of 2026-09-07 — the two refutations never reached these claims, and claims no refuter reached are carried on the candidate, not split off it | Overdrive, Distortion, Fuzz, Saturation |
| 8 | Waveshaper — hysteresis state option | 1 ask | **survives** — an option on candidate 7, unblocked by the ruling of 2026-09-07 and landing with it | Saturation TP3 |
| 9 | **DC-clean float biquad + first-order all-pass** (new own module) | 5 asks | **survives** | Phaser Tier 1 + P4 (+ P2/P6 tightened); Tier 1 for LowPass, HighPass, BandPass, Notch, ParametricEQ, GraphicEQ, CabinetSim, Distortion; HighPass T1 |
| 10 | `audiomath.Hold` — fractional zero-order hold | 2 asks | **refuted** | — |
| 11 | `audiodynamics` — `DYN_TRANSIENT` time constants exposed | 1 ask | **survives** (1–1 split) | Exciter T5 (tau clause) |
| 12 | `audiodynamics` — RMS detector | 2 asks | **survives** | Compressor V3, Expander E2, DeEsser D6 |
| 13 | `audiodynamics` — feedback detector topology | 1 ask | **survives** | Compressor F4, O5, M4, V5 |
| 14 | `audiodynamics` — BS.1770 true-peak detector | 1 ask | **survives** | Limiter L1 |
| 15 | `audiodynamics` — side-chain band (12 dB/oct + LP corner + key) | 2 asks | **survives** | Expander E3, NoiseGate G3, DeEsser D2 |
| 16 | `audiodynamics` — `depth_db` floor | 1 ask | **survives** (1–1 split) | Expander E4; NoiseGate G4 **refuted** by one vote |
| 17 | `audiodynamics` — four-stage gate envelope with hold | 1 ask | **survives** | NoiseGate G1/G2/G5/G7, Expander E5/E6 |
| 18 | `audiodynamics` — relative-threshold detection | 1 ask | **survives** | DeEsser D1, D2 |
| 19 | `audiodynamics` — `release_db_per_sec` | 1 ask | **refuted** | — |
| 20 | `audiodynamics` — program-dependent attack | 1 ask | **survives** (1–1 split) | DeEsser D5 |
| 21 | `audiodynamics` — simultaneous attack + sustain gains | 1 ask | **survives** (1–1 split) | TransientShaper T2 |
| 22 | `audiodynamics` — peak-hold on the slow envelope | 1 ask | **survives** | TransientShaper T4 |
| 23 | `audiodynamics` — second release stage with memory | 1 ask | **refuted** | — |
| 24 | **`audioladder.Ladder`** (new own module) | 2 asks | **survives** | LadderFilter T3, T4, T5 |
| 25 | **`audioverb.Tank`** (Dattorro; new own module) | 2 asks | **survives** | Reverb T1/T2/T3/T8/T9/T10 direct, T4/T5/T6 via the dispersive chain, Tier 1 |
| 26 | `audioconvolve.Convolver` — non-uniform (Gardner) partitioning | 1 ask | **recorded, deferred — NEED: NONE** | — |
| 27 | **`audiomath.SubOctave`** (OC-2 divider) | 2 asks | **survives** | Octaver O1, O2, O3, O5, O6 |
| 28 | **`audioroute.MidSide`** | 1 ask | **survives** | StereoWidener W3, W5 (M/S half), W6 |

**Six new modules or nodes** among the survivors: `audiobiquad` (the DC-clean biquad + all-pass), `audioshaper.Waveshaper` (the oversampled table waveshaper, candidate 7), `audioladder.Ladder`, `audioverb.Tank`, `audiomath.SubOctave`, `audioroute.MidSide`. Everything else is an **additive option on an audioif-own node**, per D1; **no CircuitPython-ported node is proposed for modification anywhere in the 46 seeds.**

### The verdicts, two lines per candidate

**1. `wow_shape` table — SURVIVES.**
*Composition:* not refuted. The one non-trivial route is a cascade of `FeedbackDelay` stages, but every oscillator initialises to `sine=0, cosine=1` with no phase input (`:163-164`) and depth is clamped non-negative (`:117-118`), so every achievable composite is a sine series odd about *t*=0 while the BBD's reciprocal-of-a-ramp trajectory is even about its turning points — measured 14.5 % RMS of span against F1's 2 % bar, and 14.475 % again with the sign constraint lifted, so the binding constraint is the fixed phase, not the sign.
*Measurement/cost:* not refuted — 43 dB of separation on the controlled metric, ~4 flops plus one load per frame, a 512 B–1 KB shared table. Three corrections carried: the **F6 half of the unblock claim is not shown** (F6 steps the *centre* delay, which a cyclic table with no readable phase cannot render onto an asynchronous Python step); the single planned measurement never exercises F6 at all; and the magic-circle oscillator yields sine and cosine but never a phase, so the option needs its own accumulator and must keep the existing sine as a branch for byte-identity.

**2. Delay-time slew / glide — SURVIVES.**
*Composition:* not refuted. Nothing can move a delay tap continuously: `delay_ms` is a plain config float (not a synthio block slot), the only per-sample modulator is a fixed zero-mean sine, and the best composition — a crossfade between two lines — produces **no pitch bend at all**, which is exactly what TapeDelay T1a, AnalogDelay T3, DigitalDelay T2 and AirSpace AS7 demand. The palette's ceiling is one step per block: ~94 steps across CombFilter T6's one-second sweep, or 5.33 ms to 90 % against Rotary T6's 5–8 s.
*Measurement/cost:* not refuted — 44 dB of separation on T6's first-difference estimator, three flops per frame beside a loop already doing a magic-circle rotation and a per-channel lerp. **Two calibrations Gate 0 must carry:** CombFilter T6's "−60 dBFS" bar sits below its own estimator's zero-step floor (−44.4 dBFS) and must be restated against that control; and the option must be a **linear rate limit in frames/second, not a one-pole time constant**, or TapeDelay T1a's "+1193 cents held for 100.4 ms" sags and fails on the node too.

**3. `wow_am_depth` — SURVIVES.**
*Composition:* not refuted, **but the seed's stated reason is wrong and must be replaced.** A `synthio` sub-audio note through `audiomath.Multiply` *does* follow a rate change without restarting (probed: 6.8 → 0.8 → 6.8 Hz mid-render, continuous at both switch points), so "a table restarts at frame 0" is not the blocker. The durable limit is that the kernel's wow phase lives only in `state->wow_sine/wow_cosine` and is exposed nowhere, so any external modulator is an independent accumulator and quadrature is a coincidence to be timed (±7° of the ±15° budget at 6.8 Hz before drift).
*Measurement/cost:* not refuted — `set(wow_hz=…)` rewrites only `wow_step` (`:111-115`) and never touches the oscillator state, so the post-cycle quadrature reading separates the builds by construction; the sine is already computed per frame, so the option costs one add and one multiply against 28 kB (6.8 Hz) to 240 kB (0.8 Hz) of table. One design note: the law must state the polarity (gain driven by −s), or the lock lands at −90°.

**4. Signed (negative) feedback — REFUTED.**
*Composition:* refuted — 1/(1 + g·z⁻ᴹ) = (1 − g·z⁻ᴹ) · 1/(1 − g²·z⁻²ᴹ), and both factors are on the palette; the inversion through `audiomath.Multiply` against a −32768 modulator is bit-exact for every int16 but the negative rail.
*Measurement/cost:* refuted — no fixed trait rests on it. `CombFilter` withdrew the only ask (T4 measured passing on the composed path: +13.98 dB at 100/300/500/700 Hz against an ideal +13.98, within 0.01 dB), and `Flanger` — the class the vision names the option for — files no such ask and records that the "inverted feedback" claim rests on a forum reading of a schematic never shown. What survives is a cost argument: five nodes, two delay lines, a 32 kB Splitter ring, int16 requantisation per stage.

**5. Pitch shift inside the loop — SURVIVES.**
*Composition:* not refuted — no palette node has both a feedback loop and a pitch operator (`grep` finds "feedback" only in freeverb's comb gain, and `audioif_pitchshift.c` has no feedback at all), and a pull graph forbids cycles: bound with `loop=True` a Mixer→Freeverb→Mixer cycle raises `RecursionError` before a sample is pulled.
*Measurement/cost:* not refuted — all three palette configurations measure **0.00 semitones per pass** (220.0 Hz on repeats 1–4) against SH4's +12, and the cause is structural (`Echo`'s freq_shift branch advances read and write at the same rate). One qualification: the K-branch cascade alternative is ruled out by **SH6 and Tier 3**, not by SH4 as the seed says.

**6. Multiple read heads — REFUTED.**
*Composition:* refuted — `audioecho.FeedbackDelay` (filtered loop, `damping_hz` in the loop, `mix=1.0`) feeding `audiodelays.MultiTapDelay` at `decay=0` puts the darkening on laps and the heads on each lap: arrivals exactly on the grid, T4 tap-to-tap spread **0.000 dB** in every lap, T5 per-lap increment identical across taps to 0.000 dB while accumulating −8.7 / −20.5 / −32.3 dB at 8 kHz.
*Measurement/cost:* refuted, and more sharply — **T5 as written is passed by a do-nothing build**: a front-filter control in which nothing darkens differentially also scores 0.000 dB. A trait a null build passes cannot justify a node. The seed's proposed repair clause is also miscalibrated (3× the lap-2 increment misses by 6.22 dB, because darkening through an in-loop one-pole is not linear in lap count).

**7. Oversampled table waveshaper — SURVIVES (Arthur's ruling, 2026-09-07).**
*Composition:* refuted, scoped to `Tremolo` B4 — "This refutes only the Tremolo B4 line in the candidate's UNBLOCKS list; Overdrive T7, Distortion A1/F3/SC2, Fuzz A4 and Saturation A4 are alias-floor claims that oversampling still owns, and this probe neither supports nor refutes them."
*Measurement/cost:* refuted, scoped to `Tremolo` B4 — "Scope of the refutation, stated plainly: this refutes B4 as a claimant on the node. It says nothing about the Drive family's own claims, which rest on measurements I did not run and were not mine to run."
Ruling (Arthur, 2026-09-07): both refutations scope themselves to Tremolo B4 and disclaim the drive family; they refute Tremolo's use, not the node. Survives on Overdrive T7, Distortion A1/F3/SC2, Fuzz A4, Saturation A4. Sketch and cost: [`audioshaper.Waveshaper`](#audioshaperwaveshaper--oversampled-table-waveshaper-candidate-7). The full record is [The waveshaper problem](#the-waveshaper-problem).

**8. Waveshaper hysteresis state option — SURVIVES** (unblocked by the ruling on candidate 7, 2026-09-07).
*Composition:* not refuted — the strongest composition (a static table in parallel with a linear memory branch, so the memory's share grows relative to a compressing output) measures an excess that is **negative and falling**, −0.67 / −1.13 / −1.59 dB at −18/−12/−6 dBFS, where TP3 needs ≥ +6 dB and rising; the linear control reads +1.92/+1.91/+1.89 dB, flat to 0.03 dB, confirming the rig reports "no growth" rather than noise. Caveat carried: because the measure normalises by the output peak, TP3's own trend clause may bite the node too, and Phase 1 must report what the real node does rather than assume the physics.
*Measurement/cost:* not refuted — the palette's two genuine memory elements clear the ≥6 dB magnitude bar and fail on **trend**: `FeedbackDelay` is largest with its nonlinearity *off* (+9.83 → +7.18 dB as drive rises) and `Dynamics` shrinks (3.24e-5 → 1.37e-5) and swings two orders of magnitude with probe frequency. Cost is one Langevin per oversampled sample by continued-fraction tanh, no `exp`; the shipped lean patch already forces `Hysteresis` 0 on the S3. Scope tightened: **A5 unblocks TP3 and only TP3** — IR2's bars are met by a static asymmetric table with a bias input.

**9. DC-clean float biquad + first-order all-pass — SURVIVES.**
*Composition:* not refuted — the feedback clamp is inside a **CircuitPython-ported binding** (`audiofilters/Phaser.c:211`, `synthio_block_slot_get_limited(&self->feedback, 0.1, 0.9)`) and the loop it feeds is internal to the kernel, so no composition can drive feedback to exactly zero; `synthio.Biquad` has no all-pass mode and no raw-coefficient constructor. The one composition the seed had not killed — a downstream `AUDIOIF_DYNAMICS_GATE` whose −80 dB floor would round a −6 LSB constant to zero — fails on substance for the same reason the Python tail-gate does (it reaches zero by deleting any legitimate quiet tail) and reaches only half the need, since P4 stays behind `Phaser.c:211`.
*Measurement/cost:* not refuted, and re-measured this run — burst-then-silence at the class's own shipped construction holds −4 to −8 LSB through 3 s of silence at four LFO phases, and `feedback` 0.0 and 0.1 render **byte-identical** (same md5) while the unclamped control pair 0.2 / 0.3 differs. **One caveat Gate 0 must carry:** the hold is configuration-dependent — the identical probe at 22.05 kHz mono reads exact zero — so **every Gate 0 number must name its sample rate and channel count**, or a later run at another rate will read clean and look like the defect is gone.

**10. `audiomath.Hold` (fractional zero-order hold) — REFUTED.**
*Composition:* refuted — the `SpeedChanger` phase reset lands inside `fetch_source_buffer`, and its only in-loop call site sets `src_index = 0` immediately after, so a mid-hold restart emits a **new** decimated value. A reset can truncate a hold of 2 to 1; it can never extend one. Measured alphabet at fs/f_hold = 1.843 over 30 000 frames: `{1: 2542, 2: 13729}` — nothing else, length-2 fraction 0.8438 against T6's 0.843 ± 0.02.
*Measurement/cost:* refuted independently, same histogram. **The seed's contrary `{3: 173, 4: 399}` is a stimulus artefact**, not a node defect: runs of 3 or 4 require two adjacent decimated values to be equal, which a tone gives near its peaks and which an ideal fractional-hold node would score identically. T6's stimulus needs "no repeated adjacent values in the decimated stream" written into it; with that, the palette passes T6 as it stands.

**11. `DYN_TRANSIENT` time constants exposed — SURVIVES (1–1 split).**
*Composition (refuted):* a `DYN_COMPRESS` stage run as a near-total AGC in the same slot has a settle time continuous and monotone in the **existing** `attack_ms` — 30–45 ms at 8 ms, 100–105 at 20, 740–790 at 150 — so a Transient Time macro is reachable by scaling onto an existing option. Residual the refuter states himself: T6 was not re-verified under the seed's own metric, and the AGC route spreads 8–10 dB at short tau where the differential spreads 0.8 dB.
*Measurement/cost (not refuted):* the four coefficients are literals evaluated at process entry (`:215-222`) and read **only** in the transient branch (`:285-300`), while `attack_coef`/`release_coef` are read **only** in the `else` branch (`:301-307`) — so in `DYN_TRANSIENT` the settle time is invariant to every exposed knob by construction, and the seed's three-tau measurement separates an invariant from a variable by 17× at 8 ms. The form is already the cheapest possible (four floats moved from process entry into the config; it *removes* four `expf` per call).

**12. RMS detector — SURVIVES.**
*Composition:* not refuted — an RMS compressor needs `g = f(mean-square)` applied to `x`, and the palette has no divide, no log, no reciprocal, and no node whose output falls as its input level rises. Squaring is reachable (`Multiply(x,x)`) and even yields the exact RMS gain law through a ratio-2 `Dynamics`, but that gain is welded to the squared stream and nothing can divide it back out. `sidechain_coef` is a one-pole low-pass **of the node's own input**, not an external key.
*Measurement/cost:* not refuted — on one axis (10 %-duty train vs sine of equal peak, ∞:1, knee 0), peak reads +0.48 dB and mean-|x| +16.06 dB, straddling RMS's 6.99 ± 1 dB from **opposite sides**, so no threshold or makeup offset closes the gap. Cost: `x*x` replacing `fabsf`, the existing one-pole reused, and the square root folded into the dB domain as one ×0.5 — **no `sqrtf`, no new buffer, no per-instance RAM.**

**13. Feedback detector topology — SURVIVES.**
*Composition:* not refuted — the detector is seeded from `source[]` (`:254`) while the gain is applied to `delayed[]` (`:313`), no option redirects it, `Dynamics` has no external key input, no node emits an envelope as a sample stream, and `FeedbackDelay`'s loop cannot host another node's gain cell. The only static-matched composition (k stages at ratio R^(1/k), exact because (1−s)^k = 1/R) runs the ordering **backwards at 24 of 24 settings**, which is F4's own stated disconfirmation.
*Measurement/cost:* not refuted — without the option the trait has one arm and cannot be measured in either direction, and V5 (the VCA row, whose whole content is that the feed-forward build is strictly *faster*) has nothing to compare against. Cost: one previous-output float per channel plus one branch; no new buffer, no latency.

**14. BS.1770 true-peak detector — SURVIVES.**
*Composition:* not refuted — four routes, all closed by files read this run. There is no external side-chain seam in `audioif_dynamics_config_t`; BS.1770's final operation is `max(|phase₀..₃|)` and the palette has no max (Splitter sums, Multiply multiplies); Python gain-riding is block-rate by the palette's own seam; and `grep -rn "resampl|oversampl|polyphase"` over `src/shared` returns exactly one line — the kernel's own concession that "proper true-peak metering oversamples by four and this does not pretend to be that."
*Measurement/cost:* not refuted — 1.12 dB TP escapes by S1's own filter and 1.04 dB read independently with an 8× windowed sinc, against L1's 0.5 dB; and an **ideal** 2× detector already under-reads 0.688 dB at f_s/4, so no 2×-class detector can meet L1 in principle. A fixed offset is unbounded: probed over 400 random band-limited multi-tones, the worst under-read is 1.465 dB, larger than the 1.18 dB tone worst case an offset would be sized on. **Correction to Tier 3:** the FIR's ~6 samples of group delay consume 6 samples of the lookahead window rather than being free.

**15. Side-chain band (12 dB/oct, LP corner, external key) — SURVIVES.**
*Composition:* not refuted — one `float sidechain_coef` in the config, one `sidechain_lp[2]` state (one pole), spent as a high-pass by subtraction; no key field in the struct, no key keyword in the binding. `Splitter` + `Filter` build the band perfectly and have nowhere to hand it, because the detector array is filled from the same `source[]` the VCA scales; the stereo trick dies on the cross-channel `max` at `:263-268`; cascading two `Dynamics` does not cascade the slopes, only the gain reductions.
*Measurement/cost:* not refuted — with the band set 500 Hz–2 kHz the palette has no top at all, so a 4 kHz tone drives the gain across the whole −60 → 0 dBFS sweep against E3/G3's "< 1 dB"; cost is one multiply-add per sample per channel and 2–4 floats of state. **Two form notes:** steepening `sidechain_hz` in place would move existing output, so the second pole belongs behind its own opt-in defaulting to one; and only the **external key** half needs a new sample input threaded through the process call — the internal band is the smaller ask and every cited trait unblocks without the key.

**16. `depth_db` floor — SURVIVES (1–1 split), and the split is informative.**
*Composition (refuted):* `Dynamics`' `makeup_db` is an **unclamped** float attenuator, so `Splitter → [dry: LIMIT with makeup_db = D] + [gate path] → Mixer` at level 1.0 measures −0.002 / −0.034 / −0.269 dB error at −20 / −40 / −60 dB. But the deep end fails for the option too: −70 → −0.803 dB, −80 → −3.961 dB, −90 → digital silence, and the cause is the **truncating int16 write at `:319`** on a signal at ~1.6 LSB, which a settable literal would meet identically. So the composition is better than the seed thought *and* the node does not unblock the deep end either.
*Measurement/cost (not refuted for E4, refuted for G4):* G4's four named settings are met by the two-stage blend (−0.00 / −0.01 / −0.04 / −0.32 dB) and its span clause by the node's own −83.94 dB floor, so **G4 cannot justify the ask**. E4 survives on a different mechanism the seed never measured: `Expander` must run `DYN_EXPAND` for E1's slope law, and that branch's floor literal is **−60 dB** (`:185`), 20 dB short of E4's "reaches at least −80 dB" — and V-E4 tested a `DYN_GATE` graph and transferred the conclusion.
**Recommendation to the implementation session:** restate the ask as the EXPAND floor at `:185`, drop the claim that G4's measurement fails, and re-run E4 in `DYN_EXPAND`.

**17. Four-stage gate envelope with hold — SURVIVES.**
*Composition:* not refuted — the VCA half **is** composable (`audiomath.Multiply` under a `synthio` note envelope, measured smooth and click-free), and the detector level is even readable from Python via `gain_reduction_db()`. What is missing is a place to run the trigger: the `Component` surface has no `poll`/`tick`/`update`, the live surface is frozen by roadmap §3, and a block-rate decision floors G2's 2 ms hold at 5.33 ms. A composed gate would not be a component; it would be a pattern the application hand-drives.
*Measurement/cost:* not refuted — ONESHOT separates by ~80 dB (palette −80.00 dB in all 90 blocks against a required climb to 0 dB), and the same trace falsifies G1 and G2 at once. **Refinement:** a per-block trace quantises to 5.33 ms, so ONESHOT must run with `hold_ms` well above one block, or capture per sample if G2's 2 ms end is to be demonstrated.

**18. Relative-threshold detection — SURVIVES.**
*Composition:* not refuted — no external side-chain port (detector hardwired to `source` at `:254`), no invertible gain signal (the reduction lives only in state, readable from Python, never as audio), no division node. The leveller route makes the second node level-independent only by squashing programme dynamics into the leveller's window, which is a different effect and cannot be undone downstream. `TRANSIENT` mode's dB difference is temporal (fast vs slow on the same signal), not spectral.
*Measurement/cost:* not refuted — on the shipped construction a fixed 200 Hz + 6 kHz balance gives −10.57 / −0.00 / 0.00 dB of reduction at −6 / −20 / −40 dBFS, where D1 allows 1 dB across the whole window; the collapse is the falsifier and it is a standing planted fault that goes red today. Cost: one extra one-pole and one full-band rectification per channel per sample, no new buffer, **zero added latency**.

**19. `release_db_per_sec` — REFUTED.**
*Composition:* refuted — the one-pole smooths the **detector level**, not the output gain, and an exponential decay toward zero is exactly a straight line in dB; the gain computer above it is affine in env_db and clamps at 0 dB in finite time. So `release_ms` **is** a dB/sec rate under a change of variable: rate = (1 − 1/R)·8685.89 / release_ms. Measured at the resulting 7.0426 ms with `knee_db = 0`: fitted 925.0 dB/sec, max straight-line deviation **1e-5 dB**, 12.958 ms against D4's 13.0 ms ± 10 %.
*Measurement/cost:* refuted independently by the same derivation: 12.97 ms with a 0.019 dB residual, i.e. one sample step. The premises "convex in dB" and "never reaches 0 dB" are both false. What D4 needs is one sentence of unit conversion in the seed and `knee_db = 0` named — no C, no new state.

**20. Program-dependent attack — SURVIVES (1–1 split), with D5 needing a rewrite either way.**
*Composition (refuted):* two frozen `Dynamics` in series (A: thr −24 / ratio 4 / attack 1.8 ms into B: thr −14 / ratio 6 / attack 0.5 ms) give t63 1.917 ms at 10 dB over and 0.583 ms at 20 dB over — **ratio 3.29, all three D5 targets inside 25 %** — while B contributes 0.00 dB of steady-state reduction, leaving the static curve exactly the lone ratio-4 curve.
*Measurement/cost (not refuted):* the same refuter shows **D5's stated disconfirmer is arithmetically wrong**: a linear follower crossing a dB target already gives t63 = 1.90 with a fixed coefficient, not 1.0, invariant across attack_ms (1.90 / 1.89 / 1.90) — so the palette's baseline is 1.90 and D5's band is 2.5–4.1. **Required before the gate:** D5's disconfirmation cell must read "palette baseline 1.90 (log-law artefact), D5 requires 2.5–4.1", the kit must report the absolute t63 pair as well as the ratio, and the residual the node buys is ~1.7× on top of the 1.90 that comes free — the 10 dB point is already met at attack_ms = 2 ms and only the 20 dB point discriminates.

**21. Simultaneous attack + sustain gains — SURVIVES (1–1 split), and this one should be re-examined at Gate 0.**
*Composition (not refuted):* the series interaction is structural — the downstream node's detector reads the upstream node's gain-shaped output — measured 10.36 dB against T2's 0.5 dB; `Multiply` squares the signal rather than composing two gains; and the parallel-weight system has no solution (equal weights give +7.9 dB on the transient and −4.1 dB on the decay).
*Measurement/cost (refuted):* **one** `DYN_TRANSIENT` node already carries both signs across a hit (25 blocks positive, 55 negative), and its detector is strictly feed-forward and gain-independent, so `gain(both set) ≡ gain(attack alone) + gain(sustain alone)` sample by sample — measured **0.000000 dB** divergence over 80 blocks, five hundred times inside T2's allowance. The proposed change (`attack·max(norm,0) + sustain·max(−norm,0)`) is arithmetically identical to the ternary already there. The 10.36 dB belongs to the two-node topology the seed chose, not to the palette.
**Recommendation:** treat T2 as met by a single node and re-label the 10.36 dB as a note on why the class must not be built as two nodes in series; the ask should be withdrawn or re-scoped before an audioif issue is filed.

**22. Peak-hold on the slow envelope — SURVIVES.**
*Composition:* not refuted — the compressor composition (a `DYN_COMPRESS` stage after a `DYN_TRANSIENT` set for attack only) fails T4's first clause (worst sample 1.46 / 1.02 dB below the running maximum against 0.25 dB) and, decisively, is a **calibration and not a shape**: with the same settings and the same notes 12 dB quieter, the trace is 0.00 dB for every block. A peak-hold references the note's own onset; a fixed threshold references absolute level.
*Measurement/cost:* not refuted — the four transient coefficients are compiled-in literals no keyword reaches, and a hold and a decay are different shapes, so no series arrangement of `DYN_TRANSIENT` nodes holds. Cost: one float peak register and one sample counter in the state struct, plus a compare in a branch that already tests `level > slow_env`; latency zero; default off keeps every existing caller byte-identical.

**23. Second release stage with memory — REFUTED.**
*Composition:* refuted — two `Dynamics` in series measured t50 42.7 ms, t95 1189 ms, **t95/t50 = 27.9** against O1's ≥ 8, with the single-stage control at 1.7; the memory O2 asks for is carried free by the slow stage's own `attack_coef` (a 2.5 s attack is still climbing at 200 ms and settled at 10 s).
*Measurement/cost:* refuted independently at three drives (30.7 / 31.6 / 32.6, control 1.8), depth pinned so the 20 dB loophole is closed. What survives is a Tier 3 cost point (a second per-frame `logf` and `expf`), which under vision §6's compose-first rule cannot revive the ask.

**24. `audioladder.Ladder` — SURVIVES.**
*Composition:* not refuted. The strongest candidate is `audioecho.FeedbackDelay`, which genuinely is a per-sample loop with an odd cubic saturator inside it — but it can never sustain: feedback is clamped to 0.99 and every loop element is passive (one-pole magnitude ≤ 1, cubic slope ≤ 1), so loop gain is strictly < 1 at every frequency, and the source's own comment says why the clamp is there. At the delay length that would decay slowly enough for T3 (N ≥ 2566 ≈ 58 ms) the structure is a **comb with resonances every 17.2 Hz and no cutoff parameter at all**; the two requirements move in opposite directions on the same single knob.
*Measurement/cost:* not refuted — the linear two-biquad build reproduces T1/T2 to 0.01 dB and tracks resonance to −0.05 dB at every k through 3.95, and is therefore **exactly** what T3, T4 and T5 are stated against: it cannot sustain from silence, k = 4 is an infinite Q it cannot represent, and its level dependence is identically zero (T5's own disconfirmation). **Cost caveat for Phase 1:** the 180 cycles/sample/channel estimate assumes ~1 instruction per cycle; Xtensa LX7 float has multi-cycle result latency, so the 14 %-of-block S3 figure could land 2–3× higher and must be measured on silicon before it is quoted as fact.

**25. `audioverb.Tank` (Dattorro) — SURVIVES.**
*Composition:* not refuted — a tank recirculates and a pull graph has no cycles (`RecursionError` on the first `get_buffer`, re-measured); Freeverb's eight comb and four all-pass lengths are literal integer assignments in a **CircuitPython-ported binding** with no sample-rate term, and the kernel takes only `roomsize`, `damp`, `mix`. What *does* compose is the diffusion alone (Splitter + wet-only FeedbackDelay + two constant Multiply gains, one negative, + Mixer — a real Schroeder all-pass, flat to 0.00 dB), so the honest statement is that the all-passes are reachable at five nodes each and the recirculation is not; four of Fig. 1's eight sit inside the loop that cannot exist.
*Measurement/cost:* not refuted, and the gate measurement was run: Freeverb's first non-zero-lag autocorrelation peak is at lag 1188 = **24.75 ms**, below T4's sourced 30–53 ms span, and does **not move** when `roomsize` halves (the comb peaks stay at the same lags). The `_banks` entry point that takes `comb_sizes[8]`/`allpass_sizes[4]` was examined as the cheaper form and reaches lengths only — no excursion, no dispersion, no per-band decay. Memory arithmetic checks out: 22 494 samples at 29 761 Hz × 48000/29761 = **36 279 words = 72.6 kB as int16**, 145 kB as float32.
**Two estimator corrections M4 must carry:** a naive "first non-zero-lag peak" mis-reads the roomsize-0.5 case as 2.81 ms (an all-pass short-lag artefact), so the search needs a floor ≥ ~500 samples or a prominence rule; and the Size-1.0 clause is rate-dependent (1116 samples is 23.25 ms at 48 kHz but **50.6 ms at 22.05 kHz, inside the sourced span**), so the gate runs at 48 kHz and the rate-independent discriminator is the Size-halving clause.
**Board correction:** the trait id list carried on this candidate elsewhere (T1, T4, T5, T6, T9, T10) is the set Freeverb *fails*, not the unblock set. The board carries the unblock set.
**One cost note that is also a Tier 1 decision:** int16 line memory with magnitude truncation is not only the S3 memory budget — it is also what lets the tail reach exact zero rather than a held DC floor, so the memory choice and the Tier 1 silence invariant are **one decision** and must be specified together.

**26. Gardner non-uniform partitioning — RECORDED, DEFERRED. NEED: NONE.**
*Composition:* refuted as a need — D3 as fixed re-measured **passing** (loaded first arrival at frame 256, unloaded max |out − in| = 0 over 1 s), and Gardner would move that arrival off 256 and so **disconfirm** the trait rather than serve it. The one clause the node does not serve is class-side and costs no kernel change: `Convolver.taps` already publishes `loaded × 256`, so `taps > 0 ⇔ loaded` is a one-line Python rule.
*Measurement/cost:* refuted as a need — no convolution measurement can show the palette failing against a 52–418 ms platform floor (one partition is 5.33 ms at 48 kHz), and the node's own header prices and refuses the change in the author's words: *"roughly triples the code for a saving that matters only when monitoring a live player. Deliberately not done."*
**Reopen condition:** a Phase 1 platform round trip measured under 10 ms on a P4 or S3 through the `audiodev` pump and the I2S ring. That is a platform spike, not a convolution measurement.

**27. `audiomath.SubOctave` — SURVIVES.**
*Composition:* not refuted — a subharmonic is not in the input's spectrum, so no LTI arrangement can make one, and a memoryless nonlinearity maps period T to period T. That leaves the two nodes with both memory and nonlinearity, and each is closed in the kernel: `FeedbackDelay`'s inverting-comb route needs negative feedback the API forbids, and its bifurcation route is closed because the odd cubic's slope is ≤ 1 everywhere and feedback ≤ 0.99, making the loop a strict contraction with a single stable trajectory; `Dynamics` modulates by a rectified envelope that carries no phase of the input.
*Measurement/cost:* not refuted — eight rendered compositions leave 110 Hz **≥ 42.5 dB down, at the analyser's own leakage floor**, so O6's filter has nothing to discriminate; the `PitchShift` substitute the class ships today lands at 205.08 Hz (−121.6 cents, not 220/2) with up to 10.7 ms of wet delay against O5's zero. Cost is strictly less arithmetic per frame than `audiomath.Multiply`. Observation recorded rather than claimed: folding the divider into `Multiply` as a mode would save a node and a Splitter tap, but was not pursued to a refutation and O3's "null the modulator, OCT2 falls below −80 dBFS" check wants the square to be a separable stream.

**28. `audioroute.MidSide` — SURVIVES, and the seed's §5 fallback should be replaced.**
*Composition:* not refuted, **but a better composition exists than the one the seed measured.** Putting the unavoidable one-frame delay in the *side correction* rather than the mid cancels the mono-sum comb by construction: W3 reads 0.0098 dB (inside 0.05 dB, against A6's 2.010 dB failure) and W5 is byte-identical at Width 1.0 with latency 0. It still fails **W6** at w = 0 — −5.869 dB against the ideal −6.021, 0.152 dB outside the 0.1 dB tolerance — because the correction is one sample late, and that error grows with frequency (≈ 6 dB at 10 kHz by the same arithmetic). No composition can hold W6's frequency-independent matrix law while the cross-channel term is delayed, and every cross-channel path in the palette runs through `FeedbackDelay`.
*Measurement/cost:* not refuted — the one-frame floor is **structural to a read-before-write interpolating line** (the read at `:214-219` computes its index before the current input is written at `:255`), not a conservative constant someone can relax; at offset 0 the read returns the sample from a whole line ago. The node is the cheap option: zero state, four multiply-adds and two shifts per frame, against a 32 kB Splitter ring plus two int16 delay lines and their requantisation.
**Replace the recorded Gate-0 fallback** with this side-only matrix: latency 0, W5 byte-exact, W3 within 0.01 dB, and only W6 restated as "exact at unity width, degrading with frequency away from it, 0.15 dB at 1 kHz and w = 0".

### The waveshaper problem

The candidate was filed as **refuted**, and the two votes did not support it. Arthur's ruling of 2026-09-07 makes it a **survivor**; what follows is the record the ruling rests on, with both refuters' words kept verbatim.

Both refuters attacked one claimant — `Tremolo` B4, "the clipping threshold moves with the bias" — and both won that argument the same way: a **bias track summed ahead of a static curve** is an input offset, `f(x + b(t))`, which is what a valve grid-bias shift actually is, and `audiomixer.Mixer` supplies it per sample. Refuter 1 measured +8.29 dB against B4's ≥ 3 dB bar at a −1.2 dBFS crest with a 0.00 dB control; refuter 2 measured +19.6 dB at −1.2 dBFS with a flat (+0.1 / +0.1 / −0.0 / 0.0 dB) control. Both are clean refutations of B4, and B4 should be struck from the node's claimant list. The seed's own palette route (`Multiply` → static curve → `Multiply`) was the wrong composition: it modulated *drive*, scraped the bar by 0.0–0.2 dB, and delivered its crest 24.6 dB below unity.

Both then said, unprompted and in terms, that this settles nothing about the drive family:

> "This refutes only the Tremolo B4 line in the candidate's UNBLOCKS list; Overdrive T7, Distortion A1/F3/SC2, Fuzz A4 and Saturation A4 are alias-floor claims that oversampling still owns, and this probe neither supports nor refutes them."

> "Scope of the refutation, stated plainly: this refutes B4 as a claimant on the node. It says nothing about the Drive family's own claims, which rest on measurements I did not run and were not mine to run."

So the merge turned two narrow refutations into one broad verdict. The consequences on the board today:

- **Five classes** (`Overdrive`, `Distortion`, `Fuzz`, `Saturation`, and `Tremolo` for B4 alone) name this node in their §5, and it is the node vision §6 singles out: *"The node the palette genuinely lacks is a table-driven waveshaper with oversampling."*
- The candidate carried **no design sketch and no cost estimate** — which Gate 0 requires of a *survivor*. One is now written: [`audioshaper.Waveshaper`](#audioshaperwaveshaper--oversampled-table-waveshaper-candidate-7), with the ×2/×4/×8 cost per stereo block on both boards. The ten per-module sketches now cover all 23 survivors.
- Candidate **#8**, the hysteresis state option, is written as *"an option on the A1 waveshaper, not a node"* — so it presupposes this node. With 7 a survivor it is **unblocked** and lands as an option on it.
- The palette verifier independently established the two facts that make the alias claims live and that no refuter contradicted: **there is no oversampling anywhere in the palette** (`audiospeed.SpeedChanger` reads `phase >> SPEED_SHIFT` with no interpolation and no anti-alias filter, and both `SpeedChanger` composition routes were measured and refuted for the drive family in `Overdrive`/`Distortion` §5), and **nothing on the palette gives gain above unity** except the drive node itself (`MixerVoice.level` clamps 0..1 silently; `Multiply` scales by `>> 15`).

**What settled it (Arthur, 2026-09-07):** both refutations scope themselves to `Tremolo` B4 and disclaim the drive family; they refute `Tremolo`'s use of the node, not the node. Candidate 7 therefore **survives**, on Overdrive T7, Distortion A1/F3/SC2, Fuzz A4 and Saturation A4. `Tremolo` B4 stays struck from its UNBLOCKS list, candidate **7a** is absorbed back into 7, and candidate 8 is unblocked. The drive family's own claims still carry their measurements — the alias floors (Overdrive T7, Distortion A1, Fuzz A4, Saturation A4), the sourced-curve traits (Fuzz G1/G2/C1, Saturation TU1–TU3/TP2) and Distortion F3/SC2 at h7 — and any refuter who wants them is free to run against the palette's four fixed curves; nothing here forecloses that. **What is still owed:** the audioif issue for candidates 7 and 8, which the eight filed on 2026-09-07 do not cover.

### Design sketches (survivors)

Phase 0 wrote **ten** sketches — nine in the original pass, plus `audioshaper.Waveshaper` written when candidate 7 was ruled a survivor (2026-09-07) — and they are **per module, not per candidate**: the `FeedbackDelay` sketch covers candidates 1, 2, 3 and 5; the `Dynamics` sketch covers 11–18 and 20–22. Each names its module, its API shape, its DSP and precision convention, its Python/C split, its latency, its parity probe and its cost against an existing kernel's per-block multiply count.

#### `audioecho.FeedbackDelay` — the additive options (candidates 1, 2, 3, 5)

**Module** `audioecho` (audioif's own), `FeedbackDelay`.

**API** `FeedbackDelay(..., wow_shape=buf)` / `set(wow_shape=buf)`: ReadableBuffer of int16 Q15, one period, power-of-two length 2..4096; `None` = today's sine. A buffer, so handle it beside `sample_rate`/`max_delay_ms` (FeedbackDelay.c:39-40), not in the float table (:19-29). **No BlockInput** — this node has no synthio block slots, every option is a plain float (:39-56), which is why the shape must live in C.

**DSP** float working precision per the kernel's own comment (audioif_feedback_delay.c:4-7); line int16 (:255, to_s16 :186-194), table Q15 read as `t*(1/32768)` like the line. With no table the magic-circle pair runs untouched (:209-210), so existing goldens hold byte-for-byte. With a table, add a uint32 Q32 phase accumulator, step `wow_hz*2^32/rate` set in the OPT_WOW_HZ case (:111-115); `i = phase>>(32-log2N)`, interpolate `tab[i],tab[i+1]`, substitute for `state->wow_sine` at :212-213. Keep stepping the magic circle so `wow_am_depth` stays locked. A ramp period is a linear clock ramp (F1); a shaped-edge two-level table bounds the post-step first difference (F6).

**Python/C** Python builds the `array('h')` table; C does phase, index, interp.

**Latency** zero; nothing looks ahead.

**Probe** two cases appended to tests/parity/feedback_delay_probe.py (CASES form; verify_dsp.py:47,:57 pins one cross-interpreter hash): 64-point ramp, 64-point shaped step, both at `wow_hz=5, wow_depth_ms=3`. Defaults unchanged = existing `wow`/`everything` hashes do not move.

**Cost** baseline 19 float multiplies/stereo frame (:209,:210,:213,:228,:249,:253-254,:256,:261) = 4864/block; the table drops 2, adds 2 — net ~0 plus a load, under 1 us on P4 or S3 vs a 5.33 ms block (~10 cyc/mult; baseline ~122 us P4, ~203 us S3).

> *Note:* this sketch is written for `wow_shape`. Candidates 2 (delay slew), 3 (`wow_am_depth`) and 5 (in-loop pitch shift) are carried under it in the record and **do not have sketches of their own**; their design detail lives in their need statements and verdicts above (in particular: the slew must be a linear rate limit, not a one-pole; `wow_am_depth` must drive the wet gain by −s; the pitch shift inserts after the damping filter alongside the existing in-loop one-poles and cubic clip at `:231-243`). Phase 1 should split them before filing the audioif issues.

#### `audiodynamics.Dynamics` — the additive options (candidates 11–18, 20–22)

**Module** `audiodynamics` — four additive options on the existing own node.

**API** `fast_attack_ms=1.0, fast_release_ms=50.0, slow_attack_ms=25.0, slow_release_ms=300.0`, constructor and `set()`, plain floats (Dynamics.c:19-31 is scalar). Defaults are exactly the literals at audioif_dynamics.c:215/:217/:219/:221, so an unset node is byte-identical to today.

**DSP** Move those four `audioif_dynamics_ms_to_coef()` calls from process entry into `audioif_dynamics_config_t` as `fast_attack_coef` etc. Four enum entries appended after `AUDIOIF_DYNAMICS_OPT_TRUE_PEAK` (audioif_dynamics.h:36-47; that order is the bindings' keyword order, so append only), four rows in `dynamics_option_names[]`. Keep the sentinel: `config_init` leaves them 0.0f, `config_finish` fills 1/50/25/300 if still zero, as attack/release at :42-51. Arithmetic unchanged: float coefficients and envelopes (:286-289). Python owns Exciter's Transient Time macro — tau maps to the four times at the literals' ratios (tau/50, tau, tau/2, 6*tau); C sees four milliseconds.

**Latency** Zero: one-pole followers. `lookahead_ms` stays the node's only latency option, default 0 (audioif_dynamics.h:73-76).

**Probe** Extend `dynamics_extras_probe.py`, not `dynamics_probe.py` — the oracle never had these (docstring 5-10). Case 1 sets none and must match `dynamics_probe.py`'s `transient` checksums byte for byte; then each option alone; then tau = 8/20/150 ms, **measuring** the step reaching within 1 dB of steady state in tau +/-25% (Exciter T5's clause). Planted fault: swap fast_att and slow_att, that measurement must fail.

**Cost** Nothing per sample; it *removes* 4 `expf` per process() call (:215-222). The transient path stays 256 frames x (2 muls :286-289 + 2 `logf` :291-292) + 256 `expf` (:310) per stereo block.

> *Note:* this sketch is written for candidate 11. The other ten `Dynamics` survivors are carried under it and **do not have sketches of their own** — RMS detection, the feedback topology, the true-peak FIR, the side-chain band and key, the `depth_db` floor, the gate state machine, relative-threshold detection, the program-dependent attack, the second envelope pair and the peak-hold each need their own API line, state field and probe case. Phase 1 must write them before the audioif issues are filed; the cost and latency arguments are in the verdicts above.

#### `audiobiquad` — the DC-clean biquad and all-pass (candidate 9)

**Module** New own module `audiobiquad`: `Biquad` and `AllPass` (Gate 0 names it). Copy the cookbook algebra, don't touch frozen `audioif_biquad.c`; share `audioif_sincos_reflect()` (audioif_trig.c:72) so both agree at one W0.

**API** `Biquad(mode, frequency=1000.0, Q=0.7071, gain_db=0.0, sample_rate, mix=1.0)`, modes as audioif_biquad.c:76-113; `AllPass(stages=4, frequency, feedback=0.0, mix=1.0)`. `frequency`/`feedback` are synthio BlockInputs (LadderFilter.md:281-283); `feedback` is **not** clamped — 0.0 is exactly 0, unlike audiofilters/Phaser.c:211.

**DSP** Direct Form I, **float32** state and coefficients — the own-kernel convention (audioif_dynamics.c:239, :313-319), and the ask: the frozen integer recursion (audioif_biquad.c:169-178) can park on a non-zero `y` and hold it. A flush guard (`|y| < 1e-20f -> 0`) makes "reaches exact zero" literal. AllPass stage `v = c*(x - s_out) + s_in`, a state pair per stage per channel; the block value interpolates linearly to a per-sample `c` — what P2/P6 want. Python: mode names, macro->(f,Q,gain_db), GraphicEQ's ten bands. C: coefficients and recursion.

**Latency** Zero, both kernels; no option adds any, `latency_samples` is 0.

**Probe** `filter_f32_probe.py`, extras-probe shape, not byte-gated against the port. Exact-zero tail after a full-scale burst at 31.25/62.5 Hz; the null at `feedback=0.0`; dB agreement with `audiofilters.Filter` mid-band. Planted fault: restore the saturating int16 write-back, the tail case must fail.

**Cost** Biquad 5 muls/sample (audioif_biquad.c:170-172) x 512 = 2560 float muls/block, the frozen kernel's count, 32- not 64-bit: ~8-15 us P4, 15-30 us S3. AllPass 4 stages x 2 muls (audioif_phaser.c:32-35) + fb + mix = 10/sample, 5120/block: ~15-30 us P4, 30-60 us S3; under 1% of 5.33 ms.

#### `audioshaper.Waveshaper` — oversampled table waveshaper (candidate 7)

**Module** new own module `audioshaper` (candidate 8's module), kernel `shared/audioif_shaper.c/.h`.

**API** `Waveshaper(source, *, curve, oversample=4, pre_filter_hz=0.0, pre_gain=1.0, bias=0.0, post_gain=1.0, mix=1.0)`; `curve` (int16 Q15, computed on CPython, shipped as data) and `oversample` (×2/×4/×8) construction-time, the rest in `set()`. **`pre_gain` and `bias` may be BlockInputs**, against the own-node scalar convention (Dynamics.c:19-31): `Tremolo` B4 and `Fuzz`'s gating move the operating point per sample.

**DSP** int16 in, **float** working, int16 out — the own-kernel convention (audioif_dynamics.c:239; clamp back :313-319); table read as `t·(1/32768)`. Per base sample: optional first-order pre-filter, `x = pre_gain·x + bias`, up through cascaded two-path polyphase **half-band IIR** all-passes (4 muls/stage/sample), a lerp lookup per shaped sample, decimation, `post_gain`, mix, `to_s16`. Minimum-phase: no bulk delay, `latency_samples` **0** (Overdrive.md:109-110).

**Python/C** Python: Newton on the diode equation → an `array('h')` of 1024–4096 points, **never built on the target** (vision §6), plus the macro→gain/bias law. C: filters, lookup, clamp.

**Probe** new `tests/parity/waveshaper_probe.py` in feedback_delay_probe.py's shape (argv module, `CASES`, per-block FNV), **golden from the port, oracle None** — no CircuitPython ancestor (docstring :5-7). Cases: `mix=0` wire; ×1/×2/×4/×8; `bias` as a block; 1010 Hz −6 dBFS.

**Cost** per stereo 256-frame block, against audioif_multiply's 3 muls/sample (audioif_multiply.c:38, :39) = 1536/block, priced P4 1 % / S3 2 % (RingMod.md:271-273): **×2 ≈7.2 k muls (P4 ~5 %, S3 ~9 %), ×4 ≈16.4 k (~11 %, ~21 %), ×8 ≈34.8 k (~23 %, ~45 %)**. ×8 misses the S3's 0.25 budget (Saturation.md:751) — the "Lean" ×2 patch's job. **Phase 1 owes the alias floor at each factor:** non-harmonic energy vs the −60 dB bar (Overdrive T7, Distortion A1, Fuzz A4, Saturation A4) at 1010 and 3700 Hz, 48 and 44.1 kHz, both boards.

> *Note:* candidate 8 (hysteresis) is an **option on this node**, [sketched below](#waveshaper-hysteresis-option-candidate-8).

#### Waveshaper hysteresis option (candidate 8)

**Module** `audioshaper` — an *option* on the A1 waveshaper, not a node (own module per family, LadderFilter.md:279-281).

**API** `Waveshaper(..., hysteresis=0.0, hysteresis_width=0.02)`, both in `set()`, plain floats not BlockInputs: they move a recursion's fixed point, and own-node keyword tables are scalars (Dynamics.c:19-31). `hysteresis=0.0` is off, byte-identical to the static node.

**DSP** A *play* (backlash) operator ahead of the table, in `float` — the own-kernel convention is int16 in, float per-sample, int16 out (audioif_dynamics.c:239, :313-319; feedback_delay `soft_clip`, :180-184). Per channel one state `p`, one direction byte `d`: `if (x > p+w) {p = x-w; d = +1;} else if (x < p-w) {p = x+w; d = -1;}`, then the existing lookup on `p`, `d` picking the half-width so the loop may be asymmetric. `w = hysteresis_width * (1 + hysteresis*drive)`. Enclosed area is 2w x the table's output span; the span saturates as drive rises while `w` grows, so normalised area rises monotonically — TP3's shape by construction. Python: drive macro -> the two floats. C: operator and table.

**Latency** Zero; the option adds none. All latency here is A1's oversampling FIR, in `latency_samples`.

**Probe** `waveshaper_probe.py` in the `dynamics_extras_probe.py` shape (no oracle; fixture from the port, docstring 1-12). Case 1 at `hysteresis=0.0` reproduces the static checksums; then a triangle sweep at three drives, area measured; planted fault — force `d` constant, monotonicity must fail.

**Cost** No multiplies: 2 compares + 1 add per oversampled sample. At 4x, 2048 shaped samples per stereo 256-frame block, ~6k int ops, against `audioif_multiply`'s 1536 muls for that block (audioif_multiply.c:38-39). ~10 us P4 (400 MHz), ~20 us S3 (240 MHz): under 0.4% of 5.33 ms.

> *Note:* this sketch presupposes the waveshaper node of candidate 7, which **survives** on Arthur's ruling of 2026-09-07 — [its sketch](#audioshaperwaveshaper--oversampled-table-waveshaper-candidate-7), and [The waveshaper problem](#the-waveshaper-problem) for why.

#### `audioladder.Ladder` (candidate 24)

**Module** new own module `audioladder`, kernel `shared/audioif_ladder.c/.h`, recorded in `docs/upstream-diff.md` as audioif's own.

**API** `Ladder(sample_rate=48000, channel_count=2)`; constructor and `set()` take `cutoff_hz`, `resonance` (k 0–4.2), `drive`, `poles` (1–4), `passband_comp` (default 0), `oversample` (1|2, default 2), `mix`. Floats only, no BlockInput (own-node convention, Dynamics.c:20-30). The class re-`set()`s `cutoff_hz` once a block, ~187 Hz at 48 kHz (upstream-diff.md:730).

**DSP** float working precision, int16 in/out, matching audioif_feedback_delay.c:3-7. Per sample per channel: `x = in/32768 · drive_gain`; `u = x − k·sat(y4_prev)` (one-sample-delayed feedback, no iteration); four TPT one-poles `v=(u−z)·G; y=v+z; z=y+v`; tap the `poles`-th stage, scale by `1 + passband_comp·k`, mix, `to_s16` (:186-194). `sat` is the palette's cubic (:180-184) — odd, third-harmonic only, two multiplies, what T4(b)/(c) need. `G = tan(πf/fs)/(1+tan)` is computed once per `set()`, precedent :30-38, never per sample. 2× oversampling: linear interpolation up, two-tap average down — half a sample of group delay, reported latency 0, proved by the click test. Python owns macro mapping and the block-rate glide.

**Probe** new `tests/parity/ladder_probe.py` in feedback_delay_probe.py's shape (per-block FNV checksum, golden only): `mix=0` wire, k = 0/2/3.9/4.0, drive 0/0.5/1, poles 1–4, oversample on/off, mid-stream `set()`.

**Cost** ~50 float multiplies per stereo frame at 2× (2 ch × 2 passes × [4 stages + feedback + 3 cubic + drive + comp], plus mix and resampler) ≈ 12.8 k per 256-frame stereo block, against FeedbackDelay's 23/frame ≈ 5.9 k (:209-263): ≈2.2× at 2×, ≈1.1× oversample off, no per-sample transcendental, same ratio on P4 and S3.

#### `audioverb.Tank` (candidate 25)

**Module** new own module `audioverb`, kernel `shared/audioif_tank.c/.h`, recorded in upstream-diff.md as own. Freeverb untouched.

**API** `Tank(sample_rate=48000, channel_count=2, delays=<line lengths>, taps=<tap indices>, max_predelay_ms=200)` — character and Size re-cut the topology, so those tables come from Python. `set()`: `decay`, `diffusion`, `damping_hz`, `bandwidth_hz`, `low_cut_hz`, `predelay_ms`, `mod_depth_ms`, `mod_rate_hz`, `drive`, `width`, `tone_db`, `mix`. Floats and arrays only, no BlockInput (FeedbackDelay.c:20-29).

**DSP** float arithmetic over int16 lines, matching audioif_feedback_delay.c:3-7, int16 line write at :254. Predelay → bandwidth one-pole → four Schroeder all-passes → a two-half tank; each half: a modulated all-pass (fractional read off a quadrature LFO as at :209-214), a delay, a damping one-pole, the `decay` multiply, a second all-pass, crossed into the other half; each wet channel sums fixed taps from both halves. `drive` uses the palette cubic (:180-184). Hz→coefficient conversions run in C at `set()` (:30-38); Python computes the line tables and tap sets. Latency zero dry-to-wet; `predelay_ms` defaults 0, wet-only.

**Probe** new `tests/parity/tank_probe.py` in feedback_delay_probe.py's golden-checksum shape: `mix=0` wire, short/long decay, mod off/on, dispersion off/on, each character's table, starved.

**Cost** ~65 float multiplies per stereo frame (diffusion 8, tank 2×9, LFO 2, drive 3, bandwidth and low cut 4, tone 10, mix 4) ≈ 16.6 k per 256-frame stereo block. Freeverb spends 29 int16 multiplies per sample per channel (audioif_freeverb.c:28, :36, :38 ×8 combs, :42, :52-54) ≈ 14.9 k: ~1.1×, float not Q15. The P4 absorbs it; the S3 is the part to measure, `Plate — lean` the ~0.6× valve.

#### `audiomath.SubOctave` (candidate 27)

**Module:** `audiomath` (own).

**API:** `SubOctave(source, *, order=1, mix=1.0, threshold=0.01, hold_ms=8.0, sample_rate=48000, channel_count=2)`; `set()` takes the same four options mid-stream (`Multiply.c:105-121`). `source` is the only node input; no BlockInput (`Multiply` takes `mix` as a plain float, `:64-67`).

**DSP:** int16 in/out, Q15 coefficients, int32 intermediates — `audioif_multiply.c:38-45`'s convention; no float on the pull path. One divider drives both channels, fed by `x = (L+R)>>1`, so the pair stays phase-locked. Per frame: a Schmitt comparator on `x`, high above `+thr`, low below `-thr` (Q15); each low→high edge past the hold counter toggles FF1 (f/2) and reloads it; FF1's rising edge toggles FF2 (f/4, `order=2`). The ±1 square is a negate, not a multiply — `q = ff ? s : -s` per channel — then `:39-45`'s blend and clamp verbatim, `(dry*s + wet*q) >> 15`. Silence in, silence out: no edge, no toggle.

**Python/C:** all per-sample work in C; floats become Q15 and frames at set time (`audioif_multiply_set_mix:17-25`, `audioif_dynamics.c:95`).

**Latency:** zero; no option adds any — the hold gate debounces the comparator, it never delays the signal.

**Probe:** `tests/parity/suboctave_probe.py` in `multiply_probe.py`'s shape — own module, no oracle (`:5-12`); per-block checksum diffed across interpreters (`:65-68`). Cases: 220 Hz/20000-peak sine and its 221 Hz twin, `order` 1 and 2, `mix` 0/0.35/1, a two-tone for the hold gate, silence.

**Cost:** two Q15 multiplies and a clamp per sample, one fewer than `audioif_multiply.c:38-45`'s three (the square is a negate), plus three compares and a counter. `Multiply` at that rate prices P4 1 %, S3 2 % of a stereo 256-frame block (`RingMod.md:271-273`); this is under it: **P4 ~1 %, S3 ~2 %**.

#### `audioroute.MidSide` (candidate 28)

**Module:** `audioroute` (own).

**API:** `MidSide(source, *, width=1.0, sample_rate=48000, channel_count=2)`; `set(width=)` mid-stream (`Multiply.c:105-121`). `source` is the only node input; no BlockInput — `width` is a plain float, clamped 0…2 in C as `audioif_multiply_set_mix` clamps `mix` (`:17-25`).

**DSP:** int16 in/out, Q15 `width`, int32 intermediates — `audioif_multiply.c:38-45`'s convention; no state, no float on the pull path. Per frame: `sum = L+R`, `diff = L-R`, `q = (w*diff)>>15`, `outL = clamp16((sum+q+1)>>1)`, `outR = clamp16((sum-q+1)>>1)`. Halving LAST makes the identity exact: at `width=1` (`w = 32768`) `q == diff` exactly (65535×32768 fits int32), so `sum+q = 2L` and `(2L+1)>>1 = L` for every int16 — a byte-identical wire with no special case. The `+1` rounds both halves the same way, holding the mono sum to 1 LSB. At `width=2` the numerator reaches ±131070 — hence the clamp. `channel_count=1` is passthrough (`diff = 0`).

**Python/C:** every frame in C; Python converts `width` to Q15 once per `set()`.

**Latency:** zero, no option adds any — the trait the `FeedbackDelay` composition cannot hold, its delay clamping at one frame (`audioif_feedback_delay.c:81-83`).

**Probe:** `tests/parity/midside_probe.py` in `multiply_probe.py`'s shape — own module, no oracle (`:5-12`); per-block checksum (`:65-68`) over a decorrelated ramp at `width` 0/0.5/1/1.5/2, plus two assertions checksums cannot make: at `width=1` output bytes equal input bytes, and at every width `|(outL+outR) - (L+R)| <= 1` per frame.

**Cost:** one Q15 multiply, two adds, two shifts, two clamps per FRAME — a sixth of `audioif_multiply.c:38-45`'s three multiplies per sample. `Multiply` prices P4 1 %, S3 2 % of a stereo 256-frame block (`RingMod.md:271-273`): **P4 <0.3 %, S3 <0.5 %**.

#### `audioconvolve.Convolver` — non-uniform partitioning (candidate 26)

**Recorded, not built.** No fixed trait needs it, and ConvolutionReverb D3 as fixed would be disconfirmed by it. D3's second clause is class-side and costs no kernel change: `Convolver.latency` returns `AUDIOIF_CONVOLVE_FRAMES` unconditionally (Convolver.c:240-242) and should report the loaded state instead.

**Module** existing own module `audioconvolve`; a construction-time option on `shared/audioif_convolve.c`.

**API** `Convolver(…, head_taps=0)` — 0 keeps today's behaviour byte-identical, non-zero selects the hybrid. Construction-time only, never `set()`: it re-cuts the frequency-delay line. `latency` then reads `head_taps ? 0 : (loaded ? 256 : 0)`.

**DSP** float throughout, unchanged (the complex MAC is :287-290; FFT 512, BINS 257, audioif_convolve.h:51-56). The hybrid adds a direct-form time-domain FIR over the impulse's first `head_taps`, run per sample at zero latency, and delays each uniform 256-frame partition one extra block so the halves line up; the overlap-save window and FDL loop (:268-290) are untouched. Python still hands over int16 taps and a gain.

**Probe** extend `tests/parity/convolve_probe.py`: `head_taps=0` must reproduce the existing golden exactly, then click cases at 64 and 256 head taps showing first arrival at frame 0, against the unloaded case.

**Cost** the reason to defer, more than the missing trait. Today's CMAC is 4 multiplies per bin per loaded partition (:287-290): 2 ch × 8 partitions × 4 × 257 ≈ 16.4 k per 256-frame stereo block plus four 512-point rFFTs. A 64-tap head is 64 multiplies per sample per channel = 2 × 256 × 64 ≈ 32.8 k per block — it triples the node on the P4 and does not fit the S3 beside anything else.

### Asks killed inside the seeds, before the node list

Twenty-five asks were raised and refuted by the palette-verification pass **within the seeds themselves**, so they never reached the two-refuter list. Six of them reappear there because a later seed or the merge re-raised them.

| Unit | Ask refuted in-seed | Trait it claimed |
|---|---|---|
| Tremolo/AutoPan/RingMod | table-driven phase-continuous LFO inside `audiomath` (N1) — raised by all three | Tremolo, AutoPan (no trait id), RingMod W3 |
| Rotary | `wow_phase_deg` (R2); `wow_damping_depth` (R4) | Rotary T7; T5(a) |
| Overdrive/Distortion | oversampling from `audiospeed.SpeedChanger`; a curve from cascaded `Multiply`; a 3 Hz DC blocker node | (self-raised candidates, all measured and killed) |
| Bitcrusher/Exciter | `LoFi` node (B1) on three traits; oversampled waveshaper (E1); envelope-following bias (E2) on two traits | Bitcrusher T1/T4/T5; Exciter T7; T5/T6 |
| Compressor/Limiter | second release stage (N-C1); geometric envelope scaling (N-C3); second brickwall stage (N-L1) | O1/O2/M3; V1; L2/L3 |
| NoiseGate/MultibandCompressor | duck mode (N-GATE-4); bounded pull on `Splitter` (N-MB-1) | G7; M5 |
| ParametricEQ/LadderFilter | a unity-plus gain node; the resonance-shortfall justification | (surface); LadderFilter's node ask, re-justified |
| CombFilter/DynamicEQ | signed feedback (Ask 1); a gain-reduction read-out; a fifth `Splitter` tap | T4; (already exists as `gain_reduction_db()`); (capped at 4) |
| TapeDelay/MultiTapDelay | multiple read heads (N1); a second modulation oscillator (N2 as asked) | T5; T4's two-component clause |
| PingPongDelay | independent ping/pong times; a mono cross-feed path | (surface); `cross_feed` at `channel_count` 1 |

---

## audioif#23 — the settled DC residual, verbatim

The roadmap's Gate 0 requires the 48 kHz settled-state measurement for **every shipped EQ and Phaser configuration**, with the result posted to audioif#23 either way. The table below is the measurement as recorded. **`all_reach_zero` is FALSE** — three configurations hold a permanent non-zero constant — so the DC-clean candidate is **not** refuted, and candidate 9 stands.

**audioif#23 — settled DC residual of the shipped fixed-point biquad.** 48 kHz stereo, 0.09 s of 1 kHz at −6 dBFS (peak 16422) then digital silence, pulled to 600 blocks. "Settled residual" is the peak |sample| of the final block; every non-zero residual below is a single constant value across all frames of the block (true DC, not ringing). "Blocks to settle" counts output blocks after the first all-silent input block until the output block stops changing for good.

| Configuration | W0 (rad/sample) | Settled residual (LSB) | Blocks to settle |
|---|---|---|---|
| LowPass, defaults (1000 Hz, q=0.707) | 0.130900 | 0 | 0 |
| HighPass, defaults (1000 Hz, q=0.707) | 0.130900 | 0 | 0 |
| BandPass, defaults (1000 Hz, q=0.707) | 0.130900 | 0 | 0 |
| Notch, defaults (1000 Hz, q=0.707) | 0.130900 | 0 | 0 |
| ParametricEQ, defaults `bands=()` — builds **no** biquad, `_output = source` | n/a | 0 | 0 |
| ParametricEQ, one bell 1000 Hz +6 dB q=1.4 (added: the default is a wire) | 0.130900 | 0 | 1 |
| GraphicEQ, defaults (flat ⇒ every band dropped, **no** biquad) | n/a | 0 | 0 |
| GraphicEQ, +6 dB on the 1 kHz band, q=1.4 (added: the default is a wire) | 0.130900 | 0 | 1 |
| DynamicEQ, defaults (3000 Hz, q=2.0; notch + band-pass) † | 0.392699 | 0 | 1 |
| Phaser, defaults (6 all-pass stages) ‡ | 0.143990 | **4** (constant −4) | 20 |
| LowPass, 100 Hz, default q=0.707 | 0.013090 | **1** (constant +1) | 2 |
| LowPass, 40 Hz, q=8 | 0.005236 | **4** (constant −4) | 33 |

† DynamicEQ's output is its `audiomixer.Mixer`, which hands out 128-frame blocks; every other row is 512 frames per block. Its "1 block" is therefore ~2.7 ms, not ~10.7 ms.

‡ The Phaser does **not** use the shipped biquad. `grep -rln audioif_biquad /home/brad/gh/pydevices/audioif/src/` matches only `synthio/Biquad.{c,h}`, `shared/audioif_biquad.{c,h}`, `shared/audioif_trig.h` and `cpython/_audioif.c` — not `shared/audioif_phaser.c`. Its hold comes from its own `int16_t allpass_words[]` / `feedback_words[]` (audioif_phaser.c:28-38), which are in plain sample units with no fractional bits. Listed because the brief asked for it; it is a separate defect from #23, in a CircuitPython-ported node.

**Endurance.** The three non-zero residuals are permanent, not slow decays: re-run to 3000 blocks (32 s of audio) with the settle window excluded, the set of distinct sample values over blocks 60..3000 is exactly `[1]` for LowPass 100 Hz, `[-4]` for LowPass 40 Hz q=8, and `[-4]` for the Phaser. Block 100 and block 2999 are identical.

**Why a residual sticks (from `/home/brad/gh/pydevices/audioif/src/shared/audioif_biquad.h` and `.c`, line numbers by `grep -n`).** The header defines `AUDIOIF_BIQUAD_STATE_SHIFT 12` (audioif_biquad.h:14) and states that `audioif_biquad_state_t.y[2]` "carries AUDIOIF_BIQUAD_STATE_SHIFT extra fractional bits" while `x[2]` is in sample units (audioif_biquad.h:22-26). In `audioif_biquad_process` (audioif_biquad.c:159-182) the feedback recursion runs entirely in that 12-extra-bit domain: with the input and both `x` history taps at zero, `accumulator = -(a1*y0 + a2*y1)`, `output = (accumulator + rounding) >> shift` (line 173), and the sample the caller sees is `(output + 2048) >> 12` (lines 177-178). Two consequences: (a) the recursion is round-to-nearest at every step, so once the per-sample change in `y` falls below half a quantum the state reproduces itself exactly and stops moving — there is no dither and no leak term to drag it to zero; (b) because the state has 12 bits below the sample LSB, a parked `y` of magnitude ≥ 2048 still rounds up to a visible ±1 or more at the output. The lower W0 is, the closer `a1 → -2·2^shift`, `a2 → +2^shift` and the sooner the increment falls under a quantum — which is exactly the ordering measured: 0 LSB at W0 = 0.1309, 1 LSB at W0 = 0.01309, 4 LSB at W0 = 0.005236 with q=8 (high Q also lengthens the approach, 33 blocks vs 2).

**Harness note that mattered.** `audiocore.RawSample._get_buffer` returns the *whole* buffer in one call (32880 frames here), and `audioroute.Splitter._pull` writes that straight into an 8192-frame ring whose write drags every lagging tap cursor forward (`audioif_splitter.c:33-38`). Feeding DynamicEQ a plain RawSample therefore laps the ring and reads only the silent tail — output is all zeros and the measurement is void. The final probe replaces RawSample with a 512-frame-per-pull block source, which is why every row above shows a non-zero tone peak (11618…28521) before the silence.

### Reading it

Three findings the seeds and the Gate 0 answer must carry:

1. **The candidate is not refuted.** The refutation condition the roadmap sets — "refuted only if every configuration reaches exact zero" — is not met: three configurations hold a permanent constant, verified to 32 s of audio.
2. **Two of the twelve rows are wires, not measurements.** `ParametricEQ` at `bands=()` and `GraphicEQ` flat build no biquad at all, so their zeros say nothing; the probe added one bell each so the table measures the biquad rather than the default. This is the absence-reads-as-agreement shape, caught inside the measurement.
3. **The Phaser row is a different defect in a different, ported kernel.** It is listed because Gate 0 asked for it, but `audioif_phaser.c` does not call `audioif_biquad` at all — its hold comes from its own int16 `allpass_words[]`, which is why candidate 9 must carry an all-pass kernel beside the biquad, and why the Phaser's row cannot be fixed by fixing #23.
4. **Every future number must name its rate and channel count.** The refuter's independent re-measurement found the Phaser hold at 48 kHz stereo and **exact zero** at 22.05 kHz mono on the identical probe. A run at another rate will read clean and look like the defect is gone.

**Not yet done:** the results have not been posted to audioif#23. The roadmap's Phase 0 work item requires it "either way".

---

## The measurement-kit spec

**Written:** [`docs/effects-kit-spec.md`](effects-kit-spec.md) — 46.4 KB on disk after the refutation pass. Not committed; Arthur commits.

One grep over the 46 seeds pulled the Measurement cell of every Tier 2 row and they collapse to **nineteen distinct measurements**, because the seeds' local names (ENV, LAW, CLICK, SB, SPLIT, LEVELS, M1–M8…) are the same dozen algorithms under different labels.

**Shape.** Sample rate, `channel_count` and interpreter are **axes over the whole kit**, not measurements of their own. The renderer is stdlib-only and dual-runtime (WAV + FNV digest from CPython, desktop MicroPython and the patched CircuitPython); every FFT, fit and envelope runs afterwards on the desktop under CPython + numpy. The kit never asks MicroPython for an FFT — the sole exception is the board cost runner, whose arithmetic is a division.

**Reuse ledger (§2), with line numbers.** `render_component.py:39` gives the renderer's shape; `test_cpython_effects_library.py` gives the numpy-free analysis primitives lifted into `tools/effect_analysis.py` (`_fft:143`, `spectrum:121`, `harmonic_db:174`, `rms:90`/`peak:63`, `sine:80`, `burst:192`, `channels:204`), while its old-surface assertions, its module-level `configure()` at `:22` and `spectrum()`'s hardcoded `SAMPLE_RATE / float(size)` at `:140` are discarded; `measure_hits.py` already carries the τ→T60 estimator DECAY needs; `measure_voice_headroom.py:78-88` carries the whole cost method; `compare_rig.py` / `test_rig_comparator.py` contribute the discipline (a floor, and a control that must pass) rather than code; DIGEST is `audioif/tests/parity/effects_component_probe.py:15`'s FNV-1a used unchanged.

**Contents.** Probes fixed as data under `tools/effect_probes/` with a digest manifest so a stale probe cannot pass as fresh. Six Tier 1 measurements (WIRE, TAIL, LEVEL, CLICK, STATE, DIGEST); eleven Tier 2 (RESPONSE with its two excitations and a stated selection rule, SPECTRUM, CURVE, GAINTRACE, ENVELOPE, IFREQ, TAPS, DECAY, STEREO, RESIDUAL, TRUEPEAK); two platform runners — COST (blocks/s and rt factor per class and node on the P4 and S3, driven with mpftp's write-to-file-then-`get` pattern, heartbeats against the ~10 s quiet timeout, `/main.py` renamed aside) and ROUNDTRIP (board loopback, click through a wire and a five-effect chain at each `chunk_ms` / `lookahead_chunks` / `LOW_LATENCY_QUEUE_MS` / `ibuf` setting, starvation counted not guessed).

**Every measurement names a planted fault**, and §6 maps them onto workspace-craft's three ways a check fails to fail: *absence reads as agreement* (COST refuses a silent render, ROUNDTRIP a run with no correlated capture); *a summarising statistic cancels* (DIGEST's fault is the exact +256/−1 LSB pair `sum(data)` hides); *the material cannot reach the mechanism* (RESPONSE's excitation rule, ENVELOPE's record-length rule). Every fault must land as a committed test in `tests/test_effect_kit.py` alongside a control that passes, with the rule that **a measurement whose planted-fault run is not committed is not one a class gate may cite.**

### What the kit's refuter found

The refuter answered four questions and fixed the spec in place. **Six of the planted faults would not have turned their measurement red:**

| Measurement | Why the first draft's fault did not fire |
|---|---|
| WIRE | ×32767/32768 with round-half-to-even returns `v` unchanged for every \|v\| ≤ 16384, so the faulted render is byte-identical on material peaking below −6.02 dBFS — green on `chord`, one of the two probes it named. |
| TAIL | "Red on residual; the tail-length readout stays green" is false: a state that never returns to zero has no last non-zero sample, so the length readout goes red too. The measurement had no control at all. |
| CURVE | The fault is a clamped drive knob and the stated red is THD monotonicity — that is **SPECTRUM's** readout. A fault whose red appears elsewhere leaves CURVE unproven. |
| IFREQ | "Hold the modulation depth at zero" is an inert modulator: every readout flattens at once. Always-red, which §6 forbids. |
| TRUEPEAK | Factually wrong against the seed. Reading sample peak does not collapse to one number; it returns a different, plausible pair and passes. The real fault is that the flag-off build then reads −6.00 dBFS, *exactly its ceiling*, certifying L1 while 3.05 dB escapes. |
| ROUNDTRIP | The cross-correlation guard catches the wire-out fault and **not** the second one it is written for: correlating the emitted click against the *playback* buffer is correlating it with itself, peaks at lag ≈ 0, satisfies the guard, and the latency collapses. |

Two more were weaker: RESIDUAL's fault fires only under *floor* truncation, and STATE's allocation check is flat when nothing was pulled.

**A census correction:** the seeds carry **332** Tier 2 rows by the refuter's count, against the **327** counted here by parsing each seed's Tier 2 table — a difference of five that nobody has reconciled. The 327 is the figure this survey uses because it reconciles exactly against all sixteen units' own tallies. *(The refuter's own note: the first draft's count "missed `Compressor.md`'s **21** entirely, the one seed whose traits live in four per-character sub-tables.")*

**A tool the spec had omitted:** `audioif/lib/audiorender/` — `events.py:27` `build_events(..., block=256)`, `events.py:79` `deliver()`, `tempo.py:12` `TempoMap` (which the transport `Rack` R7 and STATE's `tempo_sync` need and the renderer had no flag for), `wav.py:8`. Added as a reuse row.

**A fourth axis the spec lacked — source block size.** `MultibandCompressor` M5 requires byte-identical output from 256 / 8192 / 16384 / 20000 / 32768-frame sources, and A-M5 measures the shipped class returning **zero non-zero samples** at three of them. `RawSample.get_buffer()` returns the whole array in one call, so a kit that loads a probe WAV into one `RawSample` renders silence for the whole split family. This is the same trap the audioif#23 harness hit.

**A twentieth measurement, NULL** — defeated-path rows with a stated floor (`Octaver` O3's −80 dBFS, and eight seed *controls that must pass*); a digest cannot express a floor. Plus **DIGEST mode (b)**, build-vs-build comparison, which `GraphicEQ` T4, `Rack` R3/R6 and `Compressor`'s paired build had nowhere to live in. Plus a **level search** (many rows are stated *at a GR depth*, not at an input level — "at exactly 10 dB of GR" — and are unmeasurable without one). Plus `t50`, fit residual beside every fitted number, THD's N and window, and block-rate sideband lines.

**Probes that cannot serve rows as written:** `tones_step` was 1/12-octave 50 Hz–10 kHz where `MultibandCompressor` SUM needs 1/6-octave 30 Hz–20 kHz; there is no square or 10 %-duty train at matched RMS *and* matched peak (`Compressor` V3, XF, `NoiseGate` G6), no two-tone sibilant (`DeEsser` LEVEL), **no worst-phase f_s/4 tone — which `Limiter` L1's own disconfirmation clause makes mandatory** — no N-dB-over-threshold step (`Compressor` V2), no burst train (M3), and fixed levels only where `StereoWidener` W6 needs −12 dBFS and `Overdrive` T1 needs −72.

**Also corrected:** the DIGEST fault's arithmetic. Under +256 LSB / −1 LSB the unsigned-byte sum moves by **exactly 0**, not 255 — the stronger statement, and the probe docstring's own.

### What the refuter left open

Recorded in the spec's §8, and open at the gate:

- Cell-by-cell resolution of the seeds' six local vocabularies to the twenty measurement names (and three names collide: `ENV` means ENVELOPE in `AutoPan` but GAINTRACE in `NoiseGate`/`Expander`/`DeEsser`; `LEVEL` is Tier 1 here but a sibilance GR trace in `DeEsser`; `CLICK` is Tier 1 latency here, impulse-vs-dry in `MultibandCompressor`, and a zipper spectrum in `NoiseGate`).
- The **cost** of the block-size ladder — which measurements run all five sizes and which run 256 and 16384.
- GAINTRACE's level-search tolerance (0.1 dB is written and unsourced) and what it does when GR never reaches the target.
- `staircase` against `Limiter` L6's "24 dB above the ceiling", which is off-scale at a high ceiling.
- ~~`tools/probes/` sits one word from the existing `tools/probes_scratch/` (the SPICE composers) — pick another name.~~ **Settled 2026-09-07:** the kit spec now names the directory **`tools/effect_probes/`** throughout, so Phase 1 never builds against a name the spec itself calls the naming half of a stale-artifact bug. `tools/probes_scratch/` is untouched.
- Whether COST's per-node figures can be taken at all on nodes that only exist inside a class's graph.

---

## The SPICE proof

**Status: proven, re-run, and used as the worked example.** The workflow lives at [`tools/spice/ts808/`](../tools/spice/ts808/README.md) (audiocomponents `6ceace0`, 2026-09-06): a netlist we transcribed, `run.sh` driving `/usr/bin/ngspice`, `analyze.py` exporting the clipper's transfer curve and the tone stack's response at three knob positions as data the kit can compare against.

**Re-run 2026-09-07** with `out/` deleted first: output **identical line for line** to the README's recorded table and to `Overdrive.md` Appendix A. Every SPICE figure the seed's T1–T6 quote is present with its analytic value beside it — the drive stage's 720.6 Hz fitted corner against 720.5 Hz analytic, gains 23.3 / 38.8 / 37.7 dB, plateau 107.8 against 118.2 ideal, the nine THD/harmonic rows, and the nine tone points against a 796 Hz analytic corner to **0.03 dB** by an independent nodal solve.

**The transcription check.** Both stage drawings were fetched as PNGs and read as images; `models.lib` was checked against Nexperia's own `.prm` read in full and against the NJM4558 and TI RC4558 datasheets. **All 21 component values S1 supplies are confirmed, 16 of them twice (drawing *and* BOM); all fourteen model numbers check. No mismatch, and no trait row needed a "netlist unverified" mark.**

Four things the check turned up:

1. **A wrong claim in the SPICE README, corrected.** It said "the text summary gives the (−) input resistor as 1K, but 720 Hz and gain 118 both need 4K7". The page contains no such claim — R4 appears exactly once, in the BOM, as 4K7, and the drawing agrees. The netlist value was never in doubt; only the account of a conflict was wrong.
2. **The one real conflict is R8, and it touches T4.** Drawing and prose put 220 Ω on the tone wiper; the BOM reads "4 Resistors 1K (R1, R8, R11, R12) / 1 Resistor 220 (R10)". Arithmetic settles it: 220 Ω gives a zero at 3288 Hz and a boost of 14.9 dB, which is the page's own "3.2 kHz" and PedalPCB's independent 14.9 dB; the BOM reading gives 723.4 Hz and 6.0 dB, claimed nowhere. **T4's source cell now reads "S1's drawing and prose, not its BOM".**
3. **The mirror is missing every formula.** All eighteen `gif.latex` `<img>` tags point at one path returning a single 370-byte GIF reading `r_π << R12`. **No equation on the mirror is readable** — every number from S1 must come from prose, drawing or BOM, and any future citation to "the article's formula" was not read there.
4. **`RA` is 0 Ω by the page's own BOM note**, so omitting it from the netlist is exact, not a simplification.

Two smaller source defects recorded: **R7 has no BOM line at all**, and the page's designators self-contradict in two more places (the tone drawing labels *both* 1 K resistors "R11"; §1.6's prose calls R12 a 510 K and R13 a 10 K where the BOM says the reverse).

**A method finding for `agent-knowledge/instrument-sources.md`** (not yet written there): a `WebFetch` of this same page for its parts list returned a **clean, self-consistent** list with "R8: 220" and "R10: 220" — silently reconciling the contradiction and dropping the 1 K assignment that is the entire conflict. The file's PDF rule ("a fetch summary is a lead, not a citable fact") holds for HTML too, and **bites hardest exactly where the source disagrees with itself**, because a summariser's instinct is to make the list agree.

**Two files were edited outside `docs/effects/`:** `tools/spice/ts808/README.md` (the two corrected sentences above). It is the one file the brief names and leaving a known-false sentence in the worked example seemed worse than the overreach; the seed stands without it.

---

## Vision §10 — the open questions

### 1. The SPICE workflow — **ANSWERED**

The working form is proven on the TS808 and re-run this week: a netlist we transcribe under `tools/spice/<circuit>/`, `run.sh` calling ngspice, `analyze.py` exporting the transfer curve and the swept response as data, a knob position becoming a parameter sweep, and every SPICE number carried into the dossier beside an independent analytic value. Netlists we write are ours, MIT. The transcription discipline is now part of the workflow: read the drawing as an image at 3–5× *and* the BOM, record every conflict rather than reconciling it, and never take a fetch summary as the parts list. **Nine of the ten circuit-grade seeds have not yet run a deck** — ngspice decks are named as Station A's first job for `Distortion` (rat, ds1), `RingMod` (which would lift it from literature to circuit), `Octaver` (oc2), `Tremolo` (the 6G2 output stage, which B1's number depends on) and `Fuzz` (a germanium model).

### 2. The node list — **ANSWERED**

51 raw asks → 28 candidates → **23 survivors, 5 refuted, 0 unrefuted**, each with a need statement, two refutation records, and a cost estimate per board through ten per-module design sketches. **The hole is closed:** the waveshaper (candidate 7) was recorded refuted on two votes that both disclaim the scope; Arthur ruled it a survivor on 2026-09-07, and its sketch and cost are written. Nine audioif issues are owed and **eight are filed** — candidates 7 and 8 are the ninth, and it is not filed.

### 3. Oversampling — **OPEN**

Four seeds defer the same question to Phase 1 in the same words: the waveshaper's factor (×2/×4/×8) and its anti-aliasing filter, as a cost-versus-alias-floor table on both boards. `Overdrive` Q2 asks which factor reaches T7's −60 dB on the S3 inside Tier 3; `Fuzz` Q4 and `Saturation` Q5 ask it drive-family-wide, "answered once by Phase 1's cost/alias table"; `LadderFilter` Q1 asks for its saturator's table resolution and factor to be answered *with* the waveshaper's rather than separately. **What would settle it:** the Phase 1 table, measured on a P4 and an S3, with the lean-patch valve (`Fuzz` and `Saturation` already ship a ×2 lean patch and `A4` is graded at a stated factor). Nothing can settle it in Phase 0 — the node it prices does not exist yet, though candidate 7 now survives and its sketch carries a first ×2/×4/×8 cost estimate for the table to replace with measurement.

### 4. Compressor characters — **ANSWERED: NO**

Four characters over one detector are **not** honest to all four, and `Compressor`'s dossier answers so with evidence rather than deference: the four standouts differ in detector law, release law, ratio law and sidechain topology, so each character carries its own rows — **21 Tier 2 rows, FET 5 / Optical 5 / VCA 6 / Vari-Mu 5**, every character clearing the three-row bar on its own and none carried by another's. Three of the four need something the current detector does not have, and those needs became the surviving asks: **RMS detection** (V3 — peak and mean-|x| straddle the RMS value from opposite sides) and a **feedback detector topology** (F4/O5/M4/V5 — the 1176, the LA-2A and the Fairchild all tap the side chain after the gain cell). The optical two-stage release, which §10.4 named as the likely node, does **not** need one: two `Dynamics` in series measure t95/t50 = 27.9 against O1's ≥ 8, so N-C1 is refuted and the memory rides free on the slow stage's own attack coefficient.

### 5. The Octaver's mechanism — **ANSWERED: a divider**

Specifically a **synchronous multiplier clocked by a flip-flop divider**, not a square-wave switch and not a pitch shifter, read off the factory drawing and confirmed by two independent accounts of the CMOS flip-flop. The palette cannot do it: eight rendered compositions leave the f/2 line ≥ 42.5 dB down at the analyser's leakage floor, and the `audiodelays.PitchShift` the class ships today lands at 205.08 Hz — **−121.6 cents, not 220/2** — with up to 10.7 ms of wet delay against O5's zero-latency requirement. `audiomath.SubOctave` survives with a sketch and a cost (P4 ~1 %, S3 ~2 % of a stereo block). Left open in the seed: an octave *up* (the standout has none; squaring is the honest mechanism and a full-wave-rectifier octave-up fuzz is a different standout), and the two output filters' corners, which Station A's `tools/spice/oc2/` deck settles.

### 6. The spring — **ANSWERED: the tank node carries it, not the ported phaser**

`Reverb`'s ask **N-tank** includes *"one off-by-default dispersive all-pass chain on the input for the spring character"*, and T4, T5 and T6 — the chirp traits — are unblocked **through that chain**, not through `audiofilters.Phaser`. The supporting measurement is Freeverb's, not the phaser's: its first non-zero-lag autocorrelation peak is 24.75 ms, below the 30–53 ms span S3 measures across five real springs, and it does not move when Size halves. So the spring is an option on a new own node, and no per-sample phaser is needed for it. **What stays open:** the 6G15's tone/mixer network — T7 states only the two corners the drawn values give directly, and the wet path's route through a 50 kΩ Tone pot, a 250 pF series capacitor and a 250 kΩ Mixer is unresolved.

### 7. Characters versus classes — **ANSWERED: yes, each character its own trait set**

The recommendation was taken, and it earned its place three times over.
`Compressor` answers §10.4 with a No **because** its four characters are separately gated. `Tremolo`'s 13 rows split L1–L4 (shared LFO) / B1–B5 (bias) / O1–O4 (optical); `RingMod`'s nine split M1–M5 (multiplier) / W1–W4 (switching), with **W4 added specifically** so the switching character cannot inherit the multiplier's +3.01 dB makeup; `Fuzz` splits G1–G4 (germanium) / C1–C4 (cascade) plus a shared A4; `Saturation` splits TU / TP / IR plus a shared A4; `AnalogDelay`, `TapeDelay`, `CabinetSim` and `Distortion` each carry two characters with their own rows.
The clearest vindication is `Reverb` **T9, which is new**: hall, room and chamber are three of five characters and shared a single row, so *"three identical tunings under three names would have passed everything — exactly what vision §10.7 says a character trait set must prevent."* T9 was written to stop it.
One consequence to carry into Phase 3+: `TapeDelay`'s header now requires every **shared** row to be measured and reported **per character**, "which is exactly how a failing character hides".

*(§10.8, the latency target, is outside this list and is open — see below.)*

---

## What was not found

Recorded as not found, never as evidence. **109 sources are logged as not reached**; these are the ones that cost a trait, a grade or a licence call.

### Network facts from this machine

- **`www.electrosmash.com` does not resolve** (`getent hosts` returns nothing; `curl` returns http=000 on both rights URLs). The archive mirror `electrosmash.mas-effects.com` serves the same articles and drawings and carries the mirror's own "unofficial" line, so four classes (`Phaser`, `Overdrive`, `Distortion`, `Fuzz`) read their primary source there.
- **`web.archive.org` is blocked for the fetch tool but ANSWERS `curl`** (HTTP 200). What the first pass recorded as unreachable was a tool limit, not a network one — **this re-opens every 403'd route in the run**, and it is how the Phaser's ElectroSmash rights line was finally read at the rights holder (capture 20260514234042).
- **A default `curl` User-Agent is refused where a browser's is not.** `celestion.com` (Cloudflare) returns 403 to both `curl` and WebFetch and serves the datasheets to a browser UA with an `Accept-Language` header; `hobby-hour.com`'s DM-2 page was recorded as 403 and returns 200 with a browser UA. Both were false negatives.
- `valhalladsp.com` and `reverb.com` return HTTP 403 and stayed unreached. `apiaudio.com` returns no HTTP status at all (OpenSSL `sslv3 alert handshake failure`). `help.uaudio.com` 403.
- PDFs are often unreadable by the fetch tool and readable with `pypdf` — that is how S1s for `Limiter`, `Compressor`, `Reverb`, `SlapbackDelay` and `Saturation` were actually read. `thehistoryofrecording.com`'s EQP-1A manual is HTTP 200 with **8 pages and 0 extractable characters**.
- Dead: `native-instruments.com/.../VAFilterDesign_2.1.0.pdf` (404); `ccrma.stanford.edu/~jos/filters/Comb_Filters.html` (404); Griesinger's AES pan-laws paper (404, with two guessed CCRMA/JOS URLs also 404); the Giannoulis, Massberg & Reiss compressor paper, **mis-diagnosed twice** (first as a TLS failure, then as a 301 the tool will not follow) before the real failure was recorded.

### Missing schematics

| Class | What is missing | Consequence |
|---|---|---|
| `Flanger` | the **original 1976 Electric Mistress** drawing. Four routes failed. Tonepad's *Rev.2.Nov.1.2005* redraw **was** reached (S15) — download session-gated, needing a shared cookie jar across three pages — but its subject is the 9 V single-battery unit, "the LFO of the Deluxe … and the signal path of the ORIGINAL". | Grade stays **literature**; no trait rests on S15, which is why the grade did not move. |
| `Compressor` | **no 1176 schematic** reached at all; a **Fairchild 670 schematic with component values** not reached (the manual was, as S10, contradicting the earlier "unreachable"). | Grade **literature, not circuit**, contrary to the grade hint. Only Optical reaches a schematic with values. |
| `Expander`, `NoiseGate` | the full **Drawmer DS201** schematic. elektrotanya serves its first two pages as preview images (S5) and page 1 is legible — enough to overturn "'VCA' is unsourced" — but the sheets themselves were not obtained. | Grade stays literature; the audit records that no trait is derived from the previews. |
| `MultiTapDelay` | the RE-201 **echo board**. Page n5 of the service notes (the OP-13/OP-14B/FL-7 circuit diagram) was read at 216 ppi for its mode-selector table; the echo board itself is unread. | Grade stays literature. |
| `Reverb` | any **primary EMT document**. Every secondary page quotes 0.5–5.5 s reverb time; none was reached. | §6's 0.2–12 s decay span is stated as *our design range*, not a claim about the machine. |
| `Saturation` | a **console or preamp schematic with a transformer's turns ratio and core geometry**. | The `console` character has **no named referent**; IR1's numbers stay coarse. |
| `ParametricEQ` | the **factory EQP-1A schematics**, which S1 states are not public. Two hobbyist redraws with values were reached in the audit (jbb.ru over http; Gyraf's own drawing, which the seed had written off "as nothing usable" without opening it). | Grade literature; T3 and T4 carry medium confidence. |
| `GraphicEQ` | component values — the M-108 schematic was reached and is an **image-only PDF**. | Grade literature; T2's Q is scaled from Bohn's third-octave figures by argument, not measured. |
| `DigitalDelay` | the DD-2 schematic **drawing** (the service notes' text was read; the drawing is a scanned image with no extractable text). | Grade literature. Where the DD-2's feedback is summed — analog before the A/D, or inside the RDD63H101 — decides whether T3 is a fact about the pedal or only about a well-built delay. |
| `Rotary` | the Leslie 122's own **schematic scan** (ManualsLib p.22, re-fetched and confirmed unusable). | The dividing network's coil/capacitor pairing is unresolved; T1 rests on the manual's prose. |
| `Bitcrusher` | the SP-1200 scan's **schematic pages**, not read. | No component values; every §3 number comes from prose or the quantisation literature. |

### Unsourced values a trait or a default rests on

Each is labelled in its seed rather than dressed up:

- **`Rotary`: the horn radius r_s** — it fixes T3's absolute Doppler depth, macro 9's default and the class's stated latency, and no reachable source prints a number (DAFx-02 uses the symbol; x42-whirl has the parameter but is GPL).
- **`Rotary`: the "2 kHz horn band-pass"** — Penniman's app note attributes it to Henricksen, and a targeted re-read of Henricksen found **no such statement**. Either the attribution is wrong or the claim is.
- **`Fuzz`: the gating mechanism.** Vision §6 assumes "the Fuzz Face's gating is a bias point that moves with the signal" as an input to the waveshaper node's design. **Nothing reached this run sources it** — S1 describes a static DC bias with an AC-shunted emitter.
- **`NoiseGate`, `Expander`: hysteresis.** Every practitioner's account names it and **no source reached states a figure for any unit**, the DS201 included; both manual editions were grepped. The proposed Hysteresis macro is provisional and ships only if a source is reached.
- **`Phaser`: the Speed knob's range in Hz.** No reached source gives more than "tenths of a Hz to some Hertzs"; Dunlop publishes no figure. The proposed 0.05–10 Hz is the seed's own.
- **`Phaser`: which LFO ramp is longer.** S3 models a 65 % duty triangle (rise long) while S4 **measured** a real unit and reports the falling edge longer. The two sources disagree in **direction**, so P9 fixes only the magnitude of the asymmetry and is labelled a surface requirement, not a circuit trait.
- **`Chorus`: whether the LFO injection is frequency-linear or resistance-modulating.** T2's probe discriminates against the model, not against hardware.
- **`Vibrato`: what Roland's "Delay Time … 4 ms (Depth)" means** — the mean delay (the seed's reading) or the swing at full depth.
- **`RingMod`: the ring diodes' part number.** The drawing marks the four only as "SELECT DIODES"; the general note ("ALL DIODES 1N485A UNLESS NOTED") may or may not cover them. And a **real sourced tension recorded rather than resolved**: Bode's own 1984 history credits multiplier-type behaviour to **germanium** diodes in their square-law region and names silicon separately.
- **`SlapbackDelay`: the tape speed.** 134–137 ms and the Ampex 350's speed list imply 1.03 in at 7½ ips or 2.06 in at 15 ips; the derivation is labelled as one.
- **`Compressor`, `Limiter`: the ESP32-P4/S3 budget percentages** rest on one number stated from memory — "a single-precision `expf` or `logf` from newlib costs of the order of 100–200 cycles" — which is flagged as unsourced in the seed.
- **`Rotary`: the speed of sound, c = 343 m/s**, in Tier 3's latency derivation — left in place and named rather than struck, as a physical constant.

### Licence calls that could not be verified

Under vision §5, an unfound licence is copyleft until shown otherwise. The audit **downgraded** these to "licence unverified — treated as copyleft" after re-fetching and grepping:

`Overdrive` S1 and `Distortion` S2 (ElectroSmash on the MAS mirror — **no rights line on either page**, and the assertion that S1's line "is taken to cover this article too" was removed); the Waves **dbx 160 User Guide** (no rights line on any of 9 pages); Dattorro's *Effect Design* PDF (no rights statement anywhere in 25 pages); the Boss DD-2/DD-3 archive item (no `licenseurl`, no `rights` field, re-read this run); Raffel & Smith DAFx-10; Zhang's CCRMA course report; the Roland VB-2 owner's manual (**no rights notice anywhere** — cover, specification page and back page all checked; the back carries only "BOSS Products of Roland" and "Printed in Japan '82 Mar."); the Panasonic MN3207 sheet (no rights notice, and the host serves the PDF without terms).

The audit also **corrected upward** where a licence was better than recorded: the Aion FX build doc's page 13 is headed "LICENSE & USAGE" and grants commercial use (recorded as "no licence granted"); the SP-1200 service manual's Public Domain Mark 1.0 was re-checked against the document itself; `schematicheaven.net/copyright.html` was reached (linked only from the homepage footer — the footer-link trap `instrument-sources.md` names) and grants free copying but not sale. And two sources the seeds had marked "states no terms" do carry a bare copyright with no grant (`guitar-gear.ru`, `moogfoundation.org`).

**`McQuillan & van Walstijn` (DAFx-20in21) was a wrong licence call in the other direction:** recorded as "no rights statement → treated as copyleft" when the PDF's own page 1 carries one. Corrected.

### Still open at the gate

- ~~**`docs/effects-survey-audit.md` does not exist**~~ — **written 2026-09-07**: [effects-survey-audit.md](effects-survey-audit.md). It assembles the record; nothing was fetched to write it, and it labels the 160 / 160 / 158 correction counts as the **floors** they are (the record caps each unit's list at ten, and passes 1 and 2 hit 16 × 10 exactly).
- ~~**The audioif#23 results have not been posted to the issue**~~ — **posted 2026-09-07**, [audioif#23 comment](https://github.com/PyDevices/audioif/issues/23#issuecomment-5568874859): the 12-row table, the endurance paragraph, the `audioif_biquad.h:14` / `.c:159-182` cause and the harness note, verbatim. The Phaser row was split out as its own audioif issue, [audioif#36](https://github.com/PyDevices/audioif/issues/36), because `audioif_phaser.c` never calls `audioif_biquad` and #23's fix cannot move it.
- ~~**No audioif issue is filed for any surviving node ask**~~ — **eight filed 2026-09-07**, one per surviving node ask, each body carrying its need statement, its unblocked traits and its design sketch verbatim:

| Node ask | Candidates | audioif issue |
|---|---|---|
| `audioecho.FeedbackDelay` — `wow_shape`, delay slew, `wow_am_depth`, in-loop pitch shift | 1, 2, 3, 5 | [audioif#37](https://github.com/PyDevices/audioif/issues/37) |
| `audiodynamics.Dynamics` — the eleven-option set | 11–18, 20–22 | [audioif#38](https://github.com/PyDevices/audioif/issues/38) |
| `audiobiquad` — DC-clean float biquad + first-order all-pass | 9 | [audioif#39](https://github.com/PyDevices/audioif/issues/39) |
| `audioladder.Ladder` | 24 | [audioif#40](https://github.com/PyDevices/audioif/issues/40) |
| `audioverb.Tank` | 25 | [audioif#41](https://github.com/PyDevices/audioif/issues/41) |
| `audiomath.SubOctave` | 27 | [audioif#42](https://github.com/PyDevices/audioif/issues/42) |
| `audioroute.MidSide` | 28 | [audioif#43](https://github.com/PyDevices/audioif/issues/43) |
| `audioconvolve.Convolver` — non-uniform partitioning (**NEED: NONE**, deferred; filed to record the decision) | 26 | [audioif#44](https://github.com/PyDevices/audioif/issues/44) |
| `audioshaper.Waveshaper` — oversampled table waveshaper, with the hysteresis-state option | 7, 8 | [audioif#47](https://github.com/PyDevices/audioif/issues/47) |

Candidate **7** (`audioshaper.Waveshaper`) and candidate **8** (its hysteresis option) are **not filed**: Arthur's ruling made 7 a survivor on 2026-09-07, after these eight issues went up, so a ninth audioif issue covering the module and its hysteresis option is **owed**. Candidate **7a** is absorbed into 7 and needs no issue of its own.

- **The oversampling table (§10.3) is Phase 1's**, and cannot be produced before the node it prices exists.
- **The latency target (§10.8) is unanswered.** `Limiter`'s Q3 asks how the perceptible-monitoring-delay figure is reached and records it open; vision §9a's working assumption of "a round trip under ten milliseconds" therefore still has no citation. The live-path spike is filed as `pydevices#26`; the number it must be measured against is not sourced. **Phase 0 owed this one** — vision §9a says "What 'acceptable' means is sourced in Phase 0 from the literature on perceptible monitoring delay and stated in the survey."
- **42 of 46 seeds are still over the length rule**, after every derivation, source excerpt, measurement note, pass record and per-row prose block was moved under each seed's `## Appendix` (median 29.8 KB → **16.2 KB**; 4 seeds now inside 8–12 KB; corpus §§1–8 1474 KB → 812 KB; nothing deleted, every moved byte re-emitted in the appendix and verified). What remains is gate-read content — trait statements, disconfirmations, source ids and URLs, the macro table, the six header fields — about 12 KB before any argument. **The decision this needs is the implementation session's:** move the number for trait-dense classes, or move trait statements to the appendix and make §3 an index.
- **The waveshaper's audioif issue (candidates 7 and 8) is owed and unfiled**, per item 1 — the ruling that made candidate 7 a survivor came after the eight issues went up.
- **The reopened `web.archive.org` route was proven once and never retried.** [Network facts](#network-facts-from-this-machine) records that the archive is blocked for the *fetch tool* but answers `curl` (HTTP 200), and says in bold that this **re-opens every 403'd route in the run** — and no route was retried. The route was proven on the `Phaser` alone (capture `20260514234042`, the ElectroSmash rights line read at the rights holder). The two retries it most likely repays: **`Compressor`'s 1176 schematic with values** (`Compressor.md:94` records `web.archive.org` among the four hosts that failed, and the class is graded *literature* for want of it) and **`Flanger`'s original 1976 Electric Mistress drawing** (`Flanger.md:141-143`, which already names the route as open in terms). This line is a **record correction, not a fetch**: no retry was run in this pass, and the retries themselves are Station A's.

---

## Method

**Units.** The 46 classes were surveyed in **16 units**, grouped by family and by shared standout so that one researcher held the sources a group has in common: phaser-flanger; chorus-vibrato; tremolo-autopan-ringmod; rotary; overdrive-distortion; fuzz-saturation; bitcrusher-exciter-cab; compressor-limiter; gate-deesser-transient-multiband; parametric-graphic-ladder; simple-filters; tape-analog-multitap; digital-slapback-pingpong; reverbs; pitch-stereo; racks.

**Passes.** Each unit's seeds went through four passes after the research pass:

1. **Licence and citation audit** — every URL re-fetched by an agent that had not written the seed, every quotation located in the fetched bytes, every line citation checked with `grep -n`. **160 corrections recorded.**
2. **Trait critic** — every Tier 2 row re-cut for falsifiability: a disconfirmation that is the complement of the claim, a stated threshold, a stated level and rate, and a *control that must pass* so a suite of only failures cannot prove a checker always fails. **160 rewrites recorded**, including rows that a correct build would have failed (Flanger F6, Exciter T1, Compressor F1/F4, Overdrive T5, Distortion F1, SlapbackDelay T2) and rows a null build would have passed (MultiTapDelay T5, RingMod W2).
3. **Palette verifier** — every §4 and §5 claim re-read against the C under `audioif/src/shared` and the bindings under `audioif/src/<module>/`, and **probed on the CPython build** rather than argued. **158 corrections recorded**, several of which killed a node ask outright and several of which found a *palette* claim that was simply wrong.
4. **Node refutation** — 51 raw asks merged into 28 candidates; **each candidate given two independent refuters** working different lenses (composition; measurement and cost), each instructed that proving a thing *can* fail is not proving it always does, and each required to record a measurement rather than an argument. **No candidate went unrefuted.** Five candidates fell; four survived a 1–1 split, and every split is reported above with the losing argument intact, because in three of the four the losing refuter found something the ask must carry.

**Units of measurement.** Every measurement in the run is stated at **48 kHz stereo, 16-bit** unless it says otherwise; levels are dBFS against a full-scale sine; block sizes are named where they matter (the palette's own block is 256 frames = 5.33 ms at 48 kHz, and `_core.pcm()`'s default buffer is 2048 bytes = 512 frames). Line citations are `file:line` from `grep -n`, never from memory. Component values, model parameters and historical facts come from a source reached in the run or are marked unsourced and kept out of the trait table.

**Counts in this document** were re-derived here rather than copied: the 327 Tier 2 rows and the 288 source rows by parsing every seed; the grade and portability tallies by extracting each seed's own **Grade** and **Portability tier** lines; the length figures by measuring each file from its start to its first `## Appendix` heading, before and after the trim. Where this survey's number differed from a pass's own, both were stated. The one such gap — 327 against the kit refuter's 332 — **is now closed** rather than left standing: 332 counted non-header table lines, 327 counts traits, and the five-line difference was four `Reverb` character sub-header rows plus one `RingMod` prose line that began with a `|`. Both were reshaped in the seeds, and the corpus now parses to 327 either way (see [The headline numbers](#the-headline-numbers)).

**Date.** Research, audit, trait-critic and palette passes: **2026-09-06**. Node-refutation, SPICE-transcription and kit-refutation passes: 2026-09-06 to 2026-09-07 where they say so. This survey assembled 2026-09-07. No run ids are recorded because none were assigned.

---

## Gate status — roadmap Phase 0

| Gate condition | Status |
|---|---|
| 46 of 46 seeds exist; every non-design seed fixes ≥ 3 Tier 2 traits with a source and a disconfirmation | **MET** — 46/46; 32/32 non-design seeds, minimum 5 rows; the 14 design seeds carry rows too |
| Every source named in the survey was reached during the run; dead links recorded as not found | **MET** — 200 reached, 109 recorded not reached, with the failure mode per entry |
| Every node candidate has a need statement and a refutation record; survivors have a sketch and a cost estimate | **MET** — **all 23 survivors have a sketch and a cost**, the ten per-module sketches covering every one of them (1/2/3/5, 7, 8, 9, 11–18 + 20–22, 24, 25, 26, 27, 28). The one unsettled verdict was candidate 7, the oversampled waveshaper, recorded refuted on two votes that both scoped themselves to `Tremolo` B4 and disclaimed the drive family while five classes name the node in their §5: **Arthur ruled it a survivor on 2026-09-07** — B4 stays struck, 7a is absorbed back into 7, candidate 8 is unblocked — and its sketch and cost are now written ([`audioshaper.Waveshaper`](#audioshaperwaveshaper--oversampled-table-waveshaper-candidate-7)). (Secondary, and not a failure: the sketches are per-module rather than per-candidate, so ten `Dynamics` options and three `FeedbackDelay` options still owe their own API line, state field and probe case at Phase 1.) |
| audioif#23 carries the 48 kHz settled measurement for every shipped EQ and Phaser configuration, and the Gate 0 answer cites it | **MET** — the measurement is reproduced verbatim above and was **posted to the issue on 2026-09-07** ([comment](https://github.com/PyDevices/audioif/issues/23#issuecomment-5568874859)): the 12-row table, the endurance paragraph, the `audioif_biquad.h:14` / `.c:159-182` cause and the harness note. The Phaser row is split out as [audioif#36](https://github.com/PyDevices/audioif/issues/36) — a separate defect in a ported kernel that never calls `audioif_biquad`, so #23's fix cannot move it. Candidate 9's ask, [audioif#39](https://github.com/PyDevices/audioif/issues/39), cites the comment. |
| The TS808 netlist runs under ngspice on this machine and its curves appear in the `Overdrive` seed | **MET** — re-run 2026-09-07, output identical line for line; every figure present with its analytic value beside it |
| Every measurement in the kit spec names its planted fault | **MET** — and six faults that would not have fired were found and replaced by the kit's refuter |
| The audit's corrections are applied and its report is committed | **MET on the corrections and the report; the commit is Arthur's** — the corrections were applied by the pass that made them during the run, and [`docs/effects-survey-audit.md`](effects-survey-audit.md) is written (2026-09-07), listing them by class and by kind. It records the 160 / 160 / 158 counts as **floors** (ten-per-unit cap; 16 × 10 hit exactly twice) and carries its own limits — assembled not independent, source-row census unreconciled, archive route retried on nothing. |
| Issues filed: one per surviving node ask on audioif | **MET** — nine of nine: audioif#37–#44 for the eight groups the fix round filed, and audioif#47 for the waveshaper (with its hysteresis option), filed after the ruling|
| The live-path spike filed on `pydevices`; the survey answers §10.8 | **PARTLY MET** — `pydevices#26` is filed; **§10.8 is unanswered** — no sourced figure for perceptible monitoring delay was reached |

**Not committed.** This file, the 46 seeds, `docs/effects-survey-audit.md`, `docs/effects-kit-spec.md` and the two corrected sentences in `tools/spice/ts808/README.md` are all uncommitted. Arthur commits.

<!-- Assembled 2026-09-07 by the Phase 0 survey session, from the sixteen units' records, the four audit passes and the twenty-eight node refutations. Shape mirrors accuracy-survey.md. Every count in the headline numbers was re-derived from the seeds in this session; where a count differs from a pass's own, both are stated. -->
