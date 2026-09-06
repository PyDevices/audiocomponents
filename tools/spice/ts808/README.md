# TS808 in ngspice — Phase 0 of the effects program

Proof that the SPICE workflow in the effects vision (`docs/effects-vision.md` §4 in the PyDevices anchor repo)
works on the `Overdrive` standout, the Ibanez TS808 Tube Screamer: schematic
read → netlist we wrote → ngspice → numbers → falsifiable traits. Two stages
are modelled, the clipping ("drive") stage and the tone/volume stage. The
input and output buffers are not (they are unity followers).

## Run

```sh
./run.sh                                   # ngspice -b, ~2 s, writes out/*.csv
/home/brad/gh/pydevices/micropython-vst3/.venv/bin/python analyze.py
```

`run.sh` needs `/usr/bin/ngspice` (override with `NGSPICE=`); `analyze.py`
needs numpy and nothing else. `analyze.py` exits non-zero if either sanity
check in the brief fails (corner within a few percent of analytic; THD rising
monotonically with drive at each input level).

## Files

| File | What it is |
|---|---|
| `ts808_drive.cir` | Clipping stage: non-inverting 4558 stage, R4/C3 to ground on the (−) input, R6 + Distortion pot + anti-parallel 1N4148 pair + 51 pF in the feedback loop. Its `.control` block runs nine 1 kHz transients (pot at 0 / 0.5 / 1 of 500K × input peaks 50 / 200 / 500 mV) and one small-signal AC sweep at pot max. |
| `ts808_tone.cir` | Tone/volume stage: R7/C5 low-pass node with R9 to bias, the 20K Tone pot strung between the op-amp's (+) and (−) inputs with the 220 Ω/0.22 µF network on its wiper, 1K feedback, then C7/R12 and the Level pot at max. AC sweep at tone 0 / 0.5 / 1. |
| `models.lib` | Shared by both: the 1N4148 (Nexperia's parameter values in our `.model` line) and the behavioural JRC4558. |
| `run.sh` | Runs both decks under `ngspice -b`, converts `wrdata`'s whitespace columns to commas, fails on any ngspice error. |
| `analyze.py` | Reads `out/`, prints the results below. numpy only. |
| `out/` | Generated: 9 transient CSVs (`time, v(out), v(inp)`), 1 drive AC CSV (`frequency, vdb(out), vp(out)`), 3 tone AC CSVs (`frequency, vdb(tout), vp(tout), vdb(lv), vp(lv)`), two ngspice logs. Phase columns are **radians** (ngspice's default for `vp()`). |

Pot positions are resistance fractions, not knob rotation: `pos` is the
fraction of the 500K Distortion pot in circuit (0 / 250K / 500K), `tone` is
the fraction of the 20K Tone pot between the wiper and the (+) end, so
`tone = 0` is the bass end (wiper on the low-pass node) and `tone = 1` the
treble end (wiper on the feedback node). The real pots are log ("500K Log")
and G-taper respectively, so mid-rotation on the pedal is not `0.5` here.

## Simplifications, named

- **Op-amp**: one transconductance stage into an R-C that sets the open-loop
  gain (100 dB) and a single dominant pole so that GBW = 3 MHz, then a hard
  min/max clamp 1 V inside each rail. No slew limit (1–1.7 V/µs on the
  datasheets; the stage needs 6 mV/µs at 1 kHz), no offset, bias current,
  noise, second pole, or output resistance. In the drive stage the diodes hold
  the swing to about ±1 V around the 4.5 V bias, so the clamp never engages.
- **Input buffer** omitted: the drive stage is driven by an ideal source
  through C2/R5. The series resistor ElectroSmash draws as "RA" carries no
  value on the drawing and is left out.
- **Supply and bias** are ideal 9 V and 4.5 V sources (the real bias is a
  10K/10K divider with a 47 µF cap — AC ground either way).
- **Diodes**: 1N4148 per the brief; the drawing says MA150. Both diodes are
  the same model, so the clipping is exactly symmetric — see trait 2.
- **Level pot** fixed at maximum; C7/R12/P3 are in the deck and reported as
  a second column, but the tone numbers below are at the op-amp's pin 7.
- **Pot tapers** not modelled (see above).
- **1 Ω** added in series with each pot section so a zero-ohm resistor never
  appears.
- Transients use a fixed 1 µs step and `linearize` onto that grid; the THD
  window is the last 10 of 30 ms (the C2/R5 coupling has a 10 ms time
  constant). THD sums harmonics 2–20.

## Sources reached, with the license call for each

Every component value and every model parameter in the decks comes from one
of these, fetched on 2026-09-06.

**S1. ElectroSmash, "Tube Screamer Circuit Analysis"**, read at the MAS
Effects archive mirror
<https://electrosmash.mas-effects.com/tube-screamer-analysis.html>, including
its two stage drawings
<https://electrosmash.mas-effects.com/images/tube-screamer-analysis/tube-screamer-clipping-amplifier.png>
and
<https://electrosmash.mas-effects.com/images/tube-screamer-analysis/tube-screamer-tone-volume.png>.
The original host `www.electrosmash.com` did not resolve from this machine
(`getaddrinfo ENOTFOUND`, twice), so the mirror was used; its footer reads
"An unofficial, non-commercial backup of ElectroSmash.com, preserved by MAS
Effects from the Internet Archive. All content and images belong to their
original authors/owners." ElectroSmash's own rights page could not be fetched;
a web search result for `electrosmash.com/rights` quotes it as "All work in
Electrosmash.com is licensed under a Creative Commons
Attribution-NonCommercial 4.0 International License." **License call:** a
schematic on a hobby site is a document (vision §5); it was read for topology
and values and nothing from it is reproduced — the netlists are ours. The
values taken: C2 1 µF, R5 10K, R4 4K7, C3 0.047 µF, R6 51K, P1 500K log,
C4 51 pF, D1/D2 MA150 (text: "MA150/1N4148/1N914"), U1 JRC4558, 9 V supply,
4.5 V bias; R7 1K, C5 0.22 µF, R9 10K, P2 20K, R8 220 Ω, C6 0.22 µF, R11
1K, C7 1 µF, R12 1K (the drawing labels both 1K output resistors R11; the BOM
lists R11 and R12 as 1K), P3 100K. Its stated figures we check against: gain
12–118, high-pass corner 720 Hz, tone low-pass 723.4 Hz, treble corner
3.2 kHz. Two places where the mirror's text and drawing disagree were
resolved by the drawing plus the site's own arithmetic: the text summary
gives the (−) input resistor as 1K, but 720 Hz and gain 118 both need 4K7
(drawn as R4 4K7); the BOM swaps R8/R10 (220 Ω vs 1K) relative to the text,
but the drawing puts 220 Ω on the wiper and 1K in the feedback, and the
14.9 dB treble boost that PedalPCB (S5) also reports needs it that way.

**S2. Nexperia, 1N4148 SPICE model**,
<https://assets.nexperia.com/documents/spice-model/1N4148.prm>: IS 4.352E-9,
N 1.906, BV 110, IBV 0.0001, RS 0.6458, CJO 7.048E-13, VJ 0.869, M 0.03,
FC 0.5, TT 3.48E-9, in a subcircuit with a 5.827E+9 Ω reverse-mode shunt. The
file carries no license text. Nexperia's Terms of Use
<https://www.nexperia.com/about/terms-and-policies/terms-of-use> say
"Copyright and all other proprietary rights in the Content … rests with
NEXPERIA or its licensors", "Software made available for downloading … is
licensed subject to the terms of the applicable license agreement", and all
content is "PROVIDED 'AS IS'". **License call:** not permissive; treated as a
document. `models.lib` carries the ten parameter values (facts about the
part, cited) in our own `.model` line and does not reproduce the file's
text. If Arthur wants even that out of an MIT tree, `run.sh` could download
the file at run time instead — his call. (Diodes Inc.'s 1N4148W model was
tried first and returned HTTP 403.)

**S3. Nisshinbo (New Japan Radio) NJM4558 datasheet, Ver.2013-11-05**, read
via an HTML rendering at
<https://pdf.datasheet.support/50c18840/njr.com/NJM4558LD.html>: "Large
Signal Voltage Gain 86 dB (min), 100 dB (typ)" at RL ≥ 2 kΩ, VO = ±10 V;
"Maximum Output Voltage Swing ±12 V (min), ±14 V (typ)" at RL ≥ 10 kΩ;
"Gain Bandwidth Product 3 MHz"; "Slew Rate 1 V/µs"; operating ±4 V to ±18 V.
These give the op-amp model its AOL = 1e5, VSAT = 1 V and GBW = 3 MHz. No
terms found on the aggregator page. **License call:** numbers read from a
datasheet — facts. (The manufacturer's and DigiKey's PDFs were fetched but
their text could not be extracted here; DigiKey's HTML copy returned 410;
datasheet4u 403; Mouser timed out; Marutsu's PDF was unreadable.)

**S4. Texas Instruments RC4558 product page**,
<https://www.ti.com/product/RC4558>: GBW 3 MHz typ, slew rate 1.7 V/µs typ,
total supply 10–30 V; datasheet identified as SLOS073H (Rev. H, Oct 2024) at
<https://www.ti.com/document-viewer/rc4558/datasheet> (only its table of
contents rendered). Cross-check for GBW. **License call:** facts.

**S5. Cross-checks, read only:** PedalPCB forum, "Tone Stacks Part 3 —
Tube Screamer"
<https://forum.pedalpcb.com/threads/tone-stacks-part-3-tube-screamer-hm-2-gyrators.8557/>
(bass-end corner ≈ 400 Hz, treble boost from 725 Hz to 4 kHz, maximum
14.9 dB, passive low-pass 720 Hz); m0xpd, "Analysis of the Tube Screamer"
<https://m0xpd.blogspot.com/2012/11/analysis-of-tube-screamer.html> (220 nF
paralleled with 10 kΩ at the tone input, 220 nF/220 Ω on the wiper, LTspice
and measurement overlaying his analysis); Wikipedia, "Ibanez Tube Screamer"
<https://en.wikipedia.org/wiki/Ibanez_Tube_Screamer> (CC BY-SA 4.0; JRC4558D,
"two silicon diodes in anti-parallel arrangement into the negative feedback
circuit", symmetric because Boss held the asymmetric-clipping patent).
Nothing taken from these but confirmation.

**Not reached:** R.G. Keen's GEOFEX "The Technology of the Tube Screamer"
(`geofex.com`, connection reset on three attempts, http and https);
`web.archive.org` (blocked for this tool); pedalparts.co.uk's TS PDF was
fetched but is a board photo and layout with no values, and was not used.

## Results — `analyze.py` output, verbatim, from the run on 2026-09-06

```
1. Drive stage, small-signal AC at drive max (pos = 1)
   peak gain                   39.7 dB at    1905 Hz
   gain at 100 Hz / 1 kHz / 5 kHz    23.3 /  38.8 /  37.7 dB
   high-pass corner (fit)      720.6 Hz   analytic 1/(2 pi R4 C3)        =   720.5 Hz   dev  +0.0 %
   low-pass corner  (fit)       6046 Hz   analytic 1/(2 pi (R6+P1) C4)   =    5664 Hz   dev  +6.8 %   (with the diodes' 11.3 MOhm each in parallel: 6215 Hz, dev  -2.7 %)
   plateau gain 1+A (fit)      107.8      analytic 1+(R6+P1)/R4        =   118.2      dev  -8.8 %   (with the diodes: 107.8, dev  -0.0 %)
   fit residual              0.001 dB rms over 150 points, 20 Hz .. 20 kHz; op-amp aol = 1e+05, gbw = 3 MHz from models.lib
   ideal-op-amp fit            741.9 Hz corner (dev  +3.0 %), 4830 Hz low-pass, gain 111.0, residual 0.001 dB rms   -- the 4558's finite GBW read as a corner shift
   naive -3 dB below peak      583.8 Hz   (biased low by the 51 pF pole 8x above; not the corner)

2. Drive stage, 1 kHz transient: THD and harmonics 2..5 re fundamental
   (window 20..30 ms = 10 periods, THD over harmonics 2..20)
   pos   in pk    out pk    h1 gain   THD      h2       h3       h4       h5
         (mV)     (V)       (dB)      (%)      (dB)     (dB)     (dB)     (dB)
     0      50    0.356      17.7       8.4     -94.6    -21.5   -109.0    -46.0
   0.5      50    0.412      19.7      26.7     -90.4    -12.9    -92.6    -19.1
     1      50    0.415      19.9      28.3     -90.3    -12.6    -92.1    -18.4

     0     200    0.619      10.8      20.8     -90.8    -14.8    -94.1    -21.6
   0.5     200    0.632      11.1      26.2     -90.4    -13.6    -92.3    -18.9
     1     200    0.633      11.1      26.6     -90.3    -13.5    -92.2    -18.8

     0     500    0.972       6.4      19.2     -90.9    -16.2    -94.1    -21.7
   0.5     500    0.978       6.5      20.8     -90.8    -15.8    -93.5    -20.9
     1     500    0.978       6.5      21.0     -90.8    -15.8    -93.5    -20.9

   THD vs drive at  50 mV: 8.4% < 26.7% < 28.3%   rises monotonically: OK
   THD vs drive at 200 mV: 20.8% < 26.2% < 26.6%   rises monotonically: OK
   THD vs drive at 500 mV: 19.2% < 20.8% < 21.0%   rises monotonically: OK

3. Tone stage, small-signal gain at op-amp pin 7 (Level at max), dB
   tone     100 Hz    1 kHz    5 kHz   |  analytic, ideal op-amp:  100 Hz    1 kHz    5 kHz   |  after C7/R12/P3 (lv): 100 Hz  1 kHz  5 kHz
      0     -1.12    -9.64   -19.95   |                            -1.12    -9.64   -19.95   |                         -1.21  -9.73 -20.04
    0.5     -0.91    -4.50   -16.13   |                            -0.91    -4.50   -16.13   |                         -0.99  -4.59 -16.22
      1     -0.78     0.53    -3.51   |                            -0.78     0.52    -3.54   |                         -0.87   0.44  -3.60
   (analytic low-pass node: 1/(2 pi (R7||R9) C5) = 796 Hz; ElectroSmash's 1/(2 pi R7 C5) = 723.4 Hz ignores R9; treble shelf zero 1/(2 pi R8 C6) = 3288 Hz, max boost 1+R11/R8 = 14.9 dB)

Sanity: high-pass corner within a few percent of analytic: OK (0.0 %);  THD monotonic in drive at every input level: OK
```

### Reading the numbers

- **High-pass corner: 720.6 Hz simulated vs 720.5 Hz analytic.** The corner
  is extracted by fitting the stage's three-parameter small-signal model —
  shelf pole, 51 pF pole, plateau gain — to the AC sweep, with the 4558's
  single-pole open loop (as `models.lib` defines it) inside the fit. The
  fit is never told the analytic corner. Fitting the same data with an
  *ideal* op-amp instead reads 741.9 Hz (+3.0 %): the 4558's finite GBW
  (loop gain ≈ 27 at 1 kHz) droops the response by 0.1 dB around 1 kHz, and
  a model without it absorbs that as a corner shift. The naive "−3 dB below
  the peak" reading, 584 Hz, is not the corner at all — the 51 pF pole is
  only 8× above it. Both are printed so nobody reaches for them.
- **Plateau gain 107.8, not ElectroSmash's 118.** Two zero-biased 1N4148s
  sit across the feedback network; at 0 V the Nexperia model gives each a
  small-signal resistance N·Vt/IS = 11.3 MΩ, and 551K ‖ 5.7 MΩ = 502K. The
  51 pF pole moves with it (6215 Hz), and the last −2.7 % is the two
  0.7 pF junction capacitances on top of 51 pF (6215 × 51/52.4 = 6049 Hz).
  SPICE and an exact analytic of the same network agree to 0.001 dB at every
  frequency; the differences from ElectroSmash's round numbers are theirs.
- **THD.** Rises with drive at every input level (the brief's check). At
  drive max it *falls* as the input rises (28.3 → 26.6 → 21.0 %): the
  non-inverting stage passes the input straight through (its "+1") and adds
  the clipped feedback voltage on top, so the output peak is the input peak
  plus a diode drop — 0.415, 0.633, 0.978 V for 50, 200, 500 mV in — and the
  dry part keeps growing while the clipped part has stopped. Even harmonics
  are at −90 dB, i.e. zero: the topology is symmetric.
- **Tone.** The low-pass node is 796 Hz with 0.8 dB of passband loss (R9's
  10K loads R7's 1K), not the 723 Hz quoted without R9. The knob moves 1 kHz
  by 10.2 dB and 5 kHz by 16.4 dB, but 100 Hz by only 0.34 dB. The
  independent ideal-op-amp nodal solve agrees with SPICE to 0.03 dB.

## What this says an `Overdrive` trait should look like

The drive stage is a shelf, not a high-pass: unity gain below ~6 Hz, rising
to a plateau of ~108 above the 720 Hz R4·C3 pole, then rolling off above
~6 kHz through the 51 pF — so a note's fundamental is driven into the diodes
by a gain that depends on its pitch, while the note itself always passes
through at unity and has the clipped feedback voltage added to it. Three
statements a rebuild must survive, each with the number that fails it:
**(1) Pitch-dependent drive.** At maximum drive the small-signal gain at
100 Hz is 15.5 dB below the gain at 1 kHz (23.3 vs 38.8 dB), so at equal
input level a 100 Hz tone must show less THD than a 1 kHz tone; a rebuild
whose pre-clip gain at 100 Hz is within 10 dB of its 1 kHz gain at max drive
fails. **(2) Symmetric soft clipping with the dry signal summed.** Harmonic
energy is odd-only (h2 and h4 below −60 dB with matched diodes), h3 dominates
and moves from −21.5 dB (min drive, 50 mV) to −12.6 dB (max drive, 50 mV),
and the output peak tracks input peak + 0.37–0.48 V so THD at max drive falls
as input rises; a rebuild with a second harmonic above −40 dB, or whose THD
at max drive keeps rising from 200 to 500 mV, fails. (This disconfirms the
vision's illustrative "gains a second harmonic as the stage asymmetry
engages": the standout's topology has no asymmetry; any is a component
mismatch and belongs to a character, not the trait.) **(3) A fixed low-pass
plus a movable shelf, not a moving corner.** The tone control is a 796 Hz
first-order low-pass that never moves, followed by a stage that is a unity
follower with an extra 220 Ω/220 nF shunt at the bass end and a +14.9 dB
shelf with its zero at 3.3 kHz at the treble end; its whole range moves
1 kHz by 10 dB and 5 kHz by 16 dB while 100 Hz moves under 0.5 dB, and the
brightest setting is still 3.5 dB down at 5 kHz; a rebuild whose tone knob
changes 100 Hz by more than 1 dB, or whose brightest setting is flat at
5 kHz, fails.
