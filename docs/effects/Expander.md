# Effects Dossier — `Expander` (Drawmer DS201, with RaneNote 155 for the law)

**Class:** `lib/audioeffects/dynamics.py` — the current implementation is
read once, for §7, and not otherwise consulted.
**Family / phase:** Dynamics, roadmap Phase 2
**Standout:** Drawmer DS201 *(proposed, vision §4.2)* — **confirmed as the
architecture referent and corrected on one point.** The DS201 is a gate: its
manual gives Threshold, Attack, Hold, Decay, Range and a two-ended key filter,
and **no ratio control anywhere on the panel** (S1), while a downward expander
is defined by a ratio below threshold (S2). No swap is proposed; a second
source is added beside it. The DS201 fixes the envelope, the key filter and
the depth (E3–E6, shared with `NoiseGate`, which is the same box); RaneNote
155 fixes the gain law and the detector (E1, E2).
**Grade:** literature — the two sources that fix the traits describe
behaviour, not a circuit. *(Audit correction: two Drawmer schematic sheets
**were** reached in the audit run, as preview page images — S5, §2. The grade
stays literature under vision §4.1 because no trait below is derived from them
and no SPICE model or analytic derivation was made from them; revisiting the
grade is the implementation session's call, with S5 in hand.)*
**Portability tier:** needs audioif-own nodes (`audiodynamics`)
**Status:** seed (Phase 0), written 2026-09-06

## 1. The circuit, in one paragraph

The DS201 is a dual-channel gate whose intelligence is all in the side-chain:
the audio path is input, gain element, output, with a Bypass position that
"routes the input signal to the output with no processing" (S1). Neither manual
edition names the gain element, but Drawmer's own service documents do — the
schematic sheet reached in the audit run is titled "DS 201 (Fig.1) Audio and
VCA Circuits", and the service manual's setting-up procedure probes the "output
of V.C.A. op. amp channel 1" and trims a "F.e.t. bias pre-set" (S5) — so **the
gain element is a VCA, and that is now sourced**; no trait below rests on it. The control path takes the channel's own input or an external Key and passes
it through two
variable filters in series — a Low Frequency control **25 Hz to 4 kHz** that
"works by severely attenuating frequencies below the cut-off", and a High
Frequency control **250 Hz to 35 kHz** above it, so "it is the range between
the two settings that is allowed to pass" — then compares the result with a
Threshold settable **−54 dB to infinity** (S1; Drawmer's own current manual,
S4, says "-50dBFs" — the editions differ, §2). Crossing it starts a one-shot
envelope: Attack **10 µs to 1 s**, Hold **2 ms to 2 s** timed from the moment
the key falls back below threshold, Decay **2 ms to 4 s**; the envelope is
committed once triggered — "the envelope cycle will complete even if the Key
source falls below the Threshold level before the Attack phase is completed"
(S1). What the VCA settles to when shut is not zero but **Range**, "the amount
of attenuation applied to the input signal when the gate is closed, variable
from 0 dB to −80 dB" (S1's 2005 edition; S4's 2008 manual says "0dB - 90dB"),
which the manual itself recommends setting near −15 dB
when full closure is too obvious. Gate/Duck inverts the sense, Key Listen
monitors the filtered side-chain, Stereo Link drives both envelopes from
channel one. There is no ratio: below threshold the DS201 goes to Range, not
down a slope. **An expander is the same box with the gain computer told to do
something else** — RaneNote 155: "the topology for an expander looks just like
a compressor … the expander reduces gain for signals below the threshold. The
ratio still defines output change verses [sic] input change", with an RMS
detector, and "true rms detection is necessary for compressor and expander modes" where
a gate needs peak (S2).

## 2. Sources and license calls

All fetched 2026-09-06. Nothing from memory; no component value appears
anywhere in this seed, because no schematic was reached.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Drawmer, *DS201 Dual Noise Gate Operator's Manual* … (App. S1) | Every control range in §1 … (App. S1) | The PDF carries no licence line … (App. S1) | <https://umlsrt.com/StudioDocuments/drawmer%20ds201%20manual.pdf> | yes — PDF fetched, text via `pypdf` |
| **S2** Jeffs, Holden & Bohn, *Dynamics Processors*, RaneNote 155 | Expander law and block diagram (Figs. 16a/b) … (App. S2) | PDF line "© 2005 Rane Corporation" … (App. S2) | <https://www.ranecommercial.com/legacy/pdf/ranenotes/Dynamics_Processors.pdf> | yes — PDF fetched, text via `pypdf` |
| **S3** Drawmer, DS201 product page | Feature list and audio spec table … (App. S3) | Footer: "Copyright © 2026 All rights … (App. S3) | <https://www.drawmer.com/products/pro-series/ds201.php> | yes — HTML; this host answers WebFetch with HTTP 429, so the audit fetched it directly (HTTP 200) |
| **S4** Drawmer, *DS201 Operator's Manual* … (App. S4) | The same control descriptions … (App. S4) | "This manual is copyrighted © 2008 by Drawmer … (App. S4) | <https://www.drawmer.com/uploads/manuals/ds201_operators_manual.pdf> | yes — PDF fetched (HTTP 200, 14 pp.), text via `pypdf`; **added by the audit run**, where the first run had recorded this URL as unreachable |
| **S5** Drawmer, *DS201 Service Information* (7 pp.) and *DS201 Comp … (App. S5) | Two legible hand-drawn Drawmer sheets with component … (App. S5) | The drawings are Drawmer's … (App. S5) | <https://elektrotanya.com/drawmer_ds201_comp_sch.pdf/download.html> (preview images under `/PREVIEWS/63463243/23432455/drawmer/`) | yes — preview images fetched (HTTP 200) and read; the full PDFs were **not** obtained. Added by the audit run |
| **Local** `audioif/src/shared/audioif_dynamics.{c,h}`, `audioif/docs/upstream-diff.md`, the probes in the Appendix | What the palette's expander actually does | MIT (audioif) | — | yes |

*Second-pass result: licence calls S1–S4 stand as written; S5 added; the "no
schematic" and "VCA unsourced" findings overturned; one flag on E5.*

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

Kit: **LAW** = 1 kHz steady-sine staircase, 1 dB steps −80 to −10 dBFS,
output RMS over the settled half of each render; **XF** = the same with a sine
and a square of equal RMS; **KEY** = swept sine, gain-reduction trace per
block; **ENV** = burst-then-silence, gain trace per block.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| E1 | Below threshold the output falls `ratio` dB per 1 dB of input drop: over the 30 dB below threshold, at ratios 1.5, 2, 4 and 8, the least-squares slope of output-dB against input-dB is within 5 % of the set ratio **and** no point on the staircase is more than 0.5 dB from that fitted line; above threshold the gain is 0.00 ± 0.05 dB | S2, Fig. 16b ("for every 10 dB of reduction … (App. E1) | high | A fitted slope more than 5 % off the set ratio at any of the four ratios; a point more than 0.5 dB off the line; a slope that changes by more than 5 % when the whole staircase is moved 20 dB up or down with the threshold moved with it | LAW |
| E2 | The detector is **RMS**: a sine and a square of equal RMS, both 15 dB below threshold, get the same gain within 0.5 dB | S2 ("true rms detection is necessary for … (App. E2) | high | A difference near 3.0 dB × (ratio−1), which is what a peak detector gives | XF |
| E3 | The key path is a **band**: low cut settable 25 Hz–4 kHz, high cut 250 Hz–35 kHz (clamped below Nyquist), and with the band set to 500 Hz–2 kHz a tone an octave outside either end, swept from −60 dBFS to 0 dBFS, moves the gain less than 1 dB from its floor at every level | S1 | high | An out-of-band tone at any level up to full scale moving the gain more than 1 dB off the floor; a gain that opens fully as an out-of-band tone is raised. *(Two clauses of the first draft are struck as unsourced: "a skirt shallower than 12 dB/oct at either end" — neither source states the key filters' order, which is a design choice, §5 — and "at any level", which is unbounded and therefore unfalsifiable; the level span the kit actually drives is named instead. **Critic pass, 2026-09-06.**)* | KEY |
| E4 | **Depth is a control:** with the input 30 dB below threshold at −6 dBFS, the settled attenuation equals the Depth setting within 0.5 dB at 0, −20, −40 and −60 dB, and the control's full span reaches at least −80 dB | S1 (Range: "0dB to -80dB" in the 2005 … (App. E4) | high | A settled attenuation more than 0.5 dB from the setting at any of the four; a floor that does not move with the control; a span that stops short of −80 dB | LAW at four Depth settings |
| E5 | **The envelope is one-shot:** once threshold is crossed the attack completes to full open even if the key falls back first, and Hold (2 ms–2 s) times from that fall | S1, verbatim ("the envelope cycle will … (App. E5) | medium — unambiguous … (App. E5) | A 1 ms key burst under a 200 ms attack that never reaches full open | ENV |
| E6 | Attack spans 10 µs–1 s and release 2 ms–4 s: at settings 1, 10, 100 and 1000 ms of attack and 10, 100, 1000 and 4000 ms of release the measured 10–90 % transition is within 15 % of the setting, and settings below one sample period (20.8 µs at 48 kHz) are held only to "one sample or less" | S1 | medium — panel … (App. E6) | A measured transition more than 15 % from the setting at any of the eight; a setting past which the measured time stops changing; a fastest attack longer than one sample | ENV |

No characters. E1 and E2 make this class an expander rather than a gate;
E3–E6 are shared with `NoiseGate` and are demonstrated separately in each
class's own evidence pack.

### Tier 3 — cost and latency

Budget as a fraction of one stereo block's real-time deadline: ESP32-P4
**6 %**, ESP32-S3 **12 %**. Lean patch expected: **no** — one detector, one
gain per frame, at most four side-chain biquads.

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

Compose first. `audiodynamics.Dynamics(DYN_EXPAND)` already carries the shape:
a per-sample envelope follower with settable attack and release, a gain
computer silent above threshold and applying `over × (ratio − 1)` below it
(`audioif_dynamics.c:184`), and a per-sample VCA. **E1 is reachable today** —
at 2:1 the fitted slope is 1.02 dB of extra attenuation per dB, at 4:1 it is
3.4 (A2) — so most of the rebuild is surface work: `ratio`, `threshold_db`,
`attack_ms` and `release_ms` all move live through `Dynamics.set()`. Four
parts of the set are not reachable, each shown by measurement:

- **E2** — the detector is a peak follower, `fabsf(detector[channel])` at …  *(argument in full: App. R)*
- **E3** — `sidechain_hz` is one pole and one end: a single coefficient …  *(argument in full: App. R)*
- **E4** — the floor is the literal `cut < -60.0f ? -60.0f` at `:185`;
  measured, the law stops there and then quantises to exact zero (A2).
- **E5** — the follower is a plain one-pole with no trigger state (`:302-307`), …  *(argument in full: App. R)*

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

All are additive options on `audiodynamics`, audioif's own module (D1), each
defaulting to today's behaviour so `dynamics_probe.py`'s hash is unchanged —
the discipline `upstream-diff.md:837` records for this node's last two options.

- **N-EXP-1 — RMS detection (unblocks E2).** An RMS detector option for …  *(argument in full: App. R)*
- **N-EXP-2 — a two-ended key band and an external key (unblocks E3).** …  *(argument in full: App. R)*
- **N-EXP-3 — a settable depth (unblocks E4).** `depth_db`, defaulting to …  *(argument in full: App. R)*
- **N-EXP-4 — a one-shot envelope with `hold_ms` (unblocks E5, E6's hold).** …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Ten macros; all UNIPOLAR except the two toggles.

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Threshold | UNIPOLAR | −80 … 0 dB | DS201 Threshold |
| 1 | Ratio | UNIPOLAR | 1.0 … 8.0, log | RaneNote 155's ratio |
| 2 | Depth | UNIPOLAR | 0 … −80 dB | DS201 Range |
| 3 | Attack | UNIPOLAR | 0.01 … 1000 ms, log | DS201 Attack |
| 4 | Hold | UNIPOLAR | 2 … 2000 ms, log | DS201 Hold |
| 5 | Release | UNIPOLAR | 2 … 4000 ms, log | DS201 Decay |
| 6 | Key Low | UNIPOLAR | 25 … 4000 Hz, log | DS201 L.F. |
| 7 | Key High | UNIPOLAR | 250 Hz … Nyquist, log | DS201 H.F. |
| 8 | Key Listen | TOGGLE | off / on | DS201 Key Listen |
| 9 | Detector | TOGGLE | RMS / peak | RaneNote 155's rms-for-expanders |

Characters: none. Patches, named for what they do: **Gentle Lift**, **Noise
Floor Trim**, **Snare Tighten**, **Guitar Amp Hum**, **Room Reduction**,
**Hard Downward**. Key Listen is a diagnostic and is off in every patch.

## 7. Defects in the current class the rebuild must not repeat

- **No surface.** `MACRO_LABELS = ()` (`dynamics.py:147`) and
  `PATCHES = {0: ("Default", ())}` (`:149`): nothing for a host to turn, and a
  placeholder patch. Threshold, ratio, attack and release (`:151-152`) are
  construction-only and can never move again.
- **The floor is invisible.** The class exposes `ratio` but not the −60 dB
  clamp underneath it (`audioif_dynamics.c:185`), so 8:1 stops obeying the
  ratio 7.5 dB below threshold and nothing says so.
- **The detector type is undocumented.** The docstring (`dynamics.py:141`)
  says only "below the threshold, quiet gets quieter", so a user setting a
  threshold from an RMS meter is 3 dB out on a sine and further on anything
  peakier.
- **No hold, no key filter, no depth** — and nothing states the omissions, so
  they read as design.

## 8. Open questions

1. **Is `Expander` a distinct implementation from `NoiseGate`** once both have
   Depth and Ratio? They differ only in slope-versus-floor, and the DS201 is
   one box. The 46 names are frozen (roadmap §3), so "merge" is not available;
   the question is one implementation with two defaults. *Implementation
   session, Phase 2.*
2. **Does N-EXP-1's RMS detector need a settable averaging window** or is a
   fixed one enough for E2? *Phase 1 node design, from this seed and
   `Compressor`'s.*
3. **E5's confidence.** The completion sentence is the manual's and no
   waveform corroborates it; a DS201 schematic would move it to high or strike
   it. *Phase 0 if a drawing turns up; otherwise it ships at medium, quoted.*
4. **The DS201 schematic** exists on elektrotanya and was not obtained.
   Nothing in the trait set depends on a component value, so this is a
   one-line note for the survey, not a blocker. *Arthur.*


## Appendix

All probes ran 2026-09-06 against the CPython build of audioif in
`audiocomponents/.venv`, 48 kHz, stereo, 16-bit.

**A method note the measurement kit should inherit: measure a frequency
response with steady sines, not with an int16 impulse.** An impulse through
this stack under-reads because a filter's low-amplitude tail quantises away —
a `HIGH_PASS` at 200 Hz measured **−0.86 dB** of passband gain by impulse-FFT
and **−0.024 dB** by steady sine. The first number is the measurement's error,
not the node's, and it was caught only by running the same claim two ways.

**A1 — the gate law, for contrast (`DYN_GATE`, threshold −40 dB).** 1 kHz
sine; column is output-minus-input in dB. Gain is 0 until the *peak* crosses
threshold (RMS −42.01 dBFS = peak −39.0), then falls about 8 dB per dB:
−2.26, −10.26, −18.47 at 1, 2 and 3 dB further down, and −45.31 at 6 dB down.
Below −50 dBFS RMS the int16 output is exactly zero.

**A2 — the expander law (`DYN_EXPAND`, threshold −40 dB).** Ratio 2: gain
−0.29, −5.33, −10.43, −15.92, −21.91 dB at input RMS −43, −48, −53, −58,
−63 dBFS — 1.02 dB of extra attenuation per dB, as E1 asks. Ratio 4: −0.85,
−16.06, −33.11 dB at −43, −48, −53 dBFS, then exact zero from −63 dBFS down,
where the −60 dB clamp plus int16 rounding ends the law.

**A3 — peak versus RMS (`DYN_EXPAND`, ratio 2, threshold −20 dB).** 1 kHz sine
and 1 kHz square, both −35.00 dBFS RMS: −12.44 and −15.05 dB, a 2.61 dB gap.
The same pair at ratio 4, threshold −30 dB: −0.87 and −9.03 dB. E2 allows 0.5.

**A4 — the side-chain's shape (`DYN_COMPRESS`, ratio 20, knee 0, threshold
−60 dB, `sidechain_hz=5000`).** Detector level inferred from reported gain
reduction, 0.5-amplitude sine per frequency: 100 Hz −43.17, 200 −37.18,
500 −29.23, 1 k −23.35, 2 k −17.79, 5 k −12.21, 10 k −10.17, 20 k −9.47 dBFS.
That is 6.0, 5.9 and 5.6 dB per octave through the skirt, corner at the set
5 kHz — one pole, one end.

**A5 — latency.** An impulse at frame 128 through `DYN_GATE`, `DYN_EXPAND`,
`DYN_COMPRESS` and `DYN_TRANSIENT` with look-ahead off came back at frame 128
in every case. With `DYN_LIMIT` and `lookahead_ms=5.0` it came back 240 frames
later — exactly 5.00 ms.

**A6 — the one-shot envelope, refuted on the palette.** A 1 ms full-scale
burst then silence into `DYN_GATE`, threshold −40 dB, `attack_ms=200`: the
reported gain stayed at −80.00 dB for all 90 blocks rendered. The gate never
opened.

---

### Palette verification, 2026-09-06

An independent run against the CPython build of audioif in
`audiocomponents/.venv`, 48 kHz, stereo, 16-bit. Numbers are this run's own.

**V-E1 — the detector's floor is mean-absolute, not peak.** `DYN_EXPAND`,
ratio 2, threshold −20 dB, 1 kHz sine and 1 kHz square at equal RMS
(−35 dBFS), `attack_ms == release_ms`:

| attack = release | sine | square | gap |
|---|---|---|---|
| 5 ms | −15.95 | −15.05 | **0.90 dB** |
| 50 ms | −15.96 | −15.05 | 0.91 |
| 200 ms | −15.96 | −15.05 | 0.91 |
| 1 s | −17.64 | −16.71 | 0.93 |
| 5 s | −26.63 | −25.70 | 0.93 |

0.90 dB is the sine/square difference of a *mean-absolute* detector
(20·log₁₀(2/π · √2) = 0.91 dB); a peak detector gives 3.01. The one-pole on
`|x|` reaches it whenever attack and release are equal, so the 2.4–2.6 dB
figures in A3 are the asymmetry (attack 5 ms, release 150 ms), not the node's
limit. E2 allows 0.5 dB, so the node still fails — by 0.4 dB, not by 2.1.

**V-E2 — E5's one-shot, re-measured.** 1 ms full-scale burst, `DYN_GATE`,
threshold −40 dB, `attack_ms=200`: reported gain pinned at **−80.00 dB for all
90 blocks**. The gate never opens. A6 reproduced.

**V-E3 — the side-chain's one pole, re-measured.** `DYN_COMPRESS`, ratio 20,
knee 0, threshold −60 dB, `sidechain_hz=5000`, detector level inferred from the
reported gain reduction: 100 Hz −43.55, 200 −37.58, 500 −29.65, 1 k −23.76,
2 k −18.24, 5 k −12.63, 10 k −10.62, 20 k −9.94 dBFS — **5.97 / 6.00 / 5.89 /
5.52 dB per octave**, corner at the set 5 kHz. One pole, one end. A4
reproduced.

**V-E4 — depth by composition (the N-EXP-3 refutation).** Graph:
`RawSample → Mixer(guard) → Splitter(taps=2)`, tap 0 → `Dynamics(DYN_GATE,
threshold 40 dB above the signal, so the gain sits on its −80 dB floor)`,
tap 1 → dry; both into a two-voice `Mixer` at levels `1−d` and `d`. Signal a
1 kHz sine at 0.5 amplitude (−9.03 dBFS RMS); settled output measured over the
second half of a 0.5 s render.

| depth set | one-stage blend | error | two-stage blend | error |
|---|---|---|---|---|
| 0 dB | −0.00 | −0.00 | — | — |
| −10 | −10.00 | −0.00 | — | — |
| −20 | −20.01 | −0.01 | — | — |
| −30 | −30.02 | −0.02 | — | — |
| −40 | −40.06 | −0.06 | −40.04 | −0.04 |
| −50 | −50.18 | −0.18 | −50.15 | −0.15 |
| −60 | −60.72 | **−0.72** | −60.32 | −0.32 |
| −70 | −72.02 | −2.02 | −71.08 | −1.08 |
| −80 | −86.63 | −6.63 | −83.94 | −3.94 |

Open-state control, gate held open at four depth settings: **−0.000, −0.001,
−0.001, −0.001 dB** — the blend is a wire when the gain is up. Node-alone
control at the same setting: **−83.94 dB**, its fixed floor, which is where the
−80 dB row lands once the dry branch has quantised away. Two-stage = the dry
branch attenuated by √d through a second `Mixer` before the sum.

**V-E5 — latency, re-measured.** An impulse at frame 128 through `DYN_GATE`,
`DYN_EXPAND`, `DYN_COMPRESS`, `DYN_TRANSIENT` and `DYN_LIMIT` with look-ahead
off came back at frame **128** in every case; `DYN_LIMIT` with
`lookahead_ms=5.0` came back at frame **368**, 240 frames = 5.00 ms. A5
reproduced.

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

**Mono:** one gain from a channel-linked detector, applied to every channel —
a mono source gets identical processing and no stereo statement is owed.
**Rate:** E3's key span runs to 35 kHz, above Nyquist at every rate here; the
span clamps (Tier 1) and E3 is stated against the clamped top, so it holds at
44.1 and 22.05 kHz with the top reading "wide open". **`capabilities` (D10):
`()`** — nothing in an expander's law refers to tempo, and neither source's
unit has a tempo input.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| **S1** Drawmer, *DS201 Dual Noise Gate Operator's Manual* (manufacturer's text, captured from `drawmer.com/op201.htm`, 7 pp.) | Every control range in §1, the envelope-completion sentence, the Range advice, Gate/Duck, Key Listen, the side-chain trigger-delay note | The PDF carries no licence line; its header prints `http://www.drawmer.com/op201.htm`, 31 Jan 2005 — Drawmer's own page on a third-party mirror (UMass Lowell SRT, whose only notice, "Copyright © 2026 UML SRT", covers the mirror, not the text). Chased to the rights holder: Drawmer's own manual (S4) says it "may not be duplicated in whole or in part without the written consent of Drawmer" — **verified all-rights-reserved**. Read as a document, nothing reproduced | <https://umlsrt.com/StudioDocuments/drawmer%20ds201%20manual.pdf> | yes — PDF fetched, text via `pypdf` |
| **S2** Jeffs, Holden & Bohn, *Dynamics Processors*, RaneNote 155 | Expander law and block diagram (Figs. 16a/b); gate's ∞:1-plus-depth law (Figs. 17a/b); "true rms detection is necessary for compressor and expander modes"; hold 0–3 s and depth 0 to −80 dB as professional ranges | PDF line "© 2005 Rane Corporation"; the site's Terms of Use (reached this run, <https://www.ranecommercial.com/legacy/terms-of-use.html>) is "Copyright © 2012-2018 inMusic Brands, Inc. All rights reserved." — personal, non-commercial viewing only, no redistribution without written permission. **Verified all-rights-reserved**, not "no further terms". Read only | <https://www.ranecommercial.com/legacy/pdf/ranenotes/Dynamics_Processors.pdf> | yes — PDF fetched, text via `pypdf` |
| **S3** Drawmer, DS201 product page | Feature list and audio spec table; confirms Gating/Ducking and the external key | Footer: "Copyright © 2026 All rights reserved. Drawmer Electronics Ltd." — **verified all-rights-reserved**, not merely unstated. Read only | <https://www.drawmer.com/products/pro-series/ds201.php> | yes — HTML; this host answers WebFetch with HTTP 429, so the audit fetched it directly (HTTP 200) |
| **S4** Drawmer, *DS201 Operator's Manual*, the manufacturer's own current edition, 14 pp. | The same control descriptions, and **two values that differ from S1's 2005 capture**: Threshold "-50dBFs - infinate" and Range "0dB - 90dB". Also an explicit copyright line, and a block diagram on p. 14 (an image, not extracted) | "This manual is copyrighted © 2008 by Drawmer Electronics, Ltd. With all rights reserved. Under copyright laws, this manual may not be duplicated in whole or in part without the written consent of Drawmer." Read only | <https://www.drawmer.com/uploads/manuals/ds201_operators_manual.pdf> | yes — PDF fetched (HTTP 200, 14 pp.), text via `pypdf`; **added by the audit run**, where the first run had recorded this URL as unreachable |
| **S5** Drawmer, *DS201 Service Information* (7 pp.) and *DS201 Comp Sch* (3 pp.) — the manufacturer's own service documents, reached as `elektrotanya.com`'s own preview page images (first two pages of each) | Two legible hand-drawn Drawmer sheets with component values: "DS 201 (Fig.1) Audio and VCA Circuits" (signal and key inputs, Int/Ext key source, Threshold, Range, By-Pass/Key Listen, control voltage, "All Op. Amps. TL072 or LF353") and "DS 201 (Fig. 2) Rectifier. Attack, Hold, Decay Circuits"; and a setting-up procedure naming the "output of V.C.A. op. amp channel 1" and a "F.e.t. bias pre-set". **Used here for one fact only: the gain element is a VCA.** | The drawings are Drawmer's, under S4's all-rights-reserved notice; the host's own terms read "Please do not offer the downloaded file for sell only use it for personal usage" — **personal use only**. Read as a document (vision §5); nothing reproduced, no component value carried into a trait | <https://elektrotanya.com/drawmer_ds201_comp_sch.pdf/download.html> (preview images under `/PREVIEWS/63463243/23432455/drawmer/`) | yes — preview images fetched (HTTP 200) and read; the full PDFs were **not** obtained. Added by the audit run |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| E1 | Below threshold the output falls `ratio` dB per 1 dB of input drop: over the 30 dB below threshold, at ratios 1.5, 2, 4 and 8, the least-squares slope of output-dB against input-dB is within 5 % of the set ratio **and** no point on the staircase is more than 0.5 dB from that fitted line; above threshold the gain is 0.00 ± 0.05 dB | S2, Fig. 16b ("for every 10 dB of reduction in input signal, the output is reduced by 20 dB" at 2:1) | high | A fitted slope more than 5 % off the set ratio at any of the four ratios; a point more than 0.5 dB off the line; a slope that changes by more than 5 % when the whole staircase is moved 20 dB up or down with the threshold moved with it | LAW |
| E2 | The detector is **RMS**: a sine and a square of equal RMS, both 15 dB below threshold, get the same gain within 0.5 dB | S2 ("true rms detection is necessary for compressor and expander modes") | high | A difference near 3.0 dB × (ratio−1), which is what a peak detector gives | XF |
| E3 | The key path is a **band**: low cut settable 25 Hz–4 kHz, high cut 250 Hz–35 kHz (clamped below Nyquist), and with the band set to 500 Hz–2 kHz a tone an octave outside either end, swept from −60 dBFS to 0 dBFS, moves the gain less than 1 dB from its floor at every level | S1 | high | An out-of-band tone at any level up to full scale moving the gain more than 1 dB off the floor; a gain that opens fully as an out-of-band tone is raised. *(Two clauses of the first draft are struck as unsourced: "a skirt shallower than 12 dB/oct at either end" — neither source states the key filters' order, which is a design choice, §5 — and "at any level", which is unbounded and therefore unfalsifiable; the level span the kit actually drives is named instead. **Critic pass, 2026-09-06.**)* | KEY |
| E4 | **Depth is a control:** with the input 30 dB below threshold at −6 dBFS, the settled attenuation equals the Depth setting within 0.5 dB at 0, −20, −40 and −60 dB, and the control's full span reaches at least −80 dB | S1 (Range: "0dB to -80dB" in the 2005 edition, "0dB - 90dB" in S4's 2008 manual); S2 ("typical range of 0 to -80 dB") | high | A settled attenuation more than 0.5 dB from the setting at any of the four; a floor that does not move with the control; a span that stops short of −80 dB | LAW at four Depth settings |
| E5 | **The envelope is one-shot:** once threshold is crossed the attack completes to full open even if the key falls back first, and Hold (2 ms–2 s) times from that fall | S1, verbatim ("the envelope cycle will complete even if the Key source falls below the Threshold level before the Attack phase is completed") | medium — unambiguous sentence, no waveform | A 1 ms key burst under a 200 ms attack that never reaches full open | ENV |
| E6 | Attack spans 10 µs–1 s and release 2 ms–4 s: at settings 1, 10, 100 and 1000 ms of attack and 10, 100, 1000 and 4000 ms of release the measured 10–90 % transition is within 15 % of the setting, and settings below one sample period (20.8 µs at 48 kHz) are held only to "one sample or less" | S1 | medium — panel ranges, not curves | A measured transition more than 15 % from the setting at any of the eight; a setting past which the measured time stops changing; a fastest attack longer than one sample | ENV |

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

No copyleft source was reached, so none was measured; no emulator source was
opened. **Partly found, by the licence audit:** `elektrotanya.com`'s two DS201
entries are `drawmer_ds201_sm.pdf` (7 pages) and `drawmer_ds201_comp_sch.pdf`
(3 pages), and each is served with its **first two pages as preview images**.
The audit run fetched and read all four, and two of them are legible Drawmer
schematic sheets with component values — cited as S5 above. The full PDFs were
not obtained, so the third schematic page and the rest of the service manual
remain unread. *Corrected by the audit: the first run recorded "the DS201
schematic was not obtained" and both seeds recorded "VCA" as unsourced; both
statements are now wrong. It also called both entries "a 7-page document" — only
the service manual is.* Drawmer's own manual (S4) prints a block diagram, not a
schematic. *Also corrected by the audit: the first run recorded `drawmer.com`'s
own manual PDF as unreachable (HTTP 429); that host answers WebFetch with 429
(re-confirmed this run) but serves a direct request (HTTP 200), and the manual
is cited as S4.* Also not found: a ratio-carrying hardware expander manual — the Allison Research **Kepex 500**
manual at `technicalaudio.com` fails TLS ("unable to get local issuer
certificate"), and the **dbx 904** manual from Harman's CDN fetches but is a
scanned image with no extractable text and this environment has no OCR — both
re-checked in the audit run and both claims stand.
**Unsourced, therefore absent from the trait table:**
any DS201 hysteresis figure (neither manual edition mentions hysteresis — both
checked in the audit run), its detector type, and any ratio range for a named
unit. *Audit note on the detector: S5's second sheet is titled "Rectifier.
Attack, Hold, Decay Circuits", so a drawing of it is now in reach — but the
audit derived nothing from it, and E2 stays sourced to S2's general claim.*

*(from §3)*

**Audit flag on E5's second clause.** S1 states the Hold timing twice and the
two statements disagree: the Hold control description says Hold is "the amount
of time the gate is held open after the signal falls below the Threshold", while
the Note two paragraphs later says "the Hold cycle starts as soon as the
Threshold is crossed". E5 follows the control description. The one-shot rule
itself (E5's first clause) is unaffected. The implementation session picks a
reading and records which, or measures nothing about Hold's origin.

*(from §3)*

**Latency: zero, and no option adds any.** Neither mechanism looks ahead — no
source reached shows a delay element in the DS201's audio path, and RaneNote 155
puts look-ahead in
the *gate*'s block diagram, not the expander's (S2, Figs. 16a/17a) — so the
class ships **no look-ahead option at all** and `latency_samples` is 0 at every
setting. One delay is worth naming and is not latency: S1 warns that side-chain
HF attenuation "will also cause a slight delay in the time the gate takes to
trigger", a detector-response effect measured by KEY, never reported in
`latency_samples`. Measured, a `Dynamics` node with look-ahead off returns an
impulse in the frame it arrived (A5).

*(from §4)*

- **E2** — the detector is a peak follower, `fabsf(detector[channel])` at
  `audioif_dynamics.c:265`, with no RMS path in the file. Equal-RMS sine and
  square at 2:1 got −12.44 and −15.05 dB, a **2.61 dB** gap where E2 allows
  0.5 (A3). *(Palette verification, 2026-09-06: the gap is a function of the
  attack/release asymmetry, not a fixed property of the node. With
  `attack_ms == release_ms` the one-pole on `|x|` settles to a **mean-absolute**
  detector and the gap falls to **0.90 dB** at every time constant from 5 ms to
  5 s — still nearly twice E2's allowance, and bought by giving up the
  independent attack and release E6 requires. 0.90 dB is the floor of what this
  node can reach, V-E1.)*

*(from §4)*

- **E3** — `sidechain_hz` is one pole and one end: a single coefficient
  (`:83-85`) subtracting a one-pole low-pass from the signal (`:255-262`),
  measured at **6.0, 5.9 and 5.6 dB per octave** through 100–2000 Hz with the
  corner at the set 5 kHz (A4). No low-cut end and no key input — `play()`
  takes the audio and the detector reads that same audio.

*(from §4)*

- **E5** — the follower is a plain one-pole with no trigger state (`:302-307`),
  so a 1 ms burst under a 200 ms attack never opens the gate at all (A6;
  re-measured this run, the reported gain stayed pinned at −80.00 dB for all
  90 blocks, V-E2).

*(from §4)*

**Portability tier: audioif** — `audiodynamics` is audioif's own module, not a
CircuitPython port (`audioif/docs/upstream-diff.md:661`), so the class carries
the guarded import and a construction-time `ImportError` on a stock board.
Python computes coefficients at construction and on a macro move; C runs the
follower, gain computer and VCA per sample.

*(from §5)*

- **N-EXP-1 — RMS detection (unblocks E2).** An RMS detector option for
  `DYN_EXPAND`/`DYN_COMPRESS`, default peak. Palette: `fabsf` only (`:265`).
  *Refutation, re-run 2026-09-06:* squaring the audio through
  `audiomath.Multiply` gives a stream, not a detector input the node accepts —
  `play()` sets one source (`Dynamics.c:123-126`) and the detector reads that same
  buffer (`audioif_dynamics.c:239`, `:254`) before the VCA scales it (`:313`).
  Symmetrical time constants get closest: `attack_ms == release_ms` makes the
  follower mean-absolute and narrows the equal-RMS sine/square gap to
  **0.90 dB** (V-E1), still nearly twice E2's 0.5 dB and at the cost of E6's
  independent attack and release. Ask stands, and the node design should know
  the gap it has to close is under 1 dB.

*(from §5)*

- **N-EXP-2 — a two-ended key band and an external key (unblocks E3).**
  `sidechain_lp_hz` beside `sidechain_hz`, both 12 dB/octave, plus a `key`
  source. Palette: one 6 dB/octave end, no key input (A4; re-measured this run
  at 5.97 / 6.00 / 5.89 / 5.52 dB per octave through 100–2000 Hz, corner at the
  set 5 kHz, V-E3). *Refutation, re-run 2026-09-06:* `Splitter` + `Filter` can
  build the band, but nothing can hand that stream to `Dynamics` as a detector
  — the keyword table has no `key` and no second corner
  (`Dynamics.c:20-30`; `set(key=…)` and `set(sidechain_lp_hz=…)` both raise
  `TypeError: unknown Dynamics option`), and the detector reads the same buffer
  the VCA scales (`audioif_dynamics.c:239`, `:254`, `:313`). The one route that
  would carry a gain out of the node — feeding it a DC stream so its output
  *is* the envelope — fails for the same reason: with no key input the detector
  would read the DC. The composition dead-ends at the node boundary. Ask
  stands. *Shared with `NoiseGate`; filed once.*

*(from §5)*

- **N-EXP-3 — a settable depth (unblocks E4).** `depth_db`, defaulting to
  today's −60 (`:185`) for expand and −80 (`:192`) for gate, range 0 to −80.
  **Ask stands, but only for the deep end — the first draft's refutation was
  wrong and most of the range composes.** *(Palette verification, 2026-09-06.)*
  The first draft refuted a *Python-side* floor, which does step at block rate;
  it never tried the node composition, which does not step at all. Blending the
  dry signal back through `audiomixer.Mixer` gives
  `out = x·(d + (1−d)·g)`: unity when the gain is open, `d` when it is at the
  node's floor, and the level multiply is per sample. Measured on a −9 dBFS
  sine with the gate held at its −80 dB floor, the settled attenuation tracks
  the setting to **−0.00 / −0.01 / −0.06 / −0.18 dB** at 0, −20, −40 and −50 dB
  of depth, and the open state is a wire (**−0.001 dB**). It breaks at the
  bottom: **−0.72 dB** of error at −60 dB, **−2.0** at −70 and **−6.6** at −80,
  because the `Mixer`'s level is a Q15 integer
  (`src/audiomixer/Mixer.c:332`) and there is no value between 3/32768
  (−80.8 dB) and 4/32768 (−78.3 dB). Splitting the dry attenuation across two
  cascaded mixers recovers −60 dB (**−0.32 dB** error) and no further: −70 is
  1.08 dB out and −80 lands on the node's own floor (V-E4). E4 asks for
  0.5 dB at −60 **and a span reaching −80 dB**, so the ask survives — for the
  last 20 dB of range, and for cost: the composition spends a `Splitter`
  (an 8192-frame ring, **32 KB** of RAM, `audioif_splitter.h:20`, `:29`) and
  two `Mixer`s where the option is one float. *Shared with `NoiseGate`; filed
  once.*

*(from §5)*

- **N-EXP-4 — a one-shot envelope with `hold_ms` (unblocks E5, E6's hold).**
  Palette: the follower has no trigger state and no hold (A6, V-E2). The
  palette *does* have a retriggerable per-sample VCA — `audiomath.Multiply`
  modulated by a `synthio` note with a constant waveform and an envelope
  (`NoiseGate.md` V-G1) — but nothing to trigger it from: the contract gives a
  component no per-block hook (`docs/audio-component-api.md:231-233`). Ask
  stands. *Filed under `NoiseGate`; cited here.*
