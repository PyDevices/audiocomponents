# Effects Dossier — `ShimmerHall` (the Eno/Lanois shimmer: an octave around a reverb)

**Class:** `lib/audioeffects/rack.py` — read once, for §7, and not otherwise
consulted.
**Family / phase:** Racks, roadmap Phase 6
**Standout:** vision §4.2 leaves the racks at "—, mechanism". This seed
**proposes a referent with evidence**: the shimmer is a named studio technique
with a documented lineage — Daniel Lanois and Brian Eno running an Eventide pitch
shifter (H910/H949, later H3000) around a reverb on U2's *The Unforgettable
Fire*, described in those terms by Eventide itself (S2) and modelled in the
literature (S1). The rack follows the technique, not a product.
**Grade:** **literature**, argued up from the vision's implied *design*: one
published model with a block diagram and stated parameters (S1) plus two
independent descriptions of the topology (S2, S3) fix falsifiable traits that
*design* would leave ungated. Reservation in §8.2 — S1 is a CCRMA course report,
not a refereed paper, and the search for a refereed shimmer paper came back empty.
**Portability tier:** **audioif** — needs `audioroute` (fan-out) and `audioecho`
(the stagger, and the loop for the second character). Imports cleanly on a stock
CircuitPython board and raises a clear `ImportError` at construction.
**Status:** seed (Phase 0), written 2026-09-06; audited the same day by an
independent licence and citation pass that re-fetched every row and every URL
itself, re-extracted both PDFs locally, and re-tested the two 403s. Its
corrections are marked *(audit 2026-09-06)* below.
Trait-critic pass 2026-09-07: every Tier 2 row rewritten to state its settings,
its threshold and its window; SH3 corrected against its own source (note under
the table); S1, S2 and S3 re-reached in that run before any row resting on them
was touched.
Palette-verification pass 2026-09-07 (unit racks): every §4/§5 claim about an
audioif node re-read in `audioif/src/` with `grep -n` and, where it was a claim
about behaviour, re-probed on both interpreters — including A2's cycle, which
this run reproduced with its own numbers. N1 **stands, unrefuted by the
palette**. Corrections marked *(palette 2026-09-07)*; **Appendix A6.**

## 1. The circuit, in one paragraph

There is no circuit; there is a patch, in two documented forms that sound
different and must not be conflated. **Regenerative** — the original: the
reverb's output is shifted up an octave and fed back into the reverb's input, so
every trip round the loop lifts the tail another octave and the halo climbs as
long as the loop gain allows. Eventide names that lineage and gives the loop its
controls — "FEEDBACK determines how much delayed signal is fed back into the
input of the reverb", a "Low, Mid, and High cross-over network [that] determines
which frequencies are fed back", fourths, fifths and octaves over four octaves,
and up to a second of delay on the pitched signal (S2). Reason Studios gives it
as a routing — reverb out → splitter → pitch shifter → reverb in, both shifters
at one octave, "a little pre-delay to stagger the beginning of the reverb tail",
the in-loop LPF engaged, and the line that says the loop is only conditionally
stable: "It's a good idea to lower the fader for this channel before you hit
play!" (S3).
**Feed-forward** — the published model: the input is shifted up one and two
octaves, sent through a branch reverberator, delayed 275 ms "so that the
harmonics will fade in slightly after the input signal", then summed with the dry
into a master reverberator (S1 §IV). Both share the octave and the staggered
bloom; only the regenerative one keeps climbing. The shifter in both is a windowed
process with a quality-versus-window trade-off — S1 needed "a buffer size larger
than 1024 samples" for "a decent pitch shifted output" — which is the latency knob
of Tier 3. The controls a shimmer rack generalizes: how loud the octave sits
(Shimmer), how far the halo climbs (Rise), how late it arrives (Bloom), how big
and how dark the space is (Space, Size, Damp), and which interval is shifted.

## 2. Sources and license calls

