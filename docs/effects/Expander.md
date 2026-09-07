# Effects Dossier — `Expander` (Drawmer DS201, with RaneNote 155 for the law)

**Class:** `lib/audioeffects/rebuilt/expander.py`. The old
`dynamics.py:140` class is read once, for §7, and stands untouched beneath.
**Family / phase:** Dynamics, roadmap Phase 2.
**Standout:** Drawmer DS201 *(vision §4.2)*, **corrected on one point** — it
is a gate and has no ratio control (S1), so it fixes E3–E6 and RaneNote 155
is added beside it for E1 and E2 (App. R).
**Grade:** literature; revisited at Station A with S5's schematic sheets in
hand and **left there**, because no component value reaches a trait (App. R).
**Portability tier:** **audioif** — `REQUIRES = ("audiodynamics",)`.
**Status:** **the six trait statements are the seed's of 2026-09-06, word
for word; this session changed none of them**, and the bench that settled
§§4–8 (**App. B**) ran before any class code was written. Station A,
2026-09-07.

## 1. The circuit, in one paragraph

A gate whose intelligence is all in the side-chain: input, VCA, output, with
a Bypass that passes the input "with no processing". The key path is **two
variable filters in series** — Low 25 Hz–4 kHz, High 250 Hz–35 kHz, "it is the
range between the two settings that is allowed to pass" — feeding a Threshold,
a committed Attack/Hold/Decay envelope (10 µs–1 s, 2 ms–2 s, 2 ms–4 s) and a
**Range** floor "variable from 0 dB to −80 dB" rather than silence (S1).

**There is no ratio: below threshold it goes to Range, not down a slope. An
expander is the same box with the gain computer told to do something else** —
RaneNote 155: "the expander reduces gain for signals below the threshold. The
ratio still defines output change verses [sic] input change", with an RMS
detector, because "true rms detection is necessary for compressor and expander
modes" where a gate needs peak (S2). Every range above, the editions'
disagreements and the switches left out: **App. R**.

## 2. Sources and license calls

All fetched 2026-09-06; **no URL was fetched at Station A**, and nothing
below moved. Nothing from memory. Each row's full reading — what it gave, and
its licence line read on the page that carries it — is **App. S**; §2 keeps
the id, the lead, the URL and the reached call, which are the gate conditions.

| Source | Lead | URL | Reached |
|---|---|---|---|
| **S1** | Drawmer, *DS201 Operator's Manual*, 2005 capture, 7 pp. — every control range in §1 | <https://umlsrt.com/StudioDocuments/drawmer%20ds201%20manual.pdf> | yes, PDF |
| **S2** | Jeffs, Holden & Bohn, *Dynamics Processors*, RaneNote 155 — the law, the ratio, the RMS detector | <https://www.ranecommercial.com/legacy/pdf/ranenotes/Dynamics_Processors.pdf> | yes, PDF |
| **S3** | Drawmer, DS201 product page — spec table, the external key | <https://www.drawmer.com/products/pro-series/ds201.php> | yes, HTML |
| **S4** | Drawmer, *DS201 Operator's Manual*, 2008 edition, 14 pp. — two ranges that differ from S1's | <https://www.drawmer.com/uploads/manuals/ds201_operators_manual.pdf> | yes, PDF |
| **S5** | Drawmer service sheets, as the host's preview images — one fact only, that the gain element is a VCA | <https://elektrotanya.com/drawmer_ds201_comp_sch.pdf/download.html> | previews only; full PDFs **not** obtained |
| **Local** | `audioif/src/shared/audioif_dynamics.c`, `src/audiodynamics/Dynamics.c`, `docs/upstream-diff.md:969-1098`, and App. B | — | yes |

*Every licence is **verified all-rights-reserved** or personal-use-only
(App. S). Nothing is reproduced; no component value reaches a trait.*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there
under the length rule, with this class's mono, rate and `capabilities` notes.

### Tier 2 — circuit traits

