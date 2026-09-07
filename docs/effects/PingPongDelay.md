# Effects Dossier — `PingPongDelay` (no standout — design grade)

**Class:** `lib/audioeffects/delay.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Time, roadmap Phase 5
**Standout:** **none**, per vision §4.2 — **confirmed** in §2. Ping-pong is a
routing topology over two delay lines, not a circuit; the search for a
defining product found definitions of the *structure* and no unit that owns
it.
**Grade:** design. Traits are the textbook property of the topology, stated
falsifiably, and the class is additionally graded on Tier 1 and Tier 3
(vision §4.1).
**Portability tier:** needs audioif-own nodes (`audioecho`) — the cross-feed
does not exist anywhere else on the palette (§4).
**Status:** seed (Phase 0)

## 1. The topology, in one paragraph

Two delay lines, one feeding each output channel. The input is steered into
one of them; each line's output is heard on its own channel **and** is fed
into the *other* line's input, scaled by the feedback coefficient. With one
shared time *T* and feedback *f*, repeat *n* appears at *n·T* on the left for
odd *n* and the right for even *n*, at gain *f*ⁿ⁻¹ — so the repeats alternate
at spacing *T* while each channel repeats every 2*T*. Tone.js describes the
structure as "two Tone.FeedbackDelays with independent delay values. Each
delay is routed to one channel (left or right), and the channel triggered
second will always trigger at the same interval after the first" (S1) — note
that its prose says *independent* values while its documented surface exposes
a single `delayTime` Signal governing both, which is the one-shared-time form
this dossier adopts, for the reason §2 gives. Sound On Sound documents the
asymmetric variant, two independent times: "the first echo appears in the
'ping' channel (usually the left), delayed by the ping amount, and the second
appears in the opposite 'pong' channel, delayed by the ping time plus the pong
time" (S2). There is no nonlinearity, no LFO and no filter in the definition;
the dry path is not delayed on either side, which is what separates a
ping-pong from a Haas widener — S2's caution that delaying one channel against
the other "will result in unpleasant comb filtering when the left and right
channels are summed to mono" applies to the widener and must not apply here.
The controls this dossier proposes — Time, Feedback, Mix and a Spread that
moves the topology between two independent delays and a full cross — are §6's
design choices, not a survey of products: no product was reached (§2), and
nothing here is sourced to one.

## 2. Sources and license calls

Reached on 2026-09-06; nothing from memory.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Tone.js `PingPongDelay` documentation (v15.1.22) | "a feedback delay effect where the echo is heard first … (App. S1) | No licence statement rendered on the doc … (App. S1) | <https://tonejs.github.io/docs/15.1.22/classes/PingPongDelay.html>, <https://raw.githubusercontent.com/Tonejs/Tone.js/15.1.22/LICENSE.md> | yes |
| **S2** *Sound On Sound*, "Creating & Using Custom Delay Effects" … (App. S2) | the asymmetric ping/pong definition with a worked … (App. S2) | "All contents copyright © SOS Publications … (App. S2) | <https://www.soundonsound.com/techniques/creating-using-custom-delay-effects> | yes |
| **S3** Smith & Lee, *Time Varying Delay Effects*, CCRMA RealSimple … (App. S3) | "zipper noise" from an uninterpolated moving read … (App. S3) | no copyright, `©` or licence string anywhere … (App. S3) | <https://ccrma.stanford.edu/realsimple/DelayVar/DelayVar.pdf> | yes |
| **S3b** Smith, *Physical Audio Signal Processing* … (App. S3b) | linear interpolation's amplitude error is "highly … (App. S3b) | "Copyright © 2026-08-21 by Julius O. Smith … (App. S3b) | <https://ccrma.stanford.edu/~jos/pasp/Fractional_Delay_Filtering_Linear.html> | yes |
| **S4** Disch & Zölzer, "Modulation and Delay Line Based Digital Audio … (App. S4) | the classification: a fixed-coefficient variable-delay … (App. S4) | Proceedings PDF from dafx.de's own archive … (App. S4) | <https://www.dafx.de/paper-archive/1999/disch.pdf> | yes |

**Audited 2026-09-06** by an independent licence-and-citation pass: every row
above and every URL in this file re-fetched, the corrections listed in
Appendix A3.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

A design grade states the textbook property as its traits (vision §4.1). All
five below were **demonstrated or bounded on the palette during this run**, which is
why their confidence is high and their disconfirmation conditions are numeric;
the numbers are in Appendix A1.

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

*Design grade: the textbook property of the topology, stated falsifiably.*

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **Repeats alternate.** With Spread at maximum, repeat *n* peaks at *n·T* on one channel only — odd *n* on the side First Side names, even *n* on the other — and in the ±1 ms window around each peak the opposite channel's energy is below −40 dB re that peak, for repeats 1 through 8. Flipping First Side exchanges the two channels and nothing else. | S1, S2 | high — measured on … (App. T1) | any repeat's energy on the wrong channel above −40 dB re its energy on the right one; repeats peaking at the same instant on both sides; or First Side changing anything but which channel carries the odd repeats | click identical in both channels … (App. T1) |
| T2 | **One decay ratio across the alternation, not per pair.** Counting repeats across both channels in time order, each is *f* times the one before within 1 %, and the two channels' own decay rates agree within 1 %. | S1 ("the channel triggered second will always … (App. T2) | high — measured: 20 … (App. T2) | any successive-repeat ratio more than 1 % from *f*; or the two channels' fitted decay rates differing by more than 1 % | click through at Spread max … (App. T2) |
| T3 | **The mono sum is an ordinary delay, exactly.** Summing L+R of the stereo output, in int32 so the sum cannot clip, gives *bit-identical* samples to what a `channel_count = 1` `FeedbackDelay` at the same *T* and *f* gives on the same probe; and the class built at `channel_count` 1 produces that same signal rather than losing its feedback. | the topology (S1, S2); arithmetic | high — measured both … (App. T3) | any sample of the summed stereo output differing from the mono reference at all; **or** a mono construction producing fewer repeats than the reference (the `cross_feed = 1` mono defect, §7.1) | render the class at … (App. T3) |
| T4 | **Spread is a topology control with two honest endpoints.** On a channel-identical probe: at Spread 0 the two channels' repeat trains are identical, L−R below −90 dBFS — two independent delays. At Spread 1 each channel carries only odd or only even multiples of *T*, its wrong-multiple energy below −40 dB. Between them the alternation depth — the ratio in dB of a channel's right-multiple to wrong-multiple energy — never falls more than 0.5 dB below the position before it. | S2's "a type of dual delay" … (App. T4) | high | L−R above −90 dBFS at Spread 0 on a channel-identical probe; wrong-multiple energy above −40 dB at Spread 1; or alternation depth dropping more than 0.5 dB between consecutive positions | click through at 11 Spread … (App. T4) |
| T5 | **The dry path is never delayed or spread.** In the window before the first repeat arrives (0 … *T*), L and R match the source within 0.05 dB and 1 sample of group delay on both channels, at every macro setting; so the mono sum of the dry shows no notch deeper than 0.5 dB across 20 Hz–20 kHz and S2's channel-offset comb caution does not apply to this class. | S2 (the caution, as the thing this class must … (App. T5) | high | any inter-channel magnitude difference above 0.05 dB or group-delay difference above 1 sample in the pre-repeat window, at any macro setting; or a mono-sum notch deeper than 0.5 dB in that window | swept sine at `mix = 0.2` … (App. T5) |

No characters: one topology, one behaviour set.

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**One node: `audioecho.FeedbackDelay`**, composed, not extended, with
`cross_feed = Spread` and `input_pan = ∓Spread`. The node was built for this:
each channel's loop output is summed as `loop[ch]·(1−cross) + loop[other]·cross`
before being written back (`audioif_feedback_delay.c:203-204`, `:247-256`),
and `input_pan` at hard over sends the *average* of the two input channels
into one lane and nothing into the other, precisely so a mono source panned
into one line does not arrive 6 dB hot (`:126-141`). The dry path is the
channel's own signal and never the panned one (`:257-261`), which is T5. The
two optional colour macros use the in-loop one-poles (`:231-240`), which are
skipped entirely at a zero coefficient (`:31-38`).

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**None.** Two candidates were considered and both were refuted at Phase 0.

- **Independent ping and pong times** (S2's asymmetric form). The config …  *(argument in full: App. R)*
- **A mono cross-feed path** (so `cross_feed` kept meaning something at …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Nine macros.

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Time | UNIPOLAR | 20–1000 ms, log; default 280 ms | the spacing between alternating repeats (S1's `delayTime`) |
| 1 | Feedback | UNIPOLAR | 0.0–0.99 | how many times the signal crosses before fading |
| 2 | Mix | UNIPOLAR | 0.0–2.0 (`Echo`'s convention: dry at unity to 1) | the wet/dry balance |
| 3 | Spread | UNIPOLAR | 0.0–1.0; default 1.0 | the topology itself: 0 = two independent delays, 1 = full cross (T4) |
| 4 | First Side | TOGGLE | left (default) / right | which channel the "ping" lands in (S2's naming) |
| 5 | Sync | TOGGLE | off / on | none — D2 addition; reads `transport()` |
| 6 | Division | UNIPOLAR | 16 steps, 1/32 … 1/1, dotted and triplet | none — D2 addition |
| 7 | Repeat Tone | UNIPOLAR | 800–16 000 Hz log; top = out of circuit (default) | a darkening bounce; in-loop, so it compounds per crossing |
| 8 | Repeat Cut | UNIPOLAR | 20–400 Hz log; bottom = out of circuit (default) | keeping the low end out of the bounce |

**Patches** (names describe settings, never products): `Wide Bounce` (280 ms,
f 0.45, mix 0.3, Spread 1.0) · `Eighth Note Bounce` (Sync, 1/8, f 0.5,
Spread 1.0) · `Quarter Note Bounce` (Sync, 1/4, f 0.4) · `Narrow Bounce`
(280 ms, Spread 0.5) · `Two Delays` (280 ms, Spread 0.0 — the T4 endpoint) ·
`Dark Bounce` (420 ms, f 0.65, Repeat Tone 2.5 kHz) · `Right First`
(280 ms, First Side right).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/delay.py`.

