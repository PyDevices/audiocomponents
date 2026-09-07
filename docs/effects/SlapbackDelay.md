# Effects Dossier — `SlapbackDelay` (the Sun Studio tape slap)

**Class:** `lib/audioeffects/delay.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Time, roadmap Phase 5
**Standout:** the Sun Studio tape slap — Sam Phillips' two-Ampex-350 echo on
the 1955 Elvis Presley Sun sides, per vision §4.2 — **confirmed**, and the
confirmation moves the class's default time (§2).
**Grade:** literature. There is no schematic to read: the "circuit" is two
tape machines and a patch cord. The oracle is a peer-reviewed measurement of
the finished records (S1) plus the machine's published specification (S2).
**Portability tier:** needs audioif-own nodes (`audioecho`) — same wire
measurement as `DigitalDelay` §4, restated in §4 below.
**Status:** seed (Phase 0)

## 1. The circuit, in one paragraph

Two Ampex 350 recorders. S1 says exactly one thing about the rig — "He created
a tape echo by using two Ampex 350 tape recorders" — so the rest of this
sentence is the textbook two-machine tape echo: one machine records the take,
a second takes the console feed at its record head and returns it from its
playback head a fixed distance downstream, mixed back into the console once.
Its premise *is* sourced — the 350 has "independent record and playback systems
[that] allow the tape to be monitored while recording" (S6) — but **no reached
source describes Sam Phillips' actual patching**, and that part stays
unsourced. The delay is head spacing divided by tape speed; S2 lists 3¾, 7½
and 15 ips for the model, while S6 calls the 350 "a two-speed audio recorder",
so a given unit carried two of the three — corroborated for the successor
model by Ampex's own 351 manual, which specifies "tape speed pairs of 3 3/4 inches
per second (ips) and 7 1/2 ips or 7 1/2 and 15 ips" (S7). Which pair a 350
carried is §8.1's open question. There is exactly one repeat, and that is
measured, not assumed: Halmrast's cepstrum and autocorrelation of *Baby Let's
Play House* and *Tryin' to Get to You* find "a single tape echo in mono with a
time delay of 134 - 137 milliseconds" (S1). There is no LFO, no filter and no
panel: the "controls" are the return level on the console and the transport
speed. The colour is one pass through record electronics, oxide and playback
electronics — the 350 is specified 30 Hz–15 kHz at 15 ips, 60 dB S/N
full-track, wow and flutter below 0.15 % RMS at 15 ips and 0.2 % at 7½ (S2) —
plus whatever the return level pushed into the record amplifier, which trade
writing describes as "gloriously saturated" (S3). And it is **mono**: the echo
arrives from the same place as the dry, which is the whole reason it reads as
intimate rather than as an open-air slap. S1's own listening test found that
the same 134–137 ms repeat hard-panned to the other channel "makes the whole
'room' disappear".

## 2. Sources and license calls

Reached on 2026-09-06; nothing from memory. Quotes in Appendix A2.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Tor Halmrast, "Sam Phillips' Slap Back Echo … (App. S1) | 134–137 ms measured by power cepstrum and … (App. S1) | No licence line anywhere in the PDF's … (App. S1) | <https://www.arpjournal.com/asarpwp/wp-content/uploads/2021/12/Tor-Halmrast_ARP2019.pdf> | yes |
| **S2** Reel-Reel.com, Ampex 350 entry | tape speeds "3 3/4, 7 1/2, 15" … (App. S2) | "Copyright © 2023 Reel-Reel.com - All Rights … (App. S2) | <https://reel-reel.com/tape-recorder/ampex-350/> | yes |
| **S3** *Premier Guitar*, Bryan Clark … (App. S3) | "the gloriously saturated 'slapback' delay echo from … (App. S3) | no copyright line or `©` anywhere in the … (App. S3) | <https://www.premierguitar.com/diy/recording-dojo/capturing-the-shine-of-sun-records> | yes |
| **S4** Smith & Lee, *Time Varying Delay Effects*, CCRMA RealSimple, 2008 | "zipper noise" as the artefact of an uninterpolated … (App. S4) | no copyright, `©` or licence string anywhere … (App. S4) | <https://ccrma.stanford.edu/realsimple/DelayVar/DelayVar.pdf> | yes |
| **S5** *Journal on the Art of Record Production*, Contribute page | the source for calling S1 peer-reviewed: "JARP … (App. S5) | states copyright stays with the submitting … (App. S5) | <https://www.arpjournal.com/asarpwp/contribute/> | yes |
| **S6** HistoryOfRecording.com, Ampex 350 page | "a **two-speed** audio recorder designed for use with … (App. S6) | no site licence statement … (App. S6) | <https://www.historyofrecording.com/ampex350.html> | yes |
| **S7** Ampex *Model 351* manual, Oct 1959 (88 pp., text via `pypdf`) … (App. S7) | "tape speed pairs of 3 3/4 inches per second (ips) and … (App. S7) | host asserts "fair use ... for scholarship … (App. S7) | <https://www.worldradiohistory.com/Archive-Catalogs/Ampex/Ampex-351-Manual-1959.pdf> | yes |

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
| T1 | **One repeat at 134–137 ms, and no second one.** The default patch (Repeats 0) puts the class's measured delay in 130–140 ms, and the power cepstrum of its output has one peak there with nothing above −40 dB re that peak at 2×, 3× or 4× it. **Control that must fail:** at Repeats 0.35 the 2× peak appears above −20 dB re the first. | S1 | high — a … (App. T1) | a default delay outside 130–140 ms; any energy at 2×, 3× or 4× the delay above −40 dB re the first repeat at the default patch; **or** the control not moving — no 2× peak above −20 dB at Repeats 0.35 | click through at `mix = 2` … (App. T1) |
| T2 | **The repeat makes a comb whose teeth are 1/*T*, across the whole band.** At any Time setting the magnitude spectrum's notch spacing is 1/*T* within 0.5 %, fitted over 200 Hz–2 kHz and again over 8–10 kHz, and the two fits agree within 0.5 %. At S1's measured 137 ms that is 7.30 Hz; at the class's own 135 ms default it is 7.41 Hz. | S1, which measures the spacing twice at its … (App. T2) | high | notch spacing more than 0.5 % from 1/*T* at either fit; or the two fits disagreeing by more than 0.5 %, i.e. a spacing that changes with frequency | magnitude spectrum of the class's … (App. T2) |
| T3 | **The repeat is mono and shares the dry's position.** On a probe identical in both channels the wet component is identical in both channels: L−R stays below −90 dBFS at every patch and at every macro extreme, Wow included. Nothing in the class pans, spreads or Haas-shifts the repeat, and no macro can. | S1 — "this is a single tape echo in mono" … (App. T3) | high for the record … (App. T3) | L−R above −90 dBFS at any patch or macro extreme, Wow at maximum included; **or** the class carrying a width, spread or per-channel-time macro at all | L−R RMS of the class's output on … (App. T3) |
| T4 | **The repeat is band-limited, but only slightly — a slap is not a dark effect.** Measured as a ratio against the class's own Tone-out response at the same Time and rate: at Tone 15 kHz the repeat is within 3 dB of the dry from 30 Hz to 15 kHz, and the default patch (Tone out of circuit) is within 0.5 dB of that same reference across the band. Turning Tone down is a departure from the standout, not an approach to it. | S2 ("15 ips: 30-15kHz"). **The 3 dB figure is … (App. T4) | medium — the … (App. T4) | the default patch shipping with Tone anywhere but out of circuit; more than 3 dB of ratioed deviation anywhere in 30 Hz–15 kHz at Tone 15 kHz; or more than 0.5 dB at the default | swept sine, `mix = 2` … (App. T4) |
| T5 | **The Wow macro's cents are real cents, and the ceiling is the transport's.** Peak pitch deviation of the repeat is 1.0 ± 0.25 cents at the Wow default, 3.5 ± 0.5 cents at Wow maximum, and below 0.05 cents at Wow zero; the macro cannot be driven past 4.0 cents at any setting. 0.2 % RMS wow and flutter is 3.46 cents (A4), so the ceiling is the machine's and the mapping is the thing under test. | S2 ("15 ips: < 0.15 % RMS. 7½ ips: < 0.2% … (App. T5) | medium — a transport … (App. T5) | measured deviation outside 1.0 ± 0.25 cents at the default, outside 3.5 ± 0.5 at maximum, above 0.05 cents at zero, or above 4.0 cents anywhere | instantaneous-frequency track of … (App. T5) |

No characters: one standout, one behaviour set.

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**One node: `audioecho.FeedbackDelay`**, composed, not extended.
`feedback = 0`, `cross_feed = 0`, `input_pan = 0`, `damping_hz = 0`,
`cut_hz = 0` gives the single repeat directly: the read is a per-sample
linear interpolation (`audioif_feedback_delay.c:226-228`), the in-loop
colourings are skipped at a zero coefficient (`:231`, `:236`, `:241`), and
the output is `dry·source + wet·loop` with the dry at unity below `mix = 1`
(`:201-202`, `:260-261`). The two colour macros map onto options that are
already there and are exactly right for a *single* pass: `damping_hz` for
Tone, and `loop_drive` for Saturation — the cubic soft-clip at `:180-184` is
applied to the delayed sample before it is mixed out (`:241-244`, `:261`), so
it colours the repeat and never the dry, which is what a hot tape return
does. `wow_hz`/`wow_depth_ms` give T5's small wobble from the node's
magic-circle oscillator (`:209-210`), per-sample, so it glides rather than
steps.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**None.** Every trait is reachable on `audioecho.FeedbackDelay` as it stands,
and the one thing this class would like — a click-free Time knob, since S4's
"zipper noise" applies to any moving read — is already asked for by
`DigitalDelay` §5 for a trait of its own. If that ask lands, this class uses
it; if it is refuted, nothing here fails, because no Tier 2 trait depends on
moving the time while audio runs.

## 6. Proposed surface

Six macros.

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Time | UNIPOLAR | 40–250 ms, log; default 135 ms | head spacing over tape speed; the range spans the figures S1 disputes |
| 1 | Level | UNIPOLAR | 0.0–2.0 (`Echo`'s convention: dry at unity to 1); default 0.35 | the console return fader |
| 2 | Saturation | UNIPOLAR | 0.0–1.0; default 0.15 | how hard the return drove the record amplifier (S3) |
| 3 | Tone | UNIPOLAR | 2 000–20 000 Hz log; top = out of circuit (default) | the tape path's top end (S2's 15 kHz) |
| 4 | Wow | UNIPOLAR | 0–3.5 cents peak at 0.7 Hz; default 1.0 cent | the transport's wow and flutter (S2) |
| 5 | Repeats | UNIPOLAR | 0.0–0.6; **default 0.0** | none — a D2 addition; the Sun rig had no feedback path, and the default says so |

**Patches** (names describe settings, never products): `Sun Slap` (135 ms,
level 0.35, saturation 0.15, tone off, wow 1 cent, repeats 0) ·
`Short Slap` (85 ms) · `Doubling` (35 ms, level 0.5, wow 2 cents) ·
`Hot Return` (135 ms, saturation 0.7) · `Two Repeats` (135 ms,
repeats 0.35) · `Dark Slap` (135 ms, tone 5 kHz).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/delay.py`.