Quotations in Appendix A1.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 J. Zhang, "'Shimmer' Audio Effect: A Harmonic Reverberator" … (App. S1) | the feed-forward block diagram and its numbers (A1): … (App. S1) | **no license or copyright statement anywhere … (App. S1) | https://ccrma.stanford.edu/~jingjiez/portfolio/echoing-harmonics/pdfs/Shimmer%20Audio%20Effect%20-%20A%20Harmonic%20Reverberator.pdf | yes, 2026-09-06 (WebFetch could not read the PDF; text extracted locally with `pypdf`); re-fetched and re-extracted by the audit (A4.1) |
| S2 Eventide, ShimmerVerb product page | the Lanois/Eno attribution and H910/H3000 lineage … (App. S2) | "Copyright © 2026 Eventide Inc. All Rights … (App. S2) | https://www.eventideaudio.com/plug-ins/shimmerverb/ | yes, 2026-09-06; re-fetched by the audit (A4.2) |
| S3 Reason Studios, "Building a Shimmer Reverb" | the regenerative recipe as a routing … (App. S3) | no notice on the article page itself … (App. S3) | https://www.reasonstudios.com/news/post/building-shimmer-reverb | yes, 2026-09-06; re-fetched by the audit |
| S4 J. S. Abel, K. J. Werner … (App. S4) | a refereed treatment of pitch manipulation inside a … (App. S4) | no copyright or licence line anywhere in the … (App. S4) | https://dafx.de/paper-archive/2015/DAFx-15_submission_72.pdf | yes, 2026-09-06 (text extracted locally); re-fetched and re-extracted by the audit (A4.4) |
| S5 audioif `src/shared/`, `docs/upstream-diff.md` | the loop node's behaviour … (App. S5) | MIT (PyDevices) | in tree | in tree |

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| SH1 (Bloom) | With **Shimmer 1.0**, Space 0.5 and a 220 Hz / 200 ms burst in, the 440 Hz band over the 500 ms following the burst carries **≥ 20 dB** more energy than the same band in the same window at Shimmer 0. The octave is confined to the wet path: at Shimmer 0 **and** Space 0 the rack's render is byte-identical to the source (Tier 1's wire clause). | S1 §IV; S2 | high | less than 20 dB of 440 Hz gain at full Shimmer; any 440 Hz energy above the source's own at Shimmer 0; or a render that is not byte-identical at Shimmer 0 / Space 0 | STFT of the burst … (App. SH1) |
| SH2 (Bloom) | The octave arrives after the dry by the Bloom setting, **± 1 block** (256 frames, 5.3 ms at 48 kHz), at Bloom = 20, 200 and 800 ms — the ends and the middle of the macro's range (§6). Onset is the first STFT frame in which the 440 Hz band exceeds its Shimmer-0 level in that frame by 10 dB. | S1 §IV (the 275 ms stagger); S3 (pre-delay) | high | an onset within one block of the dry at Bloom 800 ms; or an onset-to-setting relation that is not 1:1 within a block across the three settings | STFT band-onset times at the … (App. SH2) |
| SH3 (Bloom) | **One generation, not a climb — stated in time, not in frequency.** Every band that rises above its Shimmer-0 level does so within one block of the Bloom onset (SH2); **no band first rises later than Bloom + one block**, at any Interval setting including +24. The spectral centroid over the tail, measured from Bloom + 100 ms onward, does not increase from its first 200 ms window to its last by more than 5 %. | S1 §IV (A1), read this run: the input is … (App. SH3) | high | a band whose onset is a loop time after the others — an unintended feedback path; or a centroid rising through the tail | per-band onset times at f₀, 2f₀ … (App. SH3) |
| SH4 (Rise) | **Each pass climbs an octave:** with Rise > 0, energy appears at 2ᵏ·f₀ for successive k, each onset one loop time (the Bloom setting) after the previous, **± 1 block**, until 2ᵏ·f₀ exceeds the Damp corner or Nyquist. Counting a generation as a band reaching **≥ 20 dB above its Rise-0 level in the same window**, the count is non-decreasing across Rise = 0.3, 0.6, 0.9 at fixed Damp and strictly greater at 0.9 than at 0.3; it is stated as a function of the running rate, never as a fixed number. | S2 (A1: feedback into the reverb input … (App. SH4) | medium — read from … (App. SH4) | only one octave at any Rise; onsets not spaced by the loop time; or a generation count that does not move with Rise | STFT; energy at 2ᵏ·f₀ vs time … (App. SH4) |
| SH5 (Rise) | **The loop is bounded across the whole macro range, and runaway is reachable only as a planted fault.** At every Rise the macro can reach (0…0.95, §6) a 200 ms burst decays to **exact zero** within the reported `tail_samples`, at both ends of Damp. Growth is not reachable from the surface — the node clamps feedback to 0.99 (`audioif_feedback_delay.c:90`, `grep -n` this run) and N1's loop pitch adds no gain — so the unbounded half is demonstrated by the planted fault that removes the clamp, which must show tail RMS rising block over block. | S3 (the fader warning) … (App. SH5) | high for the bounded … (App. SH5) | a tail that never reaches exact zero at any Rise inside the range; or a clamp-removed render that still decays — which would mean the measurement cannot see runaway at all | burst-then-silence RMS trajectory … (App. SH5) |
| SH6 (Rise) | **Damping terminates the climb:** at Damp = 800 Hz the highest generation reaching SH4's floor is **at least one k lower** than at Damp = 16000 Hz — the ends of the macro's range (§6) — at the same Rise 0.6 and the same f₀ = 220 Hz. | S3 (the in-loop LPF); S2 (the crossover) … (App. SH6) | medium | the same highest k at both ends of Damp | the SH4 measurement at both Damp … (App. SH6) |

Why SH3 is stated in time rather than in frequency: **Appendix A5**.

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Bloom (default, buildable today).** `audioroute.Splitter(source, taps=2)`;
tap 0 is the dry into `audiomixer.Mixer` voice 0 at unity; tap 1 goes
`audiodelays.PitchShift(semitones=+12, mix=1.0, window=…)` →
`audioecho.FeedbackDelay(mix=2.0 — wet alone, `audioif_feedback_delay.c:98` —
delay = Bloom, damping_hz = Damp, a little feedback for the halo's own repeats)`
→ Mixer voice 1 at the Shimmer level; the Mixer feeds
`audiofreeverb.Freeverb(roomsize=Size, damp=Damp, mix=Space)`. Two things move
against today's class: the stagger sits **on the pitch branch only**, which is
what S1 §IV specifies and what keeps the dry unsmeared, and the octave branch is
built only when Shimmer > 0 or its macro is bound, so a rack that never shimmers
does not pay a `PitchShift`.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**N1 — a pitch shift inside `audioecho.FeedbackDelay`'s loop.** Additive, on an
audioif-own module, per D1; one option, defaulting off, so a `FeedbackDelay` built
as today *is* today's node.

- **Trait it unblocks:** SH4, and with it SH5 and SH6.
- **What the palette would do instead:** cascade K feed-forward octave branches
  (K shifters, K delays, K mixer voices), or accept Bloom's single generation.
- **Why that fails the trait:** SH4 asserts that generations keep arriving at the …  *(argument in full: App. R)*
- **Sketch:** `loop_semitones` (default 0.0 = off), and inside the loop after the …  *(argument in full: App. R)*
- **Refutation record: the palette was attacked on 2026-09-07 and N1 stands.** …  *(argument in full: App. R)*

No other ask: SH1–SH3 are reachable today.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Nine macros of the sixteen; patch names describe settings.

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Shimmer | UNIPOLAR | 0.0 … 1.0 | how loud the pitched copy sits (S1's branch level; S2's pitch mix) |
| 1 | Rise | UNIPOLAR | 0.0 … 0.95 (0 in *Bloom*) | S2's FEEDBACK; S3's loop fader |
| 2 | Bloom | UNIPOLAR | 20 … 800 ms, log | S1's 275 ms stagger; S3's pre-delay; S2's up-to-1 s delay |
| 3 | Interval | TOGGLE (stepped) | −12, −5, +7, +12, +24 semitones | S2's fourths, fifths and octaves over four octaves |
| 4 | Space | UNIPOLAR | 0.0 … 1.0 | reverb mix |
| 5 | Size | UNIPOLAR | 0.0 … 1.0 | reverb room size (S1: branch T60 9 s, master 5 s) |
| 6 | Damp | UNIPOLAR | 800 … 16000 Hz, log | S3's in-loop LPF; S2's crossover |
| 7 | Mix | UNIPOLAR | 0.0 … 1.0 | the rack's wet/dry |
| 8 | Output | UNIPOLAR | −24 … +12 dB | the return trim |

Characters: **Bloom** (default) and **Rise** (gated on N1). Patches:
`0 "Octave Bloom"`, `1 "Short Stagger"`, `2 "Long Stagger Dark"`,
`3 "Fifth Halo"`, `4 "Slow Rise"`, `5 "Rise Damped"`, `6 "Bloom - lean"`.
`capabilities` = `("tempo_sync",)`, and the class reads the transport for the
stagger, which is a musical interval and which S2's own delay offers synced (D10).

## 7. Defects in the current class the rebuild must not repeat

- **The docstring claims a mechanism the topology cannot produce.** `:124-131`
  says a reverb fed an octave above what went in "keeps growing upward, and that
  rising quality is what 'shimmer' actually names", but the chain at `:155-160` is
  `Octaver → TapeDelay → Reverb`: one feed-forward octave, no pitch in any
  feedback path (probed — a single `up` branch). The rebuild either builds the
  rise (N1) or says plainly that it blooms once.
- **The stagger is on the wrong side of the sum.** The `TapeDelay` sits after the
  Octaver's mixer (`:157-158`), so the dry is repeated along with the octave; both
  sources put the delay on the pitched branch alone (S1 §IV; S2).
- **The rack reaches into its child's private nodes.** `:168` drives
  `self.octave.mixer.voice[1].level`, past `Octaver`'s own surface — which does
  not exist (`pitch.py:79`), and that is the actual defect.
- **A macro is bound by index and works by coincidence.** `:175` calls
  `self.tape.set_macro(4, …)`; that means "Tone" only because `TapeDelay`'s span
  at `delay.py:133` is the same 800–16000 Hz log span. Re-cut those macros —
  Phase 5 will — and ShimmerHall's Tone silently moves something else.
- **The Echo macro is quantised twice.** `:170` → `_LoopDelay.set_mix`
  (`delay.py:98-99`) → `_core.macro_of`, which rounds onto the child's 0–127 grid.
  Probed: the rack's 128 Echo positions collapse to **52** distinct tape mix
  values, and the child's `patch_index` reads `None` from construction onward.
- **The octave branch is always paid for.** `:151-154` builds it at full level
  whatever `shimmer` asks, because a branch skipped at zero "could never come
  back" — an argument for building it *lazily*, not eagerly.
- **One patch on a preset rack** (`:147`), and **no Mix or Output** (`:142`), so
  Tier 1's wire clause is unreachable as shipped.
- **Latency and tail are wrong by construction**, inherited from `Rack`: probed
  `latency 0`, `tail None`, while the octave branch carries a window and the hall
  an unbounded tail (see `Rack.md` §7).

## 8. Open questions

1. **The scheduling collision, and it is the important one.** The racks are
   Phase 6; the palette closes and releases in Phase 1 (roadmap §5.2). N1 comes
   out of a *rack* dossier, so unless it is carried into the Phase 0 node list it
   arrives five phases after the only release that could land it, and *Rise*
   parks. **This seed asks Arthur to carry N1 into the survey's node list at
   Gate 0**, with Appendix A2 as its evidence. *Settles:* Gate 0.
2. **Is the grade right?** *Literature* rests on S1 plus S2/S3. If Arthur judges
   a course report and two vendor pages insufficient for a published model the
   grade drops to *design* — and SH1–SH6 stop being gated, which is the cost of
   that call, stated so it is taken deliberately. *Settles:* Arthur, at the survey.
3. **Should *Rise* be its own class?** Vision §10.7's rule is characters and this
   seed follows it, but the two architectures share only a name. The set of 46 is
   frozen (roadmap §3), so a split is not available inside this program.
   *Settles:* recorded, not reopened.
4. **What *Rise* does at 22.05 kHz** — how many generations remain, and whether
   SH4 should be stated in generations or in the frequency the climb terminates
   at. *Settles:* the implementation session, at the class gate.
5. **Which reverb node.** Bloom is written against `audiofreeverb.Freeverb`; S1
   uses two FDNs. If Phase 1 lands the algorithmic plate/hall the vision §6 names,
   this rack should be rebuilt on it and SH1–SH3 re-measured. *Settles:* the
   implementation session at Phase 6, from what Phase 1 released.
6. **The trait count if N1 falls.** Six Tier 2 rows stand, three per character.
   *Bloom* (SH1–SH3) is buildable on today's palette and is unconditional;
   *Rise* (SH4–SH6) is gated entirely on node ask N1. If N1 is refuted at Gate 0,
   *Rise* is withdrawn with it and the class ships with **exactly three**
   demonstrable traits — at the *literature* grade's bar of three, with no margin
   above it. That is the second cost of refusing N1, alongside §8.1's scheduling
   one, and it is stated here so the decision is taken knowing it. If a further
   row is lost after that, the grade drops to *design* and the class is gated on
   Tier 1 and Tier 3 alone. *Settles:* Gate 0, with N1.

---


## Appendix

### A1. Source quotations, as read on 2026-09-06

**S1, Zhang, §IV Implementation Scheme, verbatim.** "The input signal is first
up-shifted by one and two octaves and then sent into the branch FDN
reverberator, which simulates the reverberation of a huge space. A 275ms delay
is then applied to the output signal of the branch reverb module so that the
harmonics will fade in slightly after the input signal. The input signal of the
branch reverb and delay modules are both bypassed, so the original pitch-shifted
signals will not go through these modules. Finally, the input signal will be
mixed with its enhanced harmonics and sent into a master FDN reverberator, which
is based on the model of a medium room." And on the window: "the quality of the
pitch shifting effect based on the phase vocoder strongly depends on the audio
buffer size. Only with a buffer size larger than 1024 samples can the system
produce a decent pitch shifted output signal." §V B: "The longest delay line in
the branch FDN reverbreator is around 400ms, and it also has a 60dB decay time
of 9 seconds… all the delay lengths in the master FDN reverbreator are less than
300ms, with a 60dB decay time of 5 seconds."

**S2, Eventide ShimmerVerb.** "Unique reverb plug-in with parallel pitch shifters
on the reverb tail"; "Easily pitch with perfect fourths, fifths, and octaves";
"Four octaves of pitch shifting (from two octaves down to two octaves up)";
"FEEDBACK determines how much delayed signal is fed back into the input of the
reverb"; "Low, Mid, and High cross-over network determines which frequencies are
fed back"; "Delay pitched signals up to one second or sync them to your DAW's
tempo"; the technique was "popularized by Daniel Lanois and Brian Eno on U2's
*The Unforgettable Fire*" using "Eventide pitch shifting hardware, such as the
H910 or H3000, in combination with a reverb." And the sentence SH4 rests on,
added by the audit: "the ability to infinitely feedback the signal, resulting in
cascading reverbs that smear into oblivion."

**S3, Reason Studios.** "set both shifters to a shift of a single octave (by all
means experiment with different intervals, but an octave is your safest bet)";
"Add a little pre-delay to stagger the beginning of the reverb tail"; "it doesn't
hurt to engage the Polar's LPF – you can select the frequency to match your
material"; "It's a good idea to lower the fader for this channel before you hit
play!"