1. **Mono is broken, and silently.** At `channel_count` 1 the default …  *(argument in full: App. R)*
2. **The Time macro's range exceeds the line the class allocates.** …  *(argument in full: App. R)*
3. **Spread does two things because half of it is useless alone** (`:278-282`, …  *(argument in full: App. R)*
4. **`tail_samples` is `None`** (`_core.py:141`, not overridden) on a class
   whose tail is a closed form of Time and Feedback.
5. **`capabilities` is empty** (`_core.py:139`) on the class whose whole
   identity is rhythmic.
6. **`reset()` touches only the output node** (`_core.py:366-373`), so a …  *(argument in full: App. R)*
7. **No `First Side`**: `input_pan=-spread` (`:282`) hard-codes the ping to
   the left.

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Symmetric or asymmetric?** §2 and §5 settle on S1's one-time form
   because it is what the traits are stated over and what the palette
   reaches. If the implementation session wants S2's two-time form it must
   fix a trait for it first and file the node ask against that trait.
   *Settles:* the implementation session, in the Phase 5 packet.
2. **Should Spread's midpoints be documented as a control law, or only its
   endpoints?** T4 fixes both endpoints and requires monotonicity between,
   which is deliberately weaker than a stated law, because no source defines
   one. *Settles:* the implementation session, when the measurement in T4 is
   run for the first time.
3. **Is the read interpolator's high-frequency loss worth documenting here
   more than elsewhere?** `delay_frames` is a float and the read is linear
   interpolation, so a half-sample delay costs the wet path 5.11 dB at 15 kHz
   at 48 kHz (`DigitalDelay` A6, measured this run) — and at Spread 1 every
   repeat passes the interpolator twice per round trip, which is S3b's
   "highly audible ... when the loop gain is close to 1" warning arriving
   through the palette rather than through the algorithm. No trait above
   rests on it. *Settles:* the implementation session, in the Phase 5 packet.
4. **Does `Repeat Tone` compounding *twice* per round trip need saying in the
   docstring?** At Spread 1 a repeat crosses two lines per 2*T*, so an in-loop
   filter darkens it at twice the rate a mono delay would at the same setting.
   It is honest behaviour, but it is surprising. *Settles:* the
   implementation session.

---


## Appendix

### A1. Measurements taken this run

On `audiocomponents/.venv/bin/python` (the CPython build of audioif), 48 kHz,
`int16`, blocks pulled through `audiocore.get_buffer`. Probe: a single
full-amplitude click (20 000) in the first frame of every channel, then
silence, through `audioecho.FeedbackDelay(max_delay_ms=600, delay_ms=100,
feedback=0.6, mix=2)`. Peaks reported as (ms, value).

**Stereo, Spread 1 (`cross_feed=1.0`, `input_pan=-1.0`) — T1, T2:**

| channel | repeats |
|---|---|
| left | (100, 20 000) (300, 7 200) (500, 2 592) (700, 933) (900, 336) |
| right | (200, 12 000) (400, 4 320) (600, 1 555) (800, 560) (1000, 202) |

Interleaved by time: 20 000, 12 000, 7 200, 4 320, 2 592, 1 555, 933, 560,
336, 202 — a ratio of **0.600 at every step**, which is *f*. Each channel
alone falls by 0.36 = *f*², i.e. per pair. **T2's planted fault is measuring
down one channel instead of across both**: that reads a decay of 0.36 and
"confirms" a ping-pong that is really two independent delays at half rate.

**Mono, same settings — the defect in §7.1:**

| channel | repeats |
|---|---|
| mono | (100, 10 000) — **and nothing else** |

Two separate causes, both worth naming: the missing repeats are `cross_feed`
at 1.0 making `sent = loop·(1 − cross_feed) = 0` in the mono branch (`:248`),
and the half level is `input_pan` at −1 leaving `feed_own[0] = 0.5` — the
averaging at `:136-141` that keeps a mono source from arriving 6 dB hot in
the stereo case, applied where there is no second lane to average with.

**Mono with the class-side fix (`cross_feed=0`, `input_pan=0`) — T3:**

| channel | repeats |
|---|---|
| mono | (100, 20 000) (200, 12 000) (300, 7 200) (400, 4 320) (500, 2 592) (600, 1 555) (700, 933) (800, 560) (900, 336) (1000, 202) |

Identical, value for value, to the stereo build's interleaved train. That is
T3 demonstrated at Phase 0, before a line of the rebuild exists, and it is
what makes the "no node ask" call in §5 an argument rather than an assertion.

**Wire invariant, shared with the other two delay seeds.** At `mix = 0` on a
±32 000 1 kHz tone, `audioecho.FeedbackDelay` differs from the source in
**0 of 9 600** samples; `audiodelays.Echo` differs in 2 800, peak
32 000 → 28 437 (`audioif_echo.c:38`, scale at `:11`).

### A2. Node lines relied on

`audioif/src/shared/audioif_feedback_delay.c` — `:31-38` a zero cutoff gives a
zero coefficient; `:64-70` the mono path forces `feed_own`/`feed_other`;
`:81-83` `delay_ms` → `delay_frames`, one value for both lanes; `:90`
feedback clamped `0..0.99`; `:99` mix clamped `0..2`; `:120-121` `cross_feed`
clamped `0..1`; `:126-141` `input_pan`, hard over sending the *average* of
both inputs into one lane; `:203-204` the `direct`/`crossed` split;
`:212` the delay read, unsmoothed; `:226-228` linear interpolation;
`:231-240` the two in-loop one-poles; `:247-256` the cross-fed feedback write;
`:248` `other = 0` in mono — the cause of §7.1; `:257-261` the dry path is
the channel's own signal, never the panned one (T5).
`audioif/src/audioecho/FeedbackDelay.c:102-110` allocates
`line_frames × 2 × sizeof(int16_t)` — two lanes always, even in mono.
`audioif/docs/upstream-diff.md:770-785` records `audioecho` as audioif's own
node and names ping-pong as one of the three reasons it exists.

### A3. Licence and citation audit, 2026-09-06

Run by an independent licence-and-citation auditor. **Every source row in §2
and every URL in this file was re-fetched in this run**; nothing below is
carried over from an earlier pass, and no source is cited that this pass did
not reach itself.

**Read back and confirmed verbatim.** S1's description ("PingPongDelay is a
feedback delay effect where the echo is heard first in one channel and next in
the opposite channel"), its "two Tone.FeedbackDelays with independent delay
values ... the channel triggered second will always trigger at the same
interval after the first", and — the point §2 turns on — its documented
surface, which exposes **one** readonly `delayTime` Signal and one constructor
`delayTime`, against prose that says "independent delay values". The
inconsistency is real and is in the source, not in the reading of it.

S2's definition read back word for word, including "a type of dual delay", the
clause the seed depends on ("delayed by the ping time plus the pong time"), the
worked example ("if you set the ping to 200ms and the pong to 400ms, you'd
first hear the ping 200ms after the programme material out of the left channel,
and the Pong 600ms after the programme material out of the right channel"), and
the mono caution ("simply delaying one side in relation to the other will
result in unpleasant comb filtering when the left and right channels are summed
to mono"). Worth recording for T5: in the article that caution is aimed at the
**Haas-widener** technique, which is exactly the use the seed puts it to. Its
copyright line reads "All contents copyright © SOS Publications Group and/or
its licensors, 1985-2026. All rights reserved."

S3's eq. (10) and "zipper noise" sentence, and S3b's "highly audible
(particularly when the loop gain is close to 1, as it is for steel strings, for
example)", both read back. S4's header ("Proceedings of the 2nd COST G-6
Workshop on Digital Audio Effects (DAFx99), NTNU, Trondheim, December 9-11,
1999") and its one load-bearing sentence ("The variation of the delay length is
a phase modulation (PM) and its dynamic component is perceived as a frequency
modulation") read back, and the seed's negative claim was re-checked by search
rather than trusted: **`ping` and `pong` occur zero times** in its full
extracted text.

**Corrections applied by this pass.**

1. **S1's licence chain was pinned to the wrong ref.** The row documents
   Tone.js **v15.1.22** but its licence was read from the `dev` branch, whose
   `LICENSE.md` carries "Copyright (c) 2014-2025 Yotam Mann". The copy that
   governs the documented version — tag `15.1.22`, fetched this run — reads
   **"Copyright (c) 2014-2020 Yotam Mann"**. Same licence (MIT), different
   copyright line and a different ref; the row now cites the tagged URL.
   (`v15.1.22` is not a valid tag name and returns 404; the tag is `15.1.22`.)
   The licence
   **call is unchanged**: MIT, verified, and irrelevant in practice because
   only prose was read, never code.
2. **Two licence calls made explicit.** S3 and S4 recorded the absence of a
   licence but not the call the vision's §5 requires; both now read **"licence
   unverified, treated as copyleft"**. No licence call was *downgraded* in
   substance and none was upgraded. S2 stays at verified all-rights-reserved.

**What this pass did not correct, and why.** §2's design-grade paragraph and §1
already state the S1 prose/surface inconsistency and settle it on the
documented surface; that reading was re-checked against the live page and
holds. The claim that no product standout exists was not re-searched — that is
a grade question, not a citation one.

**What this pass did not check.** The A1 measurements were not re-run; they are
the technical auditor's. Every `grep -n` line citation in A2 *was* re-checked
against the audioif tree — including `:64-70`, `:203-204`, `:247-256`, `:248`
and `:257-261`, the five the "no node ask" argument rests on — and all of them
resolve to the lines claimed. `upstream-diff.md:782-785` is exactly the
ping-pong bullet, as cited.

### A4. Numbers the trait critic added, 2026-09-06

Taken this run on `audiocomponents/.venv/bin/python` (the CPython build of
audioif), 48 kHz, `int16`, a click of 20 000 identical in both channels,
`max_delay_ms=600, delay_ms=100, feedback=0.6, mix=2`.

**T3 is exact, not approximate.** A1 compared peak values; this pass compared
every sample of a 1.2 s render. The stereo build (`cross_feed=1.0`,
`input_pan=-1.0`) summed L+R against a `channel_count = 1` `FeedbackDelay`
(`cross_feed=0`, `input_pan=0`) at the same *T* and *f*: **maximum absolute
difference 0, zero differing samples**. T3's tolerance was "more than 1 LSB";
the palette gives bit-identity, so the row now says so and a 1 LSB drift is a
finding rather than a rounding.

A1's three tables reproduced exactly: left (100 ms, 20 000) (300, 7 200)
(500, 2 592) (700, 933) (900, 336); right (200, 12 000) (400, 4 320)
(600, 1 555) (800, 560) (1000, 202); the mono build with the class-side fix
giving the full interleaved train; and the unfixed mono default
(`cross_feed=1`, `input_pan=-1`) giving one repeat at 10 000 and nothing else
— §7.1's defect, reproduced.

**The wire finding shared with the other two delay seeds, re-measured.** At
`mix = 0` on a 1 kHz sine, `audioecho.FeedbackDelay` differs from the source in
**0 of 9 600** samples at amplitude 12 000 *and* at 32 000;
`audiodelays.Echo` differs in **0** at 12 000, **0** at 28 000 and **2 800 of
9 600** at 32 000, peak 32 000 → 28 437. The full-scale probe is what makes
the difference visible, exactly as the seeds state.

### A5. The palette verifier's pass, 2026-09-06

An independent pass re-ran every §4 and §5 claim about what an audioif node
can and cannot do, against the C under `audioif/src/shared` and the bindings
under `audioif/src/audioecho/`, and probed the behavioural ones on
`audiocomponents/.venv/bin/python`, 48 kHz, interleaved `int16`.

**Reproduced exactly.** A1's three repeat tables — stereo left (100 ms,
20 000) (300, 7 200) (500, 2 592) (700, 933) (900, 336) and right (200,
12 000) (400, 4 320) (600, 1 555) (800, 560) (1000, 202); the unfixed mono
default giving one repeat at 10 000 and nothing after it; the class-side fix
giving the full interleaved train. A4's bit-identity: the stereo output summed
L+R against a `channel_count = 1` `FeedbackDelay` at the same *T* and *f*,
**0 differing samples over 57 600 frames (1.2 s)**, and the mono build with
the class-side fix equal sample for sample to a plainly-built mono
`FeedbackDelay`. A1's wire row (2 800 of 9 600 for `audiodelays.Echo`, 0 for
`audioecho.FeedbackDelay`).

**Two §4 claims that had not been measured, now measured.** `input_pan = −1`
on a probe with 20 000 on the left and 8 000 on the right puts **14 000** —
exactly the average — into the left lane's first repeat and **nothing** into
the right lane, which is §4's "does not arrive 6 dB hot" claim demonstrated
rather than read. And T4's Spread 0 endpoint: `cross_feed = 0`,
`input_pan = 0`, `feedback = 0.6`, a channel-identical click, **L − R exactly
zero across 30 208 frames** — well inside the −90 dBFS bar, and reachable by
construction rather than by luck.

**Corrected in §5.** The first refuted candidate cited
`audioif_feedback_delay.c:64` for "one `delay_frames` serves both lanes"; that
line is `config->channel_count = ...` in `set_channel_count`. The single
`delay_frames` field is `audioif_feedback_delay.h:64`, and what makes two
times unreachable is that `offset` is computed from it once per frame
*outside* the per-channel loop (`audioif_feedback_delay.c:212-224`). The
citation is fixed; the refutation stands.

**One note for the rebuild, not a node ask.** `delay_ms` is clamped to
`line_frames − 2` (`audioif_feedback_delay.c:81-83`), so a line sized at
exactly the macro's 1000 ms ceiling measures 999.958 ms at the top of the
knob. The class allocates headroom above the ceiling rather than reporting a
time it cannot reach.

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

**This class is stereo by definition, and T3 is its mono statement.** A mono
source gets **the mono sum of the stereo behaviour**: an ordinary feedback
delay at the same Time and Feedback, repeats at *T*, 2*T*, 3*T* … at gains 1,
*f*, *f*² … That is not a convenience — it is arithmetically what summing the
two channels of the stereo result gives, and it was measured both ways this
run (A1). It is stated as a Tier 2 trait so the kit has to demonstrate it
rather than assume it, and because the palette does **not** give it for free
(§4). *Rate:* every trait holds at 48, 44.1 and 22.05 kHz — nothing here is
Hz-valued except the two optional loop filters, which clamp.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Tone.js `PingPongDelay` documentation (v15.1.22) | "a feedback delay effect where the echo is heard first in one channel and next in the opposite channel"; the two-line structure; **prose saying the two delays carry "independent delay values"**, against a documented surface of one constructor `delayTime` and one readonly `delayTime` Signal — the two do not say the same thing, and §2's paragraph below settles which this dossier follows | No licence statement rendered on the doc page; chased to the project's own `LICENSE.md` **at the tag matching the documented version**, fetched this run: **MIT**, "Copyright (c) 2014-2020 Yotam Mann". (The `dev` branch's copy is the same MIT text with a "2014-2025" line; the tagged copy is the one that governs v15.1.22, and `v15.1.22` is not a valid tag name — the tag is `15.1.22`.) Only the prose and the documented surface were read here, never code, so the port question does not arise either way (vision §5) | <https://tonejs.github.io/docs/15.1.22/classes/PingPongDelay.html>, <https://raw.githubusercontent.com/Tonejs/Tone.js/15.1.22/LICENSE.md> | yes |
| **S2** *Sound On Sound*, "Creating & Using Custom Delay Effects", May 2012 | the asymmetric ping/pong definition with a worked example (ping 200 ms, pong 400 ms → left at 200 ms, right at 600 ms); the mono-sum comb-filter caution for channel-offset delays | "All contents copyright © SOS Publications Group and/or its licensors, 1985-2026" — read-only, a definition | <https://www.soundonsound.com/techniques/creating-using-custom-delay-effects> | yes |
| **S3** Smith & Lee, *Time Varying Delay Effects*, CCRMA RealSimple, 2008 (PDF, text via `pypdf`) | "zipper noise" from an uninterpolated moving read; eq. (10) ω_l = ω_s(1 − Ḋ_t); linear vs allpass interpolation, and why amplitude error matters *inside a feedback loop* — which is what a ping-pong is | no copyright, `©` or licence string anywhere in the 60-page extracted text (checked this run) — **licence unverified, treated as copyleft**; read as a paper, never ported | <https://ccrma.stanford.edu/realsimple/DelayVar/DelayVar.pdf> | yes |
| **S3b** Smith, *Physical Audio Signal Processing*, "Fractional Delay Filtering by Linear Interpolation" | linear interpolation's amplitude error is "highly audible (particularly when the loop gain is close to 1)"; allpass interpolation removes it at some delay error | "Copyright © 2026-08-21 by Julius O. Smith III", attributed to *Physical Audio Signal Processing*, W3K Publishing, 2010. No licence grant, reuse permission or terms link appears beyond that bare copyright line — **licence unverified, treated as copyleft**; read as a paper, never ported | <https://ccrma.stanford.edu/~jos/pasp/Fractional_Delay_Filtering_Linear.html> | yes |
| **S4** Disch & Zölzer, "Modulation and Delay Line Based Digital Audio Effects", DAFx-99, NTNU Trondheim (PDF, text via `pypdf`) | the classification: a fixed-coefficient variable-delay structure is phase modulation, "its dynamic component is perceived as a frequency modulation" — corroborates S3 | Proceedings PDF from dafx.de's own archive; no copyright, `©` or licence string in the 4-page extracted text (checked this run) — **licence unverified, treated as copyleft**; read as a paper, never ported | <https://www.dafx.de/paper-archive/1999/disch.pdf> | yes |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **Repeats alternate.** With Spread at maximum, repeat *n* peaks at *n·T* on one channel only — odd *n* on the side First Side names, even *n* on the other — and in the ±1 ms window around each peak the opposite channel's energy is below −40 dB re that peak, for repeats 1 through 8. Flipping First Side exchanges the two channels and nothing else. | S1, S2 | high — measured on the palette (A1) | any repeat's energy on the wrong channel above −40 dB re its energy on the right one; repeats peaking at the same instant on both sides; or First Side changing anything but which channel carries the odd repeats | click identical in both channels, `mix = 2`, Spread max: per-channel peak time and level for repeats 1–8, at 48 / 44.1 / 22.05 kHz, with First Side left and right |
| T2 | **One decay ratio across the alternation, not per pair.** Counting repeats across both channels in time order, each is *f* times the one before within 1 %, and the two channels' own decay rates agree within 1 %. | S1 ("the channel triggered second will always trigger at the same interval after the first") | high — measured: 20 000, 12 000, 7 200, 4 320, 2 592, 1 555 at *f* = 0.6, ratio 0.600 at every step (A1) | any successive-repeat ratio more than 1 % from *f*; or the two channels' fitted decay rates differing by more than 1 % | click through at Spread max, *f* = 0.6 and *f* = 0.85, `mix = 2`: peak levels of repeats 1–8 interleaved by time, ratio fitted on peaks of at least 200 LSB so int16 quantisation cannot dominate the fit. **T2's planted fault is measuring down one channel instead of across both** — that reads 0.36 and confirms a ping-pong that is really two independent delays at half rate (A1) |
| T3 | **The mono sum is an ordinary delay, exactly.** Summing L+R of the stereo output, in int32 so the sum cannot clip, gives *bit-identical* samples to what a `channel_count = 1` `FeedbackDelay` at the same *T* and *f* gives on the same probe; and the class built at `channel_count` 1 produces that same signal rather than losing its feedback. | the topology (S1, S2); arithmetic | high — measured both ways this run, **0 differing samples across a 1.2 s render** (A1) | any sample of the summed stereo output differing from the mono reference at all; **or** a mono construction producing fewer repeats than the reference (the `cross_feed = 1` mono defect, §7.1) | render the class at `channel_count` 2 on a channel-identical click and sum L+R in int32; render the class at `channel_count` 1; render `audioecho.FeedbackDelay(channel_count=1, cross_feed=0, input_pan=0)` at the same *T* and *f*; all three compared sample for sample at `mix = 2`, 48 and 44.1 kHz |
| T4 | **Spread is a topology control with two honest endpoints.** On a channel-identical probe: at Spread 0 the two channels' repeat trains are identical, L−R below −90 dBFS — two independent delays. At Spread 1 each channel carries only odd or only even multiples of *T*, its wrong-multiple energy below −40 dB. Between them the alternation depth — the ratio in dB of a channel's right-multiple to wrong-multiple energy — never falls more than 0.5 dB below the position before it. | S2's "a type of dual delay"; S1's cross-coupled form | high | L−R above −90 dBFS at Spread 0 on a channel-identical probe; wrong-multiple energy above −40 dB at Spread 1; or alternation depth dropping more than 0.5 dB between consecutive positions | click through at 11 Spread positions, `mix = 2`: L−R RMS, and per channel the odd- against even-multiple energy in ±1 ms windows at *n·T*. **The probe must be identical in both channels** — with a different signal on each side L−R is not silent at Spread 0 and the endpoint reads as broken when it is not |
| T5 | **The dry path is never delayed or spread.** In the window before the first repeat arrives (0 … *T*), L and R match the source within 0.05 dB and 1 sample of group delay on both channels, at every macro setting; so the mono sum of the dry shows no notch deeper than 0.5 dB across 20 Hz–20 kHz and S2's channel-offset comb caution does not apply to this class. | S2 (the caution, as the thing this class must *not* do); the node feeds the dry path the channel's own signal, never the panned one (`audioif_feedback_delay.c:257-261`, read this run) | high | any inter-channel magnitude difference above 0.05 dB or group-delay difference above 1 sample in the pre-repeat window, at any macro setting; or a mono-sum notch deeper than 0.5 dB in that window | swept sine at `mix = 0.2`, Time 280 ms, analysed over the first 280 ms only, at Spread 0 / 0.5 / 1 and both First Side positions: L against R magnitude and group delay, and the mono sum against the source, 48 and 44.1 kHz |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Not reached, and what was looked for.** A *product* that could stand as a
standout: searches for a defining ping-pong pedal or rack, and for a DAFx/AES
paper treating cross-coupled stereo delay as a named structure, returned only
definitions of the topology (S1, S2) and forum discussion. Wiley's DAFX book
chapter is paywalled and was not read; S4 is a freely-archived DAFx-99 paper
by Disch & Zölzer, and its full extracted text contains no occurrence of
"ping" or "pong" — verified, not assumed. `kvraudio.com` threads were
surfaced by search and deliberately not cited — forum posts are not a source
of record here.

*(from §2)*

**Design grade confirmed.** Vision §4.2 proposes no standout for this class
and nothing found argues for one. Ping-pong is defined by where the wires go,
not by what any component does; the two definitions reached agree on the
alternation and differ on the times. S2 gives the two lines a separate ping
and pong time. S1 is not self-consistent: its prose says "independent delay
values" while the surface it documents is a single `delayTime` for both. That
is the one real design decision here, and §6 settles it: **one time**,
because that is the form the traits below can be stated over, the form S1's
documented surface actually offers, and the form the palette reaches exactly.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: **ESP32-P4
0.04**, **ESP32-S3 0.08** — one `FeedbackDelay`, the same hot loop as
`DigitalDelay` plus the cross-feed's two multiply-adds per frame
(`audioif_feedback_delay.c:247-249`). Lean patch expected: **no**. Line RAM
at the macro's 1000 ms ceiling is **192 KB** at 48 kHz
(`src/audioecho/FeedbackDelay.c:110`); a `max_time_ms` option lets a board
ask for less, and the docstring states that Time then clamps.

*(from §3)*

**Latency: zero, at every macro setting, patch and rate.** The dry path is a
wire on both channels and the repeats *are* the effect. **No option adds
latency** — no lookahead, no partition, no pitch window. `tail_samples` is
`ceil(T · 3 / −log10 f)` for `f > 0` and *T* at `f = 0`, recomputed on every
Time or Feedback move; note it is the same figure whether Spread is 0 or 1,
because the cross-feed redistributes the repeats between channels without
changing the loop gain. Verified by the click and burst-then-silence probes.

*(from §4)*

**Where the palette does *not* give the trait for free — and how it is
composed around rather than asked for.** `audioecho.FeedbackDelay` in mono
forces `feed_own[0] = 1`, `feed_other[0] = 0`
(`audioif_feedback_delay.c:64-70`) and takes `other = 0` in the loop (`:248`),
so `sent = loop[0]·(1 − cross_feed)` — and at the class's own default
`cross_feed = 1.0` that is **zero**: the feedback path is silenced. Measured
this run: at `channel_count` 1 with Spread 1, a click produced exactly **one**
repeat at half level, where the stereo build produced ten. The fix is a class
decision, not a node change: **at `channel_count` 1 the class sets
`cross_feed = 0` and `input_pan = 0`**, which produces the ordinary feedback
delay T3 requires — measured identical to the stereo build's interleaved
repeat train (A1). Compose-first wins here; §5 records the ask that was
therefore *not* made.

*(from §4)*

**Portability tier: audioif.** Nothing in the CircuitPython-ported palette has
a cross-feed; the vision's §6 survey says the same ("Ping-pong ... needs each
channel's output fed into the *other* channel's line. Two delays panned hard
apart, which is all the palette could do, gives repeats on both sides at
once" — `audioif/docs/upstream-diff.md:782-785`). On a stock CircuitPython
board the module imports cleanly and construction raises a clear
`ImportError`, the `CabinetSim` pattern (`drive.py:30-33`, `:331-334`).

*(from §4)*

**`capabilities`: `("tempo_sync",)`** (D10). The alternation is inherently
rhythmic — the whole point is repeats landing on a subdivision — so Sync
reads `transport()` and maps Division's note value against the returned bpm,
clamped into Time's range and the line length.

*(from §5)*

- **Independent ping and pong times** (S2's asymmetric form). The config
  carries a single `delay_frames` (`audioif_feedback_delay.h:64`), and the
  loop computes one `offset` from it *outside* the per-channel loop
  (`audioif_feedback_delay.c:212-224`), so two times are genuinely
  unreachable. **Refuted as an ask**
  because no fixed trait needs it: T1–T5 are all stated over the symmetric
  form, which is S1's definition and the one the class adopts (§2). An ask
  without a trait id is not an ask (vision §6). If a later dossier fixes a
  trait that needs two times, it files this itself.

*(from §5)*

- **A mono cross-feed path** (so `cross_feed` kept meaning something at
  `channel_count` 1). **Refuted** because the class composes around it
  exactly, with a measurement: setting `cross_feed = 0` and `input_pan = 0`
  in mono gives the ordinary delay T3 demands, sample for sample (A1). A node
  change would buy nothing the class cannot do in three lines of Python at
  construction.

*(from §5)*

This class does inherit `DigitalDelay` §5's delay-time slew ask if it lands —
S3's amplitude-error warning about interpolation "inside a feedback loop"
applies here more than anywhere, since a ping-pong at high Spread runs every
repeat through the interpolator twice per round trip — but it files no ask of
its own, because no trait above depends on moving the time while audio runs.

*(from §7)*

1. **Mono is broken, and silently.** At `channel_count` 1 the default
   `spread=1.0` (`delay.py:264`) sets `cross_feed=1.0` (`:282`), which the
   node turns into zero feedback (`audioif_feedback_delay.c:64-70`, `:248`).
   Measured: **one** repeat instead of ten, at half level (A1). Nothing in
   the class guards it and nothing reports it.

*(from §7)*

2. **The Time macro's range exceeds the line the class allocates.**
   `_MACRO_RANGES[0]` spans 20–1000 ms (`:254`) while `_build` sizes the line
   at `max(time_ms × 2, 400)` ms (`:80`, `:85`) — 560 ms at the default
   `time_ms=280` (`:263`). The docstring claims "the Time macro's range is
   fixed across every instance so a patch means the same milliseconds
   everywhere" (`:73-74`) and then says the engine clamps (`:74-75`). Both
   cannot be true: a patch at macro 100 means 560 ms on this instance and
   1000 ms on another.

*(from §7)*

3. **Spread does two things because half of it is useless alone** (`:278-282`,
   with the comment saying so). That is the right *behaviour* but it is
   undocumented in the surface, and it is why T4 has to state both endpoints.

*(from §7)*

6. **`reset()` touches only the output node** (`_core.py:366-373`), so a
   chain's reset depends on which node happens to be last. The rebuild
   enumerates the nodes it built and walks that list (roadmap §3).