1. **The default time is not the thing the class is named after.**
   `time_ms=95.0` (`delay.py:59`) against S1's measured 134–137 ms.
2. **It is `DigitalDelay` with different defaults.** `SlapbackDelay` subclasses …  *(argument in full: App. R)*
3. **No surface.** `MACRO_LABELS = ()` (`:55`),
   `PATCHES = {0: ("Default", ())}` (`:57`).
4. **The line is sized from the constructor's time and truncated** — inherited
   from `DigitalDelay.__init__`, `max_delay_ms=int(time_ms) + 100` (`:36`).
5. **The wire invariant is not held**, inherited from `audiodelays.Echo`
   (§4).
6. **`tail_samples` is `None`** (`_core.py:141`, not overridden) on a class
   whose tail is exactly one delay time and trivially computable.
7. **`reset()` touches only the output node** (`_core.py:366-373`); the
   rebuild enumerates the nodes it built and walks that list (roadmap §3).

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Which tape speed?** S1's 134–137 ms and S2's speed list imply a
   record-to-playback head spacing of 1.03 in at 7½ ips or 2.06 in at 15 ips
   (Appendix A1) — and `historyofrecording.com` calls the 350 two-speed, so a
   given unit offered two of S2's three. The spacing itself was not reached,
   so the speed — and with
   it whether T4's corner should be S2's 15 ips 15 kHz or the lower 7½ ips
   figure — is unsettled. *Settles:* an Ampex 350 manual, if one is reached;
   until then T4 uses the 15 ips figure, which is the conservative (least
   coloured) choice, and its confidence is recorded as medium.
