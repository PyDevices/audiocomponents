# Effects Dossier — `AirSpace` (the Abbey Road STEED send: tape delay, filters, chamber)

**Class:** `lib/audioeffects/rack.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Racks, roadmap Phase 6
**Standout:** vision §4.2 leaves the racks at "—, mechanism". This seed
**proposes a referent with evidence**: `AirSpace` is a send-style space, and the
documented send-style space is **S.T.E.E.D.** — Send Tape Echo Echo Delay,
developed at EMI/Abbey Road in the late 1950s by engineer Gwynne Stock (S4), a
tape delay with a filtered feedback loop feeding an echo chamber through a pair
of EMI filters (S1, S2, S3). The rack follows that routing, not a product; no
chamber impulse, no branding, no model names in the patches.
**Grade:** **design**, deliberately not *literature*: what was reached is a
plug-in user guide, a magazine review of that plug-in, an encyclopedia entry and
a studio's news page — enough to fix the **order and the elements** of the chain,
which is what a rack is, but not a schematic and not a published model. The
traits below are the documented signal flow plus the textbook properties of a
reverb send; the class is gated on Tier 1 and Tier 3 as *design* requires, with
eight Tier 2 rows offered as the stronger bar it can meet.
**Portability tier:** **audioif** — needs `audioroute` (the send split) and
`audioecho` (the filtered feedback loop). Imports cleanly on a stock
CircuitPython board and raises a clear `ImportError` at construction.
**Status:** seed (Phase 0), written 2026-09-06; audited the same day by an
independent licence and citation pass that re-fetched every row and every URL
itself, re-extracted the user guide locally and checked every page citation in
§1 and §3 against the extracted text. Its corrections are marked
*(audit 2026-09-06)* below.
Trait-critic pass 2026-09-07: every Tier 2 row rewritten to state its setting,
its threshold and its window; AS3 split into a measurable half and a half that
now has a source (S7); the user guide re-downloaded and re-extracted in that run
before any row resting on it was touched.
Palette-verification pass 2026-09-07 (unit racks): every §4/§5 claim about an
audioif node re-read in `audioif/src/` with `grep -n` and probed where it was a
claim about behaviour. N2 **stands, but its refutation record was incomplete** —
the palette does contain a delay-time doppler and this run measured it.
Corrections marked *(palette 2026-09-07)*; **Appendix A6.**

## 1. The circuit, in one paragraph

The signal splits at the input: "A direct signal is sent to output mixer. The
Chambers processing signal is sent through a buffer amplifier and then into the
system" (S1 p. 6) — the dry path never sees a filter, which is the whole point of
a *send*. The processed path goes first to a tape delay, the gap "between the
record and playback heads when the tape is running at 30 ips" (S1 p. 5),
defaulting to 111 ms because that is "the delay introduced by the 3.3 inch gap
between the record and repro heads in a BTR tape machine playing at 30 ips"
(S1 p. 13; 3.3 in ÷ 30 in/s = 110 ms — the source's own arithmetic checking out).
The delay's output splits again: one copy goes on to the chamber, the other loops
back through the tape machine, so **saturation and filtering apply once per
pass** — "Drive is created in the tape section, so each time the feedback loop
passes through the tape machine it undergoes drive processing", with the section
output "adjusted to maintain unity gain … when the Drive value changes"
(S1 p. 12). Three filters sit *in* that loop — a top cut, a bass cut and a fixed
3.5 kHz bell — and because "the signal can enter the loop several times on its
way to the chamber, these filters can have an accumulative effect" (S1 p. 12).
Only then does the signal meet the send filters proper, "Filters to Chamber" —
the EMI RS106 hi/low pass and the RS127 presence EQ (S3) — which "falls after the
Feedback section in the signal flow and is used to control the frequency range of
the signal as it enters the chamber" (S1 p. 13). The chamber is the reverb. And
the intent of the whole thing, stated plainly: "The tape feedback loop serves to
prolong the tail of the chamber sound without creating a noticeable delay effect"
(S1 p. 4) — the repeats are meant to be heard as a longer reverb, not as echoes.
The controls the rack generalizes are the send level (Echo), the recirculation
(Feedback), the tape colour (Drive, Tone), the chamber amount (Space), and the
wet/dry.

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 Waves, *Abbey Road Chambers Reverb/Delay User Guide*, 17 pp. | the whole signal flow (pp. 6–7) and the STEED controls … (App. S1) | the **PDF carries no copyright line at all** … (App. S1) | https://assets.wavescdn.com/pdf/plugins/abbey-road-chambers.pdf | yes, 2026-09-06 (fetched, then text-extracted locally with `pypdf` — WebFetch could not read it); re-fetched and re-extracted by the audit |
| S2 *Sound on Sound*, review of Waves Abbey Road Chambers | an independent statement of the same chain: "a buffer … (App. S2) | "All contents copyright © SOS Publications … (App. S2) | https://www.soundonsound.com/reviews/waves-abbey-road-chambers | yes, 2026-09-06; re-fetched by the audit (A4.2) |
| S3 Abbey Road Studios, "Inside the Waves Abbey Road Chambers Plugin" | the studio's own naming of the hardware in the send … (App. S3) | the article page carries **no** copyright … (App. S3) | https://www.abbeyroad.com/news/inside-the-waves-abbey-road-chambers-plugin-2412 | yes, 2026-09-06; re-fetched by the audit |
| S4 Wikipedia, "Send tape echo echo delay" | provenance: developed at EMI/Abbey Road in the late … (App. S4) | "Text is available under the Creative Commons … (App. S4) | https://en.wikipedia.org/wiki/Send_tape_echo_echo_delay | yes, 2026-09-06; re-fetched by the audit (A4.4) |
| S5 audioif `src/shared/audioif_feedback_delay.c` … (App. S5) | what the loop node can and cannot do … (App. S5) | MIT (PyDevices) | in tree | in tree |
| S6 audioif#23, "Three shipped filter configurations never return to … (App. S6) | the DC-hold defect the send filter inherits from … (App. S6) | MIT (PyDevices) | https://github.com/PyDevices/audioif/issues/23 | yes, 2026-09-06 (audit; issue read via `gh`, state OPEN) |
| S7 J. S. Abel, P. Huang, "A Simple … (App. S7) | the normalised echo density profile: count taps … (App. S7) | the paper's own front matter … (App. S7) | https://ccrma.stanford.edu/courses/318/mini-courses/rooms/mus318_Abel_Lecture/echo%20density.pdf | yes, 2026-09-07 (WebFetch returned the PDF unreadable; fetched and text-extracted locally with `pypdf`) |

**Looked for, not found.** A schematic or service drawing of the EMI RS106 or
RS127, or of the STEED patchbay routing: none reached — which is why the grade
stays *design*. No published model of a chamber-plus-tape-loop chain was reached.
No chamber impulse response is used or wanted: the rack builds an algorithmic
space, and `ConvolutionReverb` is where an impulse belongs.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| AS1 | **The dry path is untouched by Tone.** With Space and Echo at zero, a swept sine through the rack is flat within **0.1 dB** from 20 Hz to Nyquist at Tone = 800, 4200 and 16000 Hz — the ends and the shipped default of the macro's range (§6); the Tone filter is on the send only. | S1 pp. 6 and **16** (A1) … (App. AS1) | high | Any Tone-dependent tilt on the dry path — the exact defect audioif recorded for `TapeDelay` (upstream-diff.md, "`audioeffects.TapeDelay` was low-passing the dry signal": −19.26 dB at 10 kHz) | swept sine → transfer magnitude … (App. AS1) |
| AS2 | **Repeats darken cumulatively, the send filter once.** With Loop Tone at 3.5 kHz and Feedback at the default, the energy above 3.5 kHz in the k-th repeat window falls by a **constant per-pass loss, within ± 1 dB**, for k = 1…4 — a straight line in dB against k, whose intercept carries the single send-filter pass. With Feedback at zero exactly one pass is present and there is no k > 1 window to measure. | S1 p. 12 (A1: the loop filters' "accumulative … (App. AS2) | high | a per-pass loss varying with k by more than 1 dB; equal high-band energy in the 1st and 4th repeats; or any repeat beyond the first at Feedback 0 | impulse in, per-repeat windows … (App. AS2) |
| AS3 | **The tail is lengthened.** At the default Time (111 ms) and Feedback (§6) the chain's RT60 is **at least 1.3 ×** the RT60 of the same `Reverb` child alone at the same Size, both fitted by the same decay fit; and RT60 rises monotonically over Feedback = 0, 0.3, 0.6, 0.9. | S1 p. 4 and **p. 5** (A1 … (App. AS3) | high | an RT60 no higher than the reverb alone; or an RT60 that does not move with Feedback | RT60 by the decay fit … (App. AS3) |
| AS3b | **The repeats do not resolve as taps.** The normalised echo density profile η(t) of the rack's impulse response (S7's measure: taps outside one standard deviation in a sliding 20 ms Hanning window, normalised by erfc(1/√2) = 0.3173) reaches **1** — S7's own "start of the late field" — no later than it does for the same `Reverb` child alone at the same Size, and after the first 300 ms never falls below one late-field standard deviation of the control's profile at any multiple of the delay time. The bound is the control's own measured spread, so no threshold is invented. | S7 (A1), read this run … (App. AS3b) | medium — S7's measure … (App. AS3b) | a dip in η at multiples of the delay time — S7: "The presence of a few prominent reflections results in a low echo density value"; or η never reaching 1 where the reverb alone does | echo density profile of the … (App. AS3b) |
| AS4 | **Drive applies once per pass, at unity gain.** At the default Drive, THD in the k-th repeat window is strictly increasing for k = 1…4, each step at least **1 dB**; and sweeping Drive from 0 to full changes broadband output RMS by no more than **3 dB**. Both figures are this program's bar: S1 states the mechanism and hedges the gain claim ("as best as possible"), so it fixes no number. | S1 p. 12 (A1: drive in the tape section … (App. AS4) | medium | THD flat within 1 dB across the four repeats — drive outside the loop; or output RMS tracking Drive by more than 3 dB | harmonic spectrum per repeat … (App. AS4) |
| AS5 | **The send delay is a musical division of the transport.** With `"tempo_sync"` declared and the transport stub at 120 BPM, 1/4 measures 500 ms ± one block and 1/8 measures 250 ms ± one block; at 90 BPM, 1/8 measures 333.3 ms ± one block. With sync off the measured delay equals the Time macro in ms ± one block. A division whose value exceeds the Time range (§6: 20…500 ms) **clamps at the range end and is not refused** — Tier 1's rate/range clause, and the reason the 90 BPM case is stated at 1/8 rather than 1/4. | S1 p. 13 (A1: the Sync divisions and "the … (App. AS5) | high | a delay ignoring the stub's tempo while `"tempo_sync"` is declared, or vice versa; a division measuring anything but its arithmetic value; or a construction that refuses an out-of-range division instead of clamping | delay tracking from an impulse … (App. AS5) |
| AS6 | **The default Time is the head gap.** With no options given, `get_macro(2)` reads **111 ms ± 1 ms** and the delay measured from an impulse agrees within one block; the docstring states why — a 3.3-inch record-to-repro gap at 30 ips. | S1 p. 13 (A1: the 111 ms default and the … (App. AS6) | high | any other default, or a default the docstring does not account for; or a measured delay that disagrees with the reported macro | read the default … (App. AS6) |
| AS7 | **A Time move bends pitch, and does not click.** With a 1 kHz tone held and Time moved 111 → 222 ms over 1.0 s, the instantaneous frequency of the first repeat is **below 1 kHz throughout the move** — lengthening the line reads the tape slower — and returns to 1 kHz within one block after it; moving 222 → 111 ms puts it **above** 1 kHz throughout. The maximum sample-to-sample difference of the output during the move does not exceed the maximum in the same render with Time held, so the click half needs no invented threshold. | S1 p. 13 (A1: the tape-speed sentence) … (App. AS7) | medium — the referent … (App. AS7) | a repeat whose pitch does not move, or moves the wrong way — a crossfade implementation (§5's refutation candidate) gives no shift at all; a step rather than a continuous ramp; or a sample-to-sample maximum above the static control's | STFT / instantaneous frequency of … (App. AS7) |

How the rows were sharpened, and what AS3 cost: **Appendix A5**.

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

One `audioroute.Splitter(source, taps=2)`. Tap 0 is the **dry**, straight into
`audiomixer.Mixer` voice 0 at unity — that is AS1, built in rather than tested
for. Tap 1 is the **send**:

1. `audioecho.FeedbackDelay(mix=2.0)` — wet alone …  *(argument in full: App. R)*
2. `audiofilters.Filter` with one `synthio.Biquad` low-pass — the RS106 top cut …  *(argument in full: App. R)*
3. `audiofreeverb.Freeverb(roomsize=…, damp=…, mix=1.0)` — wet alone, since …  *(argument in full: App. R)*
4. `Mixer` voice 1 at the Space level; voice levels are Mix.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**N2 — a delay-time slew on `audioecho.FeedbackDelay`.** Additive, on an
audioif-own module, per D1. This is the candidate vision §6 already names; what
this seed adds is the trait id and the measurement.

- **Trait it unblocks:** AS7.
- **What the palette would do instead:** step the delay time from Python at
  block rate.
- **Why that fails the trait:** the node writes `delay_frames` in one assignment …  *(argument in full: App. R)*
- **Sketch:** one option (`glide_ms`, default 0.0 = today's behaviour exactly, so …  *(argument in full: App. R)*
- **Refutation record: run 2026-09-07; the case moved rather than closing.** The …  *(argument in full: App. R)*
- **Ownership:** N2 serves `TapeDelay`, `AnalogDelay` and every delay whose knob a …  *(argument in full: App. R)*

No other ask. AS1–AS6, AS3b included, are reachable on today's palette.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Nine macros of the sixteen.

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Space | UNIPOLAR | 0.0 … 1.0 | the chamber return level (S1's Reverb control) |
| 1 | Echo | UNIPOLAR | 0.0 … 1.0 | the send level into the tape machine |
| 2 | Time | UNIPOLAR | 20 … 500 ms, log | S1's Delay (0–500 ms, default 111 ms) |
| 3 | Feedback | UNIPOLAR | 0.0 … 0.95 | S1's Tape Delay Feedback (default 37.5/100; "above 85 … excessive") |
| 4 | Tone | UNIPOLAR | 800 … 16000 Hz, log | the RS106 top cut into the chamber (S1 p. 13, S3) |
| 5 | Loop Tone | UNIPOLAR | 800 … 16000 Hz, log | the loop's Top Cut, the accumulative one (S1 p. 12) |
| 6 | Drive | UNIPOLAR | 0.0 … 1.0 | S1's Drive, once per pass at unity gain |
| 7 | Mix | UNIPOLAR | 0.0 … 1.0 | S1's Wet/Dry |
| 8 | Output | UNIPOLAR | −24 … +12 dB | the return trim |

Characters: none — one chain, one set of traits. Patches (names describe
settings, never products): `0 "Long Send"` (the default: 111 ms, feedback 0.37,
Tone 5 kHz, Space 0.5), `1 "Short Send"`, `2 "Dark Loop"` (Loop Tone low,
feedback high), `3 "Bright Chamber"`, `4 "Tape Warm"` (Drive high), `5 "Dry
Room"` (Echo low, Space high), `6 "Long Send - lean"` (the S3 budget patch).
`capabilities` = `("tempo_sync",)`, and the class reads `transport()` for Time
when sync is on — S1 p. 13 makes tempo sync part of the referent, and AS5 gates
it (D10).

