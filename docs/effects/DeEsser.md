# Effects Dossier — `DeEsser` (dbx 902)

**Class:** `lib/audioeffects/dynamics.py` — read once, for §7.
**Family / phase:** Dynamics, roadmap Phase 2
**Standout:** dbx 902 De-Esser *(proposed, vision §4.2)* — **confirmed, and it
is the strongest referent in this unit.** dbx's own owner's manual was reached
(S1) and gives the mechanism, the filter order, the crossover span, the
attack and release laws and the gain-reduction range. It is also the right
*kind* of referent: RaneNote 155 independently argues that comparing the
band to the broadband level "is the best dynamics processor for this task",
which is exactly what the 902 does, and names the alternative — a side-chain
EQ feeding an ordinary compressor — as the "primitive de-esser" whose failure
it draws (S2). The class this seed replaces is that primitive one (§7).
**Grade:** literature — a manufacturer's manual with the theory of operation
and a full specification table, but no schematic (§2).
**Portability tier:** needs audioif-own nodes (`audiodynamics`, `audioroute`)
**Status:** seed (Phase 0), written 2026-09-06

## 1. The circuit, in one paragraph

The 902 is a VCA whose control voltage comes from a **comparison of two
levels, in decibels**, and that is the whole idea. The audio is split by a
"two-pole, maximally flat filter design … user adjusted over a range of
**800 Hz to 8 kHz**" — the specification table calls it "12 dB/octave, phase
coherent" — and dbx's "patented RMS level detectors" measure the
high-frequency portion and the full-bandwidth signal. *(Audit: the manual names
the detectors and names the two levels compared; it never states how many
detectors there are, so "two" is this seed's reading of the mechanism, not the
manual's word. No trait depends on the count.)* The 902 then "examines the differences in dB
between the high frequency and full-bandwidth portions of the signal", and
"when the high frequency level is excessive relative to the full bandwidth
level, the 902 will de-ess" (S1). Because the comparison is a ratio, absolute
level drops out: the manual's headline claim is de-essing "of signals which
change in level by as much as 60 dB", the specification says the unit
"operates uniformly over input range of −40 dBu to +24 dBu without requiring
adjustment", and — the sentence that separates it from every threshold-based
de-esser — "the 902 does not even have a threshold control to require
adjustment". Two knobs remain: **Frequency**, the split point (12 o'clock is
2.5 kHz), and **Range**, "the amount of de-essing effect produced when a
sibilant is detected", specified as "Maximum 'Ess' Attenuation: Variable 0 to
20 dB". A **Mode** switch chooses whether the gain reduction "affect[s] either
the entire audio bandwidth, or the high frequencies only" — the HF ONLY
setting being for "de-edging" and "de-clicking" instrumental material. The
dynamics are specified rather than knobbed: attack is program-dependent,
"2 ms for 10 dB above threshold, 600 µs for 20 dB above threshold, to achieve
63 % gain reduction", and release is a constant **925 dB/sec** — a rate, not a
time constant. Gain is unity, frequency response 20 Hz–20 kHz, and the control
voltage is available at 50 mV/dB (S1).

## 2. Sources and license calls

All fetched 2026-09-06; nothing from memory.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** dbx, *902 de-Esser* owner's manual, part no. 18-2015-B, 4/30/96 … (App. S1) | Log-domain comparison … (App. S1) | **Licence unverified** … (App. S1) | <https://adn.harmanpro.com/product_documents/documents/502_1323992524/902%20Owners%20Manual_original.pdf> | yes — PDF fetched, text via `pypdf` |
| **S2** Jeffs, Holden & Bohn, *Dynamics Processors*, RaneNote 155 | "True de-essing involves comparing the relative … (App. S2) | PDF line "© 2005 Rane Corporation" … (App. S2) | <https://www.ranecommercial.com/legacy/pdf/ranenotes/Dynamics_Processors.pdf> | yes — PDF fetched, text via `pypdf` |
| **Local** `audioif/src/shared/audioif_dynamics.{c,h}`, `audioif/docs/upstream-diff.md`, the probes in the Appendix | What the current de-esser actually does | MIT (audioif) | — | yes |