2. **How saturated is "gloriously saturated"?** S3 is the only reached source
   on the return path's level, and it is an adjective. The Saturation macro's
   0.15 default is a design choice with no source. *Settles:* the
   implementation session, in the Phase 5 packet, or a source if one turns up.
3. **Does Wow modulate the repeat's top end as well as its pitch?** Sweeping
   the delay sweeps the interpolator's fractional part, so the wet path's
   high-frequency gain wobbles with it — at the 0.46 ms depth of Wow maximum
   the fraction crosses many whole samples per LFO cycle, so the modulation is
   far faster than 0.7 Hz. Nothing in T1–T5 rests on it and no source
   describes it; it is the palette's, and it may or may not be what a tape
   return sounds like. *Settles:* the implementation session, which measures
   it once in Phase 5 and either keeps it or shortens the depth.
4. **Should `Repeats` exist at all?** It is a D2 addition to a rig that had no
   feedback path, and a user who turns it up is no longer using the standout.
   The recommendation is yes, defaulting to zero, because a class that cannot
   do two slaps is less useful and the default still states the truth.
   *Settles:* the implementation session.

---


## Appendix

### A1. Head spacing — a derivation, not a source

S1 measures 134–137 ms; S2 lists 3¾, 7½ and 15 ips. Distance = speed × time:

| Tape speed | Spacing implied by 137 ms |
|---|---|
| 3¾ ips | 0.51 in |
| 7½ ips | **1.03 in** |
| 15 ips | 2.06 in |

A record-to-playback spacing of about an inch on a half-inch-tall head stack
is ordinary; two inches is not. That points at 7½ ips, which would also make
the repeat slightly darker and noisier than T4's 15 ips figure claims. It is
**not** asserted: the head spacing was not reached, and §8.1 records it as
open. The reason it is written down is that it is checkable the moment
someone reaches a 350 manual.

### A2. Source quotes relied on

- **S1**, abstract: "Using cepstrum and autocorrelation, we find that the tape
  delay used in Sun Studios was 134 - 137 ms, which is so long that the echo
  is perceived mainly as a distinct echo in the time domain, more than a
  coloration of timbre in the frequency domain. Even though the delay time is
  long, the echo is still perceived as rather 'intimate', because the echo is
  in mono. Panned in stereo, the feeling of being inside a quite small room
  would disappear."
- **S1**, conclusions: "Our measurements of Slap Back Echo from Sun Studios
  (Baby Let's Play House, Tryin' to Get to You) show that this is a single
  tape echo in mono with a time delay of 134-137 milliseconds."
- **S1**, on the comb: "the distance between the dips is CBTB = 129.3 -122.0
  = 7.3 ms" and "every 1029.3-1022= 7.3 Hz. This is what we find by cepstrum
  analysis." (The first figure's unit is a typo in the source; both readings
  are the same 7.3 Hz spacing, and 1/0.137 s = 7.30 Hz confirms it.)