## 7. Defects in the current class the rebuild must not repeat

- **The filter is in front of everything, so Tone darkens the dry.**
  `rack.py:196` builds `("LowPass", {"frequency": 4200.0})` as the *first* chain
  entry, and `_SingleFilter` defaults to `mix=1.0` (`eq.py:101`), i.e. a full-wet
  series filter. Every sample the rack passes — the direct sound included — is
  low-passed at the Tone setting, where both sources put the send filter *after*
  the delay on the way to the chamber (S1 p. 13; S2). This is the same defect
  audioif already recorded for `TapeDelay` ("was low-passing the dry signal",
  upstream-diff.md), one class over. AS1 exists because of it.
- **There is no send.** The chain is strictly serial (`rack.py:195-199`): there
  is no dry bus split before filtering, which is the one structural thing a
  send-style space is (S1 p. 6). What reaches the output as "dry" is whatever
  each child passes through its own mix, so the direct sound is low-passed by the
  filter and coloured by the delay and the hall on its way.
- **The default frequency is written twice and one copy is ignored.**
  `rack.py:193` takes `frequency=4200.0` as an argument; `rack.py:196` hard-codes
  `4200.0` in the chain literal. Probed: `AirSpace(frequency=1000)` builds the
  filter at 4200 Hz and the macro init then moves it — the caller's value never
  reaches construction, and the two defaults can drift apart silently.