Kit names, resolved to the kit spec's twenty: **LAW** → CURVE, **XF** →
CURVE, **KEY** → RESPONSE (the swept-detector exception §5 grants E3 by name),
**ENV** → GAINTRACE. The seed's own definitions are in **App. R**.

**Frozen.** Every trait statement, disconfirmation and measurement below is
the seed's of 2026-09-06, unedited. The three bracketed notes were added at
Station A, after the bench and after the class was written, and record what a
statement was found to *imply* — never what it says. The evidence pack grades
the statements, not the notes.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Meas. |
|---|---|---|---|---|---|
| E1 | Below threshold the output falls `ratio` dB per 1 dB of input drop: over the 30 dB below threshold, at ratios 1.5, 2, 4 and 8, the least-squares slope of output-dB against input-dB is within 5 % of the set ratio **and** no point on the staircase is more than 0.5 dB from that fitted line; above threshold the gain is 0.00 ± 0.05 dB *[the 30 dB clause asks for 30·(ratio−1) dB of output range below the threshold, which at ratio 8 is 210 dB and cannot exist in a 16-bit path — App. B1]* | S2 (App. E1) | high | A fitted slope more than 5 % off the set ratio at any of the four ratios; a point more than 0.5 dB off the line; a slope that changes by more than 5 % when the whole staircase is moved 20 dB up or down with the threshold moved with it | LAW |
| E2 | The detector is **RMS**: a sine and a square of equal RMS, both 15 dB below threshold, get the same gain within 0.5 dB | S2 (App. E2) | high | A difference near 3.0 dB × (ratio−1), which is what a peak detector gives | XF |
| E3 | The key path is a **band**: low cut settable 25 Hz–4 kHz, high cut 250 Hz–35 kHz (clamped below Nyquist), and with the band set to 500 Hz–2 kHz a tone an octave outside either end, swept from −60 dBFS to 0 dBFS, moves the gain less than 1 dB from its floor at every level *[holding the floor to 0 dBFS asks for more than 40 dB of stopband rejection one octave out — an eighth-order key filter. Neither source states an order, and the ask the palette answered specified 12 dB/octave — App. B3]* | S1 | high | An out-of-band tone at any level up to full scale moving the gain more than 1 dB off the floor; a gain that opens fully as an out-of-band tone is raised. *(two clauses struck by the critic pass — App. R)* | KEY |
| E4 | **Depth is a control:** with the input 30 dB below threshold at −6 dBFS, the settled attenuation equals the Depth setting within 0.5 dB at 0, −20, −40 and −60 dB, and the control's full span reaches at least −80 dB | S1, S2 (App. E4) | high | A settled attenuation more than 0.5 dB from the setting at any of the four; a floor that does not move with the control; a span that stops short of −80 dB | LAW at four Depth settings |
| E5 | **The envelope is one-shot:** once threshold is crossed the attack completes to full open even if the key falls back first, and Hold (2 ms–2 s) times from that fall *[the node's one-shot machine exists but is gated on `DYN_GATE` and replaces the ratio law; an expander cannot have both — App. B5]* | S1, verbatim (App. E5) | medium (App. E5) | A 1 ms key burst under a 200 ms attack that never reaches full open | ENV |
| E6 | Attack spans 10 µs–1 s and release 2 ms–4 s: at settings 1, 10, 100 and 1000 ms of attack and 10, 100, 1000 and 4000 ms of release the measured 10–90 % transition is within 15 % of the setting, and settings below one sample period (20.8 µs at 48 kHz) are held only to "one sample or less" *[`attack_ms`/`release_ms` are one-pole time constants, and the 10–90 % time of a gain-in-dB trace is a function of the level step as well as the setting — App. B6]* | S1 | medium (App. E6) | A measured transition more than 15 % from the setting at any of the eight; a setting past which the measured time stops changing; a fastest attack longer than one sample | ENV |

No characters. E1 and E2 make this class an expander rather than a gate;
E3–E6 are shared with `NoiseGate` and are demonstrated separately in each
class's own evidence pack.

### Tier 3 — cost and latency

Budget, as a fraction of one stereo block's real-time deadline: ESP32-P4
**6 %**, ESP32-S3 **12 %**. Lean patch expected: **no** — one node, one
detector, one gain per frame, a two-pole key band at each end.

**Latency budget: 0 samples at every setting; no option may add any.** No
source shows a delay element in the DS201's audio path, and RaneNote 155 puts
look-ahead in the *gate*'s diagram, not the expander's (S2, Figs. 16a/17a), so
the class ships **no look-ahead option at all** — there is no latency-adding
option to name a millisecond figure for. The one delay worth naming is *not*
latency and is never reported in `latency_samples` (App. R).

*(More of §3 is in **App. R** — nothing deleted.)*

## 4. Modeling approach on the palette

**One node.** `audiodynamics.Dynamics(DYN_EXPAND)` with the Phase 1 options
carries five of the six traits; the four asks (§5) all landed on the pin
(`upstream-diff.md:969`). One trait, one option, verified at **App. B**:

| Trait | What carries it | Bench |
|---|---|---|
| E1 | the mode's gain computer, `over × (ratio − 1)` (`audioif_dynamics.c:371-381`) | slope within **1.9 %** of the ratio at 1.5, 2, 4, 8; above threshold **−0.002 dB** — B1 |
| E2 | **`detector="rms"`**, 10 ms window unset | equal-RMS sine/square gap **0.05 dB** against E2's 0.5; peak gives **2.43 dB** — B2 |
| E3 | **`sidechain_hz`** + **`sidechain_lp_hz`** at **`sidechain_poles=2`** | both ends move; rejection two octaves out **25 dB**, not the ≥40 dB an octave out E3's floor clause implies — B3 |
| E4 | **`depth_db`** | floor tracks the setting to **0.00 / 0.00 / −0.05 / −0.06 dB** at 0, −20, −40, −60 and reaches −80 — B4 |
| E5 | **nothing** — `hold_ms` is inert in this mode | identical traces with and without `hold_ms=20`; the same burst in `DYN_GATE` opens to −1.96 dB — B5 |
| E6 | **`attack_ms`** / **`release_ms`** | monotone and proportional across the span; measured 10–90 % over setting is 0.25 on attack, 2.54 on release — B6 |

**Composition was weighed and rejected on the seed's own numbers** (App. R):
V-E4's `Splitter`-and-two-`Mixer`s Depth reached −60 dB with 0.32 dB of error
and a 32 KB ring where `depth_db` is one float reaching −80; and a steeper key
band from `audiobiquad.Biquad` into `Dynamics.key()` needs four sections per
end to change E3's verdict, where the ask asked for 12 dB/octave. **The class
builds one node and no others.** `key(sample)` is a constructor option, not a
macro — the DS201's external Key (S1, S3) — borrowed like `source`: never
owned, reset or deinited.

**Portability tier: audioif.** `audiodynamics` is audioif's own module, not a
CircuitPython port (`upstream-diff.md:661`), so the module carries the guarded
import and `_require_modules()` raises `ImportError` on a stock board. Python
computes nothing per sample: each macro is one `Dynamics.set()`.

## 5. Node asks — all four delivered on the pin

Filed on `audiodynamics` as additive, default-off options
([audioif#38](https://github.com/PyDevices/audioif/issues/38)); all four on
the pin. The refutation behind each: **App. R**.

- **N-EXP-1, RMS detection (E2)** → `detector="rms"` + `rms_ms`.
- **N-EXP-2, two-ended key band and external key (E3)** → `sidechain_lp_hz`,
  `sidechain_poles`, `key(sample)`, `key_listen`.
- **N-EXP-3, settable depth (E4)** → `depth_db`.
- **N-EXP-4, one-shot envelope with `hold_ms` (E5) — for `DYN_GATE` only.**
  `audioif_dynamics.c:452-453` gates the machine on the mode and `:679-724`
  replaces the gain computer with a binary open/floor. **Not a shortfall**: a
  ratio law and a binary trigger cannot be one computer. E5 is `NoiseGate`'s.
  **No new ask.**

## 6. Surface, frozen

**Nine macros**, all UNIPOLAR except the two toggles. Engineering spans are
private (`_MACRO_RANGES`); the panel sees 0–127.

| # | Macro | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Threshold | UNIPOLAR | −80 … 0 dB | DS201 Threshold |
| 1 | Ratio | UNIPOLAR | 1.0 … 8.0, log | RaneNote 155's ratio |
| 2 | Depth | UNIPOLAR | 0 … −80 dB | DS201 Range |
| 3 | Attack | UNIPOLAR | 0.01 … 1000 ms, log | DS201 Attack |
| 4 | Release | UNIPOLAR | 2 … 4000 ms, log | DS201 Decay |
| 5 | Key Low | UNIPOLAR | 25 … 4000 Hz, log | DS201 L.F. |
| 6 | Key High | UNIPOLAR | 250 … 35000 Hz, log, clamped below Nyquist | DS201 H.F. |
| 7 | Key Listen | TOGGLE | off / on | DS201 Key Listen |
| 8 | Detector | TOGGLE | peak / RMS | RaneNote 155's rms-for-expanders |

**The seed proposed ten; Hold is dropped**, because `hold_ms` does nothing in
`DYN_EXPAND` (B5) and a knob that does nothing is worse than an absent one —
said in the class docstring, not only here. `rms_ms` is **not** exposed
(§8.2). Characters: none. **Patches**, 0 being the constructor's defaults on
the 0–127 grid: **Gentle Lift**, **Noise Floor Trim**, **Snare Tighten**,
**Guitar Amp Hum**, **Room Reduction**, **Hard Downward**. Key Listen is a
diagnostic and is off in every one.

**`capabilities` = `()`** — nothing in an expander's law refers to tempo and
neither source's unit has a tempo input, so `self._transport()` is never read.

## 7. Defects in the current class the rebuild must not repeat

- **No surface.** `MACRO_LABELS = ()` (`dynamics.py:147`), `PATCHES = {0:
  ("Default", ())}` (`:149`); threshold, ratio, attack and release
  (`:151-152`) are construction-only and can never move again.
- **The floor is invisible** — `ratio` is exposed but not the −60 dB clamp
  under it (`audioif_dynamics.c:185`), so 8:1 stops obeying the ratio 7.5 dB
  below threshold and nothing says so.
- **The detector type is undocumented** (`dynamics.py:141`), so a threshold
  set from an RMS meter is 3 dB out on a sine and further on anything peakier.
- **No hold, no key filter, no depth**, and nothing states the omissions, so
  they read as design.

## 8. Open questions — settled at Station A

1. **Distinct from `NoiseGate`? Yes — the palette decides it, not taste.**
   The one-shot machine is gated on `mode == AUDIOIF_DYNAMICS_GATE`
   (`audioif_dynamics.c:452-453`) and replaces the gain computer with a binary
   open/floor (`:679-724`): one node cannot be both a ratio law and a trigger.
   `Expander` is `DYN_EXPAND` with Ratio and Depth and no Hold; `NoiseGate` is
   `DYN_GATE` with Hold and Hysteresis and no Ratio. **Not** one
   implementation with two defaults.
2. **A settable RMS window? No.** At the unset 10 ms window the gap is
   **0.05 dB** against E2's 0.5 (B2). What the window costs is named instead,
   in the class docstring: it floors Attack (t63 **0.75 ms** at
   `attack_ms=0.01`, B6), and the peak position removes it.
3. **E5's confidence.** Moot here — E5 is not demonstrable by this class at
   all (B5) — and **left at medium** for `NoiseGate`, which measures it and
   picks between S1's two disagreeing Hold statements (App. R).
4. **The DS201 schematic** was not obtained. No trait depends on a component
   value and Station A left the grade at literature with S5 in hand: a
   one-line note for the survey, **not a blocker, not this class's to chase**.
   *Arthur.*

**Nothing in §8 is left open.** Where a question could not be answered from
this class's evidence it is named above as `NoiseGate`'s or Arthur's, with the
reason, rather than carried as an open item this rebuild is waiting on.

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

### App. B — Station A bench, 2026-09-07

Every number §§3–8 cite as B1–B7 is printed by one committed file and by
nothing else, against the CPython build of audioif in `audiocomponents/.venv`
at the pin `2f6cbc3`, 48 kHz, stereo, 16-bit. It drives
`audiodynamics.Dynamics` directly, not the class: its subject is what the
*palette* does.

```
$ PYTHONPATH=lib .venv/bin/python tools/phase0_probes/expander_station_a.py
B1  E1, the law - threshold -20 dBFS, RMS detector, depth -90 dB.
    The span per ratio is bounded by the int16 floor, not by the
    node: E1's 30 dB clause asks for 30*(ratio-1) dB of output
    range, which is 210 dB at ratio 8.
    ratio 1.5  span 30.0 dB  slope 1.5068 (+0.45%)  max residual 0.080 dB
    ratio 2.0  span 30.0 dB  slope 2.0299 (+1.49%)  max residual 0.459 dB
    ratio 4.0  span 15.0 dB  slope 4.0702 (+1.76%)  max residual 0.411 dB
    ratio 8.0  span  7.5 dB  slope 8.1522 (+1.90%)  max residual 0.488 dB
    above threshold at -15 dBFS: -0.002 dB
    above threshold at -10 dBFS: -0.002 dB
    above threshold at -6 dBFS: -0.002 dB

B2  E2, the detector - threshold -20 dBFS, ratio 2, attack 5 ms,
    release 150 ms; sine and square at equal RMS -35 dBFS.
    detector=peak sine -47.63  square -50.05  gap 2.43 dB
    detector=rms  sine -50.00  square -50.05  gap 0.05 dB

B3  E3, the key band - 500-2000 Hz, threshold -40 dBFS, ratio 4,
    depth -60 dB (so the floor is -60), RMS detector.
    poles=1     250 Hz  -60 dBFS/-60.0 dB  -40 dBFS/-21.8 dB  -20 dBFS/0.0 dB  +0 dBFS/0.0 dB
    poles=1    1000 Hz  -60 dBFS/-60.0 dB  -40 dBFS/-6.6 dB  -20 dBFS/0.0 dB  +0 dBFS/0.0 dB
    poles=1    4000 Hz  -60 dBFS/-60.0 dB  -40 dBFS/-21.7 dB  -20 dBFS/0.0 dB  +0 dBFS/0.0 dB
    poles=2     250 Hz  -60 dBFS/-60.0 dB  -40 dBFS/-43.8 dB  -20 dBFS/0.0 dB  +0 dBFS/0.0 dB
    poles=2    1000 Hz  -60 dBFS/-60.0 dB  -40 dBFS/-13.2 dB  -20 dBFS/0.0 dB  +0 dBFS/0.0 dB
    poles=2    4000 Hz  -60 dBFS/-60.0 dB  -40 dBFS/-43.4 dB  -20 dBFS/0.0 dB  +0 dBFS/0.0 dB
    rejection, poles=2, a -20 dBFS tone per frequency:
         125 Hz  gain   -15.12 dB  implied detector   -45.04 dBFS
         250 Hz  gain     0.00 dB  implied detector     0.00 dBFS
         500 Hz  gain     0.00 dB  implied detector     0.00 dBFS
        1000 Hz  gain     0.00 dB  implied detector     0.00 dBFS
        2000 Hz  gain     0.00 dB  implied detector     0.00 dBFS
        4000 Hz  gain     0.00 dB  implied detector     0.00 dBFS
        8000 Hz  gain   -13.24 dB  implied detector   -44.41 dBFS

B4  E4, depth - input -6 dBFS, threshold 30 dB above it (+24 dB),
    ratio 8, RMS detector; the settled attenuation against the
    setting.
    depth   +0.0 dB ->    -0.00 dB  (error -0.00)
    depth  -20.0 dB ->   -20.00 dB  (error -0.00)
    depth  -40.0 dB ->   -40.02 dB  (error -0.02)
    depth  -60.0 dB ->   -60.15 dB  (error -0.15)
    depth  -80.0 dB ->   -81.68 dB  (error -1.68)

B5  E5, the one-shot - a 1 ms full-scale burst then silence, under
    a 200 ms attack. Gain read once per 256-frame block.
    EXPAND hold_ms=None best gain    0.00 dB   first six blocks -43.4 -7.6 0.0 0.0 0.0 0.0
    EXPAND hold_ms=20.0 best gain    0.00 dB   first six blocks -43.4 -7.6 0.0 0.0 0.0 0.0
    GATE   hold_ms=None best gain  -80.00 dB   first six blocks -80.0 -80.0 -80.0 -80.0 -80.0 -80.0
    GATE   hold_ms=20.0 best gain   -1.96 dB   first six blocks -31.6 -25.7 -22.3 -19.9 -18.1 -16.6

B6  E6, the times - a 20 dB level step, threshold -20 dBFS,
    ratio 2, depth -20 dB, RMS detector. attack_ms and release_ms
    are one-pole time constants, so 10-90 %% of the gain-in-dB
    trace is a function of the step size too.
    attack      0.01 ms  t63     0.750 ms  10-90     0.500 ms  10-90/set 50.00   (-10.0 -> 0.0 dB)
    attack      1.00 ms  t63     1.250 ms  10-90     1.000 ms  10-90/set  1.00   (-10.0 -> 0.0 dB)
    attack     10.00 ms  t63     4.250 ms  10-90     5.000 ms  10-90/set  0.50   (-10.0 -> 0.0 dB)
    attack    100.00 ms  t63    18.750 ms  10-90    25.500 ms  10-90/set  0.26   (-10.5 -> 0.0 dB)
    attack   1000.00 ms  t63   125.750 ms  10-90   249.000 ms  10-90/set  0.25   (-20.0 -> 0.0 dB)
    release     2.00 ms  t63    45.250 ms  10-90    33.000 ms  10-90/set 16.50   (0.0 -> -10.0 dB)
    release    10.00 ms  t63    57.750 ms  10-90    37.000 ms  10-90/set  3.70   (0.0 -> -10.0 dB)
    release   100.00 ms  t63   297.250 ms  10-90   251.000 ms  10-90/set  2.51   (0.0 -> -9.8 dB)
    release  1000.00 ms  t63  2812.250 ms  10-90  2536.500 ms  10-90/set  2.54   (0.0 -> -9.8 dB)
    release  4000.00 ms  t63 11263.750 ms  10-90 10140.500 ms  10-90/set  2.54   (0.0 -> -9.8 dB)
    the fastest attack, with the RMS window taken out of it:
      attack_ms=0.01, detector=rms   t63 0.750 ms (36.0 samples at 48 kHz)
      attack_ms=0.01, detector=peak  t63 0.250 ms (12.0 samples at 48 kHz)

B7  latency, the wire states and the tail.
    impulse in at frame 128, out at frame 128
    ratio 1.0   byte-identical to the source: True  (worst 0 LSB)
    depth 0 dB  byte-identical to the source: True  (worst 0 LSB)
    key_listen=0: last non-zero frame after the burst ends: -1
    key_listen=1: last non-zero frame after the burst ends: 2905
```

**What the seven say, in one line each.**

- **B1 — E1's law holds; E1's *span* does not fit in 16 bits.** The fitted
  slope is within **1.90 %** of the set ratio at 1.5, 2, 4 and 8 and the worst
  residual is **0.488 dB** against E1's 0.5; above threshold the gain is
  **−0.002 dB** against E1's ±0.05. But the span each ratio was measured over
  is 30, 30, 15 and 7.5 dB, not 30 dB throughout: E1 asks for 30 dB below
  threshold, which at ratio 8 is 210 dB of output range below a threshold that
  is itself below full scale. The measurement stops where the int16 output
  quantises to exact zero. *The law is the node's; the 30 dB clause is the
  statement's own arithmetic.*
- **B2 — E2 is reached, and it is the option that reaches it.** The equal-RMS
  sine/square gap is **0.05 dB** with `detector="rms"` against E2's 0.5 dB
  allowance, and **2.43 dB** with the peak detector. The seed measured 0.90 dB
  as the best a mean-absolute follower could do (V-E1); the RMS detector beats
  that by a factor of eighteen.
- **B3 — the band is real and E3's floor clause is not reachable.** Both ends
  move and both reject: at two poles a −20 dBFS tone two octaves outside the
  500–2000 Hz band reads **−45.04 dBFS** at the detector, 25 dB of rejection.
  But a −20 dBFS out-of-band tone already opens the gain to **0.0 dB** against
  a −40 dBFS threshold, and E3 asks the gain to stay at its floor to 0 dBFS —
  better than 40 dB an octave out, an eighth-order key filter. No source states
  an order and the node ask specified 12 dB/octave.
- **B4 — E4 is met.** The settled attenuation tracks the setting to
  **−0.00 / −0.00 / −0.02 / −0.15 dB** at 0, −20, −40 and −60 dB, against E4's
  0.5 dB, and the span reaches **−81.68 dB** at the −80 setting, so "at least
  −80 dB" is met. (The seed's composed route reached −60 dB with 0.32 dB of
  error and stopped there; `depth_db` halves that error and goes 20 dB further,
  for one float instead of a 32 KB ring.)
- **B5 — E5 is not reachable in this mode, and the palette says why.** A 1 ms
  burst under a 200 ms attack renders the *same* `DYN_EXPAND` trace with and
  without `hold_ms=20` — `−43.4, −7.6, 0.0, 0.0 …` in both — while the same
  burst in `DYN_GATE` goes from never opening (`−80.00` for every block) to
  **−1.96 dB**. `hold_ms` is silently inert in `DYN_EXPAND`
  (`audioif_dynamics.c:452-453`), and the machine it drives replaces the ratio
  law rather than sitting under it (`:679-724`).
- **B6 — the times track, but not by E6's clock.** `attack_ms` and
  `release_ms` are one-pole time constants. Measured 10-90 % over the setting
  is **0.25** at the long attacks and **2.54** at the long releases, both
  stable across a decade — a fixed factor, not drift — and both a function of
  the 20 dB step as much as of the setting. E6's "within 15 % of the setting"
  is a claim about a 10-90 % time being the same number as a time constant,
  which it is not. On the fastest setting, `attack_ms=0.01`, the RMS window
  puts t63 at **0.75 ms** and the peak detector at **0.25 ms** — 12 samples,
  which is this trace's own resolution (the 1 kHz sine's peaks are 12 and 36
  samples apart), so E6's "one sample or less" is met as far as this
  measurement can see and is not resolved further here.
- **B7 — latency zero, two wire states, and the one path with memory.** An
  impulse at frame 128 comes back at frame **128**. Both wire states are
  **byte-identical to the source, worst 0 LSB**: Ratio at 1.0, and Depth at
  0 dB. After a 200 ms burst the audio output's last non-zero frame is the
  burst's own — a multiplicative VCA has no tail. `key_listen=1` is the
  exception, **2905 frames (60.5 ms at 48 kHz)**, because the output is then
  the side-chain's signal and the 25 Hz high-pass has memory; that is a
  diagnostic state, off in every patch, and it is recorded rather than folded
  into `TAIL_SAMPLES`.

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


*(from §1, the full paragraph, moved at Station A 2026-09-07 under the length rule)*

The DS201 is a dual-channel gate whose intelligence is all in the side-chain:
the audio path is input, gain element, output, with a Bypass position that
"routes the input signal to the output with no processing" (S1). **The gain
element is a VCA**, sourced from Drawmer's own service documents (S5); no
trait below rests on it (App. R). The control path takes the channel's own
input or an external Key and passes it through two variable filters in
series — a Low Frequency control **25 Hz to 4 kHz** that "works by severely
attenuating frequencies below the cut-off", and a High Frequency control
**250 Hz to 35 kHz** above it, so "it is the range between the two settings
that is allowed to pass" — then compares the result with a Threshold settable
**−54 dB to infinity** (S1; Drawmer's own current manual, S4, says "-50dBFs" —
the editions differ, §2).

Crossing it starts a one-shot envelope: Attack **10 µs to 1 s**, Hold **2 ms
to 2 s**, Decay **2 ms to 4 s**, committed once triggered (S1, quoted at E5).
What the VCA settles to when shut is not zero but **Range**, "the amount of
attenuation applied to the input signal when the gate is closed, variable from
0 dB to −80 dB" (S1's 2005 edition; S4's 2008 manual says "0dB - 90dB").
Gate/Duck, Key Listen and Stereo Link are the remaining switches (App. R).
**There is no ratio: below threshold the DS201 goes to Range, not down a
slope. An expander is the same box with the gain computer told to do
something else** — RaneNote 155: "the topology for an expander looks just
like a compressor … the expander reduces gain for signals below the
threshold. The ratio still defines output change verses [sic] input change",
with an RMS detector, and "true rms detection is necessary for compressor and
expander modes" where a gate needs peak (S2).

*(from §4, the prose the length rule shortened, moved at Station A 2026-09-07 under the length rule)*

**Composition was weighed and rejected**, on the seed's own numbers: V-E4's
`Splitter`-plus-two-`Mixer`s Depth reached −60 dB with 0.32 dB of error and a
32 KB ring, where `depth_db` is one float and reaches −80; and a steeper key
band out of `audiobiquad.Biquad` sections fed to `Dynamics.key()` needs four
sections per end to change E3's verdict, where the ask itself asked for
12 dB/octave. **The class builds one node and no others**, so the Tier 3
budget is a budget for one node.

**`key(sample)` is a constructor option, not a macro** — the DS201's external
Key input (S1, S3), borrowed like `source`: never owned, reset or deinited.

**Portability tier: audioif.** `audiodynamics` is audioif's own module, not a
CircuitPython port (`audioif/docs/upstream-diff.md:661`), so the class carries
the guarded import and `_require_modules()` raises a clear `ImportError` on a
stock board. Python computes nothing per sample: each macro is one
`Dynamics.set()`, and C runs the detector, the gain computer and the VCA.

*(The seed's pre-Phase-1 palette argument, and what each ask was refuted
against, are in **App. R** — nothing deleted.)*

*(from §1, the second précis the length rule shortened, moved at Station A 2026-09-07 under the length rule)*

The DS201 is a dual-channel gate whose intelligence is all in the side-chain:
input, VCA, output, with a Bypass that "routes the input signal to the output
with no processing" (S1). The key path is **two variable filters in series** —
Low Frequency 25 Hz–4 kHz, High Frequency 250 Hz–35 kHz, "it is the range
between the two settings that is allowed to pass" — feeding a Threshold, an
Attack (10 µs–1 s) / Hold (2 ms–2 s) / Decay (2 ms–4 s) envelope that is
committed once triggered, and a **Range** floor "variable from 0 dB to −80 dB"
rather than silence.

**There is no ratio: below threshold the DS201 goes to Range, not down a
slope. An expander is the same box with the gain computer told to do something
else** — RaneNote 155: "the expander reduces gain for signals below the
threshold. The ratio still defines output change verses [sic] input change",
with an RMS detector, and "true rms detection is necessary for compressor and
expander modes" where a gate needs peak (S2). Every quoted range above, its
edition disagreements and the switches this précis leaves out are in **App. R**.
