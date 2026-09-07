# Effects Dossier — `DigitalDelay` (Boss DD-2)

**Class:** `lib/audioeffects/delay.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Time, roadmap Phase 5
**Standout:** Boss DD-2 Digital Delay (1983), proposed in vision §4.2 —
**confirmed**, with the "light touch" reading argued at the end of §2.
**Grade:** literature — the manufacturer's service notes (specifications,
parts list, clock-adjustment procedure, and the schematic sheet's `fc=7kHz`
annotations) and one repair analysis were reached; the schematic *drawing*
was fetched but is a scanned image with no extractable text, so this is not
a circuit grade.
**Portability tier:** needs audioif-own nodes (`audioecho`) — §4 carries the
measurement that forces it off the stock node.
**Status:** seed (Phase 0)

## 1. The circuit, in one paragraph

The DD-2 is the first digital delay in stompbox form (S5) and it splits into
two paths that meet only at the output mixer. The **dry path** is the "direct
sound", specified 10 Hz–60 kHz (S1 gives the range with no tolerance for this
path). The **wet path** is a 7 kHz active low-pass of discrete 2SC732
transistors (S1 annotates `LPF Q3-Q6 ... fc=7KHz`)
→ an NE570 compander compressing on the way in (S1 parts list; S3, S6) → a
sigma-delta A/D with an external comparator (S3) → **12-bit** words (S3; S1
states no bit depth anywhere) in three "64K D-RAM"s under an RDD63H101
controller (S1, S3) → a resistor-network D/A (S3) → the NE570 expander → a
matching 7 kHz reconstruction low-pass (`LPF Q9-Q10`, S1) → E.LEVEL into the
mix. Delay sound is specified 40 Hz–7 kHz, +1/−3 dB at D.TIME centre; residual
noise −95 dBm IHF-A (S1). **No reached source describes an intentional
nonlinearity** — the compander and the 12-bit quantiser are both described as
bought for noise floor, not tone (S3, S6). No source reached states the
compander's transfer law. The delay time is one master clock that "is directly
controlled by the delay time knob" and clocks the whole converter, so turning
D.TIME resamples what is already in memory and "smoothly pitch-shifts" it
"without any glitching" (S3); S1's two clock-adjustment points bracket it at
MSCK 5.18 MHz (T = 12.12 µs, 82.5 kHz ± 0.4 kHz) and 1.28 MHz (T = 50 µs, 20
kHz ± 0.1 kHz). No LFO anywhere. The panel is E.LEVEL, F.BACK, D.TIME, and a
MODE switch selecting three 4:1 ranges — 12.5–50, 50–200, 200–800 ms — plus
HOLD, which loops 200–800 ms of memory (S1). What E.LEVEL does to the dry
signal is **not stated by any reached source**; what S1 does state is that the
two paths are separable at the sockets — "To DIRECT jack, only direct signal is
routed regardless of jack connections and switchings", against a MONO jack
carrying "Direct, delay mixed signal" in stereo mode.

## 2. Sources and license calls

Reached on 2026-09-06; nothing from memory. Full quotes in Appendix A3.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Boss DD-2/DD-3 Service Notes (OCR text) | specifications, parts list … (App. S1) | archive.org item has **no `licenseurl` and no … (App. S1) | <https://archive.org/stream/boss_DD-2_DD-3_SERVICE_NOTES/DD-2_DD-3_SERVICE_NOTES_djvu.txt>, <https://archive.org/metadata/boss_DD-2_DD-3_SERVICE_NOTES> | yes |
| **S2** Smith & Lee, *Time Varying Delay Effects*, CCRMA RealSimple … (App. S2) | eq. (10) ω_l = ω_s(1 − Ḋ_t); "zipper noise" … (App. S2) | no copyright, `©` or licence string anywhere … (App. S2) | <https://ccrma.stanford.edu/realsimple/DelayVar/DelayVar.pdf> | yes |
| **S2b** Smith, *Physical Audio Signal Processing* … (App. S2b) | "linear interpolation is a one-zero FIR filter" and … (App. S2b) | "Copyright © 2026-08-21 by Julius O. Smith … (App. S2b) | <https://ccrma.stanford.edu/~jos/pasp/Delay_Line_Interpolation.html>, <https://ccrma.stanford.edu/~jos/pasp/Fractional_Delay_Filtering_Linear.html> | yes |
| **S3** False Electronics, "Boss DD-2" repair write-up, 2017-08 | the master-clock/time-knob statement … (App. S3) | blogspot, no licence line rendered … (App. S3) | <http://falseelectronics.blogspot.com/2017/08/boss-dd-2.html> | yes |
| **S5** BOSS, "Comparing Analog and Digital Delay Pedals" | "the world's first digital delay in stompbox form" … (App. S5) | no copyright line on the article itself … (App. S5) | <https://articles.boss.info/comparing-analog-and-digital-delay-pedals/>, <https://www.roland.com/global/terms_of_use/> | yes |
| **S6** Analog Man, DD-5/DD-6 mod page | the DD-2/3 compander … (App. S6) | commercial page, no licence line rendered … (App. S6) | <https://www.analogman.com/dd5.htm> | yes |

**Audited 2026-09-06** by an independent licence-and-citation pass: every row
above and every URL in this file re-fetched, the corrections listed in
Appendix A5.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **The dry path is never coloured, and it sits at exactly unity.** Over the window before the first repeat arrives (0 … *T*) the output is the source: magnitude within 0.05 dB across 20 Hz–20 kHz, group delay within 1 sample of zero — at every macro setting and patch, with Repeat Tone and Repeat Cut at either extreme. No tone, cut or band-limit option reaches it. | S1 (dry 10 Hz–60 kHz against wet 40 Hz–7 kHz … (App. T1) | high | any pre-repeat magnitude deviation above 0.05 dB in 20 Hz–20 kHz, or pre-repeat group delay above 1 sample, at any macro setting or patch; **or** a pre-repeat transfer that moves by more than 0.02 dB between the two extremes of Repeat Tone or of Repeat Cut | swept sine at `mix = 0.2` … (App. T1) |
| T2 | **The time control resamples the line: it pitch-shifts while it moves, and never steps.** During a Time move the wet output's instantaneous frequency follows ω_l = ω_s(1 − Ḋ_t) within 10 cents; within 50 ms of the move ending it is back within 1 cent of ω_s; and no first difference during the move exceeds the largest first difference the same material produces on an unramped render. | S3 (the pedal's master clock *is* the time knob); S2 eq. (10) | medium for the pedal (one repair analysis); high for the physics | a first difference during the move exceeding the unramped render's maximum; **or** a peak pitch deviation more than 10 cents from ω_s(1 − Ḋ_t), which includes no measurable deviation at all; **or** a residual offset above 1 cent 50 ms after the move stops | held 997 Hz tone, `mix = 2`, Time ramped 200 → 150 ms over 250 ms, at 48 and 44.1 kHz: STFT peak track against ω_s(1 − Ḋ_t), and max \|first difference\| against the same statistic on an unramped render. **The probe frequency is part of the trait:** at 1 000 Hz the 50 ms jump is exactly 50 periods and the step vanishes, so the measurement goes green on broken code (A2) |
| T3 | **Repeats do not progressively darken at the default patch.** With Repeat Tone and Repeat Cut out of circuit, each repeat's share of energy in 100 Hz–1 kHz, 1–4 kHz and 4 kHz–Nyquist — each band normalised by that repeat's own broadband energy, so the test is spectral tilt and not level — is within 1 dB of the first repeat's share, through repeat 8. **Control that must fail:** with Repeat Tone at 3 kHz the 8th repeat's 4 kHz–Nyquist share is at least 20 dB below the first's. | S6 (only the high-cut *mod* darkens the loop … (App. T3) | medium — a mod … (App. T3) | any band share of the 8th repeat more than 1 dB from the first's, with both filters out at `feedback = 0.8`; **or** the control not moving — the 8th repeat's 4 kHz–Nyquist share less than 20 dB down with Repeat Tone at 3 kHz | burst-then-silence at `feedback = … (App. T3) |
| T4 | **The time law spans 12.5–800 ms, and one macro position means the same milliseconds on every instance.** On an instance built with the default `max_time_ms`, Time reaches both endpoints; the macro→milliseconds map is log, monotonic, and identical whatever the constructor options; where `max_time_ms` is lowered, Time clamps at that ceiling and `get_macro` reports the clamped position rather than a silently different time. | S1 (12.5–50 / 50–200 / 200–800 ms … (App. T4) | high | Time failing to reach 12.5 or 800 ms on a default instance; a measured delay off the mapped value by more than 1 sample; non-monotonicity; **or** two instances with different `max_time_ms` returning different milliseconds for the same macro position without the clamp being visible through `get_macro` | delay tracking: click through at … (App. T4) |
| T5 | **The band-limit is a knob, it defaults out of circuit, and its number is the corner it achieves.** Default patch: both filters out. At Repeat Tone 7 kHz the first repeat's measured −3 dB point is 7 kHz ± 10 %, it is no more than 3 dB down at 5 kHz, and it is more than 3 dB down at 10 kHz; both filters sit inside the loop and compound per pass. | S1 (40 Hz–7 kHz; `fc=7kHz` on both filter … (App. T5) | high | either filter defaulting to anything but out of circuit; a measured −3 dB point outside 6.3–7.7 kHz at Repeat Tone 7 kHz; more than 3 dB down at 5 kHz; or not more than 3 dB down at 10 kHz | swept sine, `mix = 2` … (App. T5) |

No characters: one standout, one behaviour set.

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**One node, composed not extended: `audioecho.FeedbackDelay`.** With
`cross_feed = 0`, `input_pan = 0`, `damping_hz = 0`, `cut_hz = 0`,
`loop_drive = 0`, `wow_hz = 0` it is exactly a clean interpolated line — the
read is a per-sample linear interpolation between two neighbours
(`audioif_feedback_delay.c:226-228`), the three in-loop colourings are all
skipped at a zero coefficient (`:231`, `:236`, `:241`, with
`one_pole_coefficient` returning 0 for a zero cutoff at `:31-38`), and the
output is `dry·source + wet·loop` with `dry = 1` below `mix = 1`
(`:201-202`, `:260-261`). Python computes nothing per sample: it maps macro
positions to node options on a move and recomputes `tail_samples`.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**One ask, for T2: a delay-time slew on `audioecho.FeedbackDelay`.**

- **Trait:** T2. A rebuild that cannot move the read pointer continuously
  cannot demonstrate ω_l = ω_s(1 − Ḋ_t), and cannot move Time without a click.
- **What the palette does instead, and the measurement.** …  *(argument in full: App. R)*
- **Design sketch.** Two additive options, `delay_target_ms` and …  *(argument in full: App. R)*
- **Refutation record (Phase 0), five palette-only routes tried and …  *(argument in full: App. R)*
- **Shared, not private.** Vision §6 already lists this candidate for the …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Nine macros.

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Time | UNIPOLAR | 12.5–800 ms, log | D.TIME plus the MODE range switch, folded into one continuous knob |
| 1 | Feedback | UNIPOLAR | 0.0–0.99 | F.BACK |
| 2 | Mix | UNIPOLAR | 0.0–2.0 (`Echo`'s convention: dry at unity to 1) | E.LEVEL |
| 3 | Glide | UNIPOLAR | 0–2000 ms for a full-range Time move (0 = jump); default 120 ms | the master clock's continuity (§5) |
| 4 | Sync | TOGGLE | off / on | none — D2 addition; reads `transport()` |
| 5 | Division | UNIPOLAR | 16 steps, 1/32 … 1/1, dotted and triplet | none — D2 addition |
| 6 | Repeat Tone | UNIPOLAR | 800–16 000 Hz log; top = out of circuit (default) | the 7 kHz reconstruction filter, moved into the loop |
| 7 | Repeat Cut | UNIPOLAR | 20–400 Hz log; bottom = out of circuit (default) | the wet path's 40 Hz corner |
| 8 | Freeze | TOGGLE | off / on (feedback 1.0, line input muted) | MODE's HOLD position |

**Patches** (names describe settings, never products): `Clean Repeats`
(350 ms, f 0.35, mix 0.30, tone and cut off) · `Eighth Notes` (Sync,
Division 1/8, f 0.40) · `Dotted Eighths` (Sync, 1/8·, f 0.45) ·
`Short Doubling` (55 ms, f 0.0, mix 0.5) · `Long Ambient` (750 ms, f 0.7,
mix 0.25) · `Band Limited Repeats` (350 ms, f 0.6, Tone 7 kHz, Cut 40 Hz —
the standout's own wet-path corners) · `Freeze Hold` (Freeze on, 600 ms).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/delay.py`.

1. **No surface at all.** `MACRO_LABELS = ()` (`delay.py:31`), …  *(argument in full: App. R)*
2. **The line is sized from the constructor's time, and truncated.** …  *(argument in full: App. R)*
3. **`freq_shift=False`** (`:37`) — the node's one continuous-time mode is
   explicitly off, so the time control steps. T2 is the answer.
4. **The wire invariant is not held**, inherited from the node and measured
   in §4: `mix = 0` is not byte-identical above ±28 000.
5. **`tail_samples` is `None`.** No delay class overrides `TAIL_SAMPLES`, so …  *(argument in full: App. R)*
6. **`capabilities` is empty** (`_core.py:139`) on the library's most obvious
   tempo-sync candidate.
7. **`reset()` touches only the output node** (`_core.py:366-373`), so a …  *(argument in full: App. R)*

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Is the light-touch reading right?** The default is a clean line with the
   DD-2's control law, not its converter (§2). The implementation session may
   overturn it at Station A and make `Band Limited Repeats` the default.
   *Settles:* the implementation session, in the Phase 5 packet.
2. **Where is F.BACK summed** — analog, before the A/D, or inside the
   RDD63H101? No source reached says. It decides whether T3 is a fact about
   the pedal or only about a well-built digital delay. *Settles:* a legible
   schematic if one is ever reached; T3 stands on S6 and S5 until then.
3. **The portability cost.** Moving this class and `SlapbackDelay` to
   `audioecho` leaves `MultiTapDelay` the only stock-tier delay. *Settles:*
   the implementation session, with Arthur's phase review.
4. **Glide's default.** 120 ms is proposed with no source — a pedal's clock
   follows the knob at whatever speed the player turns it. *Settles:* Phase 5,
   against T2's click measurement.
5. **Does a filter macro's number mean the corner it achieves?** T5 now says
   it does, which costs a rate-dependent pre-warp in Python (A6: a labelled
   7 kHz is `damping_hz ≈ 6 569` at 48 kHz, 6 495 at 44.1 kHz). The cheaper
   alternative is to let the number be the node's coefficient argument and say
   so in the docstring — the same choice the Phaser's pre-warp already made
   the other way (vision §6). *Settles:* the implementation session, Phase 5.
6. **Is the read interpolator's high-frequency loss a documented property of
   the wet path?** `delay_frames` is a float and the read is linear
   interpolation, so a half-sample delay costs 5.11 dB at 15 kHz at 48 kHz and
   6.35 dB at 44.1 kHz (A6, measured); Time lands on a fraction at nearly
   every setting, so the top of the repeats moves as the knob turns. It is the
   palette's behaviour, not the class's, and no Tier 2 trait rests on it —
   but it is either in the docstring or it is a surprise. *Settles:* the
   implementation session, which documents it or asks Phase 1 for an allpass
   or higher-order read.

---


## Appendix

### A1. Sample rate and memory — a derivation, not a source

S1 states neither a sampling frequency nor a bit depth; S3 states three
64 Kbit DRAMs and 12-bit samples. Three 65 536-bit devices hold 196 608 bits,
which at S3's 12-bit quantising is **16 384 samples**. Two checks against S1's own clock-adjustment procedure:

- 16 384 samples over the L range's 800 ms maximum → **20.48 kHz**; S1's slow
  adjustment point is "T = 50 µs (20 K ± 0.1 kHz)".
- 16 384 samples over the L range's 200 ms minimum → **81.92 kHz**; S1's fast
  point is "T = 12.12 µs (82.5 K ± 0.4 kHz)".

Both agree to under 1 %. The picture that falls out — one memory, a 4:1
continuously variable sample clock inside each MODE range, the range switch
selecting 1 024 / 4 096 / 16 384 samples — also explains the fixed 7 kHz
filters: 7 kHz is still below Nyquist (10.24 kHz) at the slowest clock, so the
wet bandwidth is constant across the whole time range and S1 can quote one
figure "at D.TIME center". Consistent too: 5.18 MHz ÷ 82.5 kHz = 62.8 and
1.28 MHz ÷ 20 kHz = 64.0, about 63 master-clock cycles per sample — the
controller is an **RDD63**H101. None of this is asserted as sourced fact; it
is arithmetic on S1 and S3, recorded because it is checkable.

### A2. Measurements taken this run

On `audiocomponents/.venv/bin/python` (the CPython build of audioif), 48 kHz,
stereo, interleaved `int16`, pulled through `audiocore.get_buffer`.

**The wire invariant on the two candidate nodes.** Probe: 4 800 frames of a
1 kHz sine at amplitude 32 000, both channels.

| Node, `mix = 0` | Samples differing from source | Peak in → out |
|---|---|---|
| `audiodelays.Echo(delay_ms=350, decay=0.4)` | 2 800 of 9 600 | 32 000 → 28 437 |
| `audioecho.FeedbackDelay(delay_ms=350, feedback=0.4)` | **0** of 9 600 | 32 000 → 32 000 |

First differing sample: index 18, 29 564 → 28 170.

**The delay-time step.** `audioecho.FeedbackDelay(max_delay_ms=600,
delay_ms=200, feedback=0, mix=2)` on a 997 Hz sine of amplitude 12 000;
`set(delay_ms=150)` issued on the block boundary at frame 20 480. Left
channel around the boundary:

```
... -6833, -5491, -4055, -2551, | -10264, -9368, -8312, -7115, -5797 ...
```

Step at the boundary **−7 713 LSB**; maximum |first difference| in the 2 000
frames either side, **1 564 LSB**. The 997 Hz probe was chosen deliberately:
at 1 000 Hz the 50 ms jump is exactly 50 periods and the step vanishes
entirely. **That is T2's planted fault** — run the measurement at 1 000 Hz
and it goes green on broken code. It is the "material cannot express the
thing being measured" failure in `agent-knowledge/workspace-craft.md`.

### A3. Source quotes relied on

- **S1**, specifications: "Delay time : 1 2.5ms(min)— 800ms(max)";
  "12.5— 50ms — MODE at S. 50ms"; "50— 200ms — MODE at M. 200ms";
  "200— 800ms — MODE at L. 800ms"; "Hold time : 200-800ms - MODE at HOLD";
  "Delay sound 40Hz— 7kHz"; "Direct sound 10Hz— 60kHz"; "D. TIME center
  +1dB, — 3dB"; "Residual noise : — 95dBm (IHF-A)". Routing: "To DIRECT
  jack, only direct signal is routed regardless of jack connections and
  switchings"; the mode table's MONO-jack row reads "Direct signal only" with
  the DIRECT jack open and "Direct, delay mixed signal" with it plugged. (The
  sentence introducing the jacks is interleaved with a second OCR column and is
  not quoted here.)
  Parts: RDD63H101 main
  controller; HM4864P-3 / M5K4164NP-20 64K D-RAM; NE570 compander NR;
  M5218L / NJM5534D op-amps; HD14066BP analog switch. Schematic annotations:
  "LPF Q3-Q6: 2SC732TM-GR fc=7KHz", "LPF Q9-Q10: 2SC732TM-GR fc=7KHz".
  Adjustment: "Adjust RT-1 on Effect Board for T=12.12µs (82.5K± 0.4kHz). The
  MSCK should be 5.18M ± 25.6kHz." / "Adjust RT-1 on Volume Board for T=50µs
  (20K ± 0.1 kHz). The MSCK should be 1.28M ± 6.4kHz."
- **S2**, eq. (10): "ω_l = ω_s(1 − Ḋ_t)", with "the delay growth-rate, Ḋ_t,
  equals the relative frequency downshift"; and "some form of interpolation
  between samples is usually required to avoid 'zipper noise' in the output
  signal as the delay length changes."
- **S3**: "everything is synchronised off a single master clock which is
  directly controlled by the delay time knob - changing the delay time
  smoothly pitch-shifts whatever audio is memory without any glitching";
  "3 64k DRAM chips"; "a NE570 compressing on the way into the digital delay
  line and expanding on the way out ... and pre-emphasis and de-emphasis
  filters at 7 kHz"; "the audio is quantised to 12-bit samples (8 is more
  typical) for lower noise" — the only reached statement of bit depth.
- **S6**: "The DD-2/3 high cut mod works in the feedback loop, so each delay
  gets darker and darker, like an analog delay"; "The delay will die out
  after several repeats with the high cut on, it will not repeat infinitely
  like on the DD-5/6 or the stock DD-2/3."

### A4. Node lines relied on

`audioif/src/shared/audioif_feedback_delay.c` — `:31-38` a zero cutoff gives
a zero coefficient; `:81-83` `delay_ms` → `delay_frames`, clamped to
`[1, line_frames − 2]`; `:90` feedback clamped `0..0.99`; `:99` mix clamped
`0..2`; `:180-184` the cubic `soft_clip`; `:201-202` the dry/wet law;
`:209-210` the magic-circle wow oscillator, unconditional; `:212-214` the read
offset; `:223-224` and `:248` the mono path; `:226-228` linear interpolation;
`:231-243` the three in-loop colourings, each skipped at zero; `:247-256` the
feedback write; `:260-261` the output. `audioif_feedback_delay.h:39` block =
256 frames; `:93` the line is `int16`.
`audioif/src/audioecho/FeedbackDelay.c:102-110` allocates
`line_frames × 2 × sizeof(int16_t)` — two lanes always.
`audioif/src/shared/audioif_echo.c:11`, `:36-38` the stock node's mixdown
limiter. `audioif/docs/upstream-diff.md:770-812` records `audioecho` as
audioif's own node and why it exists.

### A5. Licence and citation audit, 2026-09-06

Run by an independent licence-and-citation auditor. **Every source row in §2
and every URL in this file was re-fetched in this run**; nothing below is
carried over from an earlier pass, and no source is cited that this pass did
not reach itself.

**Read back and confirmed verbatim.** S1's specification block (`Delay time :
1 2.5ms(min)— 800ms(max)`, the three MODE ranges, `Hold time : 200-800ms`,
`Delay sound 40Hz— 7kHz`, `Direct sound 10Hz— 60kHz`, `D. TIME center +1dB,
— 3dB`, `Residual noise : — 95dBm (IHF-A)`), its parts list (RDD63H101,
HM4864P-3 / M5K4164NP-20 / MSM3764-20RS 64K D-RAM, NE570 Compander NR,
HD14066BP, M5218L, NJM5534D, µPC271C Comparator), both schematic annotations
(`LPF Q3-Q6: 2SC732TM-GR fc=7KHz`, `LPF Q9-Q10: 2SC732TM-GR fc=7KHz`), the
`IC8 VCO (1.28MHz— 5.18MHz)` label and both clock-adjustment points; S3's six
statements; S5's three; S6's three, including the compander sentence ("The DD2
and 3 use an analog COMPANDER chip just like an analog delay, to keep the noise
low") that §1 leans on; S2's eq. (10), its "zipper noise" sentence and its
cross-fade alternative; S2b's one-zero-FIR and zero-error-at-dc statements.
The archive.org metadata API still returns **no `licenseurl` and no `rights`
field**. Searching S1's full OCR for `bit`, `12-bit`, `sampling` returns **zero
hits**, so §1's "S1 states no bit depth anywhere" is confirmed by search, not
by impression.

**Every failed fetch failed again, the same way**: `schematicheaven.net`
returns HTTP 200 as a 1-page PDF from which `pypdf` extracts 0 characters;
`hobby-hour.com`, `effectsdatabase.com` and `support.roland.com` return HTTP
403; `henrikhansson.com` does not resolve. No component value in this dossier
comes from any of them.

**Corrections applied by this pass.**

1. **§1, the direct path.** "specified flat 10 Hz–60 kHz" → "specified
   10 Hz–60 kHz". S1 quotes a range for the direct sound and attaches its
   ±dB figure to the delay sound at D.TIME centre; no tolerance for the direct
   path was reached, and "flat" asserted one.
2. **§1, the memory.** "three 64 Kbit DRAMs" → three "64K D-RAM"s, S1's own
   words. The bit-width reading that turns "64K" into 65 536 bits is A1's
   arithmetic and is labelled there; §1 was stating it as a source's word.
3. **§1, the panel.** "E.LEVEL (wet only; the dry is not attenuated)" —
   **struck as unsourced.** No reached source says what E.LEVEL does to the
   dry signal. Replaced with what S1 does state, the socket routing ("To
   DIRECT jack, only direct signal is routed regardless of jack connections
   and switchings"), which is the reached evidence for two separable paths and
   is now quoted in A3.
4. **§3, T1's source cell.** T1 rested on the two frequency-response lines
   alone, which are evidence of two *bandwidths*, not of two paths. The socket
   routing statement is now named beside them.
5. **§2, S2b's "what it gave".** The row credited both of its URLs with the
   same content. `Delay_Line_Interpolation.html` is a **section-index page** —
   subsection links and the copyright line, no substantive text; the
   one-zero-FIR and zero-error-at-dc statements are on
   `Fractional_Delay_Filtering_Linear.html` alone. Corrected, both URLs kept.
6. **§2, four licence calls made explicit.** S1, S2, S3 and S6 recorded the
   absence of a licence but did not state the call the vision's §5 requires.
   All four now read **"licence unverified, treated as copyleft"**. No licence
   call was *upgraded* by this pass. S5 stays at verified all-rights-reserved:
   Roland's site-wide terms, re-fetched this run, read "Copyright © 2026
   Roland Corporation" and forbid copying, modification and derivative works.

**What this pass did not check.** The measurements in A2 and the arithmetic in
A1 were not re-run; they are the technical auditor's, not this one's. Every
`grep -n` line citation in A4 *was* re-checked against the audioif tree and all
of them resolve to the lines claimed.

### A6. Numbers the trait critic added, 2026-09-06

Taken this run on `audiocomponents/.venv/bin/python` (the CPython build of
audioif) and by arithmetic on the node's own formulas. Nothing here is a claim
about the DD-2; all of it is about the palette the class will be built on, and
it is why T1, T3 and T5 are stated the way they are.

**The one-pole's number is not its corner.** Both in-loop filters take a Hz
value that `one_pole_coefficient` turns into `1 − exp(−2π·hz/fs)`
(`audioif_feedback_delay.c:31-38`, read this run). Solving that filter's
magnitude for its −3 dB point:

| `damping_hz` | achieved −3 dB, 48 kHz | achieved −3 dB, 44.1 kHz |
|---|---|---|
| 3 000 | 3 032 Hz | 3 039 Hz |
| 7 000 | **7 532 Hz** | 7 649 Hz |
| 15 000 | 23 999 Hz | 22 049 Hz |

To land the −3 dB point *on* a target the class passes a pre-warped value:
7 kHz needs 6 569 (48 kHz) or 6 495 (44.1 kHz); 15 kHz needs 11 590 or 11 130.
Per-pass response at `damping_hz = 7000`, 48 kHz: −0.08 dB at 1 kHz, −1.64 dB
at 5 kHz, −4.23 dB at 10 kHz — which is what makes T5's two 3 dB clauses
consistent. T3's control floor is the same filter at 3 kHz over eight passes:
−81.7 dB at 10 kHz against −0.94 dB at 500 Hz, so a 20 dB bar is loose by
60 dB and cannot fail for a marginal reason.

**The read interpolator's high-frequency loss, measured.** `delay_frames` is a
float (`:81-83`) and the read is linear interpolation between two neighbours
(`:226-228`), which is a one-zero FIR whose magnitude at a half-sample offset
is |cos(πf/fs)|. Rendered wet-only (`mix = 2`, `feedback = 0`) against a sine,
integer delay versus the same delay plus half a sample:

| rate | tone | integer delay | half-sample delay |
|---|---|---|---|
| 48 kHz | 15 kHz | 0.00 dB | **−5.11 dB** |
| 48 kHz | 1 kHz | 0.00 dB | −0.01 dB |
| 44.1 kHz | 15 kHz | 0.00 dB | **−6.35 dB** |

Predicted −5.11 and −6.34 dB by the formula, so the arithmetic and the node
agree and the same formula can be trusted at other frequencies (−0.47 dB at
5 kHz, −2.01 dB at 10 kHz, 48 kHz). T5's sweep is therefore ratioed against
the class's own filters-out response at the same Time and rate.

**The two node claims §4 rests on, re-measured.** At `mix = 0` on a 1 kHz sine,
`audioecho.FeedbackDelay(delay_ms=350, feedback=0.4)` differs from the source
in **0 of 9 600** samples at amplitude 12 000 *and* at 32 000;
`audiodelays.Echo(delay_ms=350, decay=0.4)` differs in **0** at 12 000, **0**
at 28 000 and **2 800 of 9 600** at 32 000, peak 32 000 → 28 437. Both the
wire finding and the Tier 1 note that the probe must be full-scale reproduce
exactly as §4 and A2 state them.

### A7. The palette verifier's pass, 2026-09-06

An independent pass re-ran every §4 and §5 claim about what an audioif node
can and cannot do, against the C under `audioif/src/shared` and the bindings
under `audioif/src/<module>/`, and probed the behavioural ones on
`audiocomponents/.venv/bin/python` (the CPython build of audioif), 48 kHz,
interleaved `int16`, pulled through `audiocore.get_buffer`.

**Reproduced exactly.** A2's wire table (`audiodelays.Echo` 2 800 of 9 600
differing at `mix = 0` on a ±32 000 1 kHz tone, peak 32 000 → 28 437, first
differing sample at index 18, 29 564 → 28 170; `audioecho.FeedbackDelay` 0 of
9 600). A2's delay-time step: `set(delay_ms=150)` from 200 ms on a 997 Hz
probe gave a boundary step of **−7 712 LSB** against a largest legitimate
first difference of **1 565 LSB** in the same 4 000 frames — A2 records
−7 713 and 1 564, a one-LSB difference in how the probe sine was rounded, and
the 4.9× ratio the ask rests on is unchanged. A6's one-pole table, its
pre-warp values and its per-pass figures reproduce to the digit when the
threshold is read as exactly −3.000 dB (half-power, −3.0103 dB, would give
7 551 rather than 7 532 Hz at `damping_hz = 7000`); A6's `15 000` row, at or
past Nyquist, is the one-pole never reaching −3 dB in band, which is what the
class must state.

**Corrected in §4.** The claim that "the limiter is on the node's only output,
so nothing composes around it" is false as stated, and the route was built and
measured: `audioroute.Splitter` → (dry, `audiodelays.Echo` at `mix = 2`) →
`audiomixer.Mixer` with the wet voice at level 0 gives **0 of 9 600** samples
differing from the source on the same ±32 000 probe. `audiomixer.Mixer` alone
at one voice, level 1.0, and an `audioroute.Splitter` tap alone are each
byte-transparent too (0 of 9 600). The conclusion is unchanged and the reason
is now the true one: `audioroute` is audioif-own, nothing CircuitPython-ported
fans a source out, so the stock tier is lost either way.

**New refutation measurements, §5 routes (b), (d) and (e).**

| Route | Largest \|first difference\| during the move | Unramped maximum | Wet pitch |
|---|---|---|---|
| (b) `FeedbackDelay`, `delay_ms` stepped over 47 blocks (250 ms) | 6 058 | 1 565 | mean 1 009 Hz (T2's law asks 1 196) |
| (d) `audiodelays.Echo(freq_shift=True)`, same block-stepped ramp | 3 123 | 1 565 | 997 → 1 168 Hz, back to 997 |
| (d) the same, as one 200 → 150 ms jump | 1 548 | 1 565 | 997 → 1 329 Hz for one lap, back to 997 |
| (e) `FeedbackDelay` wow-glide, `wow_hz` 0.5 then frozen at the quarter period | **1 565** | 1 565 | 997 → 910 Hz mid-glide, **997.00** Hz after the freeze |

Achieved delay against the asked-for value, `max_delay_ms = 600`, click
through at `mix = 2`:

| asked | `Echo(freq_shift=True)` | `Echo(freq_shift=False)` | `FeedbackDelay` |
|---|---|---|---|
| 12.5 ms | 12.500 | 12.500 | 12.500 |
| 50 ms | 50.000 | 50.000 | 50.000 |
| 350 ms | **350.688** (33 samples off) | 350.000 | 350.000 |
| 500 ms | **500.333** (16 samples off) | — | — |
| 600 ms | 600.000 | 600.000 | 599.958 |

The `freq_shift` quantisation is `echo_buffer_rate = (uint32_t)(max_delay_ms /
delay_ms · 256)` (`audiodelays/Echo.c:118`) truncated to an integer; the
predicted times from that formula are 350.685 and 500.326 ms, so the node and
the arithmetic agree. The last row is `FeedbackDelay`'s own one-frame
headroom (`audioif_feedback_delay.c:81-83` clamps to `line_frames − 2`): a
line sized at exactly the class's `max_time_ms` is two samples short of it, so
the class allocates headroom above the macro's ceiling rather than reporting a
time it cannot reach — a build note for T4, not a node ask.

**Route (e) in full.** `FeedbackDelay(delay_ms=200, wow_hz=0.5,
wow_depth_ms=50)`, `set(wow_hz=0)` at block 94 (the oscillator's quarter
period at 0.5 Hz is 0.5 s = 93.75 blocks): a click train then measures a
**flat 250.00 ms** on every repeat afterwards, against 155.88 / 236.79 /
655.88 / 736.79 ms for the free-running oscillator. The frozen state holds
because `wow_step` becomes 0 and the magic circle stops rotating
(`audioif_feedback_delay.c:209-210`) while `offset` still adds
`wow_depth_frames · wow_sine` (`:212-213`). The four reasons it still cannot
be a Time knob are in §5.

**§4's mono statement, measured.** At `channel_count` 1 with `input_pan = 0`
the node's forced `feed_own[0] = 1` (`audioif_feedback_delay.c:64-70`) and the
`input_pan` value agree, so a mono build is the identical effect on its one
channel: **0 of 25 088** samples differ from the stereo build's left lane on
the same probe at `delay_ms = 350`, `feedback = 0.4`, `mix = 0.3`, and the
wire invariant holds at `mix = 0` in mono too (**0 of 4 800**). Order matters
and is worth recording for the rebuild: the bindings apply `channel_count`
first and the option kwargs after (`src/audioecho/FeedbackDelay.c:109`, `:118`;
the CPython shim does the same), so an `input_pan` passed in mono *overwrites*
the mono-forced feed weights — which is exactly the half-level repeat
`PingPongDelay` §7.1 records.

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

*Rate:* no Tier 2 trait below fails at 22.05 kHz (T5's 7 kHz corner is still
legal there; T4's 12.5 ms floor is 276 samples). T5's corner is measured at
48 and 44.1 kHz only: at 22.05 kHz its 10 kHz check point sits 1.0 kHz under
Nyquist, where the one-pole and the read interpolator both distort the
reading, so at that rate only T5's defaults-out clause is checked. *Material:* the wire check
**must** use a full-scale probe — §4 and Appendix A2 show a ±12 000 probe
passing on a node that a ±32 000 probe fails.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Boss DD-2/DD-3 Service Notes (OCR text) | specifications, parts list, the two `fc=7kHz` annotations, the clock-adjustment procedure | archive.org item has **no `licenseurl` and no `rights` field** (metadata API, re-read this run) — **licence unverified, treated as copyleft** (vision §5: an unfound licence is copyleft until shown otherwise); read as a document, never ported | <https://archive.org/stream/boss_DD-2_DD-3_SERVICE_NOTES/DD-2_DD-3_SERVICE_NOTES_djvu.txt>, <https://archive.org/metadata/boss_DD-2_DD-3_SERVICE_NOTES> | yes |
| **S2** Smith & Lee, *Time Varying Delay Effects*, CCRMA RealSimple, 2008-06-05 (PDF, text via `pypdf`) | eq. (10) ω_l = ω_s(1 − Ḋ_t); "zipper noise"; linear vs allpass interpolation; the cross-fade alternative | no copyright, `©` or licence string anywhere in the 60-page extracted text (checked this run) — **licence unverified, treated as copyleft**; read as a paper, never ported | <https://ccrma.stanford.edu/realsimple/DelayVar/DelayVar.pdf> | yes |
| **S2b** Smith, *Physical Audio Signal Processing*, "Fractional Delay Filtering by Linear Interpolation" | "linear interpolation is a one-zero FIR filter" and, of its frequency responses, "reaching zero error at dc for all fractional delays". **The `Delay_Line_Interpolation.html` URL beside it is a section-index page: it carries the subsection list and the copyright line and no substantive text** — the two statements above are on `Fractional_Delay_Filtering_Linear.html` alone | "Copyright © 2026-08-21 by Julius O. Smith III", attributed to *Physical Audio Signal Processing*, W3K Publishing, 2010. No licence grant, reuse permission or terms link appears beyond that bare copyright line — **licence unverified, treated as copyleft**; read as a paper, never ported | <https://ccrma.stanford.edu/~jos/pasp/Delay_Line_Interpolation.html>, <https://ccrma.stanford.edu/~jos/pasp/Fractional_Delay_Filtering_Linear.html> | yes |
| **S3** False Electronics, "Boss DD-2" repair write-up, 2017-08 | the master-clock/time-knob statement; **three** 64 K DRAMs; sigma-delta ADC; R-network DAC; 7 kHz pre/de-emphasis | blogspot, no licence line rendered — **licence unverified, treated as copyleft**; read as a document | <http://falseelectronics.blogspot.com/2017/08/boss-dd-2.html> | yes |
| **S5** BOSS, "Comparing Analog and Digital Delay Pedals" | "the world's first digital delay in stompbox form" (1983), 800 ms; BOSS's analog-degrades / digital-does-not contrast | no copyright line on the article itself, but its footer links Roland's site-wide Terms of Use, fetched this run: "Copyright © 2026 Roland Corporation", copying and derivative works prohibited — **verified all-rights-reserved**, not merely unverified; read as a document | <https://articles.boss.info/comparing-analog-and-digital-delay-pedals/>, <https://www.roland.com/global/terms_of_use/> | yes |
| **S6** Analog Man, DD-5/DD-6 mod page | the DD-2/3 compander; the high-cut mod is *in the feedback loop*; without it "the stock DD-2/3" repeats indefinitely | commercial page, no licence line rendered — **licence unverified, treated as copyleft**; read as a document | <https://www.analogman.com/dd5.htm> | yes |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **The dry path is never coloured, and it sits at exactly unity.** Over the window before the first repeat arrives (0 … *T*) the output is the source: magnitude within 0.05 dB across 20 Hz–20 kHz, group delay within 1 sample of zero — at every macro setting and patch, with Repeat Tone and Repeat Cut at either extreme. No tone, cut or band-limit option reaches it. | S1 (dry 10 Hz–60 kHz against wet 40 Hz–7 kHz, and the socket routing — "To DIRECT jack, only direct signal is routed regardless of jack connections and switchings"); the node holds `dry = 1` for `mix ≤ 1` (`audioif_feedback_delay.c:201`, read this run) | high | any pre-repeat magnitude deviation above 0.05 dB in 20 Hz–20 kHz, or pre-repeat group delay above 1 sample, at any macro setting or patch; **or** a pre-repeat transfer that moves by more than 0.02 dB between the two extremes of Repeat Tone or of Repeat Cut | swept sine at `mix = 0.2`, 48 and 44.1 kHz, analysed over the first *T* ms only (Time 350 ms gives a 350 ms window), at both extremes of each filter macro and at Feedback 0 and 0.8: magnitude and group delay against the source |
| T3 | **Repeats do not progressively darken at the default patch.** With Repeat Tone and Repeat Cut out of circuit, each repeat's share of energy in 100 Hz–1 kHz, 1–4 kHz and 4 kHz–Nyquist — each band normalised by that repeat's own broadband energy, so the test is spectral tilt and not level — is within 1 dB of the first repeat's share, through repeat 8. **Control that must fail:** with Repeat Tone at 3 kHz the 8th repeat's 4 kHz–Nyquist share is at least 20 dB below the first's. | S6 (only the high-cut *mod* darkens the loop; stock repeats indefinitely); S5. The control's floor is arithmetic on the node's own one-pole (`audioif_feedback_delay.c:31-38`): at 3 kHz over eight passes, −81.7 dB at 10 kHz against −0.94 dB at 500 Hz (A6) | medium — a mod vendor's page and a manufacturer editorial; no schematic trace of the feedback path | any band share of the 8th repeat more than 1 dB from the first's, with both filters out at `feedback = 0.8`; **or** the control not moving — the 8th repeat's 4 kHz–Nyquist share less than 20 dB down with Repeat Tone at 3 kHz | burst-then-silence at `feedback = 0.8`, `mix = 2`, 48 and 44.1 kHz: per-repeat three-band energy shares, repeats 1–8, run twice (both filters out; Repeat Tone 3 kHz) |
| T4 | **The time law spans 12.5–800 ms, and one macro position means the same milliseconds on every instance.** On an instance built with the default `max_time_ms`, Time reaches both endpoints; the macro→milliseconds map is log, monotonic, and identical whatever the constructor options; where `max_time_ms` is lowered, Time clamps at that ceiling and `get_macro` reports the clamped position rather than a silently different time. | S1 (12.5–50 / 50–200 / 200–800 ms, the three MODE ranges). The fixed-map half is ours, and is the answer to the defect `PingPongDelay` §7.2 records | high | Time failing to reach 12.5 or 800 ms on a default instance; a measured delay off the mapped value by more than 1 sample; non-monotonicity; **or** two instances with different `max_time_ms` returning different milliseconds for the same macro position without the clamp being visible through `get_macro` | delay tracking: click through at `mix = 2`, 17 macro positions, measured lag against the mapped value, at 48, 44.1 and 22.05 kHz; then the same 17 positions on an instance built at `max_time_ms = 300` |
| T5 | **The band-limit is a knob, it defaults out of circuit, and its number is the corner it achieves.** Default patch: both filters out. At Repeat Tone 7 kHz the first repeat's measured −3 dB point is 7 kHz ± 10 %, it is no more than 3 dB down at 5 kHz, and it is more than 3 dB down at 10 kHz; both filters sit inside the loop and compound per pass. | S1 (40 Hz–7 kHz; `fc=7kHz` on both filter blocks); S3. That the option value is *not* the achieved corner is arithmetic on the node's coefficient (A6) | high | either filter defaulting to anything but out of circuit; a measured −3 dB point outside 6.3–7.7 kHz at Repeat Tone 7 kHz; more than 3 dB down at 5 kHz; or not more than 3 dB down at 10 kHz | swept sine, `mix = 2`, first repeat gated out, at 48 and 44.1 kHz, at both knob extremes and at the standout setting. **The sweep is ratioed against the class's own filters-out response at the same Time and rate**, so the read interpolator's own high-frequency loss (A6) divides out instead of being read as the filter's |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Not reached, and what was looked for.** The DD-2 schematic drawing
(`schematicheaven.net`) — fetched, scanned image, no extractable text.
`hobby-hour.com`, `effectsdatabase.com`, Roland's own `support.roland.com`
DD-2 spec page and `henrikhansson.com`: HTTP 403 or no DNS. No DAFx/AES paper
models this pedal; the delay-line literature reached (S2) is generic, which is
the right level for it. **S1 states neither a sampling frequency nor a bit
depth** — the 12-bit figure is S3's, and Appendix A1's sample count is derived
arithmetic on S1 and S3, labelled as such. The claim that the RDD63H101
came from the Roland SDE-3000 appeared only in a search-result summary and no
fetched page, so it is not used as evidence.

*(from §2)*

**Standout confirmed, light touch, reason recorded.** The DD-2 is the right
referent: it is what "digital delay" means on a pedalboard, its documentation
is public and numeric, and its one distinctive behaviour — a time knob that
resamples the line — is a behaviour every delay class here needs anyway. But
§4.2 marks this row "light touch", and the catalogue already carries
`TapeDelay` and `AnalogDelay` for per-pass colour; a library with no clean
line in it would be worse, not more faithful. So the rebuild takes the DD-2's
**control law and its dry/wet discipline** as defaults and offers its
**converter colour as knobs that default off** (§8.1).

*(from §3)*

**Two node numbers the measurements must not be surprised by** (both derived
this run, Appendix A6): a filter macro's Hz value is the node's *coefficient*
argument, not the corner it lands on — `damping_hz = 7000` puts the achieved
−3 dB point at 7 532 Hz at 48 kHz — and the read interpolates linearly on a
float `delay_frames`, so a half-sample delay costs the wet path 5.11 dB at
15 kHz at 48 kHz (measured). T5 is stated over the *achieved* corner and
measured as a ratio for exactly those two reasons.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: **ESP32-P4
0.04**, **ESP32-S3 0.08**. Lean patch expected: **no**. The hot loop is two
interpolated reads, two writes and at most four one-pole filters per frame
with no transcendental — the wow oscillator is a two-multiply magic circle
(`audioif_feedback_delay.c:209-210`) and runs whether used or not. The real
cost is line RAM, not CPU: the node allocates two `int16` lanes regardless of
channel count (`src/audioecho/FeedbackDelay.c:110`), so a line sized for the
standout's 800 ms is **153.6 KB** at 48 kHz. A `max_time_ms` option lets a
board ask for less, and the docstring states that Time then clamps.

*(from §3)*

**Latency: zero, at every macro setting, patch and rate.** Nothing here looks
ahead. The dry path is a wire; the wet path's delay *is* the effect, not
latency. **No option adds latency** — no lookahead, no convolution partition,
no pitch window exists in this class. `tail_samples` is not zero and is
reported honestly: at Time *T* and Feedback *f* the −60 dB tail is
`ceil(T · 3 / −log10 f)` samples for `f > 0`, and *T* at `f = 0`, recomputed
on every Time or Feedback move. The click measurement verifies
`latency_samples`; burst-then-silence verifies the tail.

*(from §4)*

**Why not the stock node — measured, not argued.** `audiodelays.Echo` would
put the class in the **stock** tier, and it cannot hold Tier 1's wire
invariant: every output sample passes
`audioif_mix_down_sample(word, mixdown_scale, -28000, 28000)`
(`audioif_echo.c:38`, scale at `:11`), a soft limiter above ±28 000 applied
whether or not any wet signal exists. At `mix = 0` on a full-scale tone,
**2 800 of 9 600 samples differ**; `audioecho.FeedbackDelay` on the same probe
differs in **zero** (Appendix A2). The limiter sits on the node's only
output, but the dry path need not pass through the node at all, and that
route was tried rather than dismissed (A7): `audioroute.Splitter` → (dry,
`audiodelays.Echo` at `mix = 2`) → `audiomixer.Mixer` with the wet voice at
level 0 is byte-identical to the source, **0 of 9 600** samples differing on
the same ±32 000 probe. What that composition costs is the tier itself:
`audioroute` is one of audioif's own modules (roadmap §3) and nothing in the
CircuitPython-ported palette fans a source out, so the stock tier is lost
either way. With it lost, `FeedbackDelay` is one node instead of three and
carries the per-sample interpolation and the in-loop filters this class
needs.

*(from §4)*

**Portability tier: audioif.** On a stock CircuitPython board the module
imports cleanly and construction raises a clear `ImportError` — the guarded
pattern `CabinetSim` already uses (`drive.py:30-33`, `:331-334`). §8.3 records
the consequence. **Mono:** not stereo by definition; at `channel_count` 1 the
node runs one lane (`audioif_feedback_delay.c:223-224`, `:248`) and a mono
source gets the identical effect on its one channel — no wire, no sum. The kit
measures that statement rather than assuming it.
**`capabilities`: `("tempo_sync",)`** (D10) — Sync reads `transport()` and maps
Division's note value against the returned bpm, clamped into Time's range and
the line length. The DD-2 has no sync; this is a D2 addition, and because the
class reads the transport it declares the capability.

*(from §5)*

- **What the palette does instead, and the measurement.**
  `AUDIOIF_FEEDBACK_DELAY_OPT_DELAY_MS` writes `config->delay_frames`
  directly (`audioif_feedback_delay.c:81-83`) and the loop reads it unsmoothed
  each frame (`:212`), so a new time lands in one jump. Measured (A2): a single
  `set(delay_ms=150)` from 200 ms gave a one-sample step of **−7 713 LSB**
  where the largest legitimate step in the same material is **1 564 LSB** —
  4.9× the signal's own maximum slew — with no pitch deviation at all.
  Stepping the option from Python does not help: it is not a stream input, so
  the finest Python can move it is one 256-frame block
  (`audioif_feedback_delay.h:39`), 187 Hz at 48 kHz — a staircase of clicks.

*(from §5)*

- **Design sketch.** Two additive options, `delay_target_ms` and
  `delay_slew_ms_per_s`. `delay_frames` becomes a current value moved toward
  the target by at most `slew` frames per frame inside the existing loop: one
  compare, one add, one float of new state, no allocation. **Default
  `slew = 0` reproduces today's behaviour exactly**, so existing renders stay
  byte-identical and the extend-never-modify rule holds.

*(from §5)*

- **Refutation record (Phase 0), five palette-only routes tried and
  rejected.** Numbers in A7. (a) *Cross-fade between two read pointers* —
  S2's own alternative, which "avoids a potentially undesirable Doppler
  effect": it removes the click but also removes T2, because the pitch shift
  *is* the trait. (b) *Python steps the option per block* — measured: a
  200 → 150 ms ramp over 47 blocks gives a largest first difference of
  **6 058 LSB against the unramped 1 565**, at a mean 1 009 Hz where T2's law
  asks 1 196. (c) *Build the line in Python* — breaks the no-allocation rule
  and tri-runtime portability. (d) *`audiodelays.Echo(freq_shift=True)`* — the
  palette's one existing answer, which vision §6 names, and the DD-2's own
  single-clock mechanism: it holds the buffer at full length and varies the
  traversal rate (`audiodelays/Echo.c:116-120`). Measured, it is click-free
  and does pitch-shift, 997 → 1 329 Hz for one lap. Refuted on two counts.
  **T4:** the rate is an integer in 8.8 fixed point, so 350 ms lands at
  **350.688** — 33 samples off, where T4 disconfirms above one. **T2:** the
  excursion is a fixed ratio held for a whole lap, still 1 329 Hz 60 ms after
  the move ends, where T2 asks for 1 cent within 50 ms. The Tier 1 wire
  failure is on top of both. (e) *Drive the delay with the node's own wow
  oscillator* — the route that nearly works: freezing `wow_hz` at the
  oscillator's quarter period parks the delay at
  `delay_frames + wow_depth_frames` and holds it (200 ms + 50 ms depth
  measured at 250.00 ms), and the glide meets T2's no-step clause **exactly**
  — largest first difference 1 565 LSB, the unramped render's own maximum —
  with a real doppler, 997 → 910 Hz and back to 997.00 after the freeze. Still
  refuted, for four reasons all in the C: the oscillator turns one way only
  (`wow_step` is 0 for `wow_hz ≤ 0`, `:113`), so a downward move must detour up
  through the depth; the shape is a quarter-sine whose duration is locked to it
  at 1/(4·`wow_hz`); the freeze lands only on a block boundary
  (`audioif_feedback_delay.h:39`); and `wow_sine` cannot be re-zeroed short of
  `reset()`, which empties the line (`:167-175`). **What (e) settles: the
  per-sample machinery this ask wants is already in the node; what is missing
  is a way to drive it monotonically to a target** — the sketch above.

*(from §5)*

- **Shared, not private.** Vision §6 already lists this candidate for the
  Echoplex, RE-201 and DM-2 pitch bend. One change serves `TapeDelay`,
  `AnalogDelay`, `PingPongDelay`, `SlapbackDelay` and this class; cost it once
  in Phase 1 against all five.

*(from §7)*

1. **No surface at all.** `MACRO_LABELS = ()` (`delay.py:31`),
   `PATCHES = {0: ("Default", ())}` (`:33`). The setters `set_time` (`:41`)
   and `set_mix` (`:44`) are reachable only from Python that knows the class.

*(from §7)*

2. **The line is sized from the constructor's time, and truncated.**
   `max_delay_ms=int(time_ms) + 100` (`:36`): a class built at 350 ms can
   never be moved past 450 ms, and `int()` drops the fraction silently.

*(from §7)*

5. **`tail_samples` is `None`.** No delay class overrides `TAIL_SAMPLES`, so
   the base default at `_core.py:141` stands and a 450 ms line at
   `feedback = 0.4` reports an unknown tail.

*(from §7)*

7. **`reset()` touches only the output node** (`_core.py:366-373`), so a
   chain's reset depends on which node happens to be last. The rebuild
   enumerates the nodes it built and walks that list (roadmap §3).