### A2. The measurement behind N1 — a graph cycle carries no signal

**Re-run 2026-09-07 by the palette pass, with its own numbers.**
`audiocomponents/.venv/bin/python`, `lib/` on the path. A one-shot 220 Hz,
50 ms burst as `audiocore.RawSample` into `Mixer` voice 0 (`loop=False`);
`Freeverb(roomsize=0.9, damp=0.2, mix=1.0)` playing the Mixer; the Freeverb
returned into Mixer voice 1 at level *L*. Block RMS of 2048-frame stereo blocks,
reverb bound to the mixer first:

```
no cycle       :  650 2865 2988 8973 4806 5884 4241 4101 3589 2534 2743 1501 2040 1309
cycle, L = 0.0 : 2865 2988 8973 4806 5884 4241 4101 3589 2534 2743 1501 2040 1309 1284
cycle, L = 0.9 : 2865 2988 8973 4806 5884 4241 4101 3589 2534 2743 1501 2040 1309 1284
```

The cycle constructs and pulls without error, and *L* has no effect whatever: the
two cyclic traces are identical block for block, and both are the acyclic one
shifted by exactly one block (`Freeverb.play(mixer)` consumes a block at
construction). Bound the other way round — voice first, then `rev.play(mixer)` —
the cyclic render is **silent**: fourteen blocks of RMS 0 at both levels.

