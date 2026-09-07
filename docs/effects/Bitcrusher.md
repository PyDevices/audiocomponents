# Effects Dossier — `Bitcrusher` (early 12-bit samplers; the E-mu SP-1200)

**Class:** `lib/audioeffects/drive.py` — read once, for §7, and not otherwise
consulted.
**Family / phase:** Drive, roadmap Phase 4
**Standout:** E-mu SP-1200, per vision §4.2 (*proposed*) — **confirmed**, with
its scope narrowed (§2, Appendix C).
**Grade:** literature. The scan's schematic pages were not read, so no
component values were reached; every number in §3 comes from the manual's
prose or from the quantization and zero-order-hold literature.
**Portability tier:** **stock** — corrected 2026-09-06 by the palette
verification (§4, §5): bit depth is `audiofilters.Distortion` in `LOFI`,
round-to-nearest is an `audiomixer.Mixer` DC, and the sample-rate hold is two
`audiospeed.SpeedChanger` nodes in series — every one a CircuitPython port. One
caveat a board reader needs: `CIRCUITPY_AUDIOSPEED` is gated per port and only
`ports/raspberrypi` sets it upstream (`audioif/docs/upstream-diff.md:143-145`),
so "stock" here means a stock build *that compiles `audiospeed`*. The tier
becomes **audioif** only if §5's surviving T6 ask is granted.
**Capabilities:** `()` — nothing here is tempo-related; Rate is in hertz, not
note values (D10).
**Status:** seed (Phase 0), written 2026-09-06

## 1. The architecture, in one paragraph

For a digital machine the "circuit" is an architecture, and the SP-1200's is
short. Audio enters through an anti-aliasing filter the manual describes only
generically — "a very steep cutoff on the order of 42dB per octave and a
cutoff frequency of less than half the sample rate" — and is digitised by
successive approximation through the *same* converter that plays sound back:
"The DAC is a standard 12 bit linear device" (S1). The word is **12-bit
linear**, not companded, in "complement offset binary" ("most negative value =
000 hex, ‘zero’ = 800 hex, most positive = fff hex"), written at a fixed
period — "Sample period is fixed at {1/26.04)kHz" — into 256 K words of DRAM.
Playback is eight monophonic channels, each pitched by a per-channel increment
added to a phase accumulator whose carry advances the read pointer, and **"A
carry of 0 will cause the same sample to be played twice"**: a zero-order hold
at a fractional rate, no interpolation. Six of the eight outputs then pass an
SSM filter. There is no panel control for word length or rate — on the machine
both are architecture, and the class turns exactly those two into knobs. It
takes nothing else: the SSM filters are `LowPass`'s business, and the input
filter returns only as an option defaulting **off**, because the aliasing it
removes is the effect (T5). No LFO, no nonlinearity, no filter in the signal
path.

## 2. Sources and license calls

Every source reached in this run; quotations and license text as read are in
**Appendix D**.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1. E-mu SP-1200 Service Manual (1987), OCR text of the archive.org scan | §1; T6 | **Two answers, and the document's own wins.** … (App. S1) | https://archive.org/stream/emu-sp-1200-service-manual-1987/Emu-SP-1200-Service-Manual-1987_djvu.txt · https://archive.org/metadata/emu-sp-1200-service-manual-1987 | yes |
| S2. Lipshitz, Wannamaker & Vanderkooy … (App. S2) | T2, T3 | **license unverified … (App. S2) | https://hajim.rochester.edu/ece/sites/zduan/teaching/ece472/reading/Lipshitz_1992.pdf | yes (WebFetch cannot read this PDF; fetched with `curl`, text extracted with `pypdf` under `audiocomponents/.venv`) |
| S3. Wikipedia, "Quantization (signal processing)" | T1, T2 | CC BY-SA 4.0, as stated | https://en.wikipedia.org/wiki/Quantization_(signal_processing) | yes |
| S4. Wikipedia, "Zero-order hold" | T4 | CC BY-SA 4.0 | https://en.wikipedia.org/wiki/Zero-order_hold | yes |
| S5. Wikipedia, "Bitcrusher" | T5; two rival referents | CC BY-SA 4.0 | https://en.wikipedia.org/wiki/Bitcrusher | yes |
| S6. The palette, probed under `audiocomponents/.venv/bin/python` | §4 and Appendix A | MIT (this organization) | `audioif/src/shared/audioif_distortion.c` | yes (local) |

**Audit, 2026-09-06 (license and citation pass).** Every URL above was
re-fetched by an independent auditor, every Appendix D quotation was located
in the fetched text, and Appendix A's probe was re-run. Two corrections to
this section, both about how a licence was described rather than what it is;
the record is **Appendix E**.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | The quantizer **rounds**: on a 1 kHz sine at −6 dBFS the mean of (output − input) is within ±0.05 LSB of zero at every word length 2–16, and no sample's error exceeds 0.5 LSB. | S3, S2 (App. D) | high | Any mean outside ±0.05 LSB, or any sample's error over 0.5 LSB. The floor quantizer the palette gives today reads −0.377 LSB at 14 bits and −0.500 at 6 bits and below (App. A, re-measured by the critic pass) | Mean and max of the error … (App. T1) |
| T2 | Error power is Δ²/12: with the residual's **DC removed**, its rms is within 10 % of Δ/√12 wherever the probe spans ≥16 steps (6 bits and up at −6 dBFS), and falls 6.0 ± 1.0 dB per bit added. | S2, S3 | high | An rms more than 10 % from Δ/√12 anywhere in that range, or a per-bit step outside 6.0 ± 1.0 dB. (The palette's floor quantizer sits inside both bands — 0.95–1.03 × Δ/√12 from 4 to 14 bits, 5.8–6.3 dB per bit — so this row does **not** discriminate the T1 fix; it catches a wrong step size or a scaled residual) | rms of the error residual per … (App. T2) |
| T3 | The error is **harmonic, not noise**: dither off, on a bin-centred sine, the largest residual bin at a multiple of f0 (aliases folded) stands **≥20 dB above the median residual bin** at 6 bits and below; at 2 LSB TPDF dither that peak-to-median margin falls **below 3 dB**. | S2 | high | A margin under 20 dB with dither off — i.e. a rebuild that dithers by default, which is why dither defaults **off** — or a margin still above 3 dB with dither on (the control that must pass) | Peak-to-median ratio of the … (App. T3) |
| T4 | Rate reduction is a **hold**: the output is piecewise constant over each hold period and its magnitude follows 20·log₁₀\|sinc(fT)\| within 1 dB up to 0.9× the hold's Nyquist — **3.92 ± 0.5 dB** down at that Nyquist (S4's sinc(1/2) = 2/π), within 0.2 dB of 0 dB at DC. | S4 (re-fetched by the critic pass), S1 | high | A droop at the hold Nyquist outside 3.42–4.42 dB (linear interpolation between held values reads under 2 dB), or a deviation from sinc(fT) over 1 dB anywhere below 0.9× hold Nyquist | Run-length histogram; swept-sine magnitude against sinc(fT), 48 and 44.1 kHz |
| T5 | Rate reduction **aliases unattenuated**: a sine above the hold's Nyquist appears at \|f − k·f_hold\| within 3 dB of its own level, and the band-limit option removes it. | S2, S5 | high | A 7 kHz tone at f_hold = 8 kHz that does not appear at 1 kHz, or appears >3 dB down | STFT of a swept sine, band-limit off then on |
| T6 | The hold rate is **continuously variable** — a phase accumulator, not an integer divider: at any f_hold with fs/f_hold between 1 and 2 the run-length histogram contains **only lengths 1 and 2**, and the length-2 fraction is fs/f_hold − 1 within ±0.02 — **0.843** at S1's 26.04 kHz on a 48 kHz output (mean run 48000/26040 = 1.843), 0.694 at 44.1 kHz. | S1 ("A carry of 0 will cause the same sample … (App. T6) | medium — S1 describes … (App. T6) | A single run length (a snap to integer periods), a third run length appearing, or a length-2 fraction more than 0.02 from fs/f_hold − 1 | Run-length histogram at 26.04 kHz … (App. T6) |