*Second-pass result: both licence calls stand as written (S1's document carries
no copyright, trademark or terms line on any of its 8 pages — re-checked page by
page — so "unverified, treated as copyleft" is correct); every S1 and S2
quotation verified verbatim; three flags, marked inline.*

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| D1 | **Threshold-free and level-independent.** One probe of fixed spectral balance, rendered at −6, −20, −40 and −55 dBFS, produces gain-reduction traces whose settled values agree within 1 dB — a 49 dB window, which is what 16-bit probe material carries; S1's claim is 60 dB, and the shortfall is the int16 floor of the kit, not the class, so a float render extends the window and is recorded if made | S1 ("de-essing of signals which change in … (App. D1) | high — stated twice … (App. D1) | Settled reduction differing by more than 1 dB between any two of the four levels; any level at which the reduction collapses to zero (the shape of S2's Fig. 12, and what A8 measures on the shipped class) | LEVEL |
| D2 | **The split point is settable 800 Hz–8 kHz and each half is maximally flat with a 12 dB/octave skirt**: with the split at 2.5 kHz each band is −3.0 ± 0.5 dB at the corner (Butterworth) and its skirt fits 12 ± 1.5 dB/octave over the octave-to-two-octaves band either side (625 Hz–1.25 kHz below, 5–10 kHz above — all below Nyquist at 22.05 kHz, so the fit is rate-honest), and the −3 dB corner tracks the Frequency control within 5 % at 800 Hz, 2.5 kHz and 8 kHz | S1 ("two-pole, maximally flat filter design … … (App. D2) | high — the manual's … (App. D2) | A skirt outside 12 ± 1.5 dB/octave; a corner that does not move with the Frequency control; a corner at −6 dB (a Linkwitz-Riley alignment rather than the two-pole Butterworth S1 names) | SPLIT |
| D3 | **Two modes.** Driving 12 dB of reduction: in broadband mode both bands fall by 12 dB within 0.5 dB; in HF-only mode the high band falls by 12 dB within 0.5 dB while the low band moves less than 0.25 dB | S1 (Mode switch: "affect either the entire … (App. D3) | high | The low band moving more than 0.25 dB in HF-only mode; either band's reduction more than 0.5 dB from the commanded 12 dB; the two modes measuring within 0.25 dB of each other | SPLIT under reduction |
| D4 | **Release is linear in dB at a fixed rate**, not an exponential time constant: from 12 dB of reduction the recovery is a straight line in dB reaching 0 dB in 13.0 ms at the 902's specified 925 dB/sec, within 10 % | S1 ("Release Rate: 925 dB/sec") | high — a rate in … (App. D4) | A recovery whose dB trace curves, i.e. an exponential in linear gain | REL |
| D5 | **Attack is program-dependent**: the time to 63 % of final reduction shortens as the overshoot grows — about 2 ms at 10 dB over and 600 µs at 20 dB over, a ratio of ~3.3 within 25 % | S1 ("Attack Rate: Program-dependent … (App. D5) | high | One attack time independent of overshoot, which is what a fixed coefficient gives | ATT |
| D6 | **RMS detection**: a sine and a square of equal RMS in the high band, at the same spectral balance, produce the same reduction within 0.5 dB | S1 ("dbx patented RMS level detectors … sense … (App. D6) | high | A ~3 dB difference, which is what a peak detector gives | XF |
| D7 | **Range bounds the reduction**, variable 0 to 20 dB: with the sibilant probe driven 20 dB past the sensitivity setting, the measured reduction stops at the Range setting within 0.5 dB at 5, 10 and 20 dB, and never exceeds it; on the low tone alone (no sibilant) the gain is unity within 0.1 dB | S1 ("Maximum 'Ess' Attenuation: Variable 0 to … (App. D7) | high | Reduction exceeding the Range setting at any of the three; a settled reduction more than 0.5 dB from the setting under heavy drive; a resting gain more than 0.1 dB from unity on the no-sibilant probe | LEVEL (Range clause) … (App. D7) |
| D8 | **The audio path sums flat.** With no sibilant present and both bands at unity, the summed magnitude is within 0.25 dB of flat from 20 Hz to min(20 kHz, 0.45 × sample rate). **This is the dossier's own criterion, not S1's** — S1 says "phase coherent" and prints no summed response — and it is *not* satisfiable by the 12 dB/octave pair D2 describes: an in-phase second-order Butterworth LP+HP pair has a true **null** at the corner (A-D1) and **+3.01 dB** there with one half inverted, while a fourth-order Linkwitz-Riley pair sums to 0.0000 dB (A-D1). The audio-path order is therefore a **design choice under vision D2** and §4 records it; D2 stays the sourced description of the 902's own filter and governs the **detector** split | derived and measured this run (A-D1) … (App. D8) | high for the … (App. D8) | A summed magnitude beyond ±0.25 dB anywhere in the band; a null or a +3 dB peak at the crossover, which is what shipping D2's order in the audio path unmodified would give | SPLIT |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

Compose first, and most of it composes. `audioroute.Splitter` fans the source
to two taps; two `audiofilters.Filter` chains carry the second-order
Butterworth split (Q = 0.707, the same pair the shipped `MultibandCompressor`
already builds, `dynamics.py:250`); `audiomixer.Mixer` sums them. That is D2
and D3 built entirely from what exists — HF-only mode is the same graph with
the gain applied to one tap instead of the sum. **But the order is a decision, not a
transcription, and the critic pass caught the seed making it silently.** S1's
own filter is two-pole Butterworth (D2), and a two-pole Butterworth LP/HP pair
does **not** sum flat: in phase it nulls at the corner (a true null: −66.9 dB on a
4000-point log grid, −96.5 dB on a 200 000-point one) and with one half inverted
it peaks at +3.01 dB, while
a fourth-order Linkwitz-Riley pair — two cascaded Butterworth sections a side —
sums to 0.0000 dB (A-D1 below; the same control `MultibandCompressor.md`
records at A-M1). So the class builds the **audio-path** split as LR4 to meet
D8 and keeps the **detector** split at S1's two-pole 12 dB/octave to meet D2,
and the docstring says which is which. *(Palette verification, 2026-09-06: the LR2/LR4 difference was rebuilt from the
nodes themselves and reproduces exactly — at a 4 kHz corner the one-section
pair sums to a **true null** (all-zero output) at the corner and −6.75 / −2.65 /
−0.55 dB at 2828 / 2000 / 1000 Hz, while the two-section LR4 pair sums to
**0.00 dB at every one of those frequencies**. D8 needs LR4; D2's detector
stays at S1's two-pole.)* Second caution from the `MultibandCompressor` seed,
**corrected there by the same verification**: `audioroute.Splitter` does not
erase a long source, it discards the first `n − 8192` frames of any buffer
longer than its ring, and the fix is one block-sized node between the source
and the Splitter, so this class builds `source → block-sized node → Splitter`.
See `MultibandCompressor.md` §4 and its V-M1–V-M3 before building on the
Splitter.

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

Additive on `audiodynamics` (D1 of the vision), each defaulting to today's
behaviour so `dynamics_probe.py`'s hash is unchanged.

- **N-DEESS-1 — relative-threshold detection (unblocks D1).** A mode in which …  *(argument in full: App. R)*
- **N-DEESS-2 — a dB-linear release (unblocks D4).** `release_db_per_sec` …  *(argument in full: App. R)*
- **N-DEESS-3 — program-dependent attack (unblocks D5).** An attack …  *(argument in full: App. R)*
- **N-DEESS-4 — RMS detection (unblocks D6).** *Same ask as `Expander`'s …  *(argument in full: App. R)*
- **N-DEESS-5 — 12 dB/octave side-chain (unblocks D2's detector half).** Made …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Seven macros — the 902 has two knobs and a switch, and the extra four are the
specified behaviours it hides, exposed under D2 of the vision.

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 800 Hz … 8 kHz, log | 902 Frequency (12 o'clock = 2.5 kHz) |
| 1 | Range | UNIPOLAR | 0 … 20 dB | 902 Range |
| 2 | Sensitivity | UNIPOLAR | 0 … 24 dB of allowed HF excess | the 902's fixed internal comparison, made adjustable |
| 3 | Mode | TOGGLE | broadband / HF only | 902 Mode switch |
| 4 | Release | UNIPOLAR | 200 … 4000 dB/sec, log | the 902's fixed 925 dB/sec |
| 5 | Attack | UNIPOLAR | 0.1 … 10 ms, log | the 902's program-dependent rate, as its 10 dB-over value |
| 6 | Listen | TOGGLE | off / on | no panel control; monitors the reduced band |

Characters: none. Patches: **Vocal**, **Bright Vocal** (frequency up, range
up), **Whispered Verse** (sensitivity down), **Guitar Pick Noise** (the
manual's own instrumental case: HF only, frequency high), **Cymbal Edge**,
**Hard De-Ess** (range at maximum). Listen is a diagnostic and is off in every
patch.

## 7. Defects in the current class the rebuild must not repeat

- **It is the de-esser RaneNote 155 draws as the wrong one.** `dynamics.py:194-197`
  builds a `DYN_COMPRESS` with `sidechain_hz=frequency` and a fixed
  `threshold_db=-30.0` — S2's Fig. 12 exactly. Measured: 10.57 dB of reduction
  at −6 dBFS and none at all at −20 dBFS on identical spectral content (A8).
  The docstring at `:181-182` claims the opposite of what it does: "the
  detector hears only what is above `frequency`" describes a 6 dB/octave tilt
  (`Expander.md` A4), not a band.
- **No surface.** `MACRO_LABELS = ()` (`:188`), `PATCHES = {0: ("Default", ())}`
  (`:190`); frequency, threshold, ratio, attack and release (`:192-193`) are
  construction-only, so a host cannot even move the split point.
- **No maximum.** The 902's Range bounds the effect at 20 dB; the class's
  `ratio=6.0` bounds nothing, so a loud sibilant on a quiet track can duck the
  whole signal.
- **Broadband only.** The 902's HF-only mode is the setting its own manual
  recommends for instrumental material; the class cannot do it, because it
  never splits the audio at all.

## 8. Open questions

1. **The law between 0 dB of excess and Range.** S1 gives the endpoints
   ("when the high frequency level is excessive … the 902 will de-ess", max
   20 dB) and no curve; the seed states D7's bound and D1's level-independence
   and deliberately claims nothing about the shape. Whether the rebuild uses a
   ratio, a soft knee or a straight map from excess to reduction is a design
   choice the implementation session makes and its evidence pack records — it
   is **not** a trait, because no source fixes it. *Implementation session.*
2. **Does the split belong in the audio path at all in broadband mode?** D3's
   broadband mode needs only a detector split; keeping the audio unsplit there
   saves the eight audio-path biquads D8 costs and removes any summing error
   entirely (there is nothing to sum). *Implementation session,
   with the Tier 3 measurement.*
3. **Which filter order the audio path ships.** §4 chooses LR4 for the audio
   path (to meet D8) and S1's two-pole for the detector (to meet D2). That is a
   design choice under vision D2, taken here rather than left implicit, and it
   doubles the audio-path biquad count. The implementation session may instead
   ship a single 12 dB/octave audio split and **strike D8**, recording the
   +3.01 dB crossover peak, or the null (A-D1), as the price — but it may not claim both.
   *Implementation session, with the Tier 3 measurement.*
4. **Whether N-DEESS-1 should be a `DYN_DEESS` mode or an option on
   `DYN_COMPRESS`.** The relative detector is useful beyond de-essing —
   RaneNote 155's relative-threshold dynamic EQ is the same mechanism, and
   `DynamicEQ` is a class in this library. *Phase 1 node design; the
   recommendation is an option, so `DynamicEQ` can use it too.*


## Appendix

Probes ran 2026-09-06 against the CPython build of audioif in
`audiocomponents/.venv`, 48 kHz, stereo, 16-bit. A4 (the side-chain's measured
6 dB/octave shape) and A5 (latency) are in `Expander.md`'s appendix.

**A8 — the shipped class's level dependence.** A probe holding a constant
spectral balance — a 200 Hz tone and a 6 kHz tone at equal amplitude —
rendered at three absolute levels through the current `DeEsser`'s own
construction (`DYN_COMPRESS`, threshold −30 dB, ratio 6, knee 3, attack
0.5 ms, release 60 ms, `sidechain_hz=5000`):

| input peak | reported gain reduction |
|---|---|
| −6 dBFS | **−10.57 dB** |
| −20 dBFS | −0.00 dB |
| −40 dBFS | 0.00 dB |

D1 allows 1 dB of variation across 60 dB of level. This measurement is also
the **planted fault for the class gate**: it already goes red on today's
build, so a green result after N-DEESS-1 lands means the trait was actually
reached rather than merely claimed.

**A-D1 — what a 12 dB/octave split sums to, derived this run.** RBJ biquads at
48 kHz, double precision, Q = 0.70710678, 4000 log-spaced points 20 Hz–20 kHz,
corner 2.5 kHz:

| pair | max | min |
|---|---|---|
| second-order Butterworth LP + HP, in phase | −0.0005 dB | **a null at 2500 Hz** — −66.93 dB on a 4000-point log grid, −96.47 dB on a 200 000-point one, i.e. grid-limited, not a finite depth |
| the same with the HP inverted | **+3.0103 dB** | +0.0005 dB |
| fourth-order Linkwitz-Riley (Butterworth squared) LP + HP | −0.0000 dB | −0.0000 dB |

This is why D2 and D8 are two rows and not one: S1's own 12 dB/octave filter
cannot carry a flat audio-path sum at any polarity, and the LR4 line is the
control that must *pass* beside every summed-response measurement (the habit
workspace-craft asks for). The same LR4 control is recorded independently at
`MultibandCompressor.md` A-M1.

**Method note.** Measure the split's summed response with **steady sines, not
an int16 impulse**: an impulse through this stack under-reads because a
filter's low-amplitude tail quantises away. A `HIGH_PASS` at 200 Hz measured
−0.86 dB of passband gain by impulse-FFT and −0.024 dB by steady sine; the
first number was the method's error, not the node's, and only running the
claim two ways caught it.

---

### Palette verification, 2026-09-06

Independent run against the CPython build of audioif in
`audiocomponents/.venv`, 48 kHz, stereo, 16-bit.

**V-D1 — the absolute threshold, reproduced.** `DYN_COMPRESS`, threshold
−30 dB, ratio 6, knee 3, `sidechain_hz=5000`, `attack_ms=0.5`,
`release_ms=60` — the shipped class's own settings. Material of a **fixed**
spectral balance (0.7 × 200 Hz + 0.3 × 6 kHz), rendered at three levels; peak
gain reduction over 80 blocks:

| input | −6 dBFS | −20 dBFS | −40 dBFS |
|---|---|---|---|
| gain reduction | **−7.25 dB** | 0.00 | 0.00 |

Different numbers from A8 (a different balance and probe length) and the same
result: identical sibilance content gets the class's whole range inside about
14 dB of input level, because `over = env_db − threshold_db`
(`audioif_dynamics.c:176`) compares the side-chain to a fixed number rather
than to the programme. This is S2's Fig. 12, and it is what N-DEESS-1 exists
to fix.

**V-D2 — LR2 does not sum flat and LR4 does, measured through the nodes.**
`Splitter → two Filter chains → Mixer`, corner 4 kHz, steady sines, output
relative to input:

| Hz | 500 | 1000 | 2000 | 2828 | 4000 | 5657 | 8000 | 16000 |
|---|---|---|---|---|---|---|---|---|
| one section a side (LR2) | −0.13 | −0.55 | −2.65 | −6.75 | **null** | −6.51 | −2.30 | −0.21 |
| two cascaded (LR4) | −0.00 | −0.00 | −0.00 | −0.00 | **−0.00** | −0.00 | −0.00 | −0.00 |

The LR2 corner is a true null — the summed output is all zeros. D8 needs the
LR4 audio path; D2's detector keeps S1's two-pole. The LR4 row is also the
control that shows this measurement can read flat, so the LR2 row is a real
red rather than a broken rig.

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

**Mono:** one gain from a channel-linked detector, applied to every channel; a
mono source gets identical processing. **Rate:** D2's split tops at 8 kHz,
below Nyquist at all three rates (11.025 kHz is the tightest), so the span
never clamps and D2 holds as stated — its skirt fit is taken at the 2.5 kHz
setting for exactly that reason, since two octaves above the 8 kHz end is
32 kHz and above Nyquist everywhere; D8's summing band is stated as
min(20 kHz, 0.45 × sample rate) for the same reason; D5's 600 µs attack is 29 samples at
48 kHz and 13 at 22.05 kHz, still resolvable. No Tier 2 trait is lost at a
lower rate.
**`capabilities` (D10): `()`** — sibilance has nothing to do with tempo.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** dbx, *902 de-Esser* owner's manual, part no. 18-2015-B, 4/30/96, served from Harman's own document CDN (`adn.harmanpro.com`) — *audit: the first run's "via the 302 from `dbxpro.com`" named no URL and could not be reproduced this run, `dbxpro.com` answering a direct request with HTTP 403; the CDN URL below is what was actually reached, twice* | Log-domain comparison, the no-threshold claim and the 60 dB span, the two-pole maximally flat 800 Hz–8 kHz split, 12 dB/octave phase-coherent filter type, RMS detection, Range 0–20 dB, the broadband/HF-ONLY Mode switch, program-dependent attack (2 ms at +10 dB, 600 µs at +20 dB, to 63 %), release 925 dB/sec, unity gain, −40 to +24 dBu operating span, CV at 50 mV/dB | **Licence unverified** — no copyright, trademark or terms line anywhere in the document (all 8 pages checked this run); it says only "This manual is part no: 18-2015-B 4/30/96", dbx Professional Products. Vision §5 treats an unfound licence as copyleft: read only, nothing reproduced or ported | <https://adn.harmanpro.com/product_documents/documents/502_1323992524/902%20Owners%20Manual_original.pdf> | yes — PDF fetched, text via `pypdf` |
| **S2** Jeffs, Holden & Bohn, *Dynamics Processors*, RaneNote 155 | "True de-essing involves comparing the relative difference between the troublesome sibilants and the overall broadband signal"; relative-threshold dynamic EQ named "the best dynamics processor for this task"; Fig. 11 (unaffected by level) against Fig. 12, the primitive side-chain-EQ de-esser that is "overly aggressive … during the loud choruses, and a completely ineffective result during the hissy, whispered verses"; split-band compression topology (Fig. 7) | PDF line "© 2005 Rane Corporation"; the site's Terms of Use (reached this run, <https://www.ranecommercial.com/legacy/terms-of-use.html>) is "Copyright © 2012-2018 inMusic Brands, Inc. All rights reserved." — personal, non-commercial viewing only, no redistribution without written permission. **Verified all-rights-reserved**, not "no further terms". Read only | <https://www.ranecommercial.com/legacy/pdf/ranenotes/Dynamics_Processors.pdf> | yes — PDF fetched, text via `pypdf` |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| D1 | **Threshold-free and level-independent.** One probe of fixed spectral balance, rendered at −6, −20, −40 and −55 dBFS, produces gain-reduction traces whose settled values agree within 1 dB — a 49 dB window, which is what 16-bit probe material carries; S1's claim is 60 dB, and the shortfall is the int16 floor of the kit, not the class, so a float render extends the window and is recorded if made | S1 ("de-essing of signals which change in level by as much as 60 dB"; "does not even have a threshold control"; "operates uniformly over input range of −40 dBu to +24 dBu"); S2 (Fig. 11) | high — stated twice in the manual and again in the spec table | Settled reduction differing by more than 1 dB between any two of the four levels; any level at which the reduction collapses to zero (the shape of S2's Fig. 12, and what A8 measures on the shipped class) | LEVEL |
| D2 | **The split point is settable 800 Hz–8 kHz and each half is maximally flat with a 12 dB/octave skirt**: with the split at 2.5 kHz each band is −3.0 ± 0.5 dB at the corner (Butterworth) and its skirt fits 12 ± 1.5 dB/octave over the octave-to-two-octaves band either side (625 Hz–1.25 kHz below, 5–10 kHz above — all below Nyquist at 22.05 kHz, so the fit is rate-honest), and the −3 dB corner tracks the Frequency control within 5 % at 800 Hz, 2.5 kHz and 8 kHz | S1 ("two-pole, maximally flat filter design … 800 Hz to 8 kHz"; "Filter Type: 12 dB/octave, phase coherent" — spelt "ocatve" in the original) | high — the manual's own filter description | A skirt outside 12 ± 1.5 dB/octave; a corner that does not move with the Frequency control; a corner at −6 dB (a Linkwitz-Riley alignment rather than the two-pole Butterworth S1 names) | SPLIT |
| D3 | **Two modes.** Driving 12 dB of reduction: in broadband mode both bands fall by 12 dB within 0.5 dB; in HF-only mode the high band falls by 12 dB within 0.5 dB while the low band moves less than 0.25 dB | S1 (Mode switch: "affect either the entire audio bandwidth, or the high frequencies only") | high | The low band moving more than 0.25 dB in HF-only mode; either band's reduction more than 0.5 dB from the commanded 12 dB; the two modes measuring within 0.25 dB of each other | SPLIT under reduction |
| D4 | **Release is linear in dB at a fixed rate**, not an exponential time constant: from 12 dB of reduction the recovery is a straight line in dB reaching 0 dB in 13.0 ms at the 902's specified 925 dB/sec, within 10 % | S1 ("Release Rate: 925 dB/sec") | high — a rate in dB/sec cannot be read as a time constant | A recovery whose dB trace curves, i.e. an exponential in linear gain | REL |
| D5 | **Attack is program-dependent**: the time to 63 % of final reduction shortens as the overshoot grows — about 2 ms at 10 dB over and 600 µs at 20 dB over, a ratio of ~3.3 within 25 % | S1 ("Attack Rate: Program-dependent, 2 ms for 10 dB above threshold, 600 µs for 20 dB above threshold, to achieve 63 % gain reduction") | high | One attack time independent of overshoot, which is what a fixed coefficient gives | ATT |
| D6 | **RMS detection**: a sine and a square of equal RMS in the high band, at the same spectral balance, produce the same reduction within 0.5 dB | S1 ("dbx patented RMS level detectors … sense level on the same basis as the human ear"); S2 | high | A ~3 dB difference, which is what a peak detector gives | XF |
| D7 | **Range bounds the reduction**, variable 0 to 20 dB: with the sibilant probe driven 20 dB past the sensitivity setting, the measured reduction stops at the Range setting within 0.5 dB at 5, 10 and 20 dB, and never exceeds it; on the low tone alone (no sibilant) the gain is unity within 0.1 dB | S1 ("Maximum 'Ess' Attenuation: Variable 0 to 20 dB"; "Gain: Unity") | high | Reduction exceeding the Range setting at any of the three; a settled reduction more than 0.5 dB from the setting under heavy drive; a resting gain more than 0.1 dB from unity on the no-sibilant probe | LEVEL (Range clause); SPLIT with the low tone alone (unity clause) |
| D8 | **The audio path sums flat.** With no sibilant present and both bands at unity, the summed magnitude is within 0.25 dB of flat from 20 Hz to min(20 kHz, 0.45 × sample rate). **This is the dossier's own criterion, not S1's** — S1 says "phase coherent" and prints no summed response — and it is *not* satisfiable by the 12 dB/octave pair D2 describes: an in-phase second-order Butterworth LP+HP pair has a true **null** at the corner (A-D1) and **+3.01 dB** there with one half inverted, while a fourth-order Linkwitz-Riley pair sums to 0.0000 dB (A-D1). The audio-path order is therefore a **design choice under vision D2** and §4 records it; D2 stays the sourced description of the 902's own filter and governs the **detector** split | derived and measured this run (A-D1); S3/S4 of `MultibandCompressor.md` for the LR alignment | high for the derivation, design choice for the bound | A summed magnitude beyond ±0.25 dB anywhere in the band; a null or a +3 dB peak at the crossover, which is what shipping D2's order in the audio path unmodified would give | SPLIT |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

*Licence and citation audit, 2026-09-06 — **two passes**. Second pass (unit
`gate-deesser-transient-multiband`): every URL above re-fetched from this
machine with `curl` (all HTTP 200), every PDF re-extracted with `pypdf` and
every quotation re-read against the document's own text, every licence line
read on the page that carries it, and every "not reached" claim re-tested.
Corrections are marked inline.*

*(from §2)*

No copyleft source was reached, so none was measured; no emulator was opened.
**Looked for and not found:** a **902 schematic or service manual** — none
found on dbx's own document host, which serves owner's manuals only; the
**dbx 904** manual fetched from the same CDN
(<https://adn.harmanpro.com/product_documents/documents/498_1323992363/904%20Owners%20Manual_original.pdf>,
HTTP 200, 12 pp.) yields zero extractable text on every one of its pages — a
scanned image, and this environment has no OCR. *Re-fetched and re-checked in
the audit run; the claim stands.*
**Unsourced, therefore absent from the trait table:** the 902's detector averaging time (the manual
says "dbx patented RMS level detectors" and gives no time constant); the shape
of the dB-difference-to-gain-reduction law between 0 and the Range maximum
(the manual gives the endpoints and no curve); and any claim about how the
902's Mode switch attenuates the high band — the manual states the *effect*,
not the topology.

*(from §3)*

Kit: **LEVEL** = one sibilant-shaped probe (a 200 Hz tone plus a 6 kHz tone at
a fixed amplitude ratio) rendered at −6, −20, −40 and −55 dBFS, gain-reduction
trace per block; **SPLIT** = steady sines at 1/6-octave spacing through the
split (**not** an impulse — see the Appendix's method note), band magnitudes,
their skirts fitted, and their sum, run both idle and under a commanded
reduction, and once with the low tone alone for the resting-gain clause; **REL** = a sibilant burst driving 12 dB of
reduction, then silence, gain trace at sample resolution; **ATT** = the same
burst at overshoots of 10 and 20 dB, time to 63 % of final reduction;
**XF** = sine and square of equal RMS in the high band.

*(from §3)*

No characters. D1 is the trait that makes this class a de-esser; the rest
describe the box that carries it. **Eight rows after the critic pass of
2026-09-06**, which split the first draft's D2 into the sourced filter
description (D2) and the summing criterion the dossier itself sets (D8), because
the two cannot both be met by one filter order.

*(from §3)*

Budget as a fraction of one stereo block's real-time deadline: ESP32-P4
**8 %**, ESP32-S3 **15 %**. Lean patch expected: **no** — one splitter, one
VCA and two detectors per frame, plus the biquads: **eight** in the audio path
(the LR4 split D8 needs, two cascaded sections per half per channel) and **two**
in the detector path (S1's own 12 dB/octave band, D2). *Critic pass, 2026-09-06:
the first draft counted four, from a single-order split that D8 shows cannot sum
flat. The P4/S3 fractions above are the seed's estimate and Station C measures
them; if the eight-biquad audio path pushes the S3 past its budget, the escape
valve is §8.2 — broadband mode needs no audio-path split at all.*

*(from §3)*

**Latency: zero, and no option adds any.** The 902 is a VCA under a detector;
nothing in S1 looks ahead, and the split is an IIR filter pair, which delays
phase but not the signal's onset. `latency_samples` is 0 at every setting and
the class ships **no look-ahead option** — a de-esser that ducked before the
"s" would be the fault the DS201 manual warns about in a different box. The
2 ms/600 µs attack of D5 is detector response, not latency, and is never
reported in `latency_samples`. Measured, `Dynamics` with look-ahead off
returns an impulse in the frame it arrived (`Expander.md` A5).

*(from §4)*

What does not compose is the detector, and it is the trait that matters.
`audiodynamics.Dynamics` has **one** detector and an **absolute threshold**
(`audioif_dynamics.c:176`), so a de-esser built on it is precisely S2's
Fig. 12. Measured on the shipped class's own settings: one probe with a fixed
200 Hz + 6 kHz balance produced **10.57 dB** of gain reduction at −6 dBFS,
**0.00 dB** at −20 dBFS and **0.00 dB** at −40 dBFS (A8). D1 allows 1 dB
across 60 dB; the shipped class spans its entire range in 14 dB. Three smaller
gaps come with it: the side-chain is one pole and 6 dB/octave, measured
(`Expander.md` A4), where D2 needs 12; the detector is a peak follower
(`:265`) where D6 needs RMS; and the release is a one-pole in linear gain
(`:303-305`) where D4 needs a constant dB/sec.

*(from §4)*

**Portability tier: audioif** (`audiodynamics`, `audioroute`;
`upstream-diff.md:661`) — guarded import, construction-time `ImportError` on a
stock board. Python computes the split coefficients at construction and on a
Frequency move; C runs the filters, the two detectors and the VCA per sample.

*(from §5)*

- **N-DEESS-1 — relative-threshold detection (unblocks D1).** A mode in which
  the gain computer's input is the **dB difference between the side-chain
  detector and a full-band detector**, with the front-panel control setting
  how many dB of excess is allowed rather than an absolute threshold. Palette:
  one detector against an absolute threshold; measured, 10.57 / 0.00 / 0.00 dB
  of reduction at −6 / −20 / −40 dBFS on identical spectral content (A8).
  **Refutation attempted and failed, and the reason is stronger than the first
  draft's.** The two detector levels can be read from two `Dynamics` nodes in
  Python via `gain_reduction_db()` — but a component has **nowhere to run that
  code**. The live surface is frozen (roadmap §3) and carries no per-block
  hook; the only entry points between pulls are the event methods, which the
  host calls when it likes, and *"pulling from `output` must not allocate,
  block, perform I/O, or depend on garbage collection"*
  (`docs/audio-component-api.md:231-233`). So the correction is not merely
  5.3 ms late and stepped through a `Mixer` level — it cannot be applied at
  all inside the contract. The ask stands, and it is the ask without which this
  class is the primitive de-esser S2 draws. *(Palette verification,
  2026-09-06.)*

*(from §5)*

- **N-DEESS-2 — a dB-linear release (unblocks D4).** `release_db_per_sec`
  beside `release_ms`, default unset so the exponential stays the default.
  Palette: `state->envelope += release_coef * (level − envelope)` in linear
  gain (`:303-305`). *Refutation:* a dB-linear ramp cannot be produced by a
  one-pole in linear gain at any coefficient — the shapes differ by
  construction, not by tuning — and cascading two such nodes multiplies two
  exponentials, whose dB sum is still not a straight line. Ask stands.
  *(Palette verification, 2026-09-06.)*

*(from §5)*

- **N-DEESS-3 — program-dependent attack (unblocks D5).** An attack
  coefficient scaled by the current overshoot, off by default. Palette: one
  fixed coefficient (`:69-71`). *Refutation:* rewriting `attack_ms` between
  blocks is 5.3 ms of granularity for a 600 µs event, and the contract gives
  the class no per-block hook to do it from (`audio-component-api.md:231-233`;
  see N-DEESS-1). Ask stands, at lower priority than N-DEESS-1.

*(from §5)*

- **N-DEESS-4 — RMS detection (unblocks D6).** *Same ask as `Expander`'s
  N-EXP-1; file once.* Palette verification, 2026-09-06: the follower is not
  fixed at peak — with `attack_ms` equal to `release_ms` it settles to a
  **mean-absolute** detector and the equal-RMS sine/square gap falls to
  **0.90 dB** (from 2.4–2.6 dB at the asymmetric settings this class uses).
  That is still nearly twice D6's allowance and it costs the independent
  attack and release the class needs, so the ask stands — but the gap to close
  is under 1 dB, not 3, which is worth knowing when the node is designed
  (`Expander.md` V-E1).

*(from §5)*

- **N-DEESS-5 — 12 dB/octave side-chain (unblocks D2's detector half).** Made
  redundant if N-DEESS-1 lands with a proper filtered detector input; recorded
  so the Phase 1 design considers them together rather than separately.