- **S1**, on the listening test: "a simulated time delay of 134-137 ms in the
  other channel makes the whole 'room' disappear, sounding like a distinct
  open air echo from one single building positioned to the side of the
  listener."
- **S1**, on the rig: "He created a tape echo by using two Ampex 350 tape
  recorders." On the disputed figures: it cites others giving 163 ms, a
  rejected 530 ms, and "75-250 ms, with little or no feedback".
- **S2**: speeds "3 3/4, 7 1/2, 15"; "15 ips: 30-15kHz"; "60db (full track)";
  "15 ips: < 0.15 % RMS. 7½ ips: < 0.2% RMS"; "full-track-mono".
- **S3**: "there's the gloriously saturated 'slapback' delay echo from the
  Ampex 350 tape machines: This is a hallmark production value that Sam
  Phillips really exploited on mostly all of the early Sun records."
- **S4**: "some form of interpolation between samples is usually required to
  avoid 'zipper noise' in the output signal as the delay length changes."

### A3. Node lines relied on

`audioif/src/shared/audioif_feedback_delay.c` — `:31-38` a zero cutoff gives a
zero coefficient; `:81-83` `delay_ms` → `delay_frames`; `:99` mix clamped
`0..2`; `:116-118` `wow_depth_ms` clamped to 1000 ms; `:126-141` `input_pan`;
`:180-184` the cubic `soft_clip`; `:201-202` and `:260-261` the dry/wet law;
`:209-210` the magic-circle wow oscillator; `:226-228` linear interpolation;
`:231-244` the three in-loop colourings; `:247-249` the cross-feed sum.
`audioif/src/audioecho/FeedbackDelay.c:102-110` allocates
`line_frames × 2 × sizeof(int16_t)` — two lanes always.
`audioif/src/shared/audioif_echo.c:11`, `:36-38` the stock node's mixdown
limiter, which is why this class is audioif-tier.
`audioif/docs/upstream-diff.md:770-812` records `audioecho` as audioif's own.

### A4. Cents arithmetic in T5, and the macro's mapping

0.2 % RMS wow and flutter is a frequency ratio of 1.002, and
1200·log₂(1.002) = 3.46 cents; 0.15 % gives 2.60 cents. T5's 3.5 cent bar is
the looser of the two, so a class that passes it at 15 ips passes at 7½ too.

The node takes a depth in milliseconds, not cents. For a sinusoidal delay
modulation of depth *D* ms at rate *f* Hz, the peak fractional pitch
deviation is 2π·f·D/1000. At the class's fixed 0.7 Hz that is 0.0044·D, so
3.5 cents (a ratio of 0.00202) is **D = 0.46 ms** and the 1.0 cent default is
**D = 0.13 ms**. The Wow macro maps cents to `wow_depth_ms` in Python at
construction and on every move; the mapping is rate-independent because the
node converts ms to frames itself (`audioif_feedback_delay.c:116-118`).

### A5. Licence and citation audit, 2026-09-06

Run by an independent licence-and-citation auditor. **Every source row in §2
and every URL in this file was re-fetched in this run**; nothing below is
carried over from an earlier pass, and no source is cited that this pass did
not reach itself.

**Read back and confirmed verbatim.** S1's abstract ("the tape delay used in
Sun Studios was 134 - 137 ms ... Panned in stereo, the feeling of being inside
a quite small room would disappear"), its conclusions ("a single tape echo in
mono with a time delay of 134-137 milliseconds"), both comb figures
("129.3 -122.0 = 7.3", "every 1029.3-1022= 7.3 Hz"), the listening test, the
rig sentence and the disputed figures; its full citation block, which reads
exactly "Halmrast. T, (2019) ... Proceedings of the 12th Art of Record
Production Conference Mono: Stereo: Multi (pp. 137-154). Stockholm: Royal
College of Music (KMH) & Art of Record Production". S2's five specification
lines and its copyright. S3's sentence, in full and in context. S4's "zipper
noise" sentence. S5's peer-review sentence and its rights sentence.

Two of §1's sharpest claims were checked by search rather than by reading:
"Ampex" occurs **once** in S1's entire extracted text, so "S1 says exactly one
thing about the rig" is exact; and `copyright`, `©` and `licen` occur **zero**
times in its 18 pages, so the licence position genuinely had to be chased to
S5. `www.arpjournal.com`'s home page still returns no readable content.
`vintagedigital.com.au` still returns HTTP 403.

**Corrections applied by this pass.**

1. **Two sources used in §1 had no row in §2.** `historyofrecording.com` was
   quoted in §1 and described only inside the not-reached paragraph. It is now
   **S6**, with its licence call, and it turns out to carry one line §1 needed
   and did not have: "Independent record and playback systems allow the tape
   to be monitored while recording" — the capability the two-machine echo
   rests on. §1's "unsourced" label is narrowed accordingly: the mechanism's
   premise is sourced, Phillips' patching is not.