Two corrections to the first run's account *(palette 2026-09-07)*. The earlier
trace showed the tail reaching exact zero by block 11; at `roomsize=0.9` this run
sees it still ringing at 1309 after fourteen blocks, so "reaches exact zero at the
same block" is not a claim this appendix supports and is withdrawn — the claim
that carries N1 is *L* having no effect, which both runs show. And the two
construction orders do **not** give "the same result": one gives the acyclic
trace shifted, the other gives silence. Either way no signal goes round.

A third way in, not tried before: binding the return with `loop=True`
(`mixer.voice[1].play(rev, loop=True)`) raises `RecursionError` inside
`audiomixer._source_chunk` before a single block is pulled — the pull walks
Mixer → Freeverb → Mixer → … until Python's stack ends. The palette's graph does
not carry a loop, quietly or loudly. This is why SH4 needs the loop inside a C
node.

### A3. Probes behind §7

`ShimmerHall` built at 48 kHz over a bare `synthio.Synthesizer`: octave branches
built = `['up']` only; `latency_samples` 0; `tail_samples` `None`;
`MACRO_LABELS` `('Shimmer','Echo','Space','Tone')`. Sweeping macro 1 across all
128 positions yields **52** distinct values of `tape.macro(2)`. `tape.patch_index`
reads `None` immediately after construction. Setting macro 3 to 100 gives
`rack.macro(3) == tape.macro(4) == 8462.97493163972` — the coincident span.

