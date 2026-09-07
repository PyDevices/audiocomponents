# Effects Dossier — `DynamicEQ` (no historical standout — design grade)

**Class:** `lib/audioeffects/eq.py` — the current implementation is read once,
for §7, and not otherwise consulted.
**Family / phase:** EQ, roadmap Phase 2
**Standout:** none, per vision §4.2 — **confirmed** (§2).
**Grade:** design
**Portability tier:** **audioif** (`audioroute.Splitter`,
`audiodynamics.Dynamics`), plus the stock `audiofilters.Filter` and
`audiomixer.Mixer`.
**Status:** seed (Phase 0)

## 1. The circuit, in one paragraph

A dynamic EQ is an equaliser band whose gain is driven by a detector watching
that same band, so the band moves only when something in it crosses a
threshold: it *"combines precision equalization with selective
compression/expansion and sidechain triggers, kicking in only when the signal
you're EQing goes above a certain threshold at the frequency you've
selected"*, with *"full control over width ('Q'), gain, range, threshold,
attack, and release"* per band, and it differs from a multiband compressor
because *"multiband compressors use crossover filters, which affect fairly
broad frequency areas, [while] a dynamic EQ allows you to specify the precise
frequencies"* (S6). The signal path has no nonlinearity; the only one is the
detector's gain law. The topology is the **exactly complementary split** —
band-pass at (f₀, Q) down one branch, notch at the same (f₀, Q) down the
other, process the band, sum. That split needs no trimming: RBJ's notch
numerator `(1, −2cos ω₀, 1)` and band-pass numerator `(α, 0, −α)` sum to the
shared denominator `(1+α, −2cos ω₀, 1−α)` (S1, both blocks verbatim), so
`H_notch + H_bandpass ≡ 1` for all z — Zavalishin's `H_N = 1 − H_BP1`
(S4 §4.7 p. 119). Idle, the processor is a wire; working, the composite is a
bell of exactly the detector's gain reduction, centred on f₀ and f₀/Q wide.