- **Patch 0 is not the constructor's arguments.** Probed:
  `AirSpace(frequency=1000)` then `program_change(0)` gives 4195 Hz — documented
  behaviour (`_core.py:176-180`), but the rebuilt class should say so in its
  docstring rather than surprise a caller.
- **One patch on a preset rack** (`:191`); **no Mix or Output** (`:188`), so
  Tier 1's wire clause is unreachable as shipped; and **no Feedback, Drive or
  Time** — three of the controls the referent's panel is mostly made of, frozen
  at the chain literal's values (`:197`).
- **Latency and tail are wrong by construction.** Inherited from `Rack`:
  probed `latency 0`, `tail None`, while the hall's tail is unbounded and the
  chain's is not zero-latency to a host that trusts the number (see `Rack.md` §7).
- **The docstring describes settings the rack does not set.** `:179-181` calls it
  "a wobbling tape delay", but `:197` passes no `wow` — whatever wobble there is
  belongs to `TapeDelay`'s default, not to this rack.

## 8. Open questions

1. **Who files N2, and when.** The slew serves every delay class, but the racks
   are Phase 6 and the palette releases once, in Phase 1 (roadmap §5.2). N2 must
   enter the Phase 0 node list now or AS7 parks. *Settles:* Gate 0, with the
   `TapeDelay` dossier writing the need statement.
2. **The biquad's DC hold.** The send filter is `audiofilters.Filter` +
   `synthio.Biquad`, the node audioif#23 found holding DC at low W0. Gate 0
   records one answer for the whole EQ family and the Phaser; this seed states
   which answer it took once that exists, and AS1's 0.1 dB flatness bound is
   measured under it. *Settles:* Gate 0.
3. **AS3b's criterion — closed, 2026-09-07, and worth stating how.** The seed
   asked whether "no noticeable delay effect" (S1 p. 4) could be rendered as a
   number, and was prepared to record AS3 as *unmeasured* if not. The
   trait-critic pass looked and found S7, so the row is a measurement with a
   planted fault instead. What remains open is smaller and named in the row: S7
   measures temporal texture against a Gaussian late field, and no source reached
   in either run gives an audibility threshold for one discrete echo. If the kit
   finds η too coarse to separate a lengthened tail from four soft taps, AS3b
   reverts to *unmeasured* with that measurement as its reason — a stronger
   negative than the seed could have written. *Settles:* the implementation
   session, at the kit spec.
4. **Which reverb node.** Written against `audiofreeverb.Freeverb`; a chamber is
   not a Freeverb. If Phase 1 lands the algorithmic plate/hall the vision §6 names,
   this rack should be rebuilt on it and AS2, AS3 and AS3b re-measured — AS3b
   especially, since echo density is a property of the reverberator's own
   topology. *Settles:* the
   implementation session at Phase 6, from what Phase 1 released.