### A4. The licence and citation audit, 2026-09-06

An independent pass re-fetched every §2 row and every URL, re-extracted both
PDFs locally, re-tested both 403s, and re-checked every in-tree line number with
`grep -n`. Corrections applied above; everything not listed was confirmed as the
seed stated it.

1. **S1 (Zhang).** Re-fetched and re-extracted. Every A1 quotation is verbatim,
   including §IV's block description, the 275 ms stagger, the "buffer size larger
   than 1024 samples" caution and §V B's 9 s / 5 s decay times; the header line
   "MUSIC 421A: AUDIO APPLICATIONS OF THE FFT — FINAL PROJECT REPORT — SPRING
   2018" and the author's CCRMA affiliation are on p. 1. No rights line exists
   anywhere in the document, so the licence call is stated as **unverified,
   treated as copyleft** rather than merely "unverified".
2. **S2 (Eventide) — one misquote, corrected.** SH4's source column quoted the
   page as saying "infinitely cascade". That phrase is **not** on the page; what
   it says is "the ability to infinitely feedback the signal, resulting in
   cascading reverbs that smear into oblivion", and SH4 now quotes that. Every
   other S2 quotation in §1 and A1 — FEEDBACK into the reverb input, the
   Low/Mid/High crossover, "perfect fourths, fifths, and octaves", "Four octaves
   of pitch shifting", the one-second/tempo-sync delay, the Lanois/Eno and
   H910/H3000 attribution — is verbatim, as is "Copyright © 2026 Eventide Inc.
   All Rights Reserved."
