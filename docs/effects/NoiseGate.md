# Effects Dossier — `NoiseGate` (Drawmer DS201)

**Class:** `lib/audioeffects/dynamics.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Dynamics, roadmap Phase 2
**Standout:** Drawmer DS201 *(proposed, vision §4.2)* — **confirmed without
reservation.** It is the right referent by the manufacturer's own claim, in
the manual reached this run: "These features and the DS201's user-friendliness
have helped it to become the worldwide 'industry standard' noise gate" (S1).
Unlike `Expander`, every trait this class needs is on the DS201's own panel;
no second source is needed for the law, only for the detector question (S2).
**Grade:** literature — the operator's manual gives every control range and
the envelope rule, and the traits below rest on it. *(Audit correction: two
Drawmer schematic sheets **were** reached in the audit run, as preview page
images — S5, §2. The grade stays literature under vision §4.1 because no trait
below is derived from them and no SPICE model or analytic derivation was made
from them; revisiting the grade is the implementation session's call.)*
**Portability tier:** needs audioif-own nodes (`audiodynamics`)
**Status:** seed (Phase 0), written 2026-09-06

## 1. The circuit, in one paragraph

Audio runs input → gain element → output, with a Bypass position on the output
selector that "routes the input signal to the output with no processing" (S1) —
neither manual edition names the gain element, but Drawmer's own service
documents do, and the audit run reached them: the schematic sheet is titled
"DS 201 (Fig.1) Audio and VCA Circuits" and the setting-up procedure probes the
"output of V.C.A. op. amp channel 1" (S5), so **the gain element is a VCA, and
that is now sourced**; no trait below rests on it. Everything the gate knows it
learns from a side-chain that never touches the sound. The key is the channel's own input or, on the Ext setting,
a separate jack, "making it possible to gate one sound according to the
dynamics of another"; it passes two variable filters in series — L.F. **25 Hz
to 4 kHz**, H.F. **250 Hz to 35 kHz**, so "it is the range between the two
settings that is allowed to pass" — and Key Listen sends that filtered
side-chain to the output for tuning, the manual noting it can simply be left
there to use the box as a filter (S1). A Threshold from **−54 dB to infinity**
(S1's 2005 edition; Drawmer's own current manual, S4, says "-50dBFs")
arms a four-stage envelope: **Attack 10 µs to 1 s** ("the fastest Attack time
ensures that the gate does not clip the leading edge of extremely fast
transients"), **Hold 2 ms to 2 s** — "the amount of time the gate is held open
after the signal falls below the Threshold … instrumental in creating the
classic gated reverb sound" — and **Decay 2 ms to 4 s**. The rule that makes
it a gate rather than a follower is stated in the Hold paragraph: "Since the
Hold cycle starts as soon as the Threshold is crossed, the envelope cycle will
complete even if the Key source falls below the Threshold level before the
Attack phase is completed" (S1). The closed state is not silence but
**Range**, "the amount of attenuation applied to the input signal when the
gate is closed, variable from 0 dB to −80 dB" (2005 edition; S4's 2008 manual
says "0dB - 90dB"), and the manual recommends about
−15 dB where full closure would make the noise floor's coming and going more
obvious than the noise. A Gate/Duck switch inverts the whole sense for
voice-overs. RaneNote 155 supplies the two general facts the panel cannot:
a gate "uses a fixed ratio of ∞:1 and a variable depth", and "like a limiter,
a gate must respond very quickly to changes in level, dictating the use of a
peak detector in the side-chain" (S2).

## 2. Sources and license calls

All fetched 2026-09-06; nothing from memory. No component value appears in
this seed because no schematic was reached.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Drawmer, *DS201 Dual Noise Gate Operator's Manual* … (App. S1) | Every control range in §1 … (App. S1) | The PDF carries no licence line … (App. S1) | <https://umlsrt.com/StudioDocuments/drawmer%20ds201%20manual.pdf> | yes — PDF fetched, text via `pypdf` |
| **S2** Jeffs, Holden & Bohn, *Dynamics Processors*, RaneNote 155 | The ∞:1-plus-depth law and gate block diagram (Figs. … (App. S2) | PDF line "© 2005 Rane Corporation" … (App. S2) | <https://www.ranecommercial.com/legacy/pdf/ranenotes/Dynamics_Processors.pdf> | yes — PDF fetched, text via `pypdf` |
| **S3** Drawmer, DS201 product page | Feature list and audio specs … (App. S3) | Footer: "Copyright © 2026 All rights … (App. S3) | <https://www.drawmer.com/products/pro-series/ds201.php> | yes — HTML; this host answers WebFetch with HTTP 429, so the audit fetched it directly (HTTP 200) |
| **S4** Drawmer, *DS201 Operator's Manual* … (App. S4) | The same control descriptions … (App. S4) | "This manual is copyrighted © 2008 by Drawmer … (App. S4) | <https://www.drawmer.com/uploads/manuals/ds201_operators_manual.pdf> | yes — PDF fetched (HTTP 200, 14 pp.), text via `pypdf`; **added by the audit run**, where the first run had recorded this URL as unreachable |
| **S5** Drawmer, *DS201 Service Information* (7 pp.) and *DS201 Comp … (App. S5) | Two legible hand-drawn Drawmer sheets with component … (App. S5) | The drawings are Drawmer's … (App. S5) | <https://elektrotanya.com/drawmer_ds201_comp_sch.pdf/download.html> (preview images under `/PREVIEWS/63463243/23432455/drawmer/`) | yes — preview images fetched (HTTP 200) and read; the full PDFs were **not** obtained. Added by the audit run |
| **Local** `audioif/src/shared/audioif_dynamics.{c,h}`, `audioif/docs/upstream-diff.md`, the probes in the Appendix | What the palette's gate actually does | MIT (audioif) | — | yes |

*Second-pass result: licence calls S1–S4 stand as written; S5 added; the "no
schematic" and "VCA unsourced" findings overturned; one flag on G2.*

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| G1 | **The envelope is one-shot.** Once the key crosses the threshold the attack runs to full open even if the key falls back below threshold first — a 1 ms key burst under a 200 ms attack still reaches 0 dB of attenuation | S1, verbatim ("the envelope cycle will … (App. G1) | high — stated as a … (App. G1) | The gate not reaching full open, or opening only in proportion to the burst's length | ONESHOT |
| G2 | **Hold is a real stage**, variable 2 ms–2 s, timed from the key falling below threshold; through it the gain sits at 0 dB and only then does the decay begin, so the measured open time equals attack + hold + decay within 10 % | S1 (Hold description) … (App. G2) | high | Decay starting at the threshold crossing, or an open time that tracks attack + decay alone | ENV |
| G3 | The key path is a **band**: low cut settable 25 Hz–4 kHz, high cut 250 Hz–35 kHz (clamped below Nyquist), and with the band set to 500 Hz–2 kHz a tone an octave outside either end, swept from −60 dBFS to 0 dBFS, moves the gain less than 1 dB off the Range floor at every level; Key Listen puts that band on the output | S1 (L.F., H.F., Key Listen) | high | An out-of-band tone at any level up to full scale moving the gain more than 1 dB off the floor; a gate that opens fully as an out-of-band tone is raised. *(Two clauses of the first draft are struck as unsourced: "a skirt shallower than 12 dB/oct at either end" — neither source states the key filters' order, which is a design choice, §5 — and "at any level", which is unbounded and therefore unfalsifiable; the level span the kit actually drives is named instead. **Critic pass, 2026-09-06.**)* | KEY |
| G4 | **The closed state is Range, not zero**: with the input 30 dB below threshold at −6 dBFS, the settled closed gain equals the Range setting within 0.5 dB at 0, −20, −40 and −60 dB, and the control's full span reaches at least −80 dB (S1's 2005 edition; S4's 2008 manual says "0dB - 90dB"). The law is a fixed depth, not a slope: two inputs 10 dB apart, both at least 20 dB below threshold, get the same gain within 0.5 dB | S1 (Range); S2 ("a gate uses a fixed ratio of … (App. G4) | high | A settled closed gain more than 0.5 dB from the setting at any of the four; a closed gain that tracks the input level, i.e. a finite slope (the shipped node's ~8 dB per dB, A1); a span that stops short of −80 dB | LAW at four Range settings |
| G5 | **Attack spans 10 µs to 1 s and decay 2 ms to 4 s**: at settings 1, 10, 100 and 1000 ms of attack and 10, 100, 1000 and 4000 ms of decay the measured 10–90 % transition is within 15 % of the setting, and at the fast end (settings below one sample period, 20.8 µs at 48 kHz) the open transition is one sample or less | S1 (Attack, Decay) | medium — panel … (App. G5) | A measured transition more than 15 % from the setting at any of the eight; a fastest attack longer than one sample; a slowest decay whose measured 10–90 % time is under 3.4 s (15 % short of 4 s) | ENV |
| G6 | **Peak detection**: a sine and a square of **equal peak** open the gate at thresholds within 0.5 dB of each other, while the same pair at **equal RMS** open at thresholds about 3.0 dB apart (the square's crest advantage); and with attack at its fastest a burst whose peak crosses the threshold reaches full open within one cycle of its own fundamental | S2 ("a gate must respond very quickly to … (App. G6) | medium — general to … (App. G6) | Equal-**RMS** material of different crest factors opening at the same threshold, which is what RMS detection gives; or an equal-peak pair whose opening thresholds differ by more than 0.5 dB. *(Critic pass, 2026-09-06: the first draft's leading clause — first-cycle opening — was measured by LAW, a steady staircase that cannot see it. The clause is kept and given ENV; the equal-peak/equal-RMS pair is what LAW measures.)* | LAW with sine and square … (App. G6) |
| G7 | **Duck mode inverts the sense**: with Duck selected, gain is 0.00 ± 0.05 dB below threshold and settles at the Range setting within 0.5 dB above it, on the same attack/hold/decay envelope — the measured open time obeys G2's attack + hold + decay within 10 % in Duck as in Gate | S1 (Gate/Duck); S3 | high | A settled ducked gain more than 0.5 dB from the Range setting; a resting gain other than unity below threshold; an envelope that ignores Hold in Duck | ENV |

No characters: gate and duck are one mechanism under a switch, and G7 states
the switch. G3–G5 are shared with `Expander` and must be demonstrated
separately in each class's own evidence pack.

### Tier 3 — cost and latency

Budget as a fraction of one stereo block's real-time deadline: ESP32-P4
**6 %**, ESP32-S3 **12 %**. Lean patch expected: **no**.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

`audiodynamics.Dynamics(DYN_GATE)` gives a per-sample peak follower, settable
attack and release, and a VCA — the audio path and G6 for free, and G7 with two
more nodes (§5). G1–G5 are out of reach, and each gap is measured, not argued:

- **G1** — the follower has no trigger state: it is two coefficients and a …  *(argument in full: App. R)*
- **G2** — there is no hold anywhere in the file; the envelope falls the
  instant `level` drops below it (`:302`).
- **G3** — `sidechain_hz` is one pole and one end, measured at 6.0/5.9/5.6 dB
  per octave with the corner at the set frequency, and there is no key input
  (`Expander.md` A4).
- **G4** — the gate law is a *slope*, not a depth: `cut = over * 8.0f` clamped …  *(argument in full: App. R)*
- **G7** — there is no duck mode in the enum (`audioif_dynamics.h:21-27`), but …  *(argument in full: App. R)*

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

All additive on `audiodynamics` (D1), each defaulting to today's behaviour so
`dynamics_probe.py`'s hash is unchanged — the discipline `upstream-diff.md:837`
records for this node's last two options.

- **N-GATE-1 — a gate envelope with hold and a committed attack (unblocks G1, …  *(argument in full: App. R)*
- **N-GATE-2 — a settable depth (unblocks G4).** `depth_db`, default −80 for …  *(argument in full: App. R)*
- **N-GATE-3 — a two-ended key band and an external key (unblocks G3).** …  *(argument in full: App. R)*
- **N-GATE-4 — duck mode (unblocks G7).** A fifth mode, or a `duck=True` …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Eleven macros; UNIPOLAR except the three toggles.

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Threshold | UNIPOLAR | −80 … 0 dB | DS201 Threshold (−54 dB … ∞) |
| 1 | Attack | UNIPOLAR | 0.01 … 1000 ms, log | DS201 Attack (10 µs … 1 s) |
| 2 | Hold | UNIPOLAR | 2 … 2000 ms, log | DS201 Hold |
| 3 | Release | UNIPOLAR | 2 … 4000 ms, log | DS201 Decay |
| 4 | Range | UNIPOLAR | 0 … −80 dB | DS201 Range |
| 5 | Key Low | UNIPOLAR | 25 … 4000 Hz, log | DS201 L.F. |
| 6 | Key High | UNIPOLAR | 250 Hz … Nyquist, log | DS201 H.F. |
| 7 | Key Listen | TOGGLE | off / on | DS201 Key Listen |
| 8 | Duck | TOGGLE | gate / duck | DS201 Gate/Duck |
| 9 | Lookahead | UNIPOLAR | 0 … 2 ms | no panel control; S2's technique, default 0 |
| 10 | Hysteresis | UNIPOLAR | 0 … 12 dB | no panel control and **no source** — see §8; ships only if §8.2 finds one |

Characters: none. Patches: **Tom Tighten**, **Gated Reverb** (long hold, fast
decay), **Vocal Breath Trim** (shallow Range, wide key), **Amp Hiss** (key
2–8 kHz, −80 Range), **Voice Over Duck**, **Drum Bleed** (key 100 Hz–1 kHz,
short hold). Key Listen is a diagnostic and is off in every patch; Lookahead
is 0 in every patch except **Kick First Cycle**, which sets 0.33 ms and says
so in its name-adjacent docstring line.

## 7. Defects in the current class the rebuild must not repeat

- **No surface, and no docstring at all.** `MACRO_LABELS = ()` at
  `dynamics.py:167`, `PATCHES = {0: ("Default", ())}` at `:169`, and the class
  body at `:161-177` carries no docstring — the only dynamics class without
  one. Threshold, attack and release (`:170-171`) are construction-only.
- **No Range**, so the class inherits the node's fixed −80 dB clamp and cannot
  offer the −15 dB setting S1 recommends for exactly the case a gate is most
  often used in.
- **No hold**, so the gate cannot make the gated-reverb sound the DS201's own
  manual names as a headline use.
- **The gate law is a slope and nothing says so.** A caller reading "noise
  gate" gets ~8 dB of attenuation per dB below the knee (A1), which is an
  expander at ratio 9, not a gate.
- **The threshold default is −50 dB** (`:170`) with no key filter, so on any
  real source the gate chatters on hum and hiss it cannot be told to ignore.

## 8. Open questions

1. **Does N-GATE-1's state machine belong in `audiodynamics` or in a new
   audioif-own node?** It is a bigger change than the last two options this
   node took. *Phase 1 node design; the recommendation here is inside
   `audiodynamics`, because it shares the detector, the side-chain and the
   VCA.*
2. **Hysteresis.** Every practitioner's account of gates names it and **no
   source reached this run states a figure for any unit**, the DS201 included.
   Macro 10 is provisional and ships only if Phase 0 or the implementation
   session reaches a source; otherwise it is struck and the seed records why.
   *Implementation session, Phase 2, with a source or not at all.*
3. **Whether Key Listen belongs on a component's macro surface** or is a
   diagnostic the host should reach another way — it changes what the output
   *is*, which no other macro in this library does. *Implementation session.*
4. **The DS201 schematic** exists on elektrotanya and was not obtained. No
   trait depends on a component value, so this is a note for the survey.
   *Arthur.*


## Appendix

Probes ran 2026-09-06 against the CPython build of audioif in
`audiocomponents/.venv`, 48 kHz, stereo, 16-bit. A1 and A4–A6 are recorded in
full in `Expander.md`'s appendix and are not repeated; the numbers this seed
leans on are:

**A1 — the palette's gate law (`DYN_GATE`, threshold −40 dB, 1 kHz sine).**
Output-minus-input in dB. Gain is 0 until the *peak* crosses threshold (RMS
−42.01 dBFS = peak −39.0), then −2.26, −10.26, −18.47 at 1, 2 and 3 dB
further down and −45.31 at 6 dB down: about 8 dB per dB, matching
`cut = over * 8.0f`. Below −50 dBFS RMS the int16 output is exactly zero —
quantisation, not the −80 dB clamp, and a reminder that "the output is silent"
is not evidence the gate closed.

**A6 — the one-shot rule refuted on the palette.** A 1 ms full-scale burst then
silence into `DYN_GATE`, threshold −40 dB, `attack_ms=200`: the reported gain
stayed at −80.00 dB for all 90 blocks rendered. This is the planted-fault
shape the class gate needs — a measurement that already goes red on today's
node, so a green result after N-GATE-1 lands means something.

**A7 — chatter, and what the probe could not show.** A 1 kHz tone whose level
wobbled ±6 dB at 4 Hz around a −36 dB threshold opened the gate exactly 4
times in 1.0 s with the gain ranging −68.1 to 0.0 dB. That is *correct*
behaviour on clean material and therefore **not** a chatter demonstration: a
hysteresis or hold trait needs material whose level crosses the threshold many
times per open — noise, or a decaying tail — and the kit's chatter probe must
be specified that way or it will pass on everything.

---

### Palette verification, 2026-09-06

Independent run against the CPython build of audioif in
`audiocomponents/.venv`, 48 kHz, stereo, 16-bit.

**V-G1 — the palette has a retriggerable per-sample VCA.**
`audiomath.Multiply(source=<audio>, modulator=<synthio.Synthesizer>, mix=1.0)`
with one note carrying a 64-sample constant waveform and
`synthio.Envelope(attack_time=0.05, release_time=0.05, sustain_level=1.0)`.
Pressing at block 4 and releasing at block 20, the per-block gain of the
Multiply output relative to its input, in dB:

```
blocks 0-3  : silent
blocks 4-12 : -25.6 -19.4 -15.9 -13.5 -11.4 -9.9 -8.7 -7.3 -6.3
blocks 13-20: -6.1 -6.0 -6.0 -6.1 -6.0 -6.0 -6.1 -6.0   (sustain plateau)
blocks 21-29: -7.0 -8.2 -9.3 -10.8 -12.8 -14.8 -17.9 -22.8 -33.9
blocks 30+  : silent
```

A smooth attack, a flat hold and a smooth release, all per sample — no
block-rate step. (The plateau sits 6 dB down because synthio's note amplitude
defaults to half scale; a `Note(amplitude=…)` or the mixer level corrects it.)
This is the fact that kills the first draft's reason for N-GATE-1. What it does
not give is a trigger: `press()`/`release()` are Python calls, and the contract
gives a component no per-block hook to make them from
(`docs/audio-component-api.md:231-233`).

**V-G2 — duck by composition (the N-GATE-4 refutation).** Graph:
`RawSample → Mixer(guard) → Splitter(taps=2)`; tap 0 →
`Dynamics(DYN_GATE)` → `Multiply(modulator = constant −32768, mix=1.0)`;
tap 1 → dry; both into a two-voice `Mixer` at levels 1.0 and `1 − Range`.

- Inverter check: 512 frames of a 1 kHz sine at 0.5 amplitude,
  `max |out + in| = **0 LSB**` — an exact sign flip, as
  `(a · −32768) >> 15 = −a` predicts (`audioif_multiply.c:38`).
- Gate open (threshold −60 dB, loud signal): duck output **all zeros**.
- Gate shut (threshold 40 dB above the signal): duck output **−0.00 dB** —
  bit-for-bit the input.
- With a Range setting: below threshold −0.000 dB at every setting; above
  threshold −6.00, −10.00, −20.00, −39.97 and −59.70 dB for Range settings of
  −6, −10, −20, −40 and −60 dB.
- Programme material (a 440 Hz burst for 8000 frames, then the same tone
  34 dB down), threshold −20 dB: **exact silence** through the burst,
  **−41.29 dBFS** afterwards, matching the source's own −41.29 dBFS.

**V-G3 — the mixer cannot invert, which is why the first draft's refutation
looked right.** `synthio_block_slot_get_limited(&voice->level, 0.0, 1.0)`
(`src/audiomixer/Mixer.c:332`) clamps a voice level to 0…1 before the Q15
multiply, so a negative level is silently zero. The inversion has to come from
`audiomath.Multiply`.

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

**Mono:** one gain from a channel-linked detector applied to every channel, so
a mono source gets identical processing; the DS201's Stereo Link is what the
class does by default and its unlinked mode is out of scope for a single
component. **Rate:** G3's key span tops at 35 kHz, above Nyquist at every rate
here; it clamps (Tier 1) and G3 is stated against the clamped top. **G5's**
10 µs attack (audit: the first draft wrote G1 here; the attack span is G5) is
0.48 of a sample at 48 kHz and 0.22 at 22.05 kHz — the trait is stated as "one
sample or less", which holds at every rate.
**`capabilities` (D10): `()`.** A gated-reverb hold in bars is tempting and
neither source's box has one; the class does not read the transport.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Drawmer, *DS201 Dual Noise Gate Operator's Manual* (manufacturer's text, from `drawmer.com/op201.htm`, 7 pp.) | Every control range in §1, the envelope-completion rule, the Range advice and the −15 dB recommendation, Gate/Duck, Ext key, Key Listen, Stereo Link, the click-on-fast-attack passage, the HF-filter trigger-delay note | The PDF carries no licence line; its header prints `http://www.drawmer.com/op201.htm`, 31 Jan 2005 — Drawmer's own page on a third-party mirror (UMass Lowell SRT, whose only notice, "Copyright © 2026 UML SRT", covers the mirror, not the text). Chased to the rights holder: Drawmer's own manual (S4) says it "may not be duplicated in whole or in part without the written consent of Drawmer" — **verified all-rights-reserved**. Read as a document, nothing reproduced | <https://umlsrt.com/StudioDocuments/drawmer%20ds201%20manual.pdf> | yes — PDF fetched, text via `pypdf` |
| **S2** Jeffs, Holden & Bohn, *Dynamics Processors*, RaneNote 155 | The ∞:1-plus-depth law and gate block diagram (Figs. 17a/b); peak detection for gates; hold 0–3 s, depth 0 to −80 dB; the look-ahead and pre-ramping numbers (96 samples = 2 ms at 48 kHz, 16 samples = 333 µs reproduces ≥750 Hz, "look-ahead one quarter of a cycle"); the measured 16 dB of above-10 kHz energy a step-opened gate adds | PDF line "© 2005 Rane Corporation"; the site's Terms of Use (reached this run, <https://www.ranecommercial.com/legacy/terms-of-use.html>) is "Copyright © 2012-2018 inMusic Brands, Inc. All rights reserved." — personal, non-commercial viewing only, no redistribution without written permission. **Verified all-rights-reserved**, not "no further terms". Read only | <https://www.ranecommercial.com/legacy/pdf/ranenotes/Dynamics_Processors.pdf> | yes — PDF fetched, text via `pypdf` |
| **S3** Drawmer, DS201 product page | Feature list and audio specs; confirms Gating/Ducking, the external key and Key Listen | Footer: "Copyright © 2026 All rights reserved. Drawmer Electronics Ltd." — **verified all-rights-reserved**, not merely unstated. Read only | <https://www.drawmer.com/products/pro-series/ds201.php> | yes — HTML; this host answers WebFetch with HTTP 429, so the audit fetched it directly (HTTP 200) |
| **S4** Drawmer, *DS201 Operator's Manual*, the manufacturer's own current edition, 14 pp. | The same control descriptions, and **two values that differ from S1's 2005 capture**: Threshold "-50dBFs - infinate" and Range "0dB - 90dB". Also an explicit copyright line, and a block diagram on p. 14 (an image, not extracted) | "This manual is copyrighted © 2008 by Drawmer Electronics, Ltd. With all rights reserved. Under copyright laws, this manual may not be duplicated in whole or in part without the written consent of Drawmer." Read only | <https://www.drawmer.com/uploads/manuals/ds201_operators_manual.pdf> | yes — PDF fetched (HTTP 200, 14 pp.), text via `pypdf`; **added by the audit run**, where the first run had recorded this URL as unreachable |
| **S5** Drawmer, *DS201 Service Information* (7 pp.) and *DS201 Comp Sch* (3 pp.) — the manufacturer's own service documents, reached as `elektrotanya.com`'s own preview page images (first two pages of each) | Two legible hand-drawn Drawmer sheets with component values: "DS 201 (Fig.1) Audio and VCA Circuits" (signal and key inputs, Int/Ext key source, Threshold, Range, By-Pass/Key Listen, control voltage, "All Op. Amps. TL072 or LF353") and "DS 201 (Fig. 2) Rectifier. Attack, Hold, Decay Circuits"; and a setting-up procedure naming the "output of V.C.A. op. amp channel 1" and a "F.e.t. bias pre-set". **Used here for one fact only: the gain element is a VCA.** | The drawings are Drawmer's, under S4's all-rights-reserved notice; the host's own terms read "Please do not offer the downloaded file for sell only use it for personal usage" — **personal use only**. Read as a document (vision §5); nothing reproduced, no component value carried into a trait | <https://elektrotanya.com/drawmer_ds201_comp_sch.pdf/download.html> (preview images under `/PREVIEWS/63463243/23432455/drawmer/`) | yes — preview images fetched (HTTP 200) and read; the full PDFs were **not** obtained. Added by the audit run |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| G1 | **The envelope is one-shot.** Once the key crosses the threshold the attack runs to full open even if the key falls back below threshold first — a 1 ms key burst under a 200 ms attack still reaches 0 dB of attenuation | S1, verbatim ("the envelope cycle will complete even if the Key source falls below the Threshold level before the Attack phase is completed") | high — stated as a rule, in the manual's own Note | The gate not reaching full open, or opening only in proportion to the burst's length | ONESHOT |
| G2 | **Hold is a real stage**, variable 2 ms–2 s, timed from the key falling below threshold; through it the gain sits at 0 dB and only then does the decay begin, so the measured open time equals attack + hold + decay within 10 % | S1 (Hold description); S2 (hold "typical range of 0 to 3 seconds") | high | Decay starting at the threshold crossing, or an open time that tracks attack + decay alone | ENV |
| G3 | The key path is a **band**: low cut settable 25 Hz–4 kHz, high cut 250 Hz–35 kHz (clamped below Nyquist), and with the band set to 500 Hz–2 kHz a tone an octave outside either end, swept from −60 dBFS to 0 dBFS, moves the gain less than 1 dB off the Range floor at every level; Key Listen puts that band on the output | S1 (L.F., H.F., Key Listen) | high | An out-of-band tone at any level up to full scale moving the gain more than 1 dB off the floor; a gate that opens fully as an out-of-band tone is raised. *(Two clauses of the first draft are struck as unsourced: "a skirt shallower than 12 dB/oct at either end" — neither source states the key filters' order, which is a design choice, §5 — and "at any level", which is unbounded and therefore unfalsifiable; the level span the kit actually drives is named instead. **Critic pass, 2026-09-06.**)* | KEY |
| G4 | **The closed state is Range, not zero**: with the input 30 dB below threshold at −6 dBFS, the settled closed gain equals the Range setting within 0.5 dB at 0, −20, −40 and −60 dB, and the control's full span reaches at least −80 dB (S1's 2005 edition; S4's 2008 manual says "0dB - 90dB"). The law is a fixed depth, not a slope: two inputs 10 dB apart, both at least 20 dB below threshold, get the same gain within 0.5 dB | S1 (Range); S2 ("a gate uses a fixed ratio of ∞:1 and a variable depth") | high | A settled closed gain more than 0.5 dB from the setting at any of the four; a closed gain that tracks the input level, i.e. a finite slope (the shipped node's ~8 dB per dB, A1); a span that stops short of −80 dB | LAW at four Range settings |
| G5 | **Attack spans 10 µs to 1 s and decay 2 ms to 4 s**: at settings 1, 10, 100 and 1000 ms of attack and 10, 100, 1000 and 4000 ms of decay the measured 10–90 % transition is within 15 % of the setting, and at the fast end (settings below one sample period, 20.8 µs at 48 kHz) the open transition is one sample or less | S1 (Attack, Decay) | medium — panel ranges, no measured curves in the sources | A measured transition more than 15 % from the setting at any of the eight; a fastest attack longer than one sample; a slowest decay whose measured 10–90 % time is under 3.4 s (15 % short of 4 s) | ENV |
| G6 | **Peak detection**: a sine and a square of **equal peak** open the gate at thresholds within 0.5 dB of each other, while the same pair at **equal RMS** open at thresholds about 3.0 dB apart (the square's crest advantage); and with attack at its fastest a burst whose peak crosses the threshold reaches full open within one cycle of its own fundamental | S2 ("a gate must respond very quickly to changes in level, dictating the use of a peak detector") | medium — general to gates, not stated of the DS201 | Equal-**RMS** material of different crest factors opening at the same threshold, which is what RMS detection gives; or an equal-peak pair whose opening thresholds differ by more than 0.5 dB. *(Critic pass, 2026-09-06: the first draft's leading clause — first-cycle opening — was measured by LAW, a steady staircase that cannot see it. The clause is kept and given ENV; the equal-peak/equal-RMS pair is what LAW measures.)* | LAW with sine and square, at equal peak and at equal RMS; ENV for the first-cycle clause |
| G7 | **Duck mode inverts the sense**: with Duck selected, gain is 0.00 ± 0.05 dB below threshold and settles at the Range setting within 0.5 dB above it, on the same attack/hold/decay envelope — the measured open time obeys G2's attack + hold + decay within 10 % in Duck as in Gate | S1 (Gate/Duck); S3 | high | A settled ducked gain more than 0.5 dB from the Range setting; a resting gain other than unity below threshold; an envelope that ignores Hold in Duck | ENV |

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
**Partly found, by the licence audit:** `elektrotanya.com` lists
`drawmer_ds201_sm.pdf` (7 pages) and `drawmer_ds201_comp_sch.pdf` (3 pages) and
serves the **first two pages of each as preview images**. The audit run fetched
and read all four, and two are legible Drawmer schematic sheets with component
values — cited as S5 above. The full PDFs were not obtained, so the third
schematic page and the rest of the service manual remain unread. *Corrected by
the audit: the first run recorded the schematic as not obtained and "VCA" as
unsourced; both are now wrong. It also described both entries as one 7-page
document — only the service manual is.* Drawmer's own manual (S4) prints a block
diagram, not a schematic. *Also corrected by the audit: the first run recorded
`drawmer.com`'s own manual PDF as unreachable (HTTP 429); that host answers
WebFetch with 429 (re-confirmed this run) but serves a direct request
(HTTP 200), and the manual is cited as S4.*
**Unsourced, therefore absent from the trait table:** any
DS201 hysteresis figure — neither manual edition uses the word, and later
Drawmer boxes are not this one; and any statement about whether the DS201's
own detector is peak or RMS, which S1 never says (G6 rests on S2's general
claim, not on the DS201). *Audit note on the second: S5's second sheet is
titled "Rectifier. Attack, Hold, Decay Circuits", so a drawing of the detector
now exists in reach — but the audit derived nothing from it, and G6 stays
sourced to S2 until someone does.*