## 2. Sources and license calls

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** RBJ, *Cookbook formulae for audio EQ biquad filter coefficients* … (App. S1) | the notch and BPF (constant 0 dB peak) coefficient … (App. S1) | the `.txt` itself carries **no license … (App. S1) | https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* … (App. S3) | *"Q … resonance frequency divided by the resonator … (App. S3) | © J. O. Smith III / CCRMA Stanford … (App. S3) | https://ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html | 2026-09-06 |
| **S4** Zavalishin, *The Art of VA Filter Design* rev. 2.1.0 (discoDSP … (App. S4) | `H_N = 1 − H_BP1 = 1 − 2R·H_BP` (§4.7 p. 119) … (App. S4) | verbatim-copy-only … (App. S4) | https://www.discodsp.net/VAFilterDesign_2.1.0.pdf | 2026-09-06 |
| **S6** Waves, *How and When to Use Dynamic EQ* | the working definition and the per-band control set … (App. S6) | *"Copyright © 2026 Waves Audio Ltd. All … (App. S6) | https://www.waves.com/how-and-when-to-use-dynamic-eq | 2026-09-06 |
| **S7** Fontana & Karjalainen … (App. S7) | first- and second-order equalization structures whose … (App. S7) | **no copyright, licence or rights line … (App. S7) | https://www.dafx.de/paper-archive/2001/papers/fontana_a.pdf | 2026-09-06 — WebFetch reached it (HTTP 200, 118 KB) but could not read a PDF; text extracted with `pypdf` |

**Reached on the audit pass, correcting "identified but not read".** The
first run recorded the Fontana & Karjalainen paper as identified only; it is
in fact served by the DAFx archive itself, at the path its own search API
gives (`2001/papers/fontana_a.pdf`, S7 above) — the run's guessed path
`…/2001/papers/dafx01_fontana.pdf` is the one that 404s, re-checked
2026-09-06. The Aalto research-portal record was re-reached as well
(https://research.aalto.fi/en/publications/magnitude-complementary-filters-for-dynamic-equalization/
— title, authors, venue and dates confirmed; no abstract, no per-publication
licence, only a site-wide *"All content on this site: Copyright © 2026 Aalto
University's research portal, its licensors, and contributors"*). **Nothing
in §3 rests on S7**; it is carried as context, and it answers §8's third open
question, which is superseded — the paper is now reachable and readable.
Still not reached: MDPI's *All About Audio Equalization* (403, re-checked).
No AES paper on dynamic EQ specifically was surfaced by search.

**Standout confirmed.** The candidate dropped was the **dbx 902 de-esser**, a
real and well-documented dynamic band — but the vision gives it to `DeEsser`
(§4.2, *proposed*) and its distinguishing traits (a fixed high band, a
specific detector time constant) belong there. `DynamicEQ` is the general
instrument: any frequency, any width, compress or expand.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **The split is exact**: with the detector idle the processor is a wire — reconstruction within 0.05 dB from 20 Hz to 0.4·F_s, and an impulse comes out at its input peak | S1 (the two numerators sum to the … (App. T1) | high | any reconstruction error above 0.05 dB with the detector below threshold, at any f₀ in 100 Hz…10 kHz and Q in 0.5…8 | swept sine through the class with … (App. T1) |
| T2 | **The band gain follows the compressor law — above the knee, and the knee is 6 dB wide by default**: for a tone at f₀ at level L with threshold T and ratio R, the composite gain is `−(L−T)(1−1/R)` dB within 1 dB **whenever L−T ≥ 3 dB**. Inside the knee the node is quadratic — `−(1−1/R)·(L−T+3)²/12` for −3 < L−T < 3 — and exactly 0 for L−T ≤ −3. So a probe sitting *on* the threshold is predicted to read −0.56 dB at R 4, not 0; stating the hard law alone would score a correct node 0.56 dB wrong at that point | S6 for the threshold semantics **only** … (App. T2) | high | any of the **five** probe levels more than 1 dB from the law that applies at that level — hard above the knee, quadratic inside it, exactly 0 below it | steady-state sine at f₀ at L ∈ … (App. T2) |
| T3 | **Below threshold it is a wire**: a tone at f₀ at 10 dB under the threshold passes within 0.05 dB of unity | S6 (*"kicking in only when the signal … goes … (App. T3) | high | more than 0.05 dB of gain change on a tone 10 dB below threshold | the T2 sweep's lowest level |
| T4 | **Out of band is untouched while the band is working**: a tone two octaves from f₀ moves by less than 0.2 dB whether the band is idle or 19 dB down | S6 (the precise-frequency distinction from a … (App. T4) | high | more than 0.2 dB of movement out of band between the two states — i.e. audible pumping of the whole signal | a tone at f₀/8 rendered twice … (App. T4) |
| T5 | **The band gain is affine in the band-pass branch's own response — and the audible bell is far narrower than f₀/Q**: the detector reads the band-pass branch, so at a steady tone of level L the reduction applied to that branch is T2's law evaluated at `L + \|H_bp(f)\|_dB` — band gain (dB) = `−(1−1/R)·(L + \|H_bp(f)\|_dB − T)` above the knee, 0 where `L + \|H_bp(f)\|_dB ≤ T − 3`. Worked at f₀ = 3 kHz, Q 2, T = −30 dBFS, R 4, L = −10 dBFS: band gain −15.00 dB at f₀, −13.55 at 2.5 kHz, −7.41 at 1.5 kHz, −3.89 at 1 kHz, 0 below 429 Hz and above 14.6 kHz; composite output −15.00 / −4.11 / −0.36 / −0.09 dB. The **half-depth width is 608 Hz against f₀/Q = 1500 Hz** — the reduction tapers with the skirt, so the bell is 2.5× narrower than the filter that steers it | S1 for `\|H_bp\|`, T2 for the law, `audioif_dynamics.c:176` and `:196-206` for the knee and the clamp; the whole worked case re-derived in A11 | high (was medium; the affine form removes the hedge, because the detector's selectivity **is** `\|H_bp\|` and is therefore known, not something the kit must hold still) | at the worked setting, any probe in f₀/8…4f₀ whose composite gain is more than 0.5 dB from the closed form built from S1 and T2 | steady-state sine, **one frequency at a time at a fixed level** — f ∈ {1 k, 1.5 k, 2 k, 2.5 k, 3 k, 3.6 k, 4.5 k, 6 k} Hz — each composite gain compared point by point with the closed form. Never a swept sine: a sweep moves the detector while it measures |

No characters: one band, one behaviour. A second band is a second instance.

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Compose first; the topology is already right and the plumbing is not.**
`audioroute.Splitter(source, taps=2)` fans the input out; one tap goes to an
`audiofilters.Filter` in `NOTCH` mode, the other to one in `BAND_PASS` mode
at the same f₀ and Q; the band feeds `audiodynamics.Dynamics`; an
`audiomixer.Mixer` sums the two at unity. That is what `eq.py:238-256` does
and it is correct — the reconstruction measures 0.015 dB (A2). What the
rebuild changes:

- **Buffer sizes match.** Sizing the Mixer to `_core.pcm()`'s 2048 aligns it
  with the Filters and drops a per-block overhead multiplier.
- **Every parameter becomes live.** `frequency` and `Q` become `synthio` …  *(argument in full: App. R)*
- **Range** (a control S6 lists and the class lacks) is the Mixer's …  *(argument in full: App. R)*
- **Mono:** every node honours `channel_count` 1 and the Splitter's kernel
  duplicates a mono frame across its ring (`audioif_splitter.c:30-31`).

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**None.** All five Tier 2 traits are reachable on today's palette, and §4
shows how; an ask without a trait id is not an ask.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 30 Hz … min(16 kHz, 0.4·F_s), log | the band's frequency knob |
| 1 | Width | UNIPOLAR | Q 0.5 … 12, log; displayed as f₀/Q | the Q knob (S6) |
| 2 | Threshold | UNIPOLAR | −60 … 0 dBFS | the threshold knob (S6) |
| 3 | Ratio | UNIPOLAR | 1 … 20, log | the ratio knob (S6) |
| 4 | Attack | UNIPOLAR | 0.1 … 100 ms, log | the attack knob (S6) |
| 5 | Release | UNIPOLAR | 5 … 1000 ms, log | the release knob (S6) |
| 6 | Range | UNIPOLAR | 0 … 24 dB, default 24 (no limit) | the range/depth knob (S6) |
| 7 | Direction | TOGGLE | down (compress, default) / up (expand) | the compress/expand switch (S6) |
| 8 | Mix | UNIPOLAR | 0 exactly … 1; values in (0, 0.01] snap to 0 | parallel processing; also Tier 1's wire test |

Nine macros, seven under the sixteen-macro ceiling. `capabilities = ()`:
attack and release are absolute times, not beat fractions, and nothing else
here is measured in bars — the class does not read `transport()` (D10,
answered).

Patches: 0 **Wide Band** (3 kHz, Q 2, −30 dBFS, 4:1, 2 ms, 80 ms, full
range, down, mix 1 — the constructor's defaults on the grid), 1 **Boxiness
Control** (400 Hz, Q 2.5, −24 dBFS, 3:1, 10 ms, 150 ms), 2 **Harshness
Control** (3.2 kHz, Q 3, −28 dBFS, 4:1, 1 ms, 60 ms), 3 **Low End Tamer**
(80 Hz, Q 1.2, −20 dBFS, 4:1, 20 ms, 250 ms), 4 **Sibilance** (7 kHz, Q 4,
−30 dBFS, 8:1, 0.2 ms, 40 ms), 5 **Lift When Quiet** (2 kHz, Q 1.5,
−36 dBFS, 2:1, 30 ms, 300 ms, up), 6 **Wide Band - lean** (the Tier 3 escape
valve: peaking section driven from a sidechain, split not exact).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/eq.py`.

- **No surface at all, on the class with the most to expose.**
  `MACRO_LABELS = ()` (`eq.py:231`) for a processor whose reference
  description lists six per-band controls (S6).
- **Nothing is live.** `frequency`, `threshold_db`, `ratio` and `q` are …  *(argument in full: App. R)*
- **Attack and release are hard-coded** at 2 ms and 80 ms (`eq.py:248`) —
  two of the six controls S6 names, unavailable at any price.
- **No range, no make-up, no direction** — `DYN_EXPAND` is one argument away
  (`eq.py:247` passes `DYN_COMPRESS`) and is never offered.
- **The Mixer is built at a 1024-byte buffer** (`eq.py:250`) while both …  *(argument in full: App. R)*
- **`reset()` and `deinit()` reach the Mixer only** (`_core.py:366-374`, …  *(argument in full: App. R)*
- **No tail is declared** (`TAIL_SAMPLES = None`, `_core.py:141`) although …  *(argument in full: App. R)*

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Whether a low-frequency band inherits the family's DC residual.** Both
   branches are biquads, and at 60–80 Hz the family holds 1–4 LSB (A3, and
   `LowPass.md` §5). The complementary sum may cancel it or may not; nobody
   has measured a `DynamicEQ` band below 200 Hz. *Settled by:* the
   implementation session at Phase 2, and it feeds Gate 0's answer.
2. **Whether the lean patch's approximation is acceptable**, and what it
   costs on the S3. *Settled by:* the implementation session, on the Phase 1
   cost table.
3. **The Fontana & Karjalainen paper** (§2), identified but not read. It may
   have a cheaper magnitude-complementary structure than a two-branch split.
   *Settled by:* the implementation session, if a copy can be reached.
4. **Whether Range belongs on the Mixer's level or on the Dynamics' ratio.**
   Limiting reduction by ceiling the band voice is exact but changes the bell
   shape at the limit; limiting by ratio does not, but is not a hard stop.
   *Settled by:* the implementation session.
5. **What the Width macro should display**, given T5. §6 shows it as f₀/Q,
   which is the *filter's* width; the audible bell is narrower than that by a
   factor that depends on ratio and on how far the signal is over threshold —
   608 Hz against 1500 at the one setting derived so far (A11). A number on a
   panel that is 2.5× the width the user hears is a defect, not a convention.
   *Settled by:* the implementation session at Phase 2, from a sweep of the
   ratio-and-overshoot plane; if no single display is honest across it, the
   macro shows Q and the docstring carries the relationship.

---


## Appendix

Run 2026-09-06 on this machine. CPython target:
`audiocomponents/.venv/bin/python`. MicroPython: `cmods/bin/micropython`.
Probes were scratch scripts, not committed; every number is reproducible from
its description. A0 and A3 share their runs with `LowPass.md`.

### A2. The measurements this seed rests on

**T1, the exact split.** The shipped class with its compressor idle
(threshold 0 dBFS, ratio 1), f₀ 3 kHz, Q 2, swept by fixed sines:

```
     500.0 Hz  reconstruction gain  -0.010 dB
    1500.0 Hz  reconstruction gain  -0.000 dB
    3000.0 Hz  reconstruction gain  +0.000 dB
    6000.0 Hz  reconstruction gain  -0.001 dB
   12000.0 Hz  reconstruction gain  +0.000 dB
```

and an impulse of amplitude 20 000 came out at peak **20 000**. T1's planted
fault: detune one branch by 1 % and the reconstruction must break by more
than 0.05 dB near f₀ — it breaks by about 0.4 dB.

**T2 and T3, the gain law.** f₀ 3 kHz, Q 2, threshold −30 dBFS, ratio 4;
tone at f₀, composite gain after the detector settles:

```
  in  -40.77 dBFS @3 kHz ->  -0.002 dB      (T3: below threshold, a wire)
  in  -30.31 dBFS @3 kHz ->  -0.288 dB
  in  -20.77 dBFS @3 kHz ->  -6.504 dB      (law predicts -6.92)
  in  -10.31 dBFS @3 kHz -> -14.347 dB      (law predicts -14.77)
  in   -4.29 dBFS @3 kHz -> -18.861 dB      (law predicts -19.28)
```

The composite sits consistently ~0.4 dB above the pure band law because the
notch branch passes a little of the tone; the trait's 1 dB tolerance covers
it, and the *consistency* of the offset is itself checkable.

**T4, out of band.** A 300 Hz tone through the same processor (f₀ 3 kHz):

```
  300 Hz at  -30.31 dBFS ->  -0.015 dB
  300 Hz at   -4.29 dBFS ->  -0.016 dB
```

Unchanged between a level that leaves the band idle and one that would drive
it 19 dB down — the property that separates a dynamic EQ from a multiband
compressor (S6).

**The Splitter hazard, and the probe that caught it.** An impulse inside a
40 000-frame `RawSample` produced **nothing at all** through `DynamicEQ`, and
`LowPass` passed the same impulse normally. Bisecting the chain put it on the
Splitter, and the cause is `audioif_splitter.c:35-38`: a `RawSample` hands
back its entire buffer in one pull, the ring is 8192 frames
(`audioif_splitter.h:20`), and everything older than the last 8192 frames is
dragged past. Confirmed by shortening the source:

```
  RawSample of    256 frames, impulse at  50 -> DynamicEQ peak  20000
  RawSample of   8192 frames, impulse at  50 -> DynamicEQ peak  20000
  RawSample of  40000 frames, impulse at 200 -> DynamicEQ peak      0
```

This is a *harness* hazard rather than a product defect — a real pump asks
for a block at a time — but it will silently zero every Splitter-based
measurement, so the kit spec must say that probe material is delivered in
blocks. It is also a ready-made planted fault for any Splitter class: feed
the probe as one long `RawSample` and the measurement must go red.

### A3. Held DC after silence

`DynamicEQ` at its shipped defaults (3 kHz) settles to exact zero on both
interpreters. The family's low-frequency residuals and the probe design that
hid them are in `LowPass.md` A3; §8 question 1 is the open part.

### A7. Desktop cost anchor (CPython target, x86-64, ns per stereo frame)

```
  Filter 1 biquad         frames= 512    146.6 ns/frame
  FeedbackDelay comb      frames= 256    141.7 ns/frame
  DynamicEQ               frames= 128   3268.4 ns/frame
  real time per stereo frame at 48 kHz = 20833.3 ns
```

The 128-frame block is the shipped class's Mixer buffer (`eq.py:250`), and
part of the 22× is paying every per-block overhead four times as often as the
Filters need.

### A8. Latency

Impulse at frame 50 through `DynamicEQ()` on an 8192-frame source: first
non-zero output at frame **50**, peak **20 000** of 20 000;
`latency_samples` reports **0**. Agreed. `audiodynamics.Dynamics`'
`lookahead_ms` is the one option that would change this and is off by
default.

### A9. Licence and citation audit, 2026-09-06

This seed's §2 carries the corrections themselves; this is the full
re-verification record behind them. Every source row in §2 and every URL
anywhere in this seed was re-fetched by a second agent that read none of the
first run's notes. Two corrections applied in place. **S1's licence call** now
records the repository's root `LICENSE.md` (full CC BY 4.0), which the first
draft did not mention — downgraded to *licence unverified, treated as
copyleft*, because that grant is the mirror's and the chain to RBJ is unshown;
treatment unchanged. And the **Fontana & Karjalainen paper is reachable after
all**: it is now S7, fetched from the DAFx archive's own path and read with
`pypdf`. §8's third open question is answered by that and should be closed
when the seed is next edited.

Re-verified exactly as the seed states them: RBJ's notch and BPF numerator
blocks; the CCRMA Q page's *"the resonance frequency divided by the resonator
bandwidth"* under a copyright with no grant; Zavalishin's `H_N = 1 − H_BP1 =
1 − 2R·H_BP` at §4.7 p. 119, verbatim, under the front-matter grant quoted in
A0; and all four **S6** quotations — the *"combines precision equalization
with selective compression/expansion and sidechain triggers, kicking in only
when the signal you're EQing goes above a certain threshold"* definition, the
*"full control over width ('Q'), gain, range, threshold, attack, and release"*
control set, the crossover-filters distinction, and the footer *"Copyright ©
2026 Waves Audio Ltd. All rights reserved."* The three repository citations
behind §3 were re-read with `grep -n`: `audioif_dynamics.h:65` is `float
ratio` and `:69` is `float release_coef` (one of each, as claimed);
`src/cpython/audiodynamics.py:19` and `:53` are the `lookahead_ms` prose and
its default; `eq.py:250` is the `audiomixer.Mixer(voice_count=2,
**_core.pcm(1024))` line.

**Unsourced, and flagged as such:** the dbx 902's attributes above (a fixed
high band, a specific detector time constant) are stated from general
knowledge — no dbx schematic or manual was reached in either run. They carry
the scope argument only; nothing in §3 rests on them.

### A10. Second licence and citation audit, 2026-09-06 (the re-fetch pass)

**Second licence-and-citation audit, 2026-09-06** — a third pass, run
independently of the first audit, in which **every URL in this seed was
re-fetched in this run** and every licence read again at its own source. What
came back, so the calls above rest on this run and not on a prior one:

- `raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt`
  — reached; the file carries **no** occurrence of *license*, *licence*,
  *copyright*, *(c)*, *warranty* or *public domain*.
- `…/master/LICENSE.md` — reached; it is the full **Creative Commons
  Attribution 4.0 International Public License** text.
- `api.github.com/repos/shepazu/Audio-EQ-Cookbook` — reached; `license.key`
  `"other"`, `license.name` `"Other"`, `license.spdx_id` **`"NOASSERTION"`**.
- `webaudio.github.io/Audio-EQ-Cookbook/audio-eq-cookbook.html` — reached;
  the only rights language is *"Adapted from Audio-EQ-Cookbook.txt, by Robert
  Bristow-Johnson, with permission"* and *"Special thanks to Robert
  Bristow-Johnson for creating the Audio EQ Cookbook and permitting its
  adaption and use for the Web Audio API"*. The chain from the mirror to the
  author is still **not** shown, so the S1 call stands as *licence unverified,
  treated as copyleft*.
- `ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html` — reached; the
  definition is verbatim *"The quality factor (Q) of a resonator may be
  defined as the resonance frequency divided by the resonator bandwidth"*, and
  the page's only rights line is *"Copyright © 2026-08-21 by Julius O. Smith
  III, Center for Computer Research in Music and Acoustics (CCRMA), Stanford
  University"* — no licence granted, so *read as a paper* stands.
- `www.discodsp.net/VAFilterDesign_2.1.0.pdf` — reached (4.9 MB, 520 pages,
  rev. 2.1.0 of 28 October 2018); WebFetch could not read it, `pypdf` could.
  The front matter (printed p. ii) carries the whole grant, verbatim:
  *"© Vadim Zavalishin. The right is hereby granted to freely copy this
  revision of the book in software or hard-copy form, as long as the book is
  copied in its full entirety (including this copyright note) and its contents
  are not modified."* Verbatim-copy-only, no derivatives — confirmed.
- Re-checked and still not reached: `musicdsp.org`'s RBJ page (reached, but
  carries no licence text at all); `native-instruments.com`'s
  `VAFilterDesign_2.1.0.pdf` (**HTTP 404**);
  `archive.org/metadata/the-art-of-va-filter-design-rev.-2.1.2` (reached; **no
  `licenseurl` field and no `rights` field**), which is why the discoDSP
  mirror's own grant is the licence actually read.

Every Zavalishin page number cited in this seed was checked against the
extracted text, page by page.

**One correction from this pass**, applied above in T2: **S6 was cited for
"threshold/ratio semantics" and the Waves page never uses the word *ratio*.**
It was re-fetched and searched in this run: the page names *"width ('Q'),
gain, range, threshold, attack, and release"* and nothing else, so S6 carries
the threshold half of T2 and the node's own header carries the ratio. §1's
long quote is verbatim and complete on the page — *"Whereas regular EQ is
applied to the sound from start to finish, dynamic EQ combines precision
equalization with selective compression/expansion and sidechain triggers,
kicking in only when the signal you're EQing goes above a certain threshold at
the frequency you've selected"* — as is the multiband-compressor distinction,
and the foot of the page reads *"Copyright © 2026 Waves Audio Ltd. All rights
reserved."* **S7 re-verified independently and stands**:
`www.dafx.de/paper-archive/2001/papers/fontana_a.pdf` was reached in this run
(HTTP 200, 118 KB, five pages, footers DAFX-1…DAFX-5) and read with `pypdf` —
PDF metadata title *Magnitude-Complementary Filters For Dynamic Equalization*,
authors *Federico Fontana, Matti Karjalainen*, header *Proceedings of the COST
G-6 Conference on Digital Audio Effects (DAFX-01), Limerick, Ireland, December
6-8, 2001*. All 20 259 extracted characters were searched for *licen*,
*copyright*, *(c)*, *©*, *warrant*, *public domain* and *rights*: **not one
occurrence**, so *licence unverified — treated as copyleft* is the correct
call. The Aalto portal record was reached again and confirms title, authors,
venue and year, with only the site-wide *"All content on this site: Copyright
© 2026 Aalto University's research portal, its licensors, and contributors.
All rights are reserved…"*. MDPI's *All About Audio Equalization*
(`mdpi.com/2076-3417/6/5/129`) was re-checked and is still **HTTP 403** — not
reached. Zavalishin §4.7 p. 119 was opened in the extracted text and carries
`H_N(s) = 1 − H_BP1(s) = 1 − 2R·H_BP(s)` exactly as cited. T1 was re-derived
from S1's own coefficients: notch plus band-pass sums to 1.000000 at 20 Hz,
100 Hz, 1 kHz, 5 kHz and 19 kHz.

**One thing this pass could not fix, because §8 is out of its scope:** §8's
third open question ("the Fontana & Karjalainen paper, identified but not
read") is **stale** — the paper is reached and read, and §2 already says so.
Station A should close it.

### A11. Trait-critic pass, 2026-09-06 — the composite-bell derivation

Arithmetic on S1's coefficients and the node's own gain law
(`audioif_dynamics.c:196-206`, `knee_db = 6.0f` at `:31`), in float64
(`audiocomponents/.venv/bin/python`, numpy 2.5.2). Not a render — it is the
prediction the render has to match.

Setting: f₀ = 3 kHz, Q 2, T = −30 dBFS, R 4, steady tone at L = −10 dBFS,
48 kHz. Band gain is the node's law at `L + |H_bp(f)|`; composite is
`|H_notch(f) + 10^(g/20)·H_bp(f)|`.

| f | \|H_bp(f)\| | band gain | composite |
|---|---|---|---|
| 1000 Hz | −14.811 dB | −3.892 dB | −0.086 dB |
| 1500 Hz | −10.127 | −7.405 | −0.360 |
| 2000 Hz | −5.892 | −10.581 | −1.163 |
| 2500 Hz | −1.936 | −13.548 | −4.112 |
| 3000 Hz | 0.000 | −15.000 | −15.000 |
| 3600 Hz | −1.967 | −13.525 | −4.062 |
| 4500 Hz | −6.045 | −10.466 | −1.114 |
| 6000 Hz | −10.518 | −7.111 | −0.322 |

The band gain column is exactly `−0.75·(L + |H_bp| − T)` at every row here,
because every one is above the knee; it reaches 0 where `|H_bp| = −23 dB`,
which is 429 Hz and 14 569 Hz.

**Widths, which is what refutes the old T5.** Depth at f₀ is −15.000 dB.
Half-depth (−7.500 dB) crossings: **2710.6 and 3318.3 Hz — 608 Hz apart**.
−3 dB absolute crossings: 2382.4 and 3766.7 Hz — 1384 Hz apart. The
band-pass's own −3 dB edges are 2342.3 and 3842.3 Hz — 1500 Hz apart, i.e.
f₀/Q. The old row asserted the third pair; the class produces the first. The
−3 dB-absolute pair lands near f₀/Q only because the depth happens to be
15 dB at this setting, and moves away as soon as ratio or level does.


### A12. Palette verification pass, 2026-09-07

Every §4/§5 claim about what an audioif node can and cannot do re-measured
independently. CPython target `audiocomponents/.venv/bin/python`, running the
same `src/shared` C the boards do. Probes were scratch scripts, not committed.

**The split reconstructs.** `DynamicEQ(frequency=3000, q=2)` with the
compressor idle (probe at −44 dBFS against a −6 dB threshold), source pumped
in 512-frame blocks, gain per probe:

```
   100 Hz  +0.0021 dB     1500 Hz  -0.0049 dB     6000 Hz  -0.0129 dB
   500 Hz  -0.0048 dB     3000 Hz  +0.0019 dB    12000 Hz  +0.0000 dB
```

Worst **0.013 dB** from unity — §4's 0.015 dB stands.

**The Splitter hazard is real and reproduces on demand.** An impulse at frame
0, `DynamicEQ` on the front, peak |y| over the first 3000 frames:

```
  4096-frame RawSample  (fits the 8192-frame ring)   peak 20000
  40000-frame RawSample (one get_buffer, one write)  peak     0   <-- lost
  the same 40000 frames pumped in 512-frame blocks   peak 20000
```

`audioif_splitter.c:35-38` drags an unread tap's cursor forward when the write
laps it, so the whole impulse is dropped and the class measures as silence.
§4's warning is confirmed and it belongs in the kit spec, not only here.

**`gain_reduction_db()` already exists.** `DYN_COMPRESS`, threshold −20 dBFS,
ratio 4, attack 2 ms, release 80 ms, full-scale 440 Hz tone:

```
  block 0  -9.570 dB    block 3  -11.270 dB
  block 1 -10.639 dB    block 4  -11.319 dB
  block 2 -11.078 dB    after set(threshold_db=-40, ratio=8): -30.939 dB
```

`audioif/src/audiodynamics/Dynamics.c:144-149` and `:208-209` expose it on
MicroPython, `audioif/src/cpython/audiodynamics.py:103-105` on CPython, and
`audioif_dynamics.h:86` is the field. `DYN_EXPAND` constructs on the same node.
§5's first "considered and not asked" is corrected accordingly: nothing was
missing.

**`audioif_splitter.h:21` caps taps at 4** — read, confirmed, and the mono
duplication §4 cites is `audioif_splitter.c:30-31`, also confirmed.

**No node ask survives or arises here.** §5's "None" stands, on firmer ground
than it was written on.

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

This is the only class in the unit that builds **four** nodes plus a splitter,
so `reset()` and `deinit()` are the invariants with teeth: today's `_core`
reaches the output `Mixer` alone (`_core.py:366-374`, `:376-385`), and
`audioroute.SplitterTap` deliberately does nothing on reset (its own comment:
rewinding one branch would desynchronise the rest), so the rebuild must
enumerate the Splitter, both Filters, the Dynamics and the Mixer and walk
that list. The residual measurement (A3) shows the class at its shipped
defaults reaching exact zero, so audioif#23 does not touch it — but a
low-frequency band would inherit the family's residual through its two
biquads, which §8 leaves open.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** RBJ, *Cookbook formulae for audio EQ biquad filter coefficients* (plain text, shepazu mirror) | the notch and BPF (constant 0 dB peak) coefficient blocks, from which the complementary identity follows; `α = sin(w0)/(2Q)` | the `.txt` itself carries **no license, copyright or warranty line** (re-verified 2026-09-06, all five terms searched) — but the repository serving it does: its root `LICENSE.md` is the full **CC BY 4.0** text (read at https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/LICENSE.md; GitHub's own licence API reports the repo as `NOASSERTION`). That is the *mirror's* grant, not RBJ's: the mirror's HTML rendering says only *"Adapted from Audio-EQ-Cookbook.txt, by Robert Bristow-Johnson, with permission"*, so the chain to the author is **not** shown (sources module: a repackager's label is an assertion). **License unverified — treated as copyleft:** read as a document for its mathematics, never ported | https://raw.githubusercontent.com/shepazu/Audio-EQ-Cookbook/master/Audio-EQ-Cookbook.txt | 2026-09-06 |
| **S3** J. O. Smith III, *Introduction to Digital Filters* — "Quality Factor (Q)" | *"Q … resonance frequency divided by the resonator bandwidth"* | © J. O. Smith III / CCRMA Stanford; no license granted. Read as a paper | https://ccrma.stanford.edu/~jos/filters/Quality_Factor_Q.html | 2026-09-06 |
| **S4** Zavalishin, *The Art of VA Filter Design* rev. 2.1.0 (discoDSP mirror, text via `pypdf`) | `H_N = 1 − H_BP1 = 1 − 2R·H_BP` (§4.7 p. 119) — the complementary identity in the analog domain | verbatim-copy-only, no derivatives (grant quoted in A0). Read as a paper | https://www.discodsp.net/VAFilterDesign_2.1.0.pdf | 2026-09-06 |
| **S6** Waves, *How and When to Use Dynamic EQ* | the working definition and the per-band control set quoted in §1; the distinction from a multiband compressor | *"Copyright © 2026 Waves Audio Ltd. All rights reserved."* Trade documentation, read for terminology only | https://www.waves.com/how-and-when-to-use-dynamic-eq | 2026-09-06 |
| **S7** Fontana & Karjalainen, *Magnitude-Complementary Filters for Dynamic Equalization*, Proc. COST G-6 Conf. on Digital Audio Effects (DAFx-01), Limerick, 6–8 Dec 2001, DAFX-1…5 | first- and second-order equalization structures whose gain and selectivity parameters are mapped so the gain can be varied dynamically and stay magnitude-complementary; **context only** | **no copyright, licence or rights line anywhere in the PDF** (all five terms searched across all five pages); licence unverified — treated as copyleft: read as a paper, never ported | https://www.dafx.de/paper-archive/2001/papers/fontana_a.pdf | 2026-09-06 — WebFetch reached it (HTTP 200, 118 KB) but could not read a PDF; text extracted with `pypdf` |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **The split is exact**: with the detector idle the processor is a wire — reconstruction within 0.05 dB from 20 Hz to 0.4·F_s, and an impulse comes out at its input peak | S1 (the two numerators sum to the denominator), derived analytically; S4 §4.7 p. 119; measured to 0.015 dB and impulse peak 20 000 → 20 000 (A2) | high | any reconstruction error above 0.05 dB with the detector below threshold, at any f₀ in 100 Hz…10 kHz and Q in 0.5…8 | swept sine through the class with threshold at 0 dBFS; response differenced against a wire; plus an impulse peak comparison |
| T2 | **The band gain follows the compressor law — above the knee, and the knee is 6 dB wide by default**: for a tone at f₀ at level L with threshold T and ratio R, the composite gain is `−(L−T)(1−1/R)` dB within 1 dB **whenever L−T ≥ 3 dB**. Inside the knee the node is quadratic — `−(1−1/R)·(L−T+3)²/12` for −3 < L−T < 3 — and exactly 0 for L−T ≤ −3. So a probe sitting *on* the threshold is predicted to read −0.56 dB at R 4, not 0; stating the hard law alone would score a correct node 0.56 dB wrong at that point | S6 for the threshold semantics **only** — the word *ratio* appears nowhere on that page (re-fetched and searched, 2026-09-06); the ratio, the knee and its shape are the node's: `audioif_dynamics.h:65` (`float ratio`), `:66` (`float knee_db`), `:69` (`float release_coef`), with `knee_db = 6.0f` set at `audioif_dynamics.c:31`, `over = env_db − threshold_db` at `:176` and the three-branch law at `:196-206`; measured −6.50 / −14.35 / −18.86 dB against a predicted −6.92 / −14.77 / −19.28 at T = −30 dBFS, R = 4 (A2) | high | any of the **five** probe levels more than 1 dB from the law that applies at that level — hard above the knee, quadratic inside it, exactly 0 below it | steady-state sine at f₀ at L ∈ {−41, −30, −21, −10, −4} dBFS, gain read after the detector settles; L = −30 sits exactly on the threshold and is the knee probe |
| T3 | **Below threshold it is a wire**: a tone at f₀ at 10 dB under the threshold passes within 0.05 dB of unity | S6 (*"kicking in only when the signal … goes above a certain threshold"*); measured −0.002 dB (A2) | high | more than 0.05 dB of gain change on a tone 10 dB below threshold | the T2 sweep's lowest level |
| T4 | **Out of band is untouched while the band is working**: a tone two octaves from f₀ moves by less than 0.2 dB whether the band is idle or 19 dB down | S6 (the precise-frequency distinction from a multiband compressor); measured −0.015 dB at 300 Hz with f₀ = 3 kHz, identical at −30 and −4 dBFS (A2) | high | more than 0.2 dB of movement out of band between the two states — i.e. audible pumping of the whole signal | a tone at f₀/8 rendered twice, once with a co-existing f₀ tone below threshold and once well above |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Independent licence and citation audit, 2026-09-06** (a second agent, none
of the first run's notes read; full record in Appendix A9). Two corrections
are applied above. **S1's licence call** now records the root `LICENSE.md`
(full CC BY 4.0) the serving repository carries — downgraded to *licence
unverified, treated as copyleft* because that grant is the mirror's and the
chain to RBJ is unshown; treatment unchanged. And the **Fontana &
Karjalainen paper is reachable after all** — it is now S7, fetched from the
DAFx archive's own path and read with `pypdf`; §8's third open question is
answered by it and should be closed when the seed is next edited. The dbx
902's attributes are **unsourced** general knowledge — no dbx schematic or
manual was reached; nothing in §3 rests on them.

*(from §2)*

**Second licence-and-citation audit, 2026-09-06** (a third pass, independent
of the first audit; **every URL in this seed re-fetched in this run**). S1,
S3, S4, S6 and S7 are all re-confirmed at their own sources, and **S7 was reached
and read again in this run** — `dafx.de/paper-archive/2001/papers/fontana_a.pdf`,
HTTP 200, five pages, PDF metadata naming Fontana and Karjalainen, and not one
occurrence of *licen*, *copyright*, *©*, *warrant*, *public domain* or
*rights* in its 20 259 extracted characters. **One correction, applied above
in T2:** S6 was cited for "threshold/ratio semantics" and the Waves page never
uses the word *ratio*; the ratio is the node's. Full record in `A10`.

*(from §3)*

**Trait-critic pass, 2026-09-06.** T2 and T5 rewritten in place. T5 was the
serious one: it claimed the composite bell's −3 dB points sit at the
band-pass's `f₀·(√(1+1/4Q²) ∓ 1/2Q)` edges, and the arithmetic of the class's
own topology refutes that — at the worked setting the half-depth width is
**608 Hz where f₀/Q is 1500**. Its measurement was unrunnable as written too
(*"a swept sine at a level that holds the detector at a constant gain
reduction"* — with the detector fed from the band branch, no level does that),
so the row now states the mechanism that governs the shape and is measured with
steady tones one frequency at a time. T2 gained the node's 6 dB soft knee
(`audioif_dynamics.c:31`, `:196-206`), without which a correct node reads
0.56 dB wrong at the threshold probe the row already lists; its "four measured
levels" is corrected to the five it names. T1, T3, T4 unchanged. Worked case in
A11. **Five Tier 2 rows after the pass.**

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: **ESP32-P4
≤ 8 %, ESP32-S3 ≤ 25 %**. Lean patch expected: **yes** — a `" - lean"` patch
dropping the notch branch and driving a `PEAKING_EQ` section's `A` from the
detector (one Filter, one Dynamics as sidechain only) is the escape valve if
the S3 misses; it costs T1's exactness, which is why it is a patch and not
the default. This is the unit's most expensive class by a wide margin:
desktop anchor **3 268 ns per stereo frame** against 20 833 ns of real time,
against 147 ns for a single `Filter` (A7) — 22×. Part is the topology, part
is the shipped Mixer's 1024-byte buffer (`eq.py:250`) making the chain a
128-frame graph; §4 fixes the second half.

*(from §3)*

**Latency: zero** — impulse at frame 50 in, frame 50 out, full 20 000 peak
(A8); `latency_samples` reports **0**. **One option adds latency and it
defaults off**: `audiodynamics.Dynamics`' `lookahead_ms`
(`src/cpython/audiodynamics.py:19`, `:53`) holds the audio back while the
detector reads ahead. Off by default; if §6 exposes it at all its span starts
at 0 and stops at 5 ms, is reported in `latency_samples` the moment it is
non-zero, and is named in the docstring in ms at 48 kHz (vision §9a).
`tail_samples` is the pole pair's ring `ceil(4·Q·F_s/f₀)` plus the release.

*(from §4)*

- **Every parameter becomes live.** `frequency` and `Q` become `synthio`
  block slots on both biquads — one `synthio.Math` shared by the pair, so the
  branches can never drift out of complement; threshold, ratio, attack and
  release go through `Dynamics.set()`, which already takes them live —
  measured, one `set(threshold_db=…, ratio=…, attack_ms=…, release_ms=…)` call
  moves the reported gain reduction on the next block (A12).

*(from §4)*

- **Range** (a control S6 lists and the class lacks) is the Mixer's
  band-voice ceiling combined with the ratio, computed in Python on a macro
  move. **Expansion** is one constructor argument: `DYN_EXPAND` is on the
  same node.

*(from §4)*

**Portability tier: audioif.** `audioroute` and `audiodynamics` are both
audioif's own (`upstream-diff.md:661`), so on a stock CircuitPython board the
class imports cleanly and raises a clear `ImportError` at construction, in
`CabinetSim`'s shape (`drive.py:30-33`, `:331-334`), leaving the other
`eq.py` classes importable.

*(from §4)*

**One palette hazard the rebuild must document.** `audioif_splitter.c:35-38`
drags an unread tap's cursor forward when the writer laps it, so an upstream
that hands back more than the ring's 8192 frames in one `get_buffer` call
loses everything but the last 8192. A real pump never trips it; a `RawSample`
trips it immediately, and an impulse inside a 40 000-frame one vanished
entirely (A2). **The kit's probe material must be delivered in blocks**, or
every Splitter-based class measures as silence and looks broken.

*(from §5)*

Two things were considered and are *not* asks. A **gain-reduction read-out**
on `audiodynamics.Dynamics` would let the class drive a `PEAKING_EQ`
section's `A` directly — the textbook "moving bell" architecture — instead of
splitting and summing. **It is already on the node**: `gain_reduction_db()`
exists on both targets (`audioif/src/audiodynamics/Dynamics.c:144-149`,
`:208-209`; `audioif/src/cpython/audiodynamics.py:103-105`) and reads live —
measured 2026-09-07, a −20 dBFS-threshold 4:1 compressor on a full-scale
440 Hz tone reads −9.57 dB after one block and settles to −11.32 dB by the
fifth, and −30.94 dB after a live `set(threshold_db=-40, ratio=8)` (A12). So
there was never a node ask here, only an architecture choice, and this seed
keeps the split-and-sum for the reason it gave: the split is already exact
(T1, measured 0.015 dB; independently 0.013 dB, A12). The moving-bell
alternative is available to the lean patch at no node cost, and the seed
records it as such rather than as something the palette lacks. A **fifth
Splitter tap** would let one instance carry more than three bands; it is not
asked for because a second band is a second instance, and
`audioif_splitter.h:21` caps taps at 4 for a reason the class does not need to
fight.

*(from §7)*

- **Nothing is live.** `frequency`, `threshold_db`, `ratio` and `q` are
  constructor arguments only (`eq.py:235-236`); the two biquads take bare
  floats (`eq.py:240`, `:243`) rather than blocks, so the band cannot be
  moved at all after construction, and there is no setter for any of them.

*(from §7)*

- **The Mixer is built at a 1024-byte buffer** (`eq.py:250`) while both
  Filters use `_core.pcm()`'s 2048 (`_core.py:64`), so the class's block is
  128 frames and every per-block overhead is paid four times as often.
  Measured 3 268 ns per stereo frame, 22× a single `Filter` (A7).

*(from §7)*

- **`reset()` and `deinit()` reach the Mixer only** (`_core.py:366-374`,
  `:376-385`). The Splitter, both Filters and the Dynamics are neither reset
  nor deinitialised — the vision's planted fault "an intermediate node left
  live" is this class's, exactly.

*(from §7)*

- **No tail is declared** (`TAIL_SAMPLES = None`, `_core.py:141`) although
  the class holds two resonators and a release envelope; `latency_samples` 0
  is right and measured right (A8).