3. **S3 (Reason Studios) — licence chased, not left unverified.** All four
   quotations and the routing are verbatim on the article page, which carries no
   notice of its own. Following the footer link, the site's terms
   (https://www.reasonstudios.com/agreements, read this run) state that "Any and
   all content in the Services, including text, graphics, logos, icons, pictures,
   sound files, digital downloads, object code, source code and/or other thereto
   related material are owned or licensed by Reason", holder Reason Studios
   Aktiebolag. Verified all-rights-reserved; the treatment is unchanged.
4. **S4 (Abel & Werner).** Re-fetched and re-extracted: "Proc. of the 18th Int.
   Conference on Digital Audio Effects (DAFx-15), Trondheim, Norway, Nov 30 -
   Dec 3, 2015", authors Jonathan S. Abel and Kurt James Werner, CCRMA — and it
   is a modal-reverberator architecture, so the seed's "adjacent, not the
   Eno/Lanois loop" reading is right. No licence line on any page: recorded as
   unverified, treated as copyleft.
5. **The two negatives hold.** valhalladsp.com's Eno/Lanois page still returns
   HTTP 403, and nothing from it is cited anywhere in this seed. A fresh search
   for a refereed shimmer paper surfaced only S1, the 403'd Valhalla pages and
   forum threads.
6. **In-tree line numbers, all clean** (`grep -n`):
   `audioif_feedback_delay.c:90` (feedback clamped 0…0.99), `:93-99` (the `mix`
   convention), `:201-202`, `:216-228` (the interpolated read), `:231-234` (the
   in-loop one-pole SH6 rests on), `:241` (the soft clip);
   `upstream-diff.md:706` and `:709-712`.

### A6. The palette-verification pass, 2026-09-07

Every §4/§5 claim about an audioif node re-read with `grep -n` and probed.
Confirmed as the seed states them: the feedback clamp `clampf(value, 0.0f, 0.99f)`
at `audioif_feedback_delay.c:90`; the `mix` convention at `:93-99` with "2 is wet
alone" on `:98` and the dry/wet gains at `:201-202`; the per-sample wow oscillator
at `:206-210` and the offset it feeds at `:212-213`; the interpolated read at
`:214-228`; the in-loop one-pole low-pass at `:231-234`; the cubic soft clip at
`:241-243`. `audiodelays.PitchShift(semitones=, mix=, window=, overlap=)` and
`audiofreeverb.Freeverb(roomsize=, damp=, mix=)` are the real signatures, and
`audioroute.Splitter(source, taps=2)` refuses more than four taps
(`src/audioroute/Splitter.c:34`, `:43`; `audioif_splitter.h:21`). The 32 KB ring
Tier 3 prices is `audioif_splitter.h:20` × `:29`.

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

MicroPython has no `MP_QSTR_deinit` in any audioif-own locals table
(`src/audioecho/FeedbackDelay.c:214-219` and the four beside it); CPython gets one
by inheritance from `_AudioSample` (`src/cpython/audiocore.py:25`), which every
own shim subclasses except `Splitter` (`src/cpython/audioroute.py:64`). This rack
builds a Splitter and a FeedbackDelay, so its Tier 1 `deinit()` item has a
different honest answer on each interpreter and must be measured on both.

**A6.2 — `SplitterTap.reset_buffer` does nothing.** Four pulls, a
`reset_buffer`, four more: the second run resumes at `[6534, 6534, 6087, …]`
where the first began at `[0, 0, 575, …]`.

**A6.3 — the dry tap is the source.** `Splitter(src, taps=2).tap(0)` is
sample-for-sample identical to the bare source over 10240 samples, and stays
identical through `audiomixer.Mixer` voice 0 at `level = 1.0`. SH1's "byte-
identical at Shimmer 0 and Space 0" has a working dry path to rest on, and the
splitter adds no latency.

**A6.4 — nothing in the palette shifts pitch once per feedback pass.** A 220 Hz,
80 ms burst; repeats windowed at the delay time and their period measured by
interpolated zero crossings:

```
                                        pass1   pass2   pass3   pass4
audiodelays.Echo(freq_shift=True )      220.0   220.0   220.0   220.0 Hz
audiodelays.Echo(freq_shift=False)      220.0   220.0   220.0   220.0 Hz
audioecho.FeedbackDelay(feedback=0.7)   220.0   220.0   220.0   220.0 Hz
```

`freq_shift` was the one candidate worth testing, because it is the only palette
delay whose read position moves at a rate other than one — but write and read
advance at the *same* rate (`audioif_echo.c:19-28`), so a completed pass is
pitch-neutral. SH4's climb has no palette source. With A2's three cycle results,
N1 is unrefuted.

### A5. The trait-critic pass, 2026-09-07

**Critic note, 2026-09-07 (trait pass).** SH3 previously read "no energy
appears at 4·f₀ or 8·f₀" and cited S1 §IV for it. Re-reading S1 this run
disconfirms that form from its own source: the paper's model shifts the input
up by **one and two** octaves, so 4·f₀ is present by design, and §6's Interval
macro offers +24 as well. What separates a bloom from a climb is *when* the
bands arrive, not which ones do, so SH3 is restated in time. Nothing about the
class's intent changed; the row can now fail for the right reason instead of
the wrong one.

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

Notes, not edits: the rate clause bites — the *Rise* character walks energy up by
2× per pass, so at 22.05 kHz fewer generations fit below Nyquist than at 48 kHz;
SH4 states its generation count as a function of the running rate rather than as a
fixed number. `ShimmerHall` is not stereo by definition; a mono source gets a
mono rack.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 J. Zhang, "'Shimmer' Audio Effect: A Harmonic Reverberator", CCRMA Stanford, MUSIC 421A final report, Spring 2018 | the feed-forward block diagram and its numbers (A1): octaves into a branch FDN, a 275 ms stagger, sum with dry into a master FDN; the shifter's window caution | **no license or copyright statement anywhere in the PDF** (all five pages searched, twice); self-hosted on a CCRMA personal page. **Licence unverified — treated as copyleft**: read and cited as a paper, nothing ported (vision §5) | https://ccrma.stanford.edu/~jingjiez/portfolio/echoing-harmonics/pdfs/Shimmer%20Audio%20Effect%20-%20A%20Harmonic%20Reverberator.pdf | yes, 2026-09-06 (WebFetch could not read the PDF; text extracted locally with `pypdf`); re-fetched and re-extracted by the audit (A4.1) |
| S2 Eventide, ShimmerVerb product page | the Lanois/Eno attribution and H910/H3000 lineage; the loop's controls — feedback into the reverb input, a Low/Mid/High crossover, intervals, delay or tempo sync (A1) | "Copyright © 2026 Eventide Inc. All Rights Reserved." — not permissive; read as documentation | https://www.eventideaudio.com/plug-ins/shimmerverb/ | yes, 2026-09-06; re-fetched by the audit (A4.2) |
| S3 Reason Studios, "Building a Shimmer Reverb" | the regenerative recipe as a routing, the single-octave default, the pre-delay stagger, the in-loop LPF, and the runaway warning | no notice on the article page itself; the audit followed the footer to https://www.reasonstudios.com/agreements and read the terms there — site content "owned or licensed by Reason", holder Reason Studios Aktiebolag, so **verified all-rights-reserved**, not merely unverified (A4.3). Not permissive; read as documentation | https://www.reasonstudios.com/news/post/building-shimmer-reverb | yes, 2026-09-06; re-fetched by the audit |
| S4 J. S. Abel, K. J. Werner, "Distortion and Pitch Processing Using a Modal Reverberator Architecture", Proc. DAFx-15 | a refereed treatment of pitch manipulation inside a reverberator — and its limit for us: a modal architecture, not the Eno/Lanois loop | no copyright or licence line anywhere in the PDF (all eight pages searched). **Licence unverified — treated as copyleft**; read as a paper, nothing ported | https://dafx.de/paper-archive/2015/DAFx-15_submission_72.pdf | yes, 2026-09-06 (text extracted locally); re-fetched and re-extracted by the audit (A4.4) |
| S5 audioif `src/shared/`, `docs/upstream-diff.md` | the loop node's behaviour (`audioif_feedback_delay.c:90`, `:93-99`, `:201-202`, `:212-228`, `:231-234`, `:241-243`); `SplitterTap.reset_buffer` does nothing (`upstream-diff.md:706`); `Splitter` has no `deinit` (`:709-712` — a sentence about audioroute and audiodynamics only; A6.1 measures the real exception set on each interpreter) | MIT (PyDevices) | in tree | in tree |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| SH1 (Bloom) | With **Shimmer 1.0**, Space 0.5 and a 220 Hz / 200 ms burst in, the 440 Hz band over the 500 ms following the burst carries **≥ 20 dB** more energy than the same band in the same window at Shimmer 0. The octave is confined to the wet path: at Shimmer 0 **and** Space 0 the rack's render is byte-identical to the source (Tier 1's wire clause). | S1 §IV; S2 | high | less than 20 dB of 440 Hz gain at full Shimmer; any 440 Hz energy above the source's own at Shimmer 0; or a render that is not byte-identical at Shimmer 0 / Space 0 | STFT of the burst; 440/220 Hz band ratio in the tail window, 48 and 44.1 kHz |
| SH2 (Bloom) | The octave arrives after the dry by the Bloom setting, **± 1 block** (256 frames, 5.3 ms at 48 kHz), at Bloom = 20, 200 and 800 ms — the ends and the middle of the macro's range (§6). Onset is the first STFT frame in which the 440 Hz band exceeds its Shimmer-0 level in that frame by 10 dB. | S1 §IV (the 275 ms stagger); S3 (pre-delay) | high | an onset within one block of the dry at Bloom 800 ms; or an onset-to-setting relation that is not 1:1 within a block across the three settings | STFT band-onset times at the three Bloom settings |
| SH3 (Bloom) | **One generation, not a climb — stated in time, not in frequency.** Every band that rises above its Shimmer-0 level does so within one block of the Bloom onset (SH2); **no band first rises later than Bloom + one block**, at any Interval setting including +24. The spectral centroid over the tail, measured from Bloom + 100 ms onward, does not increase from its first 200 ms window to its last by more than 5 %. | S1 §IV (A1), read this run: the input is up-shifted by **one and two** octaves into the branch FDN, feed-forward with the branch input bypassed — so 2f₀ **and** 4f₀ are both present, at the **same** onset, and nothing arrives a loop time later | high | a band whose onset is a loop time after the others — an unintended feedback path; or a centroid rising through the tail | per-band onset times at f₀, 2f₀, 4f₀, 8f₀ referenced to the burst end; centroid vs time over the tail window |
| SH4 (Rise) | **Each pass climbs an octave:** with Rise > 0, energy appears at 2ᵏ·f₀ for successive k, each onset one loop time (the Bloom setting) after the previous, **± 1 block**, until 2ᵏ·f₀ exceeds the Damp corner or Nyquist. Counting a generation as a band reaching **≥ 20 dB above its Rise-0 level in the same window**, the count is non-decreasing across Rise = 0.3, 0.6, 0.9 at fixed Damp and strictly greater at 0.9 than at 0.3; it is stated as a function of the running rate, never as a fixed number. | S2 (A1: feedback into the reverb input, "cascading reverbs that smear into oblivion"), re-read this run; S3 | medium — read from vendor descriptions, not a model | only one octave at any Rise; onsets not spaced by the loop time; or a generation count that does not move with Rise | STFT; energy at 2ᵏ·f₀ vs time, k = 1…4, three Rise settings |
| SH5 (Rise) | **The loop is bounded across the whole macro range, and runaway is reachable only as a planted fault.** At every Rise the macro can reach (0…0.95, §6) a 200 ms burst decays to **exact zero** within the reported `tail_samples`, at both ends of Damp. Growth is not reachable from the surface — the node clamps feedback to 0.99 (`audioif_feedback_delay.c:90`, `grep -n` this run) and N1's loop pitch adds no gain — so the unbounded half is demonstrated by the planted fault that removes the clamp, which must show tail RMS rising block over block. | S3 (the fader warning); S2 (a feedback control at all); the clamp read in the C source | high for the bounded half (the clamp is read, not inferred); medium for the climb tracking Rise (vendor description only) | a tail that never reaches exact zero at any Rise inside the range; or a clamp-removed render that still decays — which would mean the measurement cannot see runaway at all | burst-then-silence RMS trajectory and last-non-zero index, swept across Rise at both Damp ends; the same with the clamp removed |
| SH6 (Rise) | **Damping terminates the climb:** at Damp = 800 Hz the highest generation reaching SH4's floor is **at least one k lower** than at Damp = 16000 Hz — the ends of the macro's range (§6) — at the same Rise 0.6 and the same f₀ = 220 Hz. | S3 (the in-loop LPF); S2 (the crossover); `audioif_feedback_delay.c:231-234` | medium | the same highest k at both ends of Damp | the SH4 measurement at both Damp ends |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Looked for, not found.** *(a)* Valhalla DSP's "Eno/Lanois Shimmer Sound: How it
is made" and the *Valhalla Shimmer* notes PDF — both **HTTP 403**, recorded as
**not reached**; nothing from either is cited, including the signal-flow line that
search snippets quote. The audit re-tested the first URL: still HTTP 403
(A4.5). *(b)* A refereed paper on the shimmer topology itself:
searched dafx.de, aes.org, ccrma.stanford.edu and arxiv.org; the closest reachable
result is S4, a different architecture. The audit searched again independently
and found nothing refereed either (A4.5), so the grade reservation in §8.2
stands. *(c)* No hardware is on the bench and no
H910/H3000 service documentation was sought — the referent is a routing, not a
circuit.

*(from §3)*

Characters carry their own rows (vision §10.7). **Bloom** is S1's feed-forward
architecture and is buildable on today's palette; **Rise** is S2/S3's regenerative
one and depends on node ask N1 (§5). Bloom is the default so the class ships
whatever N1's fate, and a character that fails its rows cannot hide behind the
other.

*(from §3)*

Budget as a fraction of one stereo block's deadline: ESP32-P4 **0.25**, ESP32-S3
**0.60**. Lean patch expected: **yes** — on the S3, one octave branch at the
shortest usable window, Damp fixed, a smaller hall. Parts: one
`audioroute.Splitter` (32 KB ring), one `audiodelays.PitchShift`, one
`audiomixer.Mixer`, one `audioecho.FeedbackDelay` sized for the Bloom range, one
`audiofreeverb.Freeverb`. *Rise* replaces the shifter and the delay with one
N1-extended `FeedbackDelay` and should cost **less**, which is part of N1's case.

*(from §3)*

Latency: the **dry path is zero samples (0.0 ms at 48 kHz)** and
`latency_samples` reports 0 — nothing here looks ahead. Two wet-path delays are
the effect, not latency (vision §9a): the pitch window and the Bloom stagger. The
window is the one CPU-for-latency knob, named in the docstring in ms at 48 kHz;
the shipped default is **the shortest window that meets SH1**, chosen by
measurement because S1 warns a window under 1024 samples degrades the shift.
**The node's `window` is in bytes, not samples** (`src/audiodelays/PitchShift.c:64`
"// bytes"; frames are `window_len / 2 / channel_count`, `:167`), so S1's caution
is 4096 bytes on a stereo 16-bit stream and the node's own 1024 default is a
quarter of it — the dossier states the shipped value in both units so the two are
never confused *(palette 2026-09-07)*. No option defaults longer, and none adds
dry-path latency.

*(from §4)*

**Rise (second character).** One `audioecho.FeedbackDelay` carrying N1's in-loop
pitch option, feeding the Freeverb: input → FeedbackDelay(pitch = Interval, delay
= Bloom, feedback = Rise, damping_hz = Damp, loop_drive to bound it) → Freeverb.
The loop lives inside the C node because **the palette's graph has no loop**: a
cycle can be wired but carries no signal — measured, Appendix A2.

*(from §4)*

Python maps macros to node options at construction and on a move; C runs the
per-sample interpolated read (`:212-228` — `delay_frames` is read at `:212`, the
fraction and the two-neighbour interpolation at `:216-228`), the in-loop one-pole
(`:231-234`) and the cubic soft clip (`:241-243`, the call at `:242`). No tables,
so nothing ships as data. Tier **audioif**. A mono source gets a mono rack, and
SH1–SH6 are measured at `channel_count` 1 as well as 2. `reset()`/`deinit()` walk
each child's enumerated node list (roadmap §3) — `SplitterTap.reset_buffer` does
nothing (`upstream-diff.md:706`, probed this run, A6.2) and **which nodes carry a
`deinit` at all depends on the interpreter**: on the workspace MicroPython no
audioif-own node has one (Splitter, FeedbackDelay, Dynamics, Convolver, Multiply),
while on CPython only `audioroute.Splitter` lacks it (A6.1). The exceptions are
named per interpreter rather than claimed as released *(palette 2026-09-07,
correcting "`Splitter` has no `deinit`" read as the whole exception list)*.

*(from §5)*

- **Why that fails the trait:** SH4 asserts that generations keep arriving at the
  loop interval *while the tail decays*, and that their number moves with Rise and
  Damp. A K-branch cascade fixes the count at construction, emits all K at once
  rather than at loop intervals, gives Rise nothing to move, and costs K shifters
  where the loop costs one. The obvious alternative — closing the loop in the
  graph — does not work: **measured twice**, a cycle wired `Mixer → Freeverb →
  Mixer` constructs and pulls without error but carries no signal; block RMS at
  return level 0.0 and 0.9 is the same trace, and bound the other way round the
  cyclic render is silent (Appendix A2, re-run 2026-09-07 — which withdrew the
  first run's "reaches exact zero at the same block" and kept what carries N1).
  The palette's only real feedback loop is inside a C node.

*(from §5)*

- **Sketch:** `loop_semitones` (default 0.0 = off), and inside the loop after the
  damping filter the same windowed read `audioif_pitchshift.c` already implements
  (`audioif_pitchshift.c:13-38`, MIT), **mirrored into the own node, never a change
  to the ported one**, over the delay line itself — the line is already there. Cost: one interpolated
  read and a crossfade per sample per channel, of the order of the existing
  wow-modulated read; measured on both boards at Phase 1.

*(from §5)*

- **Refutation record: the palette was attacked on 2026-09-07 and N1 stands.**
  Three ways in, all measured (A6.4): *(a)* the graph cycle — reproduced, and it
  is worse than A2 recorded: bound with `loop=True` it raises `RecursionError`
  before a sample is pulled, and bound without it the cyclic render is the
  acyclic one shifted by one pull with the return level having **no effect at
  all** (L = 0.0 and L = 0.9 give identical block RMS). *(b)* `audiodelays.Echo`
  with `freq_shift=True` — the palette's one delay that changes pitch at all —
  does **not** shift per pass: a 220 Hz burst at `decay=0.7`, `delay_ms=200`
  gives repeats measured at 220.0, 220.0, 220.0, 220.0 Hz, and
  `audioecho.FeedbackDelay` at `feedback=0.7` gives the same four. The read and
  the write in `audioif_echo.c:19-28` advance at one rate, so a pass is pitch-
  neutral by construction. *(c)* the K-branch feed-forward cascade, refuted above
  on its own terms. What is still open is only whether SH4's *audible* content
  survives a three-branch cascade; the discriminating measurement is SH4's own.
  N1 is *proposed, palette-unrefuted*, and *Rise* is gated on it.