No characters: one behaviour, two axes.

### Tier 3 — cost and latency

Budget as a fraction of one stereo block's deadline: **ESP32-P4 0.03**,
**ESP32-S3 0.08**. Lean patch expected: **no** — a mask, a compare and a hold
are the cheapest arithmetic in the library; the only optional cost is dither
(one xorshift and one add per sample).

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

**Bit depth is already there.** `audiofilters.Distortion` in `LOFI` masks the
low bits — `word_mask = 0xffffffffU ^ ((1U << (uint32_t)round(drive * 14.0)) - 1U)`
(`audioif/src/shared/audioif_distortion.c:61`), applied at `:11` — spanning 16
bits down to 2. Probed here: `mix` at 0 returns the source byte-exactly
(`:47`), silence gives silence, and the error rms tracks Δ/√12 within 5 % from
6 to 14 bits, so **T2 and T3 are reachable on the ported node unchanged**
(Appendix A).

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

**Ask B1 — a lo-fi node in an audioif-own module (additive, D1).** As first
drafted this ask covered T1, T4, T5 and T6. The palette verification of
2026-09-06 (Appendix G) refutes all of it but T6.

- **Trait unblocked by a node, and the only one:** **T6**.
- **Shape, re-cut:** the ask is no longer a whole `LoFi` node. It is a …  *(argument in full: App. R)*
- **Never a modification of `audiospeed`.** The phase reset is in a …  *(argument in full: App. R)*
- **Refutation record (Phase 0), retained:** *"ship bit depth only"* — what the …  *(argument in full: App. R)*
- **If T6's ask is declined**, the class ships the composed pair and records …  *(argument in full: App. R)*

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Six macros against a ceiling of sixteen.

| # | Label | Mode | Range | Generalises |
|---|---|---|---|---|
| 0 | Bits | UNIPOLAR | 2 … 16, integer | The fixed 12-bit word (S1) |
| 1 | Rate | UNIPOLAR | 1 kHz … sample_rate, log, clamped | The fixed 26.04 kHz period and the drop-sample pitch (S1) |
| 2 | Dither | UNIPOLAR | 0 … 2 LSB TPDF, **default 0** | Nothing on the machine — the option that lets T3 be shown from both sides |
| 3 | Band Limit | TOGGLE | off / on, **default off** | The ~42 dB/octave anti-alias filter (S1) the effect exists to do without |
| 4 | Mix | UNIPOLAR | 0 … 1 | — |
| 5 | Output | UNIPOLAR | −24 … +6 dB, default 0 | — |