5. **Whether the send delay's bend should be borrowed rather than built.** The
   palette's bend lives in a CircuitPython-ported node that can never gain a
   filtered loop (§5's refutation record). If Gate 0 refuses N2, AS7 is withdrawn
   and this rack ships with six Tier 2 rows and a delay knob that clicks — stated
   here so the refusal is taken knowing it. *Settles:* Gate 0, with N2.
6. **Whether `AirSpace` should carry the loop's bell.** The referent has a fixed
   3.5 kHz ±6 dB bell in the feedback loop (S1 p. 12) that the node cannot do —
   confirmed this run: the loop carries one one-pole low-pass (`:231-234`) and one
   one-pole high-pass (`:236-239`) and nothing else. No trait depends on it, so no
   ask is filed; if a later dossier wants it, it arrives with its own trait id.
   *Settles:* recorded, not reopened here.

---


## Appendix

### A1. Source quotations, as read on 2026-09-06

**S1, Waves user guide, p. 4.** "The effect starts with a tape delay and feedback
loop. This is the STEED process. The signal then goes to an echo chamber, where
the reverb sound is created. The tape feedback loop serves to prolong the tail of
the chamber sound without creating a noticeable delay effect."

**S1, pp. 6–7 (Signal Flow).** "Input — Sets the plugin's input level. The input
signal is split into two paths: A direct signal is sent to output mixer. The
Chambers processing signal is sent through a buffer amplifier and then into the
system. Main path — The signal goes to the delay and tape effect processor and is
then split: one signal goes straight to the echo chamber through a set of
filters. This is the Main path. Loopback — The other path loops back through the
tape and delay processor. It can be equalized again on its way."

**S1, p. 11–12 (STEED section).** "Tape Delay Feedback — Controls the amount of
feedback signal returning to the Tape Machine processor. Values above 85 can
result in excessive feedback." Default 37.5. "There are three filters in Feedback
Loop… Since the signal can enter the loop several times on its way to the
chamber, these filters can have an accumulative effect." Top Cut "Range: flat to
3.5 kHz. Default: flat (24 dB per octave)"; Bass Cut "Range: flat to 6400 Hz.
Default: flat (12 dB per octave)"; Mid "Frequency (fixed): 3.5 kHz. Gain range:
-6 dB to +6 dB". "Drive is created in the tape section, so each time the feedback
loop passes through the tape machine it undergoes drive processing, as does the
signal passing directly to the chamber"; "The STEED section output level is
adjusted to maintain unity gain, as best as possible, when the Drive value
changes."

**S1, p. 13.** "Adjusts the delay value in much the same manner as changing the
tape speed as it moves between the record and repro heads." "Range with Sync off:
0 ms to 500 ms. Default with Sync off: 111 ms… This corresponds to the delay
introduced by the 3.3 inch gap between the record and repro heads in a BTR tape
machine playing at 30 ips." "Filters to Chamber Section — This section falls
after the Feedback section in the signal flow and is used to control the
frequency range of the signal as it enters the chamber."

**S1, p. 16.** "Wet/Dry Mix — … The direct signal is split from the input before
filtering and is sent directly to the output mixer, where it is mixed with the
output of the chamber."

**S2, Sound on Sound.** The chain, independently: "a buffer stage, a tape-delay
stage with an adjustable feedback loop, some basic EQ applied to the feedback
path, and post-delay EQ"; the RS106 and RS127 are "used to EQ the output of the
tape-delay section" before the chamber; feedback "allowed the reverb tail to be
extended significantly".

**S3, Abbey Road Studios.** "the original filters going into the chamber EMI's
RS106 hi/low pass filter and the EMI RS127 Presence EQ."

**S4, Wikipedia (CC BY-SA 4.0).** "The technique was developed at EMI/Abbey Road
Studios in the late 1950s, by EMI engineer Gwynne Stock." "The amount of feedback
could be controlled allowing multiple delays to be sent to the reverb chamber,
which could lengthen the effect's decay time."

### A2. The palette lines behind §4 and §5, read with `grep -n`

`audioif/src/shared/audioif_feedback_delay.c`:

- `:81-83` — `delay_frames` written from `delay_ms` in one clamped assignment.
- `:90` — `feedback = clampf(value, 0.0f, 0.99f)`, with the comment explaining
  that unity self-oscillates.
- `:93-99` — the `mix` convention: "0.3 is 'dry, plus 30 percent wet', 1 is 'dry
  plus all of it', and 2 is wet alone."
- `:201-202` — the dry/wet gains that implement it.
- `:205` — the per-sample loop opens here (`for (uint32_t frame = 0; …`); the
  seed said `:206`, which is its first comment line *(palette 2026-09-07)*.
- `:206-210` — the per-sample wow oscillator; `:212` is where `delay_frames` is
  read, unsmoothed, which is N2's whole case.
- `:214-228` — the clamp, the whole/fraction split and the two-neighbour linear
  interpolation.
- `:231-234` — the in-loop one-pole low-pass (`damping_hz`).
- `:236-239` — the in-loop one-pole high-pass (`cut_hz`): low-pass the state, then
  subtract it. Neither this nor `damping_hz` is a bell, which is why §4 records
  the referent's fixed 3.5 kHz mid as an element the rack does not claim.
- `:241-243` — the in-loop cubic soft clip (`loop_drive`); the call is on `:242`
  and the seed's `:241` is its guard *(palette 2026-09-07)*.

`audioif/docs/upstream-diff.md`: `:706` "`SplitterTap.reset_buffer` does
nothing"; `:709-712` neither `Splitter` nor `Dynamics` has `deinit`. All
re-checked with `grep -n` by the audit, along with `:830` for the −19.26 dB
figure AS1 cites and `audioif_splitter.h:20` for the 32 KB ring.

### A3. Probes behind §7

`audiocomponents/.venv/bin/python`, `lib/` on the path, source a bare
`synthio.Synthesizer(sample_rate=48000, channel_count=2)`:

```
AirSpace()                    latency 0   tail None
AirSpace(frequency=1000.0)    macro(2) = 1000.0, patch_index 0
  → program_change(0)         macro(2) = 4195.014186348894
AirSpace() default            macro(2) = 4199.999999999998
```

The chain literal at `rack.py:196` builds the LowPass at 4200 Hz whatever the
caller asked for; `_init_macros` then moves it (`rack.py:201`).

### A4. The licence and citation audit, 2026-09-06

An independent pass re-fetched every §2 row and every URL, re-extracted the user
guide locally, and checked every page citation in §1, §3 and A1 against the
extracted text. Corrections applied above; everything not listed was confirmed
as the seed stated it.

1. **S1's licence call was an assertion, not a reading.** The seed wrote "Waves
   product documentation, all rights reserved as read"; the 17-page PDF contains
   no copyright or rights line at all. The audit chased it to waves.com's
   Website Terms of Use, which states "Waves and its licensors retain all right,
   title, and interest in and to the Waves Offerings (including all worldwide
   intellectual property rights)" and forbids derivative works. The call is now
   *verified* all-rights-reserved rather than assumed, and the treatment —
   documentation, nothing ported — is unchanged. Every S1 quotation in §1 and A1
   is verbatim, and the page numbers check out: p. 4 (prolong the tail without a
   noticeable delay effect), p. 5 (the 30 ips head gap), p. 6–7 (the split, the
   buffer amplifier, Main path and Loopback), p. 11–12 (feedback range and
   default 37.5; the three in-loop filters and their "accumulative effect"; Mid
   fixed at 3.5 kHz, ±6 dB; Drive per pass at unity gain), p. 13 (the tape-speed
   sentence, Sync divisions, 0–500 ms, the 111 ms default and the 3.3-inch BTR
   gap), p. 16 (the dry split before filtering).
2. **S2 (*Sound on Sound*).** All three quotations verbatim, and the copyright
   line — "All contents copyright © SOS Publications Group and/or its licensors,
   1985-2026" — is on the page as the seed recorded it.
3. **S3 (Abbey Road Studios) — licence chased.** The RS106/RS127 sentence and the
   S.T.E.E.D. expansion are verbatim. The article page carries no copyright
   notice; the footer's "Terms Of Use" link resolves to
   https://www.abbeyroad.com/terms, read this run, which does: personal use only,
   holder Virgin Records Limited t/a Abbey Road Studios. The seed's "not
   permissive" was right; it is now read rather than inferred.
4. **S4 (Wikipedia).** The article exists, both quoted claims are on it, and the
   page states "Text is available under the Creative Commons Attribution-ShareAlike
   4.0 License".
5. **One page citation corrected.** AS1 cited "The direct signal is split from
   the input before filtering" as S1 p. 6. It is on p. 16 (Wet/Dry Mix); p. 6
   carries the equivalent "A direct signal is sent to output mixer…". A1 had the
   page right all along, so this was a slip in the trait row only, and AS1 now
   cites both pages.
6. **One missing source row added.** §3's Tier 1 class note rests on audioif#23;
   the issue had no row in §2. It is now S6, read this run via `gh` (state OPEN,
   title as quoted).

### A6. The palette-verification pass, 2026-09-07

Every §4/§5 claim about an audioif node re-read with `grep -n` and probed where
it was a claim about behaviour. Confirmed as the seed states them: the feedback
clamp at `audioif_feedback_delay.c:90`; the `mix` convention at `:93-99` with "2
is wet alone" on `:98` and the dry/wet gains at `:201-202`; `delay_frames` written
in one clamped assignment at `:81-83` and read unsmoothed at `:212`; the
interpolated read, the two one-poles and the soft clip at the lines A2 now gives.
Confirmed too, and load-bearing for N2: **`delay_ms` is a plain configure slot,
not a `synthio` block input** — `src/audioecho/FeedbackDelay.c:20-29` maps ten
option names straight onto the shared enum with no `synthio_block_assign_slot`
anywhere in the file, where `audiodelays.Echo` does assign one (`Echo.c:103`).
Python's finest grain on this node really is one block.

**A6.1 — `deinit` is a property of the interpreter, not of the node.** Probed by
`hasattr(cls, "deinit")` on `cmods/bin/micropython` and on
`audiocomponents/.venv/bin/python`:

```
                        MicroPython   CPython
audioroute.Splitter          no          no
audioroute.SplitterTap        -          yes
audioecho.FeedbackDelay      no          yes
audiodynamics.Dynamics       no          yes
audioconvolve.Convolver      no          yes
audiomath.Multiply           no          yes
audiofreeverb.Freeverb       yes         yes    (CircuitPython port)
```

No `MP_QSTR_deinit` in any audioif-own locals table
(`src/audioecho/FeedbackDelay.c:214-219` and the four beside it); CPython gets one
from `_AudioSample` (`src/cpython/audiocore.py:25`), which every own shim
subclasses except `Splitter` (`src/cpython/audioroute.py:64`).

**A6.2 — `SplitterTap.reset_buffer` does nothing.** Four pulls, a `reset_buffer`,
four more: the second run resumes at `[6534, 6534, 6087, …]` where the first began
at `[0, 0, 575, …]`.

**A6.3 — the dry tap is the source.** `Splitter(src, taps=2).tap(0)` is
sample-for-sample identical to the bare source over 10240 samples, and stays
identical through `audiomixer.Mixer` voice 0 at `level = 1.0`. AS1's dry path is
built on something that measurably is a wire.

**A6.4 — the delay-time move, on both delays, with static controls.** A 1 kHz
tone at amplitude 12000, `delay_ms` ramped 111 → 222 ms over 188 pulls; period by
interpolated zero crossings; "clicks" counts sample-to-sample steps above 1.05 ×
the tone's own natural maximum (1571):

```
                                  f before   f during   f after   clicks pre/during/post
audiodelays.Echo(freq_shift=True)  1000.0      888.9     1000.0        0 / 565 / 404
   same node, delay_ms held        1000.0      1000.0    1000.0        0 /   0 /   0
audioecho.FeedbackDelay            1000.0      1000.0    1000.0        0 / 178 /   0
   same node, delay_ms held        1000.0      1000.0    1000.0        0 /   0 /   0
```

The two held-still controls are the point: they must pass, and they do, so the
counts above are the move and not the measurement. `Echo` bends and clicks;
`FeedbackDelay` does not bend and clicks once a block. Neither is AS7.

### A5. The trait-critic pass, 2026-09-07

**Critic note, 2026-09-07 (trait pass).** AS3 previously carried both halves of
S1's claim in one row, with the second half resting on "a stated threshold" that
nothing stated. Splitting them lets the RT60 half stand at high confidence
today, and a search for a citable criterion for the second half found one — S7,
Abel and Huang's echo density profile, reached this run — so the half §8.3
expected to record as *unmeasured* is instead a measurement with a planted
fault. Four other rows ("approximately", "a stated dB bound", "every Tone
setting", "to within one block" with no tempo named) were closed the same way:
by naming the setting, the threshold and the window, never by loosening the
claim.

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

Class notes: the DC clause has a known owner here — the send filter is a
`synthio.Biquad` under `audiofilters.Filter`, the node audioif#23 found holding
DC at low W0 (**S6**). Whatever Gate 0 decides for the EQ family binds this rack too, and
the seed states which answer it took once Gate 0 records one. The Tone span is
clamped below Nyquist at 22.05 kHz rather than refused. `AirSpace` is not stereo
by definition; a mono source gets a mono rack.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 Waves, *Abbey Road Chambers Reverb/Delay User Guide*, 17 pp. | the whole signal flow (pp. 6–7) and the STEED controls (pp. 11–13), quoted in A1: the dry split before filtering, the loop's three filters and their accumulative effect, Drive per pass at unity gain, Delay 0–500 ms with the 111 ms head-gap default and its sync divisions, and "Filters to Chamber" *after* the feedback section | the **PDF carries no copyright line at all** (all 17 pages searched); its only ownership signal is the metadata, `/Author: Waves Audio Ltd`. The audit chased the licence to the site — https://www.waves.com/legal/website-terms-of-use, read this run: Waves "retain all right, title, and interest", derivative works forbidden. **Verified all-rights-reserved**, holder Waves Audio Ltd (A4.1), where the seed had written "all rights reserved as read". Not permissive — read as documentation, nothing ported | https://assets.wavescdn.com/pdf/plugins/abbey-road-chambers.pdf | yes, 2026-09-06 (fetched, then text-extracted locally with `pypdf` — WebFetch could not read it); re-fetched and re-extracted by the audit |
| S2 *Sound on Sound*, review of Waves Abbey Road Chambers | an independent statement of the same chain: "a buffer stage, a tape-delay stage with an adjustable feedback loop, some basic EQ applied to the feedback path, and post-delay EQ"; the RS106/RS127 filters "used to EQ the output of the tape-delay section" before the chamber; feedback "allowed the reverb tail to be extended significantly" | "All contents copyright © SOS Publications Group and/or its licensors, 1985-2026" — not permissive; read as documentation | https://www.soundonsound.com/reviews/waves-abbey-road-chambers | yes, 2026-09-06; re-fetched by the audit (A4.2) |
| S3 Abbey Road Studios, "Inside the Waves Abbey Road Chambers Plugin" | the studio's own naming of the hardware in the send path: "the original filters going into the chamber EMI's RS106 hi/low pass filter and the EMI RS127 Presence EQ"; S.T.E.E.D. expanded | the article page carries **no** copyright symbol or "all rights reserved" line of its own; the footer's "Terms Of Use" link, followed by the audit to https://www.abbeyroad.com/terms, does: the Materials are "protected by copyright and international laws" and "You may only access and use the Materials for personal use", holder Virgin Records Limited t/a Abbey Road Studios. **Verified all-rights-reserved / personal use only** (A4.3), where the seed had inferred it. Not permissive; read as documentation | https://www.abbeyroad.com/news/inside-the-waves-abbey-road-chambers-plugin-2412 | yes, 2026-09-06; re-fetched by the audit |
| S4 Wikipedia, "Send tape echo echo delay" | provenance: developed at EMI/Abbey Road in the late 1950s by EMI engineer Gwynne Stock; feedback amount controllable, "allowing multiple delays to be sent to the reverb chamber, which could lengthen the effect's decay time" | "Text is available under the Creative Commons Attribution-ShareAlike 4.0 License" as read | https://en.wikipedia.org/wiki/Send_tape_echo_echo_delay | yes, 2026-09-06; re-fetched by the audit (A4.4) |
| S5 audioif `src/shared/audioif_feedback_delay.c`, `docs/upstream-diff.md` | what the loop node can and cannot do — enumerated with line numbers in Appendix A2 | MIT (PyDevices) | in tree | in tree |
| S6 audioif#23, "Three shipped filter configurations never return to silence — Phaser defaults hold −4 LSB of DC forever" — row added by the audit, because §3's Tier 1 class note rests on this issue and had no source row | the DC-hold defect the send filter inherits from `audiofilters.Filter` + `synthio.Biquad`, and the Gate 0 decision this rack states an answer to | MIT (PyDevices) | https://github.com/PyDevices/audioif/issues/23 | yes, 2026-09-06 (audit; issue read via `gh`, state OPEN) |
| S7 J. S. Abel, P. Huang, "A Simple, Robust Measure of Reverberation Echo Density", AES 121st Convention, 2006 Oct 5–8, San Francisco — **row added by the trait-critic pass, 2026-09-07**, which reached it while looking for a citable criterion for AS3b | the normalised echo density profile: count taps outside one standard deviation in a sliding window, normalise by erfc(1/√2) = 0.3173, "the expected fraction of samples lying outside a standard deviation … for a Gaussian distribution"; a 20–30 ms window "works well"; the profile "starts near zero and increases over time to around one", and "the time at which a value of one is first attained" is "the start of the late field"; "The presence of a few prominent reflections results in a low echo density value"; "Listening tests indicate a correlation between echo density measured in this way and perceived temporal quality or texture" | the paper's own front matter, read this run: "All rights reserved. Reproduction of this paper, or any portion thereof, is not permitted without direct permission from the Journal of the Audio Engineering Society." **Verified all-rights-reserved.** Not permissive — read as a paper, the measure re-implemented from its stated definition, nothing ported (vision §5) | https://ccrma.stanford.edu/courses/318/mini-courses/rooms/mus318_Abel_Lecture/echo%20density.pdf | yes, 2026-09-07 (WebFetch returned the PDF unreadable; fetched and text-extracted locally with `pypdf`) |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| AS1 | **The dry path is untouched by Tone.** With Space and Echo at zero, a swept sine through the rack is flat within **0.1 dB** from 20 Hz to Nyquist at Tone = 800, 4200 and 16000 Hz — the ends and the shipped default of the macro's range (§6); the Tone filter is on the send only. | S1 pp. 6 and **16** (A1), both re-read this run; S2 ("post-delay EQ") | high | Any Tone-dependent tilt on the dry path — the exact defect audioif recorded for `TapeDelay` (upstream-diff.md, "`audioeffects.TapeDelay` was low-passing the dry signal": −19.26 dB at 10 kHz) | swept sine → transfer magnitude, the three Tone settings, 48 kHz and 44.1 kHz |
| AS2 | **Repeats darken cumulatively, the send filter once.** With Loop Tone at 3.5 kHz and Feedback at the default, the energy above 3.5 kHz in the k-th repeat window falls by a **constant per-pass loss, within ± 1 dB**, for k = 1…4 — a straight line in dB against k, whose intercept carries the single send-filter pass. With Feedback at zero exactly one pass is present and there is no k > 1 window to measure. | S1 p. 12 (A1: the loop filters' "accumulative effect"), re-read this run; the 3.5 kHz setting is S1's own Top Cut endpoint, same page | high | a per-pass loss varying with k by more than 1 dB; equal high-band energy in the 1st and 4th repeats; or any repeat beyond the first at Feedback 0 | impulse in, per-repeat windows, band energies above and below the loop's damping corner |
| AS3 | **The tail is lengthened.** At the default Time (111 ms) and Feedback (§6) the chain's RT60 is **at least 1.3 ×** the RT60 of the same `Reverb` child alone at the same Size, both fitted by the same decay fit; and RT60 rises monotonically over Feedback = 0, 0.3, 0.6, 0.9. | S1 p. 4 and **p. 5** (A1; p. 5 read this run — the quick start's own instruction to back the feedback off "to a point where you don't hear the delay taps, but rather a lengthening of the chamber reverb tail"); S4 | high | an RT60 no higher than the reverb alone; or an RT60 that does not move with Feedback | RT60 by the decay fit `measure_hits.py` already carries, at the four Feedback settings |
| AS3b | **The repeats do not resolve as taps.** The normalised echo density profile η(t) of the rack's impulse response (S7's measure: taps outside one standard deviation in a sliding 20 ms Hanning window, normalised by erfc(1/√2) = 0.3173) reaches **1** — S7's own "start of the late field" — no later than it does for the same `Reverb` child alone at the same Size, and after the first 300 ms never falls below one late-field standard deviation of the control's profile at any multiple of the delay time. The bound is the control's own measured spread, so no threshold is invented. | S7 (A1), read this run; S1 pp. 4–5 for what the trait is *for* | medium — S7's measure is a published, listening-test-correlated proxy for temporal texture, not a stated audibility threshold for "hearing a tap"; the rendering of the source's perceptual claim as this measure is this program's | a dip in η at multiples of the delay time — S7: "The presence of a few prominent reflections results in a low echo density value"; or η never reaching 1 where the reverb alone does | echo density profile of the rack's impulse response against the reverb child's. **Planted fault:** sum a discrete tap at the delay time into the control's response — η must dip there, or the measurement cannot see the thing AS3b is about |
| AS4 | **Drive applies once per pass, at unity gain.** At the default Drive, THD in the k-th repeat window is strictly increasing for k = 1…4, each step at least **1 dB**; and sweeping Drive from 0 to full changes broadband output RMS by no more than **3 dB**. Both figures are this program's bar: S1 states the mechanism and hedges the gain claim ("as best as possible"), so it fixes no number. | S1 p. 12 (A1: drive in the tape section, each pass, at unity gain "as best as possible"), re-read this run | medium | THD flat within 1 dB across the four repeats — drive outside the loop; or output RMS tracking Drive by more than 3 dB | harmonic spectrum per repeat window; broadband RMS across the Drive sweep |
| AS5 | **The send delay is a musical division of the transport.** With `"tempo_sync"` declared and the transport stub at 120 BPM, 1/4 measures 500 ms ± one block and 1/8 measures 250 ms ± one block; at 90 BPM, 1/8 measures 333.3 ms ± one block. With sync off the measured delay equals the Time macro in ms ± one block. A division whose value exceeds the Time range (§6: 20…500 ms) **clamps at the range end and is not refused** — Tier 1's rate/range clause, and the reason the 90 BPM case is stated at 1/8 rather than 1/4. | S1 p. 13 (A1: the Sync divisions and "the delay calculation is based on the host BPM setting"), re-read this run; roadmap D10 | high | a delay ignoring the stub's tempo while `"tempo_sync"` is declared, or vice versa; a division measuring anything but its arithmetic value; or a construction that refuses an out-of-range division instead of clamping | delay tracking from an impulse, at both tempi and both sync states |
| AS6 | **The default Time is the head gap.** With no options given, `get_macro(2)` reads **111 ms ± 1 ms** and the delay measured from an impulse agrees within one block; the docstring states why — a 3.3-inch record-to-repro gap at 30 ips. | S1 p. 13 (A1: the 111 ms default and the 3.3-inch BTR gap at 30 ips), re-read this run; arithmetic cross-check 3.3/30 = 0.110 s | high | any other default, or a default the docstring does not account for; or a measured delay that disagrees with the reported macro | read the default; measure the delay from an impulse |
| AS7 | **A Time move bends pitch, and does not click.** With a 1 kHz tone held and Time moved 111 → 222 ms over 1.0 s, the instantaneous frequency of the first repeat is **below 1 kHz throughout the move** — lengthening the line reads the tape slower — and returns to 1 kHz within one block after it; moving 222 → 111 ms puts it **above** 1 kHz throughout. The maximum sample-to-sample difference of the output during the move does not exceed the maximum in the same render with Time held, so the click half needs no invented threshold. | S1 p. 13 (A1: the tape-speed sentence), re-read this run | medium — the referent is a tape machine and the direction follows from a varispeed read | a repeat whose pitch does not move, or moves the wrong way — a crossfade implementation (§5's refutation candidate) gives no shift at all; a step rather than a continuous ramp; or a sample-to-sample maximum above the static control's | STFT / instantaneous frequency of the first repeat through the move, both directions; max &#124;x[n]−x[n−1]&#124; against the static render |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Looked for and found, 2026-09-07 (trait-critic pass).** A citable criterion
for "the repeats are not heard as taps", which the seed had left as a threshold
to be justified later (§8.3): S7. It is a measure of temporal texture with a
stated late-field criterion and a reported listening-test correlation, not an
audibility threshold for a single echo — so AS3b cites it for the measurement
and says plainly that rendering S1's perceptual sentence as this measure is this
program's step, not the paper's.

*(from §3)*

Eight rows: seven on today's palette, AS7 gated on node ask N2. `AirSpace` is
grade *design* and is gated on Tier 1 and Tier 3 alone (vision §4.1), so none of
these is required of it — they are offered above that bar, and AS3b in
particular is offered as measurable rather than as the *unmeasured* record §8.3
was prepared to settle for.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: ESP32-P4
**0.18**, ESP32-S3 **0.45**. Lean patch expected: **no** on the P4; **yes** on
the S3, where the lean patch drops the send filter's second stage and the loop's
soft clip. The parts are one `audioroute.Splitter` (a 32 KB ring), one
`audioecho.FeedbackDelay` sized for the Time range, one `audiofilters.Filter`
(one biquad), one `audiofreeverb.Freeverb`, one `audiomixer.Mixer`.

*(from §3)*

Latency: **zero samples (0.0 ms at 48 kHz)** on the dry path, and
`latency_samples` reports 0. Nothing here looks ahead: the delay, the filter and
the reverb all process the frames they pull. The 111 ms of delay is the effect,
on the send, not latency (vision §9a). Options that add latency: **none**, and
none default-on. This rack is a stompbox-safe design by construction, which is
worth stating because a "space" is the kind of effect a player expects to cost
something.

*(from §4)*

1. `audioecho.FeedbackDelay(mix=2.0)` — wet alone
   (`audioif_feedback_delay.c:98`, ":201-202") so nothing downstream can touch
   the dry — with `delay_ms` = Time, `feedback` = Feedback (the node clamps at
   0.99, `:90`), `damping_hz` = the loop's top cut (`:231-234`),
   `cut_hz` = the loop's bass cut (a one-pole high-pass: the state is low-passed
   at `:236-238` and then subtracted at `:239`), `loop_drive` = Drive (the cubic
   soft clip at `:241-243`), and a small transport wobble through the node's two
   wow options — the names are `wow_hz` and `wow_depth_ms`, not `wow`
   (`audioif_feedback_delay.h:48-49`; `src/audioecho/FeedbackDelay.c:25-26`)
   *(palette 2026-09-07)*. The per-sample interpolated read (`:212-228`) is what
   makes the wow a glide rather than a step.

*(from §4)*

2. `audiofilters.Filter` with one `synthio.Biquad` low-pass — the RS106 top cut
   into the chamber — at the Tone frequency. This is the **send** filter and it
   is deliberately *after* the delay, which is the order S1 p. 13 and S2 both
   give and the opposite of what the class does today (§7).

*(from §4)*

3. `audiofreeverb.Freeverb(roomsize=…, damp=…, mix=1.0)` — wet alone, since
   the dry is already carried by voice 0. The three are real constructor
   arguments and stay settable as attributes on both interpreters
   (`src/cpython/audiofreeverb.py:14`, `:17-19`). **`Size` and `Damp` are not
   macros**: §6's nine macros carry no chamber size and no chamber damping, so
   these are constructor options unless §6 gains two labels — the seed said
   `roomsize=Size, damp=Damp` as if they were, and that is a hole the surface has
   to close, not a palette limit *(palette 2026-09-07)*.

*(from §4)*

The loop's fixed 3.5 kHz bell (S1 p. 12) has no home on the node — the loop
carries one one-pole low-pass and one one-pole high-pass and no bell. That is
recorded as an element of the referent the rack does **not** claim, not as a node
ask: no Tier 2 trait depends on it.

*(from §4)*

Python maps macros to node options at construction and on a move; C runs the
interpolated read, the one-pole filters, the soft clip and the reverb. No tables,
so nothing ships as data. Tier **audioif**. A mono source gets a mono rack, one
lane throughout, and AS1–AS7 (AS3b included) are measured at `channel_count` 1
as well as 2.
`reset()`/`deinit()` walk each child's enumerated node list (roadmap §3), naming
the audioif-own nodes that cannot be reset or released rather than claiming they
were. `SplitterTap.reset_buffer` does nothing (`upstream-diff.md:706`; probed —
a tap pulled, reset and pulled again resumes where it was, A6.2). **Which nodes
carry a `deinit` at all depends on the interpreter** *(palette 2026-09-07,
correcting "the two audioif-own types")*: on the workspace MicroPython none of
`audioroute.Splitter`, `audioecho.FeedbackDelay`, `audiodynamics.Dynamics`,
`audioconvolve.Convolver` or `audiomath.Multiply` has one; on CPython only
`audioroute.Splitter` lacks it, the rest inheriting from `_AudioSample`
(`src/cpython/audiocore.py:25`). This rack builds a Splitter and a FeedbackDelay,
so its Tier 1 `deinit()` item is measured on both interpreters (A6.1).

*(from §5)*

- **Why that fails the trait:** the node writes `delay_frames` in one assignment
  (`audioif_feedback_delay.c:81-83`) and the per-sample read consumes it
  unsmoothed (`:212`, inside the sample loop that starts at `:205`), so a Time
  change lands whole on the next sample: no glide, therefore no pitch bend, and a
  discontinuity at every step — **measured this run**: no pitch movement at all
  through a 111 → 222 ms ramp, and 178 sample-to-sample steps above 1.05 × the
  test tone's own maximum against 0 in a held-still control (A6.4). Stepping from Python cannot help — `delay_ms` is a
  config option, not a stream input, so Python's finest grain is one block
  (~187 Hz at 48 kHz for a 256-frame block), which turns one click into a
  staircase of smaller ones. AS7 asks for a *continuous* frequency shift with no
  click; neither is reachable.

*(from §5)*

- **Sketch:** one option (`glide_ms`, default 0.0 = today's behaviour exactly, so
  a node built as today *is* today's node) and a one-pole approach of
  `delay_frames` toward its target inside the existing per-sample loop, beside the
  wow accumulation at `:206-213`. Cost: one multiply-add per sample per channel.

*(from §5)*

- **Refutation record: run 2026-09-07; the case moved rather than closing.** The
  palette *does* carry a delay-time doppler, in the node vision §6 already names —
  `audiodelays.Echo` with `freq_shift=True`, its default
  (`src/audiodelays/Echo.c:461`), which reads a fixed line at a rate of
  `max_delay_ms / delay_ms` (`:118`; `audioif_echo.c:19-28`). Held on a 1 kHz tone
  and moved 111 → 222 ms, it bends **down to 889 Hz through the move and returns
  to 1000.0 Hz after** — AS7's direction, measured. The seed should not have
  implied the palette had nothing. It is refuted as *this rack's* send delay on
  three counts: **(i)** it is not click-free — 565 sample-to-sample steps above
  1.05 × the tone's own maximum during the move and 404 after, against **0** in a
  static control of the same node, because the read index is quantised to 1/256 of
  a sample (`Echo.c:118`, `audioif_echo.c:20-22`); that also kills the composition
  of putting an `Echo` in front of a `FeedbackDelay` to borrow its bend;
  **(ii)** its feedback path is `echo * decay` and nothing else
  (`audioif_echo.c:23-24`, `:31`), so AS2's cumulative darkening and AS4's
  per-pass drive are unreachable on it; **(iii)** it is a CircuitPython port and
  never changes (vision §2.2), so it cannot grow the loop it lacks.
  `audioecho.FeedbackDelay`, measured on the same move, held **1000.0 Hz
  throughout** with 178 steps over the same threshold — about one per block —
  against 0 in its own static control. Numbers and controls: **Appendix A6.4**.
  Still open, as the seed said: whether AS7's click-free half can be had without
  its pitch-bend half — a crossfade between two read positions removes the click
  and gives no bend. AS7's own STFT separates them; the survey's node list closes
  it.

*(from §5)*

- **Ownership:** N2 serves `TapeDelay`, `AnalogDelay` and every delay whose knob a
  player turns. It is recorded here with a trait id so the Phase 0 node list has
  one; the need statement belongs in the `TapeDelay` dossier (see §8.1).