*(from §3)*

Kit: **ENV** = burst-then-silence, per-block gain trace; **ONESHOT** = a 1 ms
key burst under a long attack; **LAW** = 1 kHz steady-sine staircase, 1 dB
steps, output RMS per step; **KEY** = swept sine at fixed amplitude,
gain-reduction trace; **CLICK** = the gate opened onto a 100 Hz sine with the
threshold at 80 % of peak, spectrum of the output above 10 kHz.

*(from §3)*

**Audit flag on G2.** S1 states the Hold timing twice and the two statements
disagree: the Hold control description says Hold is "the amount of time the gate
is held open after the signal falls below the Threshold" (G2's reading), while
the Note two paragraphs later says "the Hold cycle starts as soon as the
Threshold is crossed". G1 quotes the rest of that same Note and is unaffected.
The implementation session picks a reading for G2's origin and records which.

*(from §3)*

**Latency: zero by default.** The DS201 has no look-ahead — no source reached
describes one, and its Bypass "routes the input signal to the output with no
processing" — so `latency_samples` is 0 and G1–G7 are all stated at zero latency.
One option adds latency and **defaults off**: RaneNote 155 argues that
"superior gating requires look-ahead and pre-ramping", and gives the numbers a
default must respect — a look-ahead of 16 samples (333 µs at 48 kHz)
"allow[s] accurate reproduction of signals at or above 750 Hz", 96 samples
(2 ms) is "somewhere around" the live-sound limit, and the rule is to look
ahead one quarter of a cycle of the lowest frequency to be preserved (S2).
So: **`lookahead_ms` defaults to 0**; when set, the smallest useful value is
16 samples and the class reports it in `latency_samples` the moment it is
turned on and names it in milliseconds in the docstring. The knob that trades
CPU for latency here is not CPU at all but low-frequency fidelity, and the
docstring says so. Measured, `Dynamics` with look-ahead off returns an impulse
in the frame it arrived; at `lookahead_ms=5.0` it returns 240 frames later,
exactly 5.00 ms (A5 in `Expander.md`).