**Characters:** none. **Patches** (names describe settings, never products):
0 `Twelve Bit, Twenty-Six` (12 bits, 26.04 kHz, no dither, no band limit — the
standout's two numbers); 1 `Eight Bit Voice` (8 bits, 22 kHz); 2 `Six Bit
Drum` (6 bits, 24 kHz — the word length S5 attributes to the TR-909);
3 `Telephone Grid` (8 bits, 8 kHz, band limit on); 4 `Grit Under The Note`
(12 bits, full rate, mix 0.35); 5 `Dithered Twelve` (12 bits, 26.04 kHz,
dither 1 LSB — T3's control); 6 `Broken Converter` (4 bits, 6 kHz).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/drive.py`.

1. **No surface.** `MACRO_LABELS = ()` and one default patch …  *(argument in full: App. R)*
2. **The −½ LSB DC is inherited and unmentioned.** `crush` goes straight to the …  *(argument in full: App. R)*
3. **Rate reduction is absent, and the docstring's reason for it is wrong** — …  *(argument in full: App. R)*
4. **Latency is right by default, not by statement.** Every class inherits …  *(argument in full: App. R)*
5. **`bits` and the node's mask agree only by coincidence** — both round
   `crush * 14` independently (`drive.py:230`, `audioif_distortion.c:61`).

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Does §4's DC-add reach T1?** **Closed 2026-09-06: yes** — mean error
   +0.0000 Δ, largest single-sample error 0.484 Δ, at 6 bits, on ported nodes
   (§4, App. G). T1 is not a node ask. What is left for the implementation
   session is the *cost* of the composed rate path: two `SpeedChanger` hops
   copy every frame twice more than a single node would, which Tier 3's 0.03
   (P4) / 0.08 (S3) budget was written for a one-node build and does not yet
   account for. *Settled by:* the Phase 1 cost table.
2. **S1's "the least significant 4 bits of each 12 bit word are only written to
   memory every other sample."** The natural reading is nibble-packing
   plumbing; the other is that alternate samples are effectively 8-bit, which
   would be a striking trait. **No trait rests on it.** *Settled by:* reaching
   the scan's schematic page images, which this run did not.
3. **Dither shape** — TPDF at 2 LSB is S2's textbook choice; table versus
   two-uniform sum is a cost question. *Settled by:* the implementation session.
4. **Where the band-limit sits when Bits and Rate are both engaged.** Before the
   hold is the machine's order; ahead of the quantizer as well would change T3.
   *Settled by:* the implementation session, T3 and T5 arbitrating.

---


## Appendix

### A. The LOFI node, measured

Probed under `audiocomponents/.venv/bin/python` on 2026-09-06 through
`audiocore.get_buffer`: a bin-centred 999.02 Hz sine (bin 341 of a
16384-point transform at 48 kHz) at 12000/32767 peak, Hann-windowed. "step"
is Δ in int16 units; harmonics are relative to the fundamental.

| bits | step | DC / step | THD (h2–h20) | error rms | step/√12 | h2 | h3 |
|---|---|---|---|---|---|---|---|
| 14 | 4 | −0.377 | 0.00 % | 1.1 | 1.2 | −116.8 dB | −115.8 dB |
| 12 | 16 | −0.466 | 0.00 % | 4.6 | 4.6 | −99.5 dB | −100.5 dB |
| 10 | 64 | −0.493 | 0.01 % | 18.3 | 18.5 | −113.9 dB | −89.8 dB |
| 8 | 256 | −0.499 | 0.20 % | 73.5 | 73.9 | −95.5 dB | −63.3 dB |
| 6 | 1024 | −0.500 | 0.84 % | 281.1 | 295.6 | −87.7 dB | −55.9 dB |
| 4 | 4096 | −0.500 | 11.83 % | 1212.0 | 1182.4 | −75.4 dB | −24.9 dB |
| 2 | 16384 | −0.500 | 45.69 % | 3734.2 | 4729.7 | −74.3 dB | −9.5 dB |

Three readings. **The DC is −½ LSB** and converges there as soon as the signal
spans a few steps — the floor quantizer, and T1's disconfirmation made
concrete. **The error rms is Δ/√12** from 6 to 14 bits within 5 %, failing only
at 2 bits where the probe spans two steps and S2's model stops applying (T2).
**The harmonics are odd** — h2 sits 50–65 dB below h3 at every depth, because a
floor quantizer is odd-symmetric about its own −½ LSB offset. That is a
property of *this* node; a rounding quantizer is odd-symmetric about zero and
gives the same structure, so T3 survives the fix.

Two Tier 1 spot checks on the same node: `mix = 0` returned the source
byte-identically, and 1024 samples of digital silence returned `{0}`.

**"error rms" is the residual with its DC removed**, which is the quantity T2
compares against Δ/√12. Measured about zero instead — DC left in — a floor
quantizer's residual is uniform on [−Δ, 0) and its rms is Δ/√3, exactly twice
Δ/√12, so a re-run that skips the mean subtraction reads 1.9 / 8.8 / 36.5 /
147.3 / 583.7 / 2379.5 / 9002.0 and appears to fail T2 by a factor of two.
Stated because the audit hit it.

Re-run independently by the audit pass on 2026-09-06 under the same
interpreter: the step and DC/step columns reproduced exactly (−0.377 at 14
bits, −0.466 at 12, −0.493 at 10, −0.499 at 8, −0.500 at 6/4/2), the error-rms
column reproduced to 0.5 % with the DC removed (1.16 / 4.67 / 73.4 / 280.6 /
1210 / 3736), and both spot checks reproduced — `mix = 0` byte-identical to the
source, silence in returning `{0}`.

A first version of this probe read a −0.249 Δ offset and a 25 % duty cycle,
which is wrong; the cause was the probe, not the node — the `RawSample` ran out
before the analysis window did, so half the window was trailing silence.
Recorded because the wrong number was plausible.

### B. Planted faults, so the measurements can fail

- **T1.** Build with the DC-add removed: the mean must read −0.5 Δ and the
  check must go red. Build with it doubled: the mean must read +0.5 Δ and it
  must go red the other way. A check that has only seen zero has not been shown
  to work (`agent-knowledge/workspace-craft.md`).
- **T2.** Scale the residual by 1.3 before the rms; the 10 % band must reject it.
- **T3.** Force dither on while the check expects it off; the harmonic-peak
  test must fail. And run the control: dither on, flatness test, must pass.
- **T4.** Replace the hold with linear interpolation between held values: the
  run-length histogram must lose its plateaus and the sinc fit must fail.
- **T5.** Enable the band limit while the check expects it off; the alias at
  1 kHz must vanish and the check must go red.
- **T6.** Snap the accumulator to integer periods: the interleaved 1/2-sample
  runs must collapse to all-2 and the check must go red.

Every one of these is *absence reading as agreement* in disguise, the shape
`workspace-craft.md` names: a silent or bypassed build passes a check that only
looks for "small error".

### C. What the standout is *not* lending this class

The SSM filters on six of eight outputs; the 8-bit multiplying DAC used as an
attenuator; the four 2.5-second banks and the 10-second ceiling; the eight-out
routing; the 42 dB/octave input filter (which returns only as an option,
defaulting off). Recorded so a later reader does not mistake the class for an
SP-1200 emulation, or file the missing parts as gaps.

### D. Source quotations, verbatim

**S1**, in the order used: "Sample period is fixed at {1/26.04)kHz" · "The
SP1200 uses 12 bit linear encoding for the sound data" · "The 12-bit data is
in “complement offset binary” format: most negative value = 000 hex, “zero” =
800 hex, most positive = fff hex" · "The DAC is a standard 12 bit linear
device. It is used both for playing and sampling sounds" · "The SP1200 uses
the successive approximation technique to digitize the incoming audio signal"
· "These filters usually have a very steep cutoff on the order of 42dB per
octave and a cutoff frequency of less than half the sample rate of the system"
· "A carry of 0 will cause the same sample to be played twice. A carry of 1
will increment the sample's address" · "SP1200 has eight monophonic
channel outputs" · "Two channels (7,8) are direct outs. The rest of the
channels are filtered" · "SSM 2044 VCF" (the IC parts list; the fault table's
"Bad SSM Chip" for a muted channel is the same part — together these are the
only support for §1's "SSM filter" and nothing else rests on it) · "The SP1200
has 10 seconds of sampling time which is divided up into (4) 2.5 second banks"
· "sound memory size of 256K words" · "the 12 bit data was split up into a
byte and a nibble" · "the least significant 4 bits of each 12 bit word are
only written to memory every other sample" (§8 Q2). License, from
`https://archive.org/metadata/emu-sp-1200-service-manual-1987`: `licenseurl` =
`http://creativecommons.org/publicdomain/mark/1.0/`. **OCR note:** the scan
garbles some words ("pla 5 dng" for "playing", "d 5 mamic" for "dynamic"); the
quotations above repair those artefacts silently. Every one was located in the
fetched text during the 2026-09-06 audit.

**S2**: "In undithered systems we know that the error is a deterministic
function of the input. If the input is simple or comparable in magnitude to the
quantization step size, the total error signal is strongly input-dependent and
audible as gross distortion and noise modulation." · "It has a maximum
magnitude of 0.5 LSB and is periodic in w with a period 0f 1 LSB." · "many sharp
peaks fall at multiples of the input sine wave frequency, indicating not only a
high degree of nonrandom structure (that is, harmonic distortion) in the error
signal, but also a strong correlation between this signal and the system input.
Inharmonic peaks are also present due to aliasing of distortion components
above the Nyquist frequency (22.05 kHz in this simulation) into the baseband."
· "a total power of A2/12 up to the Nyquist frequency."

**S3**: "SQNR ≈ 1.761 + 6.02 · Q dB" · error power "Δ²/12" · with truncation
"the error has a non-zero mean of ½ LSB" and rms "1/√3 LSB" · "At lower
amplitudes, the quantization error becomes dependent on the input signal,
resulting in distortion."

**S4**: "H_ZOH(f) = e^(−iπfT) sinc(fT)" · "a 3.9224 dB loss at the Nyquist
frequency, corresponding to a gain of sinc(1/2) = 2/π".

**S5**: "an audio effect that produces distortion by reducing the resolution or
bandwidth of digital audio data" · lowering the sample rate means "high
frequencies are aliased or, if the digital signal is first low-pass filtered,
they are lost" · "the waveform becomes metallic sounding as a result of severe
aliasing" · TR-909 "used 6-bit integer samples"; Speak & Spell "used an 8 kHz
sample rate".

### F. Trait critic pass — 2026-09-06

Sources re-reached in this pass, and what was re-measured. Nothing below is
carried from the earlier run's word.

- **S1 re-fetched** at `https://archive.org/download/emu-sp-1200-service-manual-1987/Emu-SP-1200-Service-Manual-1987_djvu.txt`
  (HTTP 200, 134 KB of OCR text). Located in it: "Sample period is fixed at
  {1/26.04)kHz" (line 1253), "Sample period is ignored, since SP1200 has only
  one playback rate, 26.04 kHz" (line 1798), "A carry of 0 will cause the same
  sample to be played twice. A carry of 1 will increment the sample's address"
  and, four lines on, "Intermediate pitch values (neither 0000000 or 1111111)
  will cause alternating 0 and 1 values at the carry out of the lower adders"
  (lines 4552–4560) — which is the interleaved 1/2-sample run T6 now states as
  a number. Also "The DAC is a standard 12 bit linear device", "The SP1200 uses
  12 bit linear encoding", and the 42 dB/octave anti-alias sentence.
  **And the licence line the earlier pass missed**: the scan's first page reads
  "For the personal use of SP1200 Owners only / Not for reproduction or sale"
  and "©1987 E-mu Systems Inc. Scotts Valley. CA All Rights Reserved", which
  appears 45 times through the scan. §2 is corrected: the archive.org Public
  Domain Mark is the uploader's label, not the rights holder's grant — the
  repackager trap `agent-knowledge/instrument-sources.md` names.
- **S4 re-fetched** (`https://en.wikipedia.org/wiki/Zero-order_hold`): "3.9224 dB
  loss at the Nyquist frequency, corresponding to a gain of sinc(1/2) = 2/π";
  footer "Text is available under the Creative Commons Attribution-ShareAlike
  4.0 License". T4's figure and tolerance are written from that.
- **Appendix A's LOFI probe re-run** by the critic under
  `audiocomponents/.venv/bin/python`: mean/step −0.377 (14 bit), −0.466 (12),
  −0.493 (10), −0.499 (8), −0.500 (6, 4, 2) and DC-removed rms 1.1 / 4.6 /
  18.3 / 73.5 / 281.1 / 1212.0 / 3734.2 — reproducing the table exactly. As a
  ratio to Δ/√12 that is 0.964 / 1.005 / 0.991 / 0.994 / 0.951 / 1.025 / 0.790,
  and the step from one word length to the next is 5.8–6.3 dB per bit. T2's
  band and its per-bit clause are written from those numbers, and T2's row now
  says what it does **not** discriminate.

**Rows rewritten, and why.** T1 (disconfirmation was one value, now the
complement of the claim, with the floor quantizer's measured range in it);
T2 (claimed 10 % but disconfirmed at 20 %, leaving a band that was neither —
and "halving per bit" had no tolerance); T3 ("within 3 dB of flat" named no
statistic — now peak-to-median, which a measurement can compute); T4 (the
3.92 dB figure carried no tolerance and the disconfirmation started at 2 dB);
T6 ("interleaved runs of 1 and 2" is not a number — now the length-2 fraction
fs/f_hold − 1, which is arithmetic from S1's own 26.04 kHz). **Six Tier 2 rows
after the pass, unchanged in count.** No row was dropped and none needed the
*unmeasured* mark.

### E. Audit record — license and citation pass, 2026-09-06

Every URL in §2 was re-fetched by an independent auditor, and every S1–S5
quotation in Appendix D was located in the fetched text. Findings:

- **S1's license holds.** `https://archive.org/metadata/emu-sp-1200-service-manual-1987`
  returns `licenseurl = http://creativecommons.org/publicdomain/mark/1.0/`.
  **Correction:** an earlier draft said the item page does not show it. It
  does — `https://archive.org/details/emu-sp-1200-service-manual-1987`
  carries a visible `Usage` line reading "Public Domain Mark 1.0" linking to
  the same URL. The metadata API remains the reliable route (the knowledge
  module's rule), but the two do not disagree here.
- **Correction to a quoted license string.** S3–S5's footers read "Creative
  Commons Attribution-ShareAlike 4.0 License" as served today, not
  "…4.0 International License" as an earlier draft transcribed. The call —
  CC BY-SA 4.0 — is unchanged.
- **S2 confirmed unlicensed.** The extracted text contains no `copyright`,
  `©`, `rights`, `permission` or `licen*` string anywhere; the downgrade to
  "license unverified — treated as copyleft" stands. Its two-column layout
  interleaves across columns on extraction, so Appendix D's S2 quotations are
  de-interleaved reconstructions of sentences that are present and continuous
  in the printed page ("In- harmonic" for "Inharmonic", and so on).
- **Appendix A re-run independently** on the same interpreter: the step and
  DC/step columns reproduce exactly (−0.377, −0.466, −0.493, −0.499, −0.500,
  −0.500, −0.500) and the error-rms column reproduces once the residual's DC
  is removed, which is the measurement T2 names (Appendix A now says so).
  Both Tier 1 spot checks reproduced.

### G. Palette verification pass — 2026-09-06

Run by the palette verifier for the bitcrusher–exciter–cabinet unit, under
`audiocomponents/.venv/bin/python`, against the C in `audioif/src/`. Every
figure below is from a graph built and pulled here, not from an argument.

**The round-to-nearest compose (T1).** `audiocore.RawSample` 1 kHz at 12000
peak → `audiomixer.Mixer` voice 0 at level 1.0 plus voice 1 carrying a looping
256-frame constant of +Δ/2 → `audiofilters.Distortion(mode=LOFI, drive=(16−b)/14,
soft_clip=False, mix=1.0)`. Residual against the un-crushed source over 22 000
frames at b = 6:

| build | mean error / Δ | max abs error / Δ |
|---|---|---|
| node alone (floor) | −0.4792 | 0.967 |
| with the +Δ/2 voice | **+0.0000** | **0.484** |

**The zero-order hold (T4, T5, T6).** `SpeedChanger(src, rate=N)` →
`SpeedChanger(·, rate=1/N)`, 48 kHz stereo, sine at 12000 peak.

- *Waveform, N = 6 on a 1 kHz sine:* `[0×6, 8485×6, 12000×6, 8485×6, 0×6, …]`
  — piecewise constant, the decimated 8 kHz sequence held, not zeros between
  samples.
- *Magnitude against sinc, N = 4 (f_hold 12 kHz, hold Nyquist 6 kHz),
  re the input:* 100 Hz −0.01 (sinc −0.00), 500 Hz −0.02 (−0.02), 1 kHz −0.09
  (−0.10), 2 kHz −0.37 (−0.40), 3 kHz −0.86 (−0.91), 4 kHz −1.55 (−1.65),
  5 kHz −2.48 (−2.64), 5.4 kHz −2.93 (−3.11). Largest deviation **0.18 dB**.
  At exactly the hold Nyquist the reading is phase-dependent, as two
  samples per cycle must be (−2.73 dB at phase 0, −5.34 dB at π/4, bracketing
  S4's −3.92).
- *Alias, N = 4:* an 8 kHz input returns a 4 kHz image at **−1.55 dB** re the
  input, i.e. within 3 dB of its own level (T5).
- *Run lengths over 30 000 output frames:* N = 2 → {2: 15000}; N = 4 →
  {4: 7500}; N = 6 → {6: 4953, 7: 40, 2: 1}; **N = 1.843 → {1: 2369,
  2: 12758, 3: 173, 4: 399}**. Cause: `self->phase = 0;` on every source-buffer
  fetch (`audioif/src/audiospeed/SpeedChanger.c:100`) against the node's fixed
  128-frame output block (`:22`). Among the 1s and 2s the length-2 fraction is
  12758/15127 = **0.8434**, against T6's fs/f_hold − 1 = 0.843.
- *Latency:* a single non-zero frame at input frame 100 emerges at output
  frames 100–103 at N = 4. Zero algorithmic latency.
- *Live control:* `s.rate = 2.0` accepted and honoured mid-stream.

**The pulse-table alternative (why §4's earlier wording was wrong).**
`audiomath.Multiply` with a looping duty-1/4 table, 1 kHz sine at 20000 peak:
output samples are `[−17321, 0, 0, 0, −20000, 0, 0, 0, …]` — piecewise *zero*.
The fundamental lands **12.04 dB** below the input, and the images at 11, 13
and 23 kHz sit at **0.00 dB** relative to that fundamental. The images are not
suppressed; the wanted signal is attenuated with them.

**What was not re-run here.** Appendix A's LOFI table (already run twice) and
every source fetch in §2 — this pass touched the palette only.

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

Rate-honest note: Rate clamps to the running rate, at which the hold is the
identity. T4's sinc figure is a property of the hold *ratio*, so every Tier 2
trait holds at 44.1 and 22.05 kHz.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1. E-mu SP-1200 Service Manual (1987), OCR text of the archive.org scan | §1; T6 | **Two answers, and the document's own wins.** The archive.org item is labelled **Public Domain Mark 1.0** (metadata API `licenseurl`, and a visible `Usage` line — Appendix E), but that is the *uploader's* label: the manual's own first page reads "For the personal use of SP1200 Owners only / Not for reproduction or sale" and "©1987 E-mu Systems Inc. Scotts Valley. CA All Rights Reserved" (re-fetched and read by the critic pass, 2026-09-06 — Appendix F). Treated as **all rights reserved, personal use only**: read as a document, nothing reproduced (vision §5). Nothing changes in practice; the honest call does | https://archive.org/stream/emu-sp-1200-service-manual-1987/Emu-SP-1200-Service-Manual-1987_djvu.txt · https://archive.org/metadata/emu-sp-1200-service-manual-1987 | yes |
| S2. Lipshitz, Wannamaker & Vanderkooy, "Quantization and Dither: A Theoretical Survey", *JAES* 40(5) 1992, 355–375 | T2, T3 | **license unverified — treated as copyleft.** The self-archived PDF carries no rights line at all (no `copyright`, `©`, `permission` or `rights` string anywhere in its extracted text). Read as a paper, for its math; nothing ported | https://hajim.rochester.edu/ece/sites/zduan/teaching/ece472/reading/Lipshitz_1992.pdf | yes (WebFetch cannot read this PDF; fetched with `curl`, text extracted with `pypdf` under `audiocomponents/.venv`) |
| S6. The palette, probed under `audiocomponents/.venv/bin/python` | §4 and Appendix A | MIT (this organization) | `audioif/src/shared/audioif_distortion.c` | yes (local) |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | The quantizer **rounds**: on a 1 kHz sine at −6 dBFS the mean of (output − input) is within ±0.05 LSB of zero at every word length 2–16, and no sample's error exceeds 0.5 LSB. | S3, S2 (App. D) | high | Any mean outside ±0.05 LSB, or any sample's error over 0.5 LSB. The floor quantizer the palette gives today reads −0.377 LSB at 14 bits and −0.500 at 6 bits and below (App. A, re-measured by the critic pass) | Mean and max of the error residual per word length, at 48 / 44.1 / 22.05 kHz |
| T2 | Error power is Δ²/12: with the residual's **DC removed**, its rms is within 10 % of Δ/√12 wherever the probe spans ≥16 steps (6 bits and up at −6 dBFS), and falls 6.0 ± 1.0 dB per bit added. | S2, S3 | high | An rms more than 10 % from Δ/√12 anywhere in that range, or a per-bit step outside 6.0 ± 1.0 dB. (The palette's floor quantizer sits inside both bands — 0.95–1.03 × Δ/√12 from 4 to 14 bits, 5.8–6.3 dB per bit — so this row does **not** discriminate the T1 fix; it catches a wrong step size or a scaled residual) | rms of the error residual per word length, DC removed |
| T3 | The error is **harmonic, not noise**: dither off, on a bin-centred sine, the largest residual bin at a multiple of f0 (aliases folded) stands **≥20 dB above the median residual bin** at 6 bits and below; at 2 LSB TPDF dither that peak-to-median margin falls **below 3 dB**. | S2 | high | A margin under 20 dB with dither off — i.e. a rebuild that dithers by default, which is why dither defaults **off** — or a margin still above 3 dB with dither on (the control that must pass) | Peak-to-median ratio of the residual spectrum, dither off then on |
| T6 | The hold rate is **continuously variable** — a phase accumulator, not an integer divider: at any f_hold with fs/f_hold between 1 and 2 the run-length histogram contains **only lengths 1 and 2**, and the length-2 fraction is fs/f_hold − 1 within ±0.02 — **0.843** at S1's 26.04 kHz on a 48 kHz output (mean run 48000/26040 = 1.843), 0.694 at 44.1 kHz. | S1 ("A carry of 0 will cause the same sample to be played twice … Intermediate pitch values … will cause alternating 0 and 1 values at the carry out", re-fetched by the critic pass); the fraction is arithmetic from S1's own 26.04 kHz | medium — S1 describes the accumulator for *pitch*; the generalisation to a Rate knob is ours | A single run length (a snap to integer periods), a third run length appearing, or a length-2 fraction more than 0.02 from fs/f_hold − 1 | Run-length histogram at 26.04 kHz and three non-integer ratios |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Not reached, and therefore not cited:** the schematic page images inside the
S1 scan (only its OCR text was fetched, which renders drawings as noise); the
E-mu SP-12 service manual PDF at vintagesynthparts.com (not attempted — S1
documents the same architecture and carries a license). **Nothing copyleft was
consulted**, so no vision §5 emulator question arose.

*(from §2)*

**The referent, argued.** S5 names two rivals and each fixes one axis: the
TR-909's 6-bit samples, the Speak & Spell's 8 kHz rate. The SP-1200 fixes
**both** at once and documents them in a manual with a license, which is why it
stays. Against it, its popular identity also includes analogue output filters
and a loud output stage, neither of which is a bitcrusher — Appendix C lists
what is deliberately left behind so a later reader does not file it as a gap.

*(from §3)*

**Latency: zero samples, 0.0 ms at 48 kHz.** Neither operation looks ahead — a
quantizer is memoryless, a hold emits the value it already holds. **No option
adds latency:** the band-limit is an IIR low-pass (group delay, not algorithmic
latency, not reported in `latency_samples`) and dither is per-sample.
`LATENCY_SAMPLES = 0`, verified by the click measurement with band-limit and
dither each on and off; `tail_samples = 0`, the hold carrying at most one
sample of state.

*(from §4)*

**Its defect is that the mask floors.** `word &= word_mask` truncates toward
−∞, so the error's mean is exactly −½ LSB — measured −0.500 Δ at 6, 4 and 2
bits, which at 4 bits is 6 % of full scale appearing and vanishing with the
signal. **Compose first:** floor(x + Δ/2) = round(x), so a DC of +Δ/2 summed in
ahead of the node turns floor into round without touching a ported node (an
`audiomixer.Mixer` voice fed by a looping one-sample `RawSample` constant, its
level recomputed when Bits moves; silence survives, since 0 + Δ/2 floors back
to 0). **Measured, it lands** (palette verification, 2026-09-06, Appendix G):
with an `audiomixer.Mixer` voice carrying a looping constant of +Δ/2 summed
into the source ahead of the node, at 6 bits the residual's mean is
**+0.0000 Δ** and its largest single-sample error **0.484 Δ**, against
−0.4792 Δ and 0.967 Δ for the same probe without the DC. **T1 needs no node.**

*(from §4)*

**Rate reduction has a node too, and this seed's first pass missed it.**
`audiospeed.SpeedChanger` reads its source through a **16.16 phase
accumulator** and takes the sample the accumulator's integer part points at,
with **no interpolation**: `uint32_t src_index = self->phase >> SPEED_SHIFT`
(`audioif/src/audiospeed/SpeedChanger.c:139` for the 8-bit path, `:160` for the
16-bit one) and `self->phase += self->rate_fp` (`:155`, `:176`), with
`SPEED_SHIFT 16` at `SpeedChanger.h:19`. That is the SP-1200's own mechanism —
S1's carry adder — and two of them in series,
`SpeedChanger(source, rate=N)` → `SpeedChanger(·, rate=1/N)`, is decimate-then-
hold: y[n] = x[N·⌊n/N⌋], which is precisely what a bitcrusher's Rate knob does.
Probed here (Appendix G): a click at input frame 100 leaves at frame 100 held
for N frames — **zero latency** — the run-length histogram at N = 2 and N = 4
is all-N with no other length in 30 000 frames, the swept magnitude tracks
20·log₁₀|sinc(fT)| **within 0.2 dB** to 0.9× the hold's Nyquist, and a tone
above that Nyquist reappears at its image **1.55 dB** below its own level.
`rate` is settable at runtime, so Rate is a live macro. `SpeedChanger` is a
CircuitPython port (`audioif/docs/upstream-diff.md:143`) and is therefore never
modified; composing with it asks nothing of audioif, though it does cost two
extra frame copies per sample (§8 Q1). **T4 and T5 are reachable on the palette
as it stands** (§5).

*(from §4)*

**What `audiomath.Multiply` gives instead, measured.** The pulse-table route —
a looping duty-1/N table, the way `RingMod` builds its carrier
(`modulation.py:240-262`; audioif's own node,
`audioif/docs/upstream-diff.md:714`) — is **impulse sampling**, not a hold. At
N = 4 the output is the source's samples separated by zeros; the whole output,
wanted signal included, sits **12.04 dB** (= 20·log₁₀ N) below the input; and
the images at 11, 13 and 23 kHz stand at **0.00 dB relative to the output's own
fundamental** — level with the signal, flat, with no sinc droop. So T4 fails on
*this* route, which is why §5's first draft asked for a node; it does not fail
on the SpeedChanger route above. (The earlier wording, "images appear
20·log₁₀(N) dB down", read as though the images were suppressed; measured, they
are not — it is the fundamental that is attenuated with them.)

*(from §4)*

Python computes the LOFI `drive`, the constant Δ/2, the two `SpeedChanger`
rates and the dither table on CPython, shipped as data, never rebuilt on a
board (`cmods/micropython/ports/esp32/mpconfigport.h:69`). The word mask and
the 16.16 rate increment are then derived from those *in C*
(`audioif_distortion.c:61`, `SpeedChanger.c:25-31`), identically on every
target; C runs one mask, one compare-and-hold and one optional add per sample.
Every operation is per-sample and channel-independent, so **a mono source gets
the mono form of the same behaviour**; nothing here is stereo by definition.

*(from §5)*

**REFUTED BY PALETTE: T1.** An `audiomixer.Mixer` voice carrying a looping
constant of +Δ/2, summed into the source ahead of `audiofilters.Distortion` in
`LOFI`, turns the node's floor into a round — floor(x + Δ/2) = round(x). At
6 bits the residual's mean measures **+0.0000 Δ** and its largest single-sample
error **0.484 Δ**, against −0.4792 Δ and 0.967 Δ without the DC. T1's bar is
±0.05 Δ and ≤0.5 Δ; both are met, on ported nodes, with no arithmetic left to
chance. Silence survives (0 + Δ/2 floors back to 0). §4 carries the topology.

*(from §5)*

**REFUTED BY PALETTE: T4 and T5.** `audiospeed.SpeedChanger` is a 16.16
phase-accumulator resampler that takes the sample the accumulator points at
with **no interpolation** (`audioif/src/audiospeed/SpeedChanger.c:139`, `:160`;
`phase += rate_fp` at `:155`, `:176`; `SPEED_SHIFT 16` at `SpeedChanger.h:19`).
Two in series — `SpeedChanger(source, rate=N)` → `SpeedChanger(·, rate=1/N)` —
are decimate-then-hold, y[n] = x[N·⌊n/N⌋], a true zero-order hold. Measured at
N = 4 (f_hold 12 kHz): the swept magnitude tracks 20·log₁₀|sinc(fT)| to
**within 0.2 dB** everywhere from 100 Hz to 5.4 kHz (0.9× the hold's Nyquist,
T4's own bound) — 0.00 / 0.01 / 0.03 / 0.06 / 0.10 / 0.16 / 0.18 dB of
deviation at 500 Hz, 1, 2, 3, 4, 5 and 5.4 kHz — and an 8 kHz tone, above the
hold's 6 kHz Nyquist, reappears at 4 kHz **1.55 dB** below its own level, well
inside T5's 3 dB. The run-length histogram at N = 2 and N = 4 is all-N across
30 000 frames. A click at input frame 100 leaves at output frame 100:
**zero latency**, so Tier 3's number is unchanged. `rate` is settable at
runtime, so Rate stays a live macro. The node is a CircuitPython port
(`audioif/docs/upstream-diff.md:143`) and is not modified — only composed with.

*(from §5)*

**The ask that survives — T6, and it is narrow.** T6 asks for a *continuously
variable* hold: at fs/f_hold between 1 and 2, run lengths of **only** 1 and 2.
The composed pair gets the *ratio* right and the *alphabet* wrong.
`fetch_source_buffer` resets the accumulator on every source buffer —
`self->phase = 0;` at `SpeedChanger.c:100` — and the upstream node emits in
fixed 128-frame blocks (`OUTPUT_BUFFER_FRAMES` at `:22`), so at a ratio that
does not divide 128 the phase restarts mid-hold. Measured over 30 000 frames at
S1's own ratio fs/f_hold = 1.843: run lengths {1: 2369, 2: 12758, **3: 173,
4: 399**} — the length-2 fraction among the 1s and 2s is **0.8434** against
T6's 0.843 ± 0.02, so the accumulator law is right, but **3.6 % of runs are
lengths T6 forbids**. At N = 6 the same effect gives 40 runs of 7 among 4994. That
is T6's own disconfirmation condition ("a third run length appearing"), met.

*(from §5)*

- **Shape, re-cut:** the ask is no longer a whole `LoFi` node. It is a
  **fractional zero-order hold whose accumulator survives a buffer boundary**
  — one option on an audioif-own node (`audiomath` is the natural home; the
  hold is arithmetic, not routing), or `audiomath.Hold(source, rate_hz)` with
  its phase carried across blocks. Bit depth, dither, the band limit and the
  Mix are all composed on the palette and are **not** part of the ask.

*(from §5)*

- **Never a modification of `audiospeed`.** The phase reset is in a
  CircuitPython-ported node; it is not touched (vision §2.2). If the reset is
  judged an upstream defect rather than a deliberate re-sync, that is an
  `upstream-emissary` report, not a patch.

*(from §5)*

- **Refutation record (Phase 0), retained:** *"ship bit depth only"* — what the
  class does today (`drive.py:206-208`) — still fails, because vision §4.2's
  entry is "bit depth and sample-rate reduction **together**"; the difference
  is that the palette now delivers the hold, so nothing is dropped.
  *"`audiodelays.PitchShift` could fake it"* still fails: a granular shifter
  adds window latency (10.7 ms at 2048 bytes, vision §9a) and changes pitch.
  *"`audiomath.Multiply` against a pulse table"* fails as §4 measures it —
  impulse sampling, images level with the fundamental, no sinc droop.

*(from §5)*

- **If T6's ask is declined**, the class ships the composed pair and records
  T6 as **met at ratios that divide 128 frames and disconfirmed elsewhere**,
  with the histogram above as the evidence. That is a legitimate result under
  vision §3, not a failure.

*(from §7)*

1. **No surface.** `MACRO_LABELS = ()` and one default patch
   (`drive.py:215-217`); `bits` (`drive.py:230`) is a plain attribute with no
   setter and `mix` is construction-only (`drive.py:223`).

*(from §7)*

2. **The −½ LSB DC is inherited and unmentioned.** `crush` goes straight to the
   node (`drive.py:231-232`) and the docstring (`drive.py:202-208`) does not say
   the node floors. Measured −0.500 Δ at ≤6 bits.

*(from §7)*

3. **Rate reduction is absent, and the docstring's reason for it is wrong** —
   "decimation needs a sample-and-hold the palette does not have"
   (`drive.py:206-208`). The palette has had one all along:
   `audiospeed.SpeedChanger` is a phase-accumulator drop-sample resampler
   (`audioif/src/audiospeed/SpeedChanger.c:160`, `:176`), and two in series are
   a zero-order hold, measured in §4. The defect the rebuild must not repeat is
   not the missing feature but the **unchecked claim about the palette**: a
   sentence that closed a question instead of probing it.

*(from §7)*

4. **Latency is right by default, not by statement.** Every class inherits
   `LATENCY_SAMPLES = 0` (`_core.py:140`) and none overrides it; nothing here
   says 0 is correct and nothing measured it.