2. **"No operation or service manual was reached" is no longer true.** Ampex's
   own *Model 351* manual (Oct 1959, 88 pages) was reached this run and is now
   **S7**. It is recorded with its scope stated: **the 351 is the 350's
   successor, not the 350**, so no number in it is imported into a trait here.
   What it does do is corroborate S2 — its flutter-and-wow table reads
   "3 3/4 .25%, 7 1/2 .2%, 15 .15%" and its S/N "60 full track", matching S2's
   350 figures exactly — and confirm the two-of-three speed structure §1
   infers ("tape speed pairs of 3 3/4 ips and 7 1/2 ips or 7 1/2 and 15 ips").
   It carries a 7½ ips response of 40 Hz–10 kHz *for the 351*, which is where
   §8.1 should look first, and **no head spacing at all** (`spacing`: 0 hits),
   so §8.1's central open question stands unmoved.
3. **§2's account of the disputed figures was loose in two ways.** 530 ms is
   *longer* than S1's measurement, not shorter, and S1 does not itself argue
   against these figures — it quotes elvispresleymusic.com rejecting 530 ms as
   "too long" and preferring 163 ms, and cites Wikipedia for "75-250 ms". The
   attribution is now explicit; the numbers were right.
4. **Two licence calls made explicit.** S3 and S4 recorded the absence of a
   licence but not the call the vision's §5 requires; both now read **"licence
   unverified, treated as copyleft"**. No licence call was *upgraded* by this
   pass. S2 stays at verified all-rights-reserved ("Copyright © 2023
   Reel-Reel.com - All Rights Reserved", re-read this run) and S1 stays at
   author-retains-copyright via S5.
5. **The RCA figures were checked and left alone.** "111/117 ms Hollywood"
   looks like a typo and is not one: S1's summary says "117 ms in Hollywood"
   and its conclusions say "a reflection after 111 ms" — the paper disagrees
   with itself, and the seed was right to record both.

**What this pass did not check.** The cents arithmetic in A4 and the head-
spacing derivation in A1 were not re-derived; they are the technical auditor's.
Every `grep -n` line citation in A3 *was* re-checked against the audioif tree
and all of them resolve to the lines claimed.

### A6. Numbers the trait critic added, 2026-09-06

Taken this run on `audiocomponents/.venv/bin/python` (the CPython build of
audioif). Nothing here is a claim about tape; it is about the palette, and it
is why T4 is stated as a ratio.

**The read interpolator's high-frequency loss.** `delay_frames` is a float
(`audioif_feedback_delay.c:81-83`) and the read is linear interpolation
between two neighbours (`:226-228`) — a one-zero FIR whose magnitude at a
half-sample offset is |cos(πf/fs)|. Rendered wet-only (`mix = 2`,
`feedback = 0`) against a sine, integer delay versus the same delay plus half
a sample:

| rate | tone | integer delay | half-sample delay |
|---|---|---|---|
| 48 kHz | 15 kHz | 0.00 dB | −5.11 dB |
| 48 kHz | 1 kHz | 0.00 dB | −0.01 dB |
| 44.1 kHz | 15 kHz | 0.00 dB | **−6.35 dB** |

**And the class's own default lands on the worst case.** 135 ms is 6 480.0
frames at 48 kHz — an integer, no loss — and **5 953.5** frames at 44.1 kHz,
exactly half a sample. So a T4 stated in absolute terms ("within 3 dB of the
dry from 30 Hz to 15 kHz") is disconfirmed at 44.1 kHz at the default patch,
by 3.35 dB, before any Tone setting is chosen. That is a real property of the
build and it belongs in the docstring; it is not a fact about an Ampex 350,
which is why T4 measures the Tone macro against the class's own Tone-out
response instead.

**The wow oscillator is shared between lanes.** It is stepped once per frame,
outside the per-channel loop, and the resulting `offset` is computed once and
used by both lanes (`audioif_feedback_delay.c:209-212`, read this run). T3's
"at every macro extreme, Wow included" is therefore reachable by construction
rather than by luck.

**The two node claims §4 rests on, re-measured.** At `mix = 0` on a 1 kHz sine,
`audioecho.FeedbackDelay(delay_ms=350, feedback=0.4)` differs from the source
in **0 of 9 600** samples at amplitude 12 000 *and* at 32 000;
`audiodelays.Echo(delay_ms=350, decay=0.4)` differs in **0** at 12 000, **0**
at 28 000 and **2 800 of 9 600** at 32 000, peak 32 000 → 28 437.

### A7. The palette verifier's pass, 2026-09-06

An independent pass re-ran every §4 claim about what an audioif node can and
cannot do, against the C under `audioif/src/shared` and the bindings under
`audioif/src/audioecho/`, and probed the behavioural ones on
`audiocomponents/.venv/bin/python`, 48 kHz, interleaved `int16`. **No §4 or §5
claim needed correcting**; §5 asks for nothing, and the three claims that had
been argued from the C rather than measured now carry measurements.

**T3's shared wow oscillator, measured.** The class's own default patch —
`delay_ms = 135`, `feedback = 0`, `cross_feed = 0`, `input_pan = 0`,
`loop_drive = 0.15`, `wow_hz = 0.7`, `wow_depth_ms = 0.46` (the Wow macro at
its ceiling) — on a channel-identical 440 Hz probe gives **L − R of exactly
zero across 110 080 frames**, maximum absolute difference 0. A6 argued this
from `audioif_feedback_delay.c:209-212`; it is now a number.

**A4's cents mapping, measured end to end.** The same render's instantaneous
frequency tracks between 439.11 and 440.89 Hz, i.e. **+3.49 / −3.50 cents**
against A4's predicted 3.5 at `D = 0.46 ms` and 0.7 Hz. The Python-side
cents → `wow_depth_ms` map A4 derives is therefore right at the ceiling, and
the macro can be checked against arithmetic rather than against taste.

**The wire finding.** `audioecho.FeedbackDelay(delay_ms=350, feedback=0.4)` at
`mix = 0` on a ±32 000 1 kHz tone differs from the source in **0 of 9 600**
samples, peak 32 000 → 32 000; `audiodelays.Echo` at the same settings differs
in **2 800 of 9 600**, peak 32 000 → 28 437, first at sample index 18
(29 564 → 28 170). §4's "why not the stock node" reproduces.

**One note for the rebuild, not a node ask.** `delay_ms` is clamped to
`line_frames − 2` (`audioif_feedback_delay.c:81-83`), so a line sized at
exactly the macro's 250 ms ceiling measures 249.958 ms at the top of the knob;
§3's 300 ms allocation already leaves the headroom that avoids it. And Tier 3
calls the default patch "every in-loop filter out of circuit", which is true of
`damping_hz` and `cut_hz` but not of the cubic `soft_clip`: `loop_drive` is
0.15 at the default (§6), so `audioif_feedback_delay.c:241-243` runs on every
frame. It is two multiplies, not a filter, and the budget is unaffected.

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

*Rate:* **T4 cannot hold at 22.05 kHz** — the standout's 15 kHz corner is
above that Nyquist, so at 22.05 kHz the Tone macro clamps and T4 is recorded
as not applicable at that rate rather than failed. Every other trait holds at
all three rates. *Material:* the wire check must use a full-scale probe (the
reason is `DigitalDelay` §4 and its Appendix A2).

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Tor Halmrast, "Sam Phillips' Slap Back Echo; Luckily in Mono", *Proceedings of the 12th Art of Record Production Conference*, Stockholm 2017 (published 2019). PDF fetched, text extracted with `pypdf` | 134–137 ms measured by power cepstrum and autocorrelation on two Sun sides; one repeat, mono, no regeneration; comb spacing CBTB = 1/Δt = 7.3 Hz at 137 ms, cross-checked two ways; the RCA comparisons (82 ms Nashville, 111/117 ms Hollywood); the stereo-panning listening test | No licence line anywhere in the PDF's extracted text (re-extracted this run: 18 pages, no `copyright`/`©`/`licen` string). Chased to the journal's own Contribute page (S5): "All material submitted remains the property of the copyright holder", and nothing is granted to a reader — so **copyright retained by the author, no reader licence; treated as copyleft** and read as a paper, never ported (vision §5). The journal's home page still returns no readable content to the fetch tool | <https://www.arpjournal.com/asarpwp/wp-content/uploads/2021/12/Tor-Halmrast_ARP2019.pdf> | yes |
| **S2** Reel-Reel.com, Ampex 350 entry | tape speeds "3 3/4, 7 1/2, 15"; frequency response "15 ips: 30-15kHz"; S/N "60db (full track)"; wow and flutter "15 ips: < 0.15 % RMS. 7½ ips: < 0.2% RMS"; "full-track-mono" heads | "Copyright © 2023 Reel-Reel.com - All Rights Reserved" — read-only, facts about a machine | <https://reel-reel.com/tape-recorder/ampex-350/> | yes |
| **S3** *Premier Guitar*, Bryan Clark, "Capturing the Shine of Sun Records", 2023-08-05 | "the gloriously saturated 'slapback' delay echo from the Ampex 350 tape machines" — the only reached source on the return path's saturation | no copyright line or `©` anywhere in the fetched page (checked this run); trade publication — **licence unverified, treated as copyleft**; read as a document | <https://www.premierguitar.com/diy/recording-dojo/capturing-the-shine-of-sun-records> | yes |
| **S4** Smith & Lee, *Time Varying Delay Effects*, CCRMA RealSimple, 2008 | "zipper noise" as the artefact of an uninterpolated moving read — why the Time macro must interpolate even here | no copyright, `©` or licence string anywhere in the 60-page extracted text (checked this run) — **licence unverified, treated as copyleft**; read as a paper, never ported | <https://ccrma.stanford.edu/realsimple/DelayVar/DelayVar.pdf> | yes |
| **S5** *Journal on the Art of Record Production*, Contribute page | the source for calling S1 peer-reviewed: "JARP operates a rigorous peer review process. All articles and conference papers submitted to JARP are anonymised and sent to 3 scholars for review." Also S1's rights position (see the S1 row) | states copyright stays with the submitting author; no reader licence, no open-access designation — **unverified as a licence, treated as copyleft** | <https://www.arpjournal.com/asarpwp/contribute/> | yes |
| **S6** HistoryOfRecording.com, Ampex 350 page | "a **two-speed** audio recorder designed for use with standard ¼ inch tape"; heads "with either full or half track"; "Independent record and playback systems allow the tape to be monitored while recording" — the reached statement that one 350 can play back what it is recording. Carries **no** response, S/N or wow-and-flutter figures | no site licence statement; credits its "Foundational text ... from the AES Historical Committee paper ... and the AMPEX Model 350 operation and service literature" — **licence unverified, treated as copyleft**; read as a document | <https://www.historyofrecording.com/ampex350.html> | yes |
| **S7** Ampex *Model 351* manual, Oct 1959 (88 pp., text via `pypdf`), hosted by WorldRadioHistory. **The 351 is the 350's successor, not the 350** — no number here is imported into a trait | "tape speed pairs of 3 3/4 inches per second (ips) and 7 1/2 ips or 7 1/2 and 15 ips", the manufacturer's own two-of-three structure; a per-speed performance table whose flutter and S/N match S2's 350 figures exactly (A5 quotes it). **No head spacing anywhere** — `spacing`: 0 hits | host asserts "fair use ... for scholarship, archiving and research" and disclaims ownership: the host's position, not a grant from Ampex — **licence unverified, treated as copyleft**; read as a document | <https://www.worldradiohistory.com/Archive-Catalogs/Ampex/Ampex-351-Manual-1959.pdf> | yes |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **One repeat at 134–137 ms, and no second one.** The default patch (Repeats 0) puts the class's measured delay in 130–140 ms, and the power cepstrum of its output has one peak there with nothing above −40 dB re that peak at 2×, 3× or 4× it. **Control that must fail:** at Repeats 0.35 the 2× peak appears above −20 dB re the first. | S1 | high — a peer-reviewed (S5) measurement of two records, cross-checked by two methods | a default delay outside 130–140 ms; any energy at 2×, 3× or 4× the delay above −40 dB re the first repeat at the default patch; **or** the control not moving — no 2× peak above −20 dB at Repeats 0.35 | click through at `mix = 2`, measured lag at 48 / 44.1 / 22.05 kHz; then a power cepstrum of the class's output on a sustained voice-like probe at the default patch and at Repeats 0.35, run with S1's own analysis |
| T2 | **The repeat makes a comb whose teeth are 1/*T*, across the whole band.** At any Time setting the magnitude spectrum's notch spacing is 1/*T* within 0.5 %, fitted over 200 Hz–2 kHz and again over 8–10 kHz, and the two fits agree within 0.5 %. At S1's measured 137 ms that is 7.30 Hz; at the class's own 135 ms default it is 7.41 Hz. | S1, which measures the spacing twice at its own 137 ms: dips 129.3 − 122.0 = 7.3, peaks 1029.3 − 1022 = 7.3 Hz | high | notch spacing more than 0.5 % from 1/*T* at either fit; or the two fits disagreeing by more than 0.5 %, i.e. a spacing that changes with frequency | magnitude spectrum of the class's impulse response at the default patch (dry and wet both present — the comb is their sum), zero-padded to 20 s so bins are 0.05 Hz; notch spacing fitted over 200 Hz–2 kHz and over 8–10 kHz, at Time 135 ms and at 137 ms |
| T3 | **The repeat is mono and shares the dry's position.** On a probe identical in both channels the wet component is identical in both channels: L−R stays below −90 dBFS at every patch and at every macro extreme, Wow included. Nothing in the class pans, spreads or Haas-shifts the repeat, and no macro can. | S1 — "this is a single tape echo in mono", and its listening test, where a 134–137 ms repeat panned to the other channel makes "the whole 'room' disappear". The design consequence is ours; the node makes it reachable — its wow oscillator is stepped once per frame outside the per-channel loop (`audioif_feedback_delay.c:209-212`, read this run), so both lanes read the same modulated offset | high for the record; high for the build | L−R above −90 dBFS at any patch or macro extreme, Wow at maximum included; **or** the class carrying a width, spread or per-channel-time macro at all | L−R RMS of the class's output on a channel-identical probe, at `mix = 0.35` and `mix = 2`, at all seven patches and at both extremes of every macro, 48 and 44.1 kHz |
| T4 | **The repeat is band-limited, but only slightly — a slap is not a dark effect.** Measured as a ratio against the class's own Tone-out response at the same Time and rate: at Tone 15 kHz the repeat is within 3 dB of the dry from 30 Hz to 15 kHz, and the default patch (Tone out of circuit) is within 0.5 dB of that same reference across the band. Turning Tone down is a departure from the standout, not an approach to it. | S2 ("15 ips: 30-15kHz"). **The 3 dB figure is ours, not S2's** — S2 quotes a band with no tolerance, and 3 dB is the conventional reading of a quoted response band, recorded here as an assumption | medium — the machine's published band, no tolerance with it, and not a measurement of Phillips' actual return path | the default patch shipping with Tone anywhere but out of circuit; more than 3 dB of ratioed deviation anywhere in 30 Hz–15 kHz at Tone 15 kHz; or more than 0.5 dB at the default | swept sine, `mix = 2`, first repeat gated out, at 48 and 44.1 kHz, at Tone out and Tone 15 kHz, each divided by the Tone-out response at the same Time. **Ratioed for a measured reason:** the read interpolates linearly on a float `delay_frames`, and the default 135 ms is 6 480.0 frames at 48 kHz but **5 953.5** at 44.1 kHz — the worst half-sample case, which costs 6.35 dB at 15 kHz on its own (A6). An absolute test of this trait fails at 44.1 kHz for a reason that has nothing to do with tape |
| T5 | **The Wow macro's cents are real cents, and the ceiling is the transport's.** Peak pitch deviation of the repeat is 1.0 ± 0.25 cents at the Wow default, 3.5 ± 0.5 cents at Wow maximum, and below 0.05 cents at Wow zero; the macro cannot be driven past 4.0 cents at any setting. 0.2 % RMS wow and flutter is 3.46 cents (A4), so the ceiling is the machine's and the mapping is the thing under test. | S2 ("15 ips: < 0.15 % RMS. 7½ ips: < 0.2% RMS"); the cents conversion and the depth mapping are arithmetic (A4) | medium — a transport spec, and the class exposes a knob the rig did not have | measured deviation outside 1.0 ± 0.25 cents at the default, outside 3.5 ± 0.5 at maximum, above 0.05 cents at zero, or above 4.0 cents anywhere | instantaneous-frequency track of the delayed copy of a held 440 Hz tone over 2 s, `mix = 2`, at Wow zero, default and maximum, 48 and 44.1 kHz |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Not reached, and what was looked for.** The Ampex 350 **head spacing** — the
one number that would settle which tape speed Phillips used — was not found.
`historyofrecording.com` (S6) was reached and carries no specifications at
all; `vintagedigital.com.au` returns HTTP 403. **No 350 manual was reached** —
a 351 manual was (S7), and the 351 is the 350's successor, not the 350, so its
per-speed numbers are evidence about the 351 and are not imported into any
trait here. The 350's own response at 7½ ips is still unreached: only the
15 ips figure has been read from a page about the 350. `www.arpjournal.com`'s
home page still returns no readable content, which is why S1's rights position
had to be chased to the Contribute page (S5). No DAFx/AES paper on modelling a tape
slap specifically was found; S1 *is* the peer-reviewed measurement (S5) and
is better than a model would be.

*(from §2)*

**Standout confirmed, and it changes a number.** The Sun slap is the right
referent and, unusually for this program, it comes with a measurement of the
finished artefact rather than a schematic — which is exactly what a
"literature" grade should look like. The confirmation is not cosmetic: the
current class defaults to **95 ms** (`delay.py:59`), and S1 measures the thing
the class is named after at **134–137 ms**. S1 also records the other figures in
circulation, and the attribution matters: the 530 ms suggestion (*longer* than
its own measurement) and the 163 ms figure are elvispresleymusic.com's, quoted
by S1, which reports that site rejecting 530 ms as "too long" and preferring
163 ms; "75-250 ms, with little or no feedback" is S1 citing Wikipedia. S1
argues against none of them in so many words — its own measurement is what
contradicts them. The rebuild's default moves to 135 ms with the range
spanning what the literature disputes.

*(from §3)*

**Why three of the five are ratioed or bounded rather than absolute.** The
node's read interpolates linearly on a float delay, so the wet path carries a
high-frequency loss that is a function of the *fractional* part of the delay,
not of anything in the tape path (A6). T4 divides it out; T2 and T5 are
unaffected because a comb's spacing and a pitch track do not read it.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: **ESP32-P4
0.03**, **ESP32-S3 0.06** — the cheapest class in the family, because the
default patch runs the node with feedback at zero and every in-loop filter
out of circuit. Lean patch expected: **no**. Line RAM at the macro's 250 ms
ceiling plus headroom (300 ms) is **57.6 KB** at 48 kHz
(`src/audioecho/FeedbackDelay.c:110` allocates two `int16` lanes regardless
of channel count).

*(from §3)*

**Latency: zero, at every macro setting, patch and rate.** The dry path is a
wire and the repeat *is* the effect. **No option adds latency** — there is no
lookahead, partition or pitch window in this class. `tail_samples` is the
delay in samples at `Repeats = 0` (the default) and
`ceil(T · 3 / −log10 f)` when Repeats is turned up; it is recomputed on every
Time or Repeats move. Verified by the click and burst-then-silence probes.

*(from §4)*

**Why not the stock node.** `audiodelays.Echo` would make this a **stock**
tier class, and it fails Tier 1's wire invariant for the same measured reason
as `DigitalDelay`: the mixdown limiter at `audioif_echo.c:38` compresses
above ±28 000 whether or not any wet signal exists (measured: 2 800 of 9 600
samples differ at `mix = 0` on a full-scale tone; `FeedbackDelay` differs in
zero). Portability tier is therefore **audioif**; on a stock CircuitPython
board the module imports and construction raises a clear `ImportError`, the
`CabinetSim` pattern (`drive.py:30-33`, `:331-334`).

*(from §4)*

**Mono, and stereo.** Not stereo by definition. At `channel_count` 1 a mono
source gets the identical effect on its one channel. At `channel_count` 2 the
node keeps each channel on its own lane with `input_pan = 0` and
`cross_feed = 0` (`audioif_feedback_delay.c:126-141`, `:247-249`), so the
repeat sits exactly where the dry sits — which is T3, and it is why this
class must never grow a spread macro.

*(from §4)*

**`capabilities`: `()`** — D10's answer for this class, and the one line of
why: a slapback's identity is a fixed physical distance over a fixed tape
speed. It has no musical relationship to a tempo, so the class does not read
the transport and does not claim to.

*(from §7)*

2. **It is `DigitalDelay` with different defaults.** `SlapbackDelay` subclasses
   it (`:48`) and its whole body is one call with `feedback=0.0` (`:60-61`).
   Nothing about tape — no saturation, no band limit, no wobble, and no way
   to reach any of them.