*(from §4)*

- **G1** — the follower has no trigger state: it is two coefficients and a
  one-pole (`audioif_dynamics.c:302-307`). Measured, a 1 ms full-scale burst
  under `attack_ms=200` left the reported gain pinned at −80.00 dB for all 90
  blocks rendered; **the gate never opened at all** (`Expander.md` A6).

*(from §4)*

- **G4** — the gate law is a *slope*, not a depth: `cut = over * 8.0f` clamped
  at −80 (`audioif_dynamics.c:191-192`). Measured, gain falls −2.26, −10.26,
  −18.47 and −45.31 dB at 1, 2, 3 and 6 dB below the knee — about 8 dB of
  attenuation per dB of input, where G4 requires a flat floor (A1). *(Partly
  composable: the slope clamps at −80 dB within 10 dB of threshold, and a dry
  blend through `Mixer` sets a flat floor per sample from 0 to −50 dB within
  0.2 dB. It stops there — see §5's N-GATE-2 and `Expander.md` V-E4.)*

*(from §4)*

- **G7** — there is no duck mode in the enum (`audioif_dynamics.h:21-27`), but
  the trait is reachable without one: `Multiply` against a constant −32768
  modulator inverts exactly, so `dry − gated` is a duck. Measured to 0.03 dB of
  the Range setting above threshold and 0.000 dB below it (V-G2). §5 records
  the refutation.

*(from §4)*

**Composition was tried again in the palette verification of 2026-09-06, and
the first draft's reason for failure was wrong.** It said "the only per-sample
gain on the palette is `audiomath.Multiply`, whose modulator is a looping
table, not an envelope the class can retrigger." `Multiply`'s modulator is any
audiosample (`Multiply.c:55-63`, `:86-97`), including a live
`synthio.Synthesizer`, and a note carrying a constant waveform and a
`synthio.Envelope` renders a **retriggerable per-sample envelope as a stream**
— measured, that graph gives a smooth click-free VCA that opens over its
attack, holds, and closes over its release (V-G1). The palette has the gain
element a gate needs.

*(from §4)*

What it does not have is anywhere to take the *decision*. The trigger would
have to come from Python reading `gain_reduction_db()`, and a component has no
per-block hook to run that in: the live surface is frozen (roadmap §3) and
*"pulling from `output` must not allocate, block, perform I/O, or depend on
garbage collection"* (`docs/audio-component-api.md:231-233`). Even given a
hook, the decision would be quantised to a 256-frame block — 5.3 ms — which
misses G6's "full open within one cycle of its own fundamental" for anything
above about 190 Hz and puts a floor of 5.3 ms under G2's 2 ms hold. So the
rebuild's shape is still **one `Dynamics` node with a real gate envelope behind
it**, and the asks in §5 are what make that node a gate — but the reason is the
trigger, not the VCA.

*(from §4)*

**Portability tier: audioif** — `audiodynamics` is audioif's own module, not a
CircuitPython port (`audioif/docs/upstream-diff.md:661`); the class carries the
guarded import and a construction-time `ImportError` on a stock board. Python
computes coefficients at construction and on a macro move; C runs the
follower, the envelope stage machine and the VCA per sample.

*(from §5)*

- **N-GATE-1 — a gate envelope with hold and a committed attack (unblocks G1,
  G2, G5).** A four-stage state machine — closed / attack / hold / decay —
  with `hold_ms` (default 0) and attack committed on the threshold crossing
  (default off, so today's follower is the default). Palette: a plain one-pole
  follower; measured, a 1 ms burst under a 200 ms attack never opens the gate
  (`Expander.md` A6, re-measured this run as −80.00 dB across all 90 blocks,
  `Expander.md` V-E2), and there is no hold at all. *Refutation, re-run
  2026-09-06 and corrected:* the palette **does** have a retriggerable
  per-sample VCA — `audiomath.Multiply` modulated by a `synthio.Synthesizer`
  note with a constant waveform and an envelope, measured smooth and click-free
  (V-G1) — so the first draft's reason ("a looping table with no retrigger")
  is wrong. What the palette lacks is the trigger: a component has no per-block
  hook to run the decision in (`docs/audio-component-api.md:231-233`; roadmap
  §3 freezes the live surface), and even given one the decision quantises to
  5.3 ms, which misses G6's one-cycle opening above ~190 Hz and floors G2's
  2 ms hold. Ask stands. **This is the one ask without which the class cannot
  be a DS201-informed gate at all.**

*(from §5)*

- **N-GATE-2 — a settable depth (unblocks G4).** `depth_db`, default −80 for
  `DYN_GATE` (today's clamp) and −60 for `DYN_EXPAND`, range 0 to −80, and
  the gate law becomes a floor rather than the `over * 8.0f` slope when a depth
  is set. Palette: the literals at `:191-192`, measured as ~8 dB per dB (A1).
  **Ask stands, but only for the deep end.** *(Palette verification,
  2026-09-06; the first draft's refutation — "clamping in Python is block-rate
  again" — answered the wrong composition.)* Blending the dry signal back
  through `audiomixer.Mixer` sets the floor per sample, not at block rate:
  measured, the settled closed gain tracks the setting to −0.00 / −0.01 /
  −0.06 / −0.18 dB at 0, −20, −40 and −50 dB, the open state stays a wire to
  0.001 dB, and G4's second clause is met because the `over * 8.0f` slope
  clamps at −80 dB within 10 dB of threshold. It fails at −60 dB (0.72 dB out,
  0.32 with the dry attenuation split across two mixers) and cannot reach
  −80 dB at all: the `Mixer` level is a Q15 integer
  (`src/audiomixer/Mixer.c:332`) with no value between −80.8 and −78.3 dB
  (`Expander.md` V-E4). G4 asks for 0.5 dB at −60 **and** a span to −80, so the
  ask survives for the last 20 dB — and for cost, since the composition spends
  a 32 KB `Splitter` ring (`audioif_splitter.h:20`, `:29`) and two `Mixer`s
  where the option is one float. *Same ask as `Expander`'s N-EXP-3; file
  once.*

*(from §5)*

- **N-GATE-3 — a two-ended key band and an external key (unblocks G3).**
  `sidechain_lp_hz` beside `sidechain_hz`, both 12 dB/octave, and a `key`
  source the node reads instead of the audio. *Refutation, re-run 2026-09-06:*
  `Splitter` + `Filter` build the band but nothing can hand it to `Dynamics` as
  a detector — the keyword table has no `key` and no second corner
  (`Dynamics.c:20-30`; both `set()` calls raise `TypeError: unknown Dynamics
  option`), and the detector reads the same buffer the VCA scales
  (`audioif_dynamics.c:239`, `:254`, `:313`). Ask stands. *Same ask as
  `Expander`'s N-EXP-2; file once.*

*(from §5)*

- **N-GATE-4 — duck mode (unblocks G7).** A fifth mode, or a `duck=True`
  option on `DYN_GATE`, inverting the gain computer's sense. Palette: not in
  the enum (`audioif_dynamics.h:21-27`).

*(from §5)*

  **REFUTED BY PALETTE: the subtraction *is* on the palette, and the composed
  duck meets G7 as written.** *(Palette verification, 2026-09-06.)* The first
  draft's "the subtraction is not on the palette" is true of `audiomixer.Mixer`
  alone — its voice level is clamped to 0…1 and quantised to Q15
  (`src/audiomixer/Mixer.c:332`), so a mixer cannot invert. But
  `audiomath.Multiply` computes `(a·b) >> 15` on signed int16
  (`audioif_multiply.c:38`), so a modulator held at the negative rail
  (−32768) is an **exact** sign flip: measured over 512 frames of a 1 kHz sine,
  `max |out + in| = 0 LSB`. The duck is then
  `Splitter → [Dynamics(DYN_GATE), dry] → Multiply(−1) on the gated branch →
  Mixer`, i.e. `x − b·g·x`. Measured with `b = 1 − Range`: below threshold
  **−0.000 dB** (G7 allows ±0.05), above threshold **−6.00 / −10.00 / −20.00 /
  −39.97 / −59.70 dB** at Range settings of −6, −10, −20, −40 and −60 dB (G7
  allows 0.5), and on burst-then-quiet material the signal ducks to exact zero
  under the burst and returns at its full level after it (V-G2). What the
  composed duck inherits is the *envelope* — it follows whatever `Dynamics`'
  one-pole does, so G7's "on the same attack/hold/decay envelope" clause is
  delivered by N-GATE-1, not by this ask. It also spends a 32 KB `Splitter`
  ring, a `Multiply` and a `Mixer` where a `duck=True` flag would spend
  nothing; that is a Tier 3 argument for the flag, not a trait the palette
  cannot reach, and Phase 1 should treat it as one.
- **N-GATE-5 — look-ahead already exists** (`lookahead_ms`, capped at 50 ms,
  `audioif_dynamics.h:53`) and needs nothing. Pre-ramping (S2) is **not**
  asked for in Phase 0: no trait in this set requires it, and it would be a
  new claim rather than a sourced one. Recorded here so a later run does not
  mistake its absence for an oversight.
