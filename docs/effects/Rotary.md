# Effects Dossier — `Rotary` (Leslie 122)

**Class:** `lib/audioeffects/modulation.py` — read once, for §7.
**Family / phase:** Modulation, roadmap Phase 3.
**Standout:** Leslie 122, per vision §4.2 — **confirmed**, no swap (A1).
**Grade:** **literature** — the 122's manual fixes the crossover, the
amplifier and the two-speed drives, but the traits that make a Leslie a
Leslie are mechanical and acoustic and come from measured modeling papers
(S3, S5), not a netlist. A SPICE deck of the dividing network would refine
two Q values, not the grade (§8.1).
**Portability tier:** **audioif** — `audioroute.Splitter`,
`audioecho.FeedbackDelay`, `audiomath.Multiply`, plus the two of §5's four
additive options that survived verification (R1, R3); on a stock
CircuitPython board the module imports and construction raises a clear
`ImportError` (the `drive.py:29-32`, `:331-332` pattern).
**`capabilities`:** `()`, transport not read (D10): rotor speeds are set by
pulleys and ramps by inertia, so nothing here has a tempo relationship.
**Status:** seed (Phase 0), from sources reached 2026-09-06. Sections 1–8
run long for this class — 14 sources, 10 traits, 16 macros; every excerpt,
probe narrative and derivation is in the Appendix. **§4 and §5 were verified
against the audioif C and re-probed on 2026-09-06 (A11): two of the four node
asks are refuted, R1's stated reason was replaced, and one line citation was
corrected.**

## 1. The circuit, in one paragraph

A Leslie 122 is one 40 W amplifier — a 6550A output pair, a 12AU7A balanced
stage, an OC3 regulator (S1, S9) — into a passive **800 Hz dividing
network**, "a 12 dB per octave, 16-ohm crossover" (S2). Above 800 Hz a
*stationary* compression driver fires through a rotating twin-bell bakelite
horn whose second bell is a dummy "serving mainly to cancel the centrifugal
force of the other", a diffuser in its mouth "to make the radiation pattern
closer to uniform" (S3 §4.1); below 800 Hz a 15" woofer fires down into a
rotating scoop in a wooden drum (S1, S2). Each rotor has its own two-speed
drive — a fast motor on a belt, a slow motor engaging it through a rubber
O-ring (S8) — so the horn turns near 400 rpm in *tremolo* and near 50 in
*chorale*, the heavier drum near 340 and 40 (S6; S7 measures 400/48 and
342/40 — though S2 has the drum ending "at approximately the same rotational
speed as the treble unit", which T2 records). **No diode: the nonlinearity
is a time-varying delay.** The horn's
mouth rides a circle of radius `r_s`, which in the far field is a sinusoidal
frequency shift (S3 eq. 20) `ω_l ≈ ω_s·[1 − (r_s·ω_m/c)·sin(ω_m·t)]` — depth
is tangential speed over sound speed. The horn is directive, so its response
falls as it turns away, "below 12 Barks or so … with high frequencies
decreasing somewhat faster with angle than low frequencies" (S3 §4.3.2, of a
Model 600 horn measured −180°…180° in 15° steps, §4.2 — twelve Barks is
about 1.7 kHz, the 12th critical band's cut-off being 1720 Hz (S14), above
which that sentence says nothing). The drum is the other half: S3 §5 reports
of S2 that "an AM 'throb' is the main effect of the rotating woofer port",
and S2 itself has the drum working "just as an AM device, and only for the
upper two octaves or so of the bass section (200 to 800 Hz)". Rotor speed is
switched remotely: S13 describes the switch "found on organs like the
Hammond B3" as having "three positions: slow (or Chorale), fast (or
Tremolo), and Stop", while the 122's own manual documents a console-connector
TREMOLO control whose CHORALE position brakes "Bass and Treble rotors … to
Chorale speed" and names no Stop on the pages reached (S1 p.5). The switch
puts "around 50 or 60 Vdc" on both input pins, which a 1 MΩ resistor feeds to
"the relay switching tube" that "turns on or off the relay" (S9) — the switch
controlling rotor speed "through … the two-speed motor assemblies" (S1);
never a step, since "the time from slow to fast _and_ fast to slow is around
5 to 8 seconds" (S8, of the lower belt) and the drum lags the horn (S2, S4). The amplifier leaned on adds
"warm rich distortion" (S2) *before* the network, so before both rotors.
Stereo is not in the cabinet: it is two microphone positions on one rotation
(S3 §3.6).

## 2. Sources and license calls

All reached this run, 2026-09-06, and every row re-fetched and its licence
re-read in the same run's independent audit pass — corrections and method in
A7. PDFs were fetched as binaries and their text extracted locally with
`pypdf` and read in full (A3 says why that mattered). Quotations are A5.
**Where no licence is stated anywhere the source is reached through, the row
reads *unverified → copyleft*** (vision §5: an unfound licence is copyleft
until shown otherwise); those are read as documents or as papers, and nothing
from them is republished or ported.

| # | Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|---|
| S1 | Leslie 122 *Installation Instructions Manual*, 26 pp., at ManualsLib | the 800 Hz network and the band split (p.3) … (App. S1) | none on the manual … (App. S1) | manualslib.com/manual/4079586/Leslie-122.html `?page=1,3,4,5,22` ; manualslib.com/terms.html | yes; p.22's schematic scan re-fetched and confirmed unusable (§8.1, A2) |
| S2 | Henricksen, "Unearthing the Mysteries of the Leslie Cabinet" … (App. S2) | the 12 dB/oct 16 Ω crossover; drum AM only 200–800 Hz … (App. S2) | **none on the page and none in the site … (App. S2) | dannychesnut.com/Music/Leslie/LeslieMystery.html | yes |
| S3 | Smith, Serafin, Abel & Berners, "Doppler Simulation and the Leslie" … (App. S3) | eq. 15–20 (§4.1); the Model 600 horn, 44W identical … (App. S3) | authors' copyright on the `/~jos/doppler/` … (App. S3) | ccrma.stanford.edu/~jos/doppler/dafx02.pdf and /~jos/doppler/ ; dsprelated.com/freebooks/pasp/Leslie.html (same result, *PASP* eq. 6.13) | yes |
| S4 | Pekonen, Pihlajamäki & Välimäki … (App. S4) | directive horns; the wooden drum's directional pattern … (App. S4) | none in the paper … (App. S4) | dafx.de/paper-archive/2011/Papers/49_e.pdf | yes |
| S5 | Herrera, Hanson & Abel, "Discrete Time Emulation of the Leslie … (App. S5) | horn and baffle modelled individually … (App. S5) | "site copyright © 2009-2023 Stanford … (App. S5) | ccrma.stanford.edu/papers/discrete-time-emulation-of-leslie-speaker | **abstract only**, re-checked |
| S6 | Wikipedia, "Leslie speaker" | 50/400 rpm horn vs 40/340 woofer … (App. S6) | CC BY-SA 4.0 (footer) | en.wikipedia.org/wiki/Leslie_speaker | yes |
| S7 | HammondWiki, "Leslie Rotation Speed" | J. Fisher on a 147, middle pulley: upper 400/48 rpm … (App. S7) | content © 2000–2002 Dairiki *et al.* … (App. S7) | dairiki.org/HammondWiki/LeslieRotationSpeed ; dairiki.org/HammondWiki/opl.html | yes (both) |
| S8 | Benton Electronics, "Servicing the Leslie Motors" | the O-ring engagement … (App. S8) | "Copyright © 2026 Benton Electronics" plus … (App. S8) | bentonelectronics.com/servicing-the-leslie-motors/ | yes |
| S9 | Benton Electronics, "Servicing the Leslie 122 Amplifier" | 6550A output pair, the 12AU7a "balanced amplifier" … (App. S9) | copyright notice plus an educational-purposes … (App. S9) | bentonelectronics.com/servicing-the-leslie-122-amplifier/ | yes |
| S10 | Penniman, "App Note 9: A Rotary Speaker Modeling Plug-In" (2014) … (App. S10) | two virtual mics at −135°/−45° … (App. S10) | "Copyright © 2014 Ross Penniman" in the … (App. S10) | willpirkle.com/Downloads/Rotary Speaker Sim App Note.pdf | yes |
| S11 | x42 Whirl Speaker (setBfree's `b_whirl`) | what the state of the art models: Model 600 IRs … (App. S11) | **GPL** — the page's only licence signal is … (App. S11) | x42-plugins.com/x42/x42-whirl | yes |
| S12 | setBfree | the emulator S11 comes from | **GPL-2.0** — the repo's `COPYING` is the GNU … (App. S12) | github.com/pantherb/setBfree (`COPYING`) | yes (both) |
| S13 | Strymon, "History of Rotary Speakers" | the switch's three positions … (App. S13) | "© 2026 Strymon, a division of Damage Control … (App. S13) | strymon.net/history-of-rotary-speakers/ | yes |
| S14 | Wikipedia, "Bark scale" | the critical-band table: band 12 has centre 1600 Hz … (App. S14) | CC BY-SA 4.0 (footer) | en.wikipedia.org/wiki/Bark_scale | yes (added by the second audit pass, A9.4) |

**Not reached, cited nowhere:** Kronland-Martinet & Voinier 2008 (the one
paper known to have measured a **122A**), S5's full text, nshos.com,
theatreorgans.com's mirror of S2, worldradiohistory.com's 1981 scan.
`geofex.com` and `web.archive.org` were not attempted (known dead here).
Searched for and not found: A2.

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **Second-order 800 Hz split.** With both Depth macros at 0, Balance centred and Brake on — no modulation in the path — the two bands' magnitudes are equal within 0.5 dB at a crossing frequency in **700–900 Hz**, and each band is **2.5–7 dB** *(ours; both classic second-order alignments, Butterworth's −3 dB and Linkwitz–Riley's −6 dB, fall inside it with margin for the reference — the alignment itself is §4's choice and is unsourced)* below its own **asymptotic passband level** (horn: mean over 3.2–6.4 kHz; drum: mean over 100–200 Hz); the **horn** band's slope fitted over **100–400 Hz** and the **drum** band's over **1.6–6.4 kHz** — two octaves into each band's own *stop*band — each read **10–14 dB/oct** (both alignments compute to 11.2–12.0 dB/oct there, A10.4). Separately, at the shipped depths, each band carries only its own rotor's rate: the other rotor's line and its harmonics sit **≥ 20 dB** *(ours)* below its own. | S1 p.3, S2, S6 (800 Hz); S2 (12 dB/oct, twice) | high on the corner … (App. T1) | an equal-magnitude crossing outside 700–900 Hz; a crossing level outside 2.5–7 dB below that band's asymptote; either fitted slope outside 10–14 dB/oct (a 6 or a 24 dB/oct build); either band showing the other rotor's rate within 20 dB of its own | **stepped** sine (1/12 octave … (App. T1) |
| T2 | **Two rotors, two speeds each, horn never slower.** At the shipped defaults each of the four rates is within **±2.5 %** *(ours)* of horn **6.67 / 0.80 Hz** and drum **5.70 / 0.667 Hz** (Fisher's 400/48 and 342/40 rpm), and at both speeds the horn's rate is **≥** the drum's. **How much faster is not sourceable, and this row claims nothing about it:** the three reached readings give 1.17/1.20 (Fisher), 1.03/1.00 (Azz) and "approximately the same rotational speed as the treble unit" (S2), so "horn ≥ drum" is the only ordering clause all three support (A10.5). | S7 (Fisher **and** Azz), S6, S2 | high on the four … (App. T2) | any of the four rates more than 2.5 % from its default; a drum rate above the horn's at either speed. Equal rates **pass**, and would agree with Azz and S2 | a steady 2 kHz tone (horn solo) … (App. T2) |
| T3 | **Horn Doppler is a sinusoid of depth `r_s·ω_m/c`.** The least-squares sinusoid fit at the rotation rate leaves a residual RMS **≤ 10 %** *(ours)* of the fitted peak deviation; the deviation's 2nd harmonic is **≥ 20 dB** *(ours)* below its fundamental; the tremolo ÷ chorale deviation ratio equals the measured rate ratio within **5 %**; and halving macro 9 (Horn Radius) halves the fitted deviation within **5 %**. The **absolute** depth is unsourced (§8.2), so no cents window is claimed. | S3 eq. 15–20 | high on shape … (App. T3) | no pitch modulation; a triangular or square deviation trace (residual over 10 %, or a 2nd harmonic within 20 dB); a deviation ratio more than 5 % off the rate ratio; a deviation that does not track macro 9 proportionally | instantaneous frequency from the … (App. T3) |
| T4 | **AM and FM are locked by geometry and do not walk.** Fit `M·cos(ω_m t + φ)` at the extracted rotation rate to the horn band's envelope and, separately, to its instantaneous-frequency deviation: the deviation **leads** the envelope by **+90° ± 15°** *(±15° is ours; the +90° is the source's geometry)* at both speeds, and still within ±15° after a chorale→tremolo→chorale cycle plus 60 s. That is "the amplitude maximum sits on the **falling** zero-crossing of the pitch deviation": eq. (20)'s deviation is `−(r_s·ω_m/c)·sin(ω_m t)` while §4.3.2 puts the amplitude maximum where the horn faces the listener, `ω_m t = 0` (A8.1, re-derived in A10.3). | S3 eq. 15–20 with §4.3.2; S2 | high — the sign … (App. T4) | **−90°**: an inverted directivity, loudest as the horn points away. **0° or 180°**: the amplitude peak at a pitch extreme, a quarter turn out. Any drift beyond ±15° across the ramps or over a minute | a 2 kHz tone, horn solo … (App. T4) |
| T5 | **AM depth grows with frequency, and the drum barely touches the bottom.** *(a)* Horn-band depth is non-decreasing across **1.0, 1.3 and 1.6 kHz** and depth(1.6 kHz) − depth(1.0 kHz) **≥ 0.5 dB** *(ours; the source gives the direction, not a size)* — all three points above the 800 Hz split and below 12 Barks — 1720 Hz, the 12th critical band's cut-off (S14) — which is the range S3's sentence covers. *(b)* Drum-band depth at 300 Hz **≥ 3 dB** while at 150 Hz **≤ 1 dB** *(ours)*. | (a) S3 §4.3.2, with S14 for the Bark→Hz … (App. T5) | (a) medium; (b) medium | (a) equal depth at 1.0 and 1.6 kHz, or depth falling with frequency — a gain tremolo wearing a crossover; (b) a modulated 150 Hz, or an unmodulated 300 Hz | steady tones at 150, 300, 1000 … (App. T5) |
| T6 | **The speed change is a ramp, and the drum lags.** Each rate moves continuously and monotonically to target; the drum reaches **90 %** *(the percentage is ours — S8 times "slow to fast and fast to slow" and defines none)* of the step in **5–8 s** both ways (S8, of the lower belt) and the horn in **≤ 0.5 ×** the drum's *measured* time on that same switch (**ours** — S2 gives only "a much longer time period" for the drum, and no reached source times the horn); T4 holds throughout; and nothing clicks — the largest `abs(x[n] − x[n−1])` during the ramp does not exceed the same statistic at steady tremolo on the same tone. | S8; S2; S4; S13; S1 p.5 (CHORALE brakes both … (App. T6) | medium | an instantaneous step in either rate; a drum 90 % time outside 5–8 s; a horn slower than half the drum; a non-monotone rate trace; a first difference above the steady-state one, which is a click at the switch | LFO extraction on a 1 s sliding … (App. T6) |
| T7 | **Stereo is two listeners, not a widener.** With a source whose two channels are identical, Mic Angle 0° gives **byte-identical** output channels. At 90°, the L and R envelopes' rotation-rate components differ in phase by the macro within **±10°** *(ours)* at chorale **and** at tremolo, with the **same channel leading** at both speeds — the angle is recovered from a phase, so the same 90° must come back at two rates 8× apart. | S3 §3.6; S10 (two mics at −135° and −45° … (App. T7) | medium | any inter-channel difference at 0° with an identical-channel source; no phase difference at 90°; a phase difference that **scales with the rate** — a lag equal in *seconds* at both speeds, which is a fixed inter-channel delay, the widener this trait denies; a recovered angle more than 10° from the macro; the leading channel swapping between speeds | horn band solo on a 2 kHz tone: … (App. T7) |
| T8 | **The drive is before the split.** At Drive 0.7 a 200 Hz tone's harmonics above 800 Hz carry the **horn's** rate while its fundamental carries the **drum's**; at Drive 0, harmonics 2–10 of the fundamental sum to **≤ −80 dB** *(ours)* re fundamental, counting only lines further than ±5 × the rotation rate from each harmonic so the rotors' own sidebands are not scored as distortion. | S2 (the signal "is sent into the Leslie … (App. T8) | high on the topology … (App. T8) | harmonics carrying the drum's rate, or the fundamental carrying the horn's — a drive after the split, or one per band; any harmonic distortion above −80 dB at Drive 0 | per-harmonic envelope-rate … (App. T8) |
| T9 | **Nothing steps.** With a steady 1 kHz carrier, every line at a block-rate offset — ±k × (fs ÷ block), k = 1…4: 187.5 Hz at 48 kHz and 256 frames, 375 Hz at 128, 172.3 Hz at 44.1 kHz and 256 — is **≤ −70 dB** re carrier, at both speeds. | mechanism (S2, S3) … (App. T9) | high | any line at a **named block-rate offset** above −70 dB re carrier, at either speed or either rate | 4 s of the horn band … (App. T9) |
| T10 | **Stop is the third position, and it stops without stopping the sound.** With Brake on both rates ramp to zero on T6's times — never a step, since "there was also a bit of lag when the brake was applied (Stop) or let go" (S13) — and after 15 s the output is time-invariant: envelope depth **≤ 0.2 dB** peak-to-peak and instantaneous-frequency deviation **≤ 0.5 Hz** *(ours)* on a 2 kHz and a 300 Hz tone, while each band's frozen level lies **inside the range its own Brake-off envelope spanned** on the same tone (min to max) — a stopped Leslie is a fixed horn and drum, neither a mute nor a gain change. | S13 (the switch's three positions … (App. T10) | medium — S13 is a … (App. T10) | modulation still present 15 s after the brake; a step to zero rather than a ramp; the output muting, or a band's frozen level outside the range its own modulation spanned; a click at the switch (T6's first-difference test) | the T2 envelope and … (App. T10) |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

The bucket brigade the vision found is the Doppler line.
`audioecho.FeedbackDelay` at `feedback=0, mix=2` is a pure per-sample
interpolated delay under a per-sample sine: `audioif_feedback_delay.c:201-202`
make dry 0 and wet 1, `:209-210` rotate a magic-circle oscillator once per
frame, `:212-214` add `wow_depth_frames × sine` to the read offset,
`:226-228` interpolate. Probed this run and re-probed independently by the
palette-verification pass (records A4 and A11): the fitted peak deviation
matched prediction to **0.0 %** at four settings and halved when `r_s` halved,
interpolation left **0.083 dB** of spurious AM at 2 kHz, every line at a named
block-rate offset sat at **−84.9 dB** re carrier or below (T9), a per-block
`set(wow_hz=)` ramp was phase-continuous with no waveform transient (T6's check
— largest `abs(x[n] − x[n−1])` over the ramp 2180 against 2183 at steady
tremolo), and an impulse through `delay_ms=3.0` peaked at frame 144 =
3.000 ms, which is where `latency_samples` comes from. One further palette fact
the Brake needs: `set(wow_hz=0)` zeroes `wow_step` and leaves the oscillator's
state untouched (`:111-115` against `:163-164`), so Brake **freezes** the rotor
where it stands instead of snapping it to zero phase — confirmed byte-identical
on CPython, MicroPython and CircuitPython (A11).

*(More of §4 is in **App. R** — moved under the length rule, nothing deleted.)*

## 5. Node asks

Four **additive options on `audioecho.FeedbackDelay`** were proposed — audioif's
own node, extend-never-modify, each defaulting off so a delay built without
them is byte-identical to today's. A new `audioecho.Rotor` with the same
arithmetic is equivalent if Phase 1 prefers not to widen a delay (§8.7).
**An independent palette-verification pass on 2026-09-06 re-read the C behind
every line cited here, re-ran every probe and tried each ask against routes
this seed had not considered: two of the four stand, two are refuted.**
Measured detail is in A4 and **A11** (the seed's pointer to "A6" was dangling;
there is no A6).

- A Mixer voice level under a `synthio.LFO` is block-rate by construction (T9) …  *(argument in full: App. R)*
- `audiomath.Multiply` with a table reaches per-sample AM, and reaches it …  *(argument in full: App. R)*
- **What a table cannot do is change rate.** It is one fixed period, so chorale …  *(argument in full: App. R)*

What R4 would buy is again **cost**: one line where the split needs two.

*(More of §5 is in **App. R** — moved under the length rule, nothing deleted.)*

## 6. Proposed surface

Sixteen macros — the ceiling, each a physical parameter of the cabinet
rather than a taste knob. The 122 sits at the defaults.

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Speed | TOGGLE | chorale / tremolo | the half-moon switch (S6, S13); sets both rotors' targets |
| 1 | Brake | TOGGLE | run / stop | the switch's third position (S13); targets 0 Hz through the ramps |
| 2 | Horn Fast | UNIPOLAR | 5.0–8.0 Hz log | the fast pulley groove (S1); default 6.67 Hz = 400 rpm |
| 3 | Horn Slow | UNIPOLAR | 0.5–1.5 Hz log | the slow motor; default 0.80 Hz = 48 rpm (S7) |
| 4 | Drum Fast | UNIPOLAR | 4.5–7.0 Hz log | default 5.70 Hz = 342 rpm (S7) |
| 5 | Drum Slow | UNIPOLAR | 0.4–1.2 Hz log | default 0.67 Hz = 40 rpm (S6, S7) |
| 6 | Horn Ramp | UNIPOLAR | 0.2–6 s log | the horn stack's inertia; default 2.5 s |
| 7 | Drum Ramp | UNIPOLAR | 1–12 s log | the drum's (S8: 5–8 s); default 6.5 s |
| 8 | Crossover | UNIPOLAR | 400–1600 Hz log | the fixed 800 Hz network; default 800 Hz, clamped below Nyquist |
| 9 | Horn Radius | UNIPOLAR | 0.01–0.40 m | the rotation radius — Doppler depth *and* the class's latency; default §8.2 |
| 10 | Horn Depth | UNIPOLAR | 0–1 | mic proximity: horn AM and directivity depth (S2's 1 foot vs 5 feet); default 0.6 |
| 11 | Drum Depth | UNIPOLAR | 0–1 | the drum's throb at the mic; default 0.5 |
| 12 | Mic Angle | UNIPOLAR | 0–180° | the pair's angular separation (S3 §3.6; S10's 90°, S11's 180°); default 90° |
| 13 | Drive | UNIPOLAR | 0–1 | the 40 W amplifier leaned on (S2); 0 = wire; the Drive family's waveshaper |
| 14 | Balance | BIPOLAR | −1…+1 | horn vs drum level — S10's convenience, which the cabinet lacks |
| 15 | Mix | UNIPOLAR | 0–1 | none on the cabinet; 0 = wire (Tier 1); default 1 |

Characters: none. Patches, named for settings and never products:
0 "Chorale Pair" (defaults, slow); 1 "Tremolo Pair" (fast); 2 "Chorale Close
Mono" (mic 0°, depths 0.9 / 0.7); 3 "Tremolo Wide" (mic 150°); 4 "Stopped"
(brake on — a fixed directive horn and drum); 5 "Driven Tremolo" (drive 0.7,
fast); 6 "Horn Only Fast" (drum depth 0, balance +0.5); 7 "Tremolo - lean"
(drum AM only, no drum Doppler line, no directivity sweep).

## 7. Defects in the current class the rebuild must not repeat

From one read of `lib/audioeffects/modulation.py`, 2026-09-06.

- `:153-154` — speed is a constructor string and **one** `rate` drives both
  rotors; no live switch, no ramp. The instrument's defining gesture is
  absent (T2, T6).
- `:155` with `:135-136` — the Doppler is a granular `audiodelays.PitchShift` …  *(argument in full: App. R)*
- `:156` with `:101-105` and `:86` — the tremolo is a Mixer voice level under …  *(argument in full: App. R)*
- `:158-159` — one panning LFO pans the **whole** signal, drum included; a …  *(argument in full: App. R)*
- `:141-160` — no crossover of any kind, so one modulation across the whole …  *(argument in full: App. R)*
- `:141-160` — no `LATENCY_SAMPLES` override, so `_core.py:140`'s 0 is …  *(argument in full: App. R)*
- `:1-3` — the module header calls the block rate "ample for musical sweep
  rates". The rebuild inherits the opposite standard (T9).

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **Crossover component pairing.** S1 p.22 carries the network's coil and
   capacitor values, but the scan could not be read reliably — a vision
   model transcribing a schematic is not evidence. T1 rests on the manual's
   *text* and S2's "12 dB per octave" instead, which fixes the trait.
   *Settles it:* Station A, from a legible p.22 or a short deck under
   `tools/spice/leslie122/`; it refines two Q values, not T1.
2. **Horn radius `r_s`** — fixes T3's absolute depth, macro 9's default and
   the class's latency; not reached. *Settles it:* Station A —
   Kronland-Martinet & Voinier 2008 (which measured a 122A), S5's full text,
   or a measurement from the manual's exploded views against the 29-inch
   cabinet width.
3. **Ramp shape** — linear or exponential in rate, and whether acceleration
   and deceleration differ (S5's abstract says they do; S8 gives one figure
   both ways). *Settles it:* the implementation session from S5 if
   obtainable; otherwise linear in hertz, one time per rotor, recorded.
4. **A fixed horn EQ.** S10 attributes "a strong band-pass characteristic
   centered at 2 kHz" to S2 — and S2's text as reached **does not contain
   it**, checked directly this run. S3 §4.3.2 does derive a Bark-smoothed
   fixed equalizer from the Model 600 measurements. *Settles it:* Station A
   — find the claim's origin or ship no fixed EQ; a constructor option
   either way, never a macro.
5. **Drive** — T8 needs a saturating stage before the split; the curve is
   the Drive family's table waveshaper, and until it lands macro 13 is
   declared and is a wire. *Settles it:* Phase 1's node list.
6. **Cabinet reflections** (S3 §5; S11's six) and a convolved
   angle-dependent horn response: out of scope for v1 on a board, and both
   add latency. *Settles it:* Phase 0's node list — it is a cost call.
7. **Ask form** — four options on `FeedbackDelay`, or one new
   `audioecho.Rotor`. **Phase 0's palette-verification pass answered half of
   it:** two of the four asks are refuted (§5, A11), so the surviving form is
   `wow_am_depth` and `wow_ramp_ms` — two floats, which is thin justification
   for a separate `Rotor`. *Settles it:* Phase 0's node list, on that basis.
8. **The CPython Mixer does not advance block inputs**, measured this run on
   three interpreters (§5 R1): an audioif bug in `src/cpython/audiomixer.py`
   independent of this class, which makes `Tremolo` and `AutoPan` static on
   CPython today. *Settles it:* Arthur files it; the implementation session
   fixes it in Phase 1 if it lands on the palette path.
9. **S3 budget** — whether two Doppler lines plus R1–R4 fit 0.30 of a block.
   *Settles it:* Station C on the boards; patch 7 is the escape valve.
10. **Length.** Sections 1–8 run to **49.6 KB** — measured after the palette
   verification pass, `head` to the `## Appendix` heading (45 KB after the
   second trait-critic pass, 39 KB before it; the seed's own "about 25 KB" was
   an estimate and was low). Well over the
   8–12 KB Phase 0 asks for, and that pass added 6 KB of it: 3.4 KB of
   measurement conditions in rows that could not be run without them, the
   rest items 13 and 14 below. The
   overrun is 14 source rows with license calls, 10 falsifiable traits with
   measurements, and 16 macros; every excerpt, probe narrative and derivation
   is already in the Appendix. *Settles it:* Arthur, at the survey — either
   the target moves for classes this dense, or he says which traits or
   sources to drop, which neither run would do on its own.
11. **T10 is an addition to a set the vision fixes before measurement.** The
   trait critic added it because the panel's only control has three
   positions and nothing gated the third: a Brake that jumps to zero, or
   that mutes instead of freezing, would have passed every other trait
   (A8.7). Adding it inside Phase 0 is legitimate — this is when the set is
   fixed — but it is a change to what the seed proposed. *Settles it:*
   Arthur, at the survey: accept T10 or strike it, before `GO effects`
   freezes the set.
12. **T8 cannot be gated until the waveshaper node lands.** Its first clause
   needs a drive stage that does not yet exist, so the class gate would
   otherwise record a trait it never exercised. The row now says so and
   carries the *unmeasured* wording. *Settles it:* Phase 1's node list — if
   the waveshaper does not survive, T8 reduces to its Drive-0 clause and the
   class ships with macro 13 declared and inert, which §6 must then say.
13. **T2's ratio clause was narrowed, not deferred.** The seed gated the
   horn ÷ drum ratio at 1.10–1.30 and asked Arthur to decide, with the
   sources 2–1 against it. The second trait-critic pass took the decision
   the evidence supports rather than leaving a gate no source carries:
   "horn ≥ drum at both speeds" is true of **all three** reached readings
   (Fisher 1.17/1.20, Azz 1.03/1.00, S2 "approximately the same"), so that
   is what T2 now gates, and the four rates stay pinned at ±2.5 % of the
   defaults §6 declares. Fisher's ratio survives as the *default*, where a
   user can move it, not as a trait. *Settles it:* Arthur may restore the
   1.10–1.30 window at the survey if he wants the class held to Fisher's
   reading; nothing else changes if he does.
14. **The real horn lobes; the model does not.** S2, on the diffuser fitted
   in the horn's mouth: the polar response is "almost omnidirectional; note,
   however, the 'lobing'. As the horn revolves, the sound will actually rise
   and fall a number of times, giving it an even more characteristic sound."
   No trait gates that — §4's build has one amplitude maximum per turn — and
   this pass would not invent a lobe count from a source that gives none.
   It is why T4 and T5 measure the envelope's **rotation-rate component**
   rather than its peaks: a lobed envelope has several peaks a turn and its
   fundamental is still where the horn faces the listener. *Settles it:*
   Station A, if S3's per-angle Model 600 measurements (§4.2) can be read
   closely enough to fix a lobe count; otherwise it stays unmodelled and
   §6 loses nothing, since no macro claims it.


## Appendix

### A1. Why the standout is not swapped to the 147

The literature that *measured* Leslies measured other cabinets: S7's speeds
are from a 147, S3's horn from a Model 600, S5's example is a 44W. That is
not an argument for a swap, because each source states the part is shared.
S6: the 147 "is the 'universal' version of the 122, designed for many
organs, and has a different amplifier input and motor speed control, but is
otherwise identical." S3 §4.1: "The Model 44W horn is identical to that of
the Model 600, and evidently standard across all Leslie models." The 122 is
also the cabinet whose own factory manual was reached — its *Installation
Instructions Manual*, not a service manual, and not the only Leslie manual
on that host: the same page's related-manuals list names Operating and
Maintenance Instructions Manuals for the 145 and the 147, neither fetched
(A9.6) — so the crossover, the amplifier and the drives come from the
standout itself; only the
mechanical and acoustic measurements are borrowed, each marked in its
trait's source column. The 122 stands.

### A2. Looked for, not found

- **A sourced horn radius.** The two modeling works that use `r_s` (S3) or a
  horn-radius parameter (S11) print no value in the text reached, and S11 is
  GPL so its defaults are not read. Kronland-Martinet & Voinier 2008 — the
  one paper known to have measured a 122A — was **not reached** on either run:
  the first recorded a publisher IdP, and the second audit pass got a bot
  "Client Challenge" interstitial from both
  `asmp-eurasipjournals.springeropen.com/articles/10.1155/2008/849696` and
  the `link.springer.com` mirror of the same DOI (A9.6). Either way it is
  cited nowhere. A targeted search for a numeric radius returned only the
  same two works.
  Recorded as unsourced; T3 claims shape and ratio only, and Tier 3's
  latency figure is stated at a provisional 0.20 m and marked as such.
- **The dividing-network values.** S1 p.22 is a scanned schematic and the
  fetch tool's reading of it was internally inconsistent (it placed a 3.2 mH
  coil under a label about reverb models). Not used. §8.1.
- **The 2 kHz band-pass claim.** §8.4.
- ~~**Motor mistuning.** S4 attributes "the speeds of the real motors are
  almost but not exactly the same" to S2; S2 as reached contains no such
  statement.~~ **Struck by the second audit pass (A9.1): S2 does contain it**
  — "ends up at approximately the same rotational speed as the treble unit"
  is the sentence S4 is paraphrasing. It is not a missing citation; it is a
  *third* rotor-speed reading, and it goes against T2's ratio clause rather
  than for it. T2 now records it.

### A3. A fetch summary is not the source

S4's fetch summary reported the paper's rotation rates as "approximately
48 RPM" slow and "342 RPM" fast — plausible, matching S7, and **wrong**. The
paper's own text says "The modulator frequency fm for slow rotation speed
was 2 Hz, and for the fast speed was 6 Hz", with the treble path 0.1 Hz
higher; those are the authors' perceptual choices, not measurements. The
summary supplied the number a reader would expect. Every PDF cited here was
therefore re-extracted with `pypdf` and read directly, as
`agent-knowledge/instrument-sources.md` already advises.

### A4. Probe record

Run against `audiocomponents/.venv/bin/python` (CPython + audioif),
`cmods/bin/micropython` and `cmods/bin/circuitpython`, 2026-09-06; every
number is quoted in §3–§5 so the seed does not depend on the scratch files.
Eight probes: the Doppler deviation fit at three settings; the L/R identity
check; the spectral-purity FFT; the block-rate `set(wow_hz=)` ramp; the
impulse latency; the mono render; the biquad DC tail at 800 and 150 Hz; the
Mixer/LFO advance on three interpreters. **The measurement method matters:**
a naive max-minus-min reading of the instantaneous-frequency trace over-read
the deviation by 47 % (62.6 Hz against a true 42.7 Hz) before the
least-squares sinusoid fit was used, which is why T3's measurement column
names the fit and not the peak — a kit that reads peaks would have called a
correct implementation wrong.

### A5. Quotations relied on, in full

- **S1 p.3:** "The internal design common to these six speakers features an
  800 Hz dividing network for separating; then channeling treble and bass
  frequencies to the treble and bass speakers." / "Signal above 800 Hz is
  channeled to the compression driver in the Treble rotor, while signal
  below 800 Hz drives the 15\" bass speaker." / "A pair of two-speed motor
  assemblies drive the Bass and Treble rotors at fast (Tremolo) or slow
  (Chorale) speed." (p.3 reads "A pair ot two-speed" — an OCR slip for "of".)
  **p.3's OCR is column-interleaved exactly as p.4's is** (A9.5), so those
  three are reconstructions from the page's own fragments — "features an
  800 Hz dividing" / "network for separat-" / "ing; then channeling treble
  and bass frequencies to" / "the treble and bass speakers." and so on — not
  contiguous strings. Every word is the page's; the ordering is ours.
  **p.4** is a two-column SPECIFICATIONS block that the page's OCR
  interleaves, so these are the page's own strings, not one contiguous
  sentence: "Models 122, 122V, 142, 222: One channel," … "40 watts" …
  "output." (the RV models' matching figure is "56 watt"); "Compression-type
  driver, permanent magnet, 16 ohm impedance."; "15 inch heavy duty,
  permanent magnet, 16 ohm impedance."; "Model 122, 122V, 122RV: 41\" high,
  29\" wide, 201/2\" deep." The 40 W reading is corroborated by S2's
  "40-watt monophonic tube amplifier", S6's "40 watt tube amplifier" and S9's
  "these amps are only 40 watts". **p.5:** "Select desired speed of the
  Treble rotor by slipping [the] Treble drive belt [into the] grooves in the
  3-step motor drive pulley"; "The Tremolo switch controls rotor speed
  through … of the two-speed [motor assemblies]" (same column scramble; the
  page's fragments are "The Tremolo" / "switch controls" / "rotor speed
  through" / "the fast and slow motors" / "of the two-speed" / "assemblies."
  — so the elision hides "the fast and slow motors", nothing else). p.5 also
  carries the console-connector control list: "TREMOLO Control" / "CHORALE:
  Small motors" … "actuated to brake Bass and" / "Treble" / "rotors" … "to
  Chorale speed." **No Stop position appears on any page reached** (A9.2).
- **S2:** the crossover appears three times and no sentence contains all of
  it at once — "an 800 Hz 16-ohm passive crossover", "a 12 dB per octave,
  16-ohm crossover", and "The stock Leslie crossover is a 12 dB per octave,
  800 Hz unit"; "a rotating wooden drum" whose "cylinder fitted with a
  'scoop' … starts vertically (the bass driver faces downward into its
  entrance) and projects sound horizontally"; the drum works
  "just as an AM device, and only for the upper two octaves or so of the
  bass section (200 to 800 Hz)"; "3/4-inch throat Jensen compression driver"
  under a "twin-bell, molded black bakelite horn"; mics "as close as 1 foot"
  and "about 5 feet away from the Leslie, aimed midway between top and
  bottom rotors"; the drum's "slower response to speed changes" and "Slower
  acceleration of the lower rotor"; a "40-watt" amp with "6550 tubes" giving
  "warm rich distortion". **And the sentence the second audit pass found
  (A9.1), which T2 must answer:** "The drum assembly is driven with a
  two-speed motor, and ends up at approximately the same rotational speed as
  the treble unit. The only difference is that the drum's inertia makes it
  approach final speed over a much longer time period."
- **S3 §4.1:** "Two horns are apparent, but one is a dummy, serving mainly
  to cancel the centrifugal force of the other during rotation." / "The
  Model 44W horn is identical to that of the Model 600, and evidently
  standard across all Leslie models." / "In the Leslie, a diffuser is
  inserted into the end of the horn in order to make the radiation pattern
  closer to uniform, so the omnidirectional assumption is reasonably
  accurate." / eq. 15–16 and "Note that the source velocity vector is always
  orthogonal to the source position vector." / eq. 20 and "in the far field,
  a rotating horn causes an approximately sinusoidal multiplicative
  frequency shift, with the amplitude given by horn length rs times horn
  angular velocity ωm divided by sound speed c." **§4.2:** "The horn was set
  manually to fixed angles from -180 to 180 degrees in increments of 15
  degrees, and at each angle the impulse response was measured using
  2048-long Golay-code pairs." **§4.3.2:** "below 12 Barks or so, the
  angle-dependence is primarily to decrease amplitude as the horn points
  away from the listener, with high frequencies decreasing somewhat faster
  with angle than low frequencies." **§5**, whose first clause is S3 reporting
  S2 and not S3's own finding — its [3] is Henricksen, and the "throb" is
  S2's own word ("The result is a low-frequency 'throb'"), A9.3: "In [3], it
  is mentioned that an AM 'throb' is the main effect of the rotating woofer
  port. A modulated lowpass-filter cut-off frequency has been used for this
  purpose by others." **§3.6:** "The two stereo
  outputs may correspond to 'left and right ears,' or, more generally, to
  left- and right-channel microphones in a studio recording set-up."
- **S4 §3.1–3.2:** "These horns are quite directive and thus the output
  effect contains significant amplitude modulation." / "This drum
  effectively adds a directional pattern to the bass sound and thus
  generates amplitude modulation when rotated." / "it is prudent to also use
  two separate oscillators for modulation. This enables the use of the
  characteristic speed-up and slowdown effects of the Leslie speaker where
  the bass unit accelerates slower due to the inertia of the unit."
- **S5 abstract:** "The midrange horn and subwoofer baffle are individually
  modeled, with their rotational dynamics separately tracked" / "The
  rotational speeds of the horn and baffle are modeled using FIR filters
  having different shapes for acceleration and deceleration."
- **S6:** "about 50 revolutions per minute (rpm) for 'chorale' and 400 rpm
  for 'tremolo', compared to the woofer's 40 rpm and 340 rpm respectively."
  / "The crossover is deliberately set to 800 Hz to give the optimum balance
  between the horn and the drum."
- **S7:** upper "400 RPM on tremolo and 48 RPM on chorale", lower "about 342
  RPM on tremolo and 40 RPM on chorale" (J. Fisher, Leslie 147, "with the
  belt in the middle pulley position and with a normal belt tension"); "the
  'chorale' speed is about .8 Hz, and the 'tremolo' or 'lush tibia' speed is
  5.7 to 6.8Hz" (D. Dillon). **And, on the same page:** "Sal Azz reports the
  upper rotor speed (middle pulley) to be 409 rpm, and lower rotor speed to
  be 396 rpm. Chorale speed is 48-49 rpm, for both upper and lower rotors."
  T2 is written from Fisher's reading and says so; Azz's would fail it.
- **S8**, under the heading *Adjusting the Lower Belt* — so the figure is
  the **drum's**: "My test for belt tension is this; 5 to 8 seconds. In other
  words, if I don't have any o'ring slippage,(which is what I want) then the
  belt is adjusted so that the time from slow to fast _and_ fast to slow is
  around 5 to 8 seconds."
- **S9:** "Relay switching in a 122 is carried out by applying a DC voltage
  to the balanced input of the Leslie Amp. This voltage is applied equally to
  both input pins. Pin-1 and Pin-6." / "There is a 1meg resistor connected to
  pin-1 of the Leslie input that goes to the relay switching tube. It senses
  the DC and turns on or off the switching tube which in turn turns on or off
  the relay." / "This voltage should be around 50 or 60 Vdc." / "Remember
  these amps are only 40 watts and can easily over driven." / "The 12AU7a
  tube requires a voltage to the plates. This is a dual tube and works as a
  balanced amplifier." / "The OC3 tube is the regulator". The article says
  nothing about what the relay switches on the motor side.
- **S10:** "The real Leslie speaker exhibits a strong band-pass
  characteristic centered at 2 kHz [1]" (its [1] is S2 — §8.4); "The
  modulation effect of the rotating baffle is simulated using a tremolo
  effect with an envelope that has a sinusoidal shape in decibels. However,
  not all frequencies are affected equally by the baffle. Frequencies below
  200 Hz are likely unaffected"; "The left microphone has a 'rotation angle'
  of -135 degrees, and the right microphone has a 'rotation angle' of -45
  degrees."
- **S13:** the switch "had three positions: slow (or Chorale), fast (or
  Tremolo), and Stop"; "it took several seconds for the speed changes to
  happen completely."

### A7. Audit corrections applied, 2026-09-06

An independent license-and-citation pass re-fetched all thirteen sources —
S1 pp. 1/3/4/5/22, S2, S3's PDF and index and its *PASP* restatement, S4's
PDF, S5's abstract page, S6's raw wikitext, S7 **and its OPL licence page**,
S8, S9, S10's PDF, S11, S12's `COPYING`, S13 — and checked every quotation in
§1, §3 and A5 against the document's own text: HTML pulled raw and stripped
of markup rather than summarised, PDFs re-extracted with `pypdf`, Wikipedia
read as wikitext (where the crossover sentence is `800&nbsp;Hz`, which is why
a naive grep for "800 Hz" misses it). Licence chains were followed one hop
past the page — ManualsLib's terms, dannychesnut.com's homepage footer,
HammondWiki's `opl.html`, x42's GPL badge into setBfree's `COPYING`.

Eight corrections landed, all in §1, §2, §3 and A5; §4–§8 were not touched.
(One defect found there and left for Arthur rather than edited: §5 points at
"A6" for each node ask's measured detail, and there is no A6 — A4 is the
probe record. This section is numbered A7 so it does not sit in that gap.)

1. **S1's title was wrong.** The document at ManualsLib `4079586` is the
   Leslie 122 *Installation Instructions Manual*, not an *Operating and
   Maintenance Instructions*. (Those exist on ManualsLib for the 145, 147 and
   147RV — a neighbouring row, not this one.)
2. **S1's p.4 quotation was a reconstruction.** "Models 122, 122V, 142, 222:
   One channel, 40 watts output." is not a contiguous string on the page; the
   spec block is two columns and the OCR interleaves them. The 40 W fact
   stands — three other reached sources give it — but A5 now shows the
   page's actual strings.
3. **S2's crossover quotation was spliced.** "a 12 dB per octave, 16-ohm
   passive crossover" appears nowhere in Henricksen. The page has "an 800 Hz
   16-ohm passive crossover" and, separately, "a 12 dB per octave, 16-ohm
   crossover". §1 now quotes the second, verbatim.
4. **The drum's "AM throb" quotation was spliced across two documents** —
   the "throb" is S3 §5's word, the "upper two octaves … (200 to 800 Hz)" is
   S2's sentence, and the seed ran them together inside one pair of quotation
   marks with an ellipsis. §1 now attributes each half.
5. **"push-pull" and "swapping mains between windings" were unsourced.** No
   reached source says the 122's output stage is push-pull, and S9 says only
   that a switching tube turns the relay on and off — never what the relay
   switches. Both cut back to what S1 and S9 say.
6. **S7's licence chain was left unread and is now read.** HammondWiki's
   "free information … under certain conditions" resolves at
   `dairiki.org/HammondWiki/opl.html` to the **OpenContent License v1.0**, a
   share-alike copyleft. Reached this run; the row now names it.
7. **S7 carries a second measurement that contradicts T2.** Sal Azz's
   409/396 rpm on tremolo and "48-49 rpm, for both upper and lower rotors" on
   chorale give ratios of 1.03 and 1.00, outside T2's window (1.10–1.25 then,
   1.10–1.30 after the trait critic pass, A8.3 — outside both) and
   against its "horn always faster" clause. The seed cited only Fisher's
   reading. T2's confidence drops to medium and names the conflict; §2 and A5
   record both readings.
8. **S3's directivity statement carries a frequency qualifier the seed had
   dropped.** The paper says "*below 12 Barks or so*, the angle-dependence is
   primarily to decrease amplitude … with high frequencies decreasing
   somewhat faster with angle than low frequencies" — twelve Barks is about
   1.7 kHz. §1 and §2 now carry the qualifier, and T5's 6 kHz point is marked
   as extrapolating past it. (A5 had quoted the sentence in full all along;
   §1, §2 and T5 had not.)

Two smaller things went in with them: T6's "the horn reaching 90 % in under
half that" is marked as an **unsourced design threshold** (S2 and S4 say
"slower", and no reached source times the horn), and S8's 5–8 s is marked as
stated of the **lower** belt, which is the drum — the use T6 already made of
it. Every other row's licence call, "reached" claim and quotation was
confirmed against the source as read this run, including the two that most
needed it: S10's 2 kHz band-pass claim really is attributed to Henricksen
([1] in the app note) and Henricksen's text really does not contain it
(§8.4), and S4 really does attribute the motors' near-but-not-equal speeds to
Henricksen, who does not say that either (A2).

### A8. Trait critic pass, 2026-09-06

An independent pass over **Tier 2 alone**, against vision §3's bar: is each
row falsifiable as stated, does it name a source, a confidence, a
disconfirmation condition and a concrete measurement. Structural checks
first: the Tier 1 block was diffed against `TEMPLATE.md` lines 37–62 and is
**verbatim, no drift**; Tier 3 carries both boards (P4 0.12, S3 0.30) and its
latency paragraph with the knob that trades it (macro 9). Sources re-reached
first-hand in this pass and used for the rewrites below: **S2, S3** (the
DAFx-02 PDF fetched and extracted locally with `pypdf`, not read from a fetch
summary — A3's rule), **S6, S7, S13**, and S3's *PASP* restatement. Nothing
below cites a source this pass did not open. Nine rows rewritten, one added;
**ten traits stand**, well over the three a non-*design* grade needs.

**A8.1 — T4's sign is right, and the row now says why.** The seed asserted
the amplitude peak sits on the *downward* zero-crossing of the pitch
deviation without deriving it, which is the one trait here an implementer
could invert while believing they had matched the dossier. From S3's own
text: eq. (16) gives the rotating horn's source velocity and notes "the
source velocity vector is always orthogonal to the source position vector";
eq. (19) reduces the far-field projection, with the listener at
`x_l = (r_l, 0)`, to `v_sl ≈ −r_s·ω_m·sin(ω_m t)·[1,0]`; eq. (20) is
`ω_l = ω_s / (1 + r_s·ω_m·sin(ω_m t)/c) ≈ ω_s·[1 − (r_s·ω_m/c)·sin(ω_m t)]`.
At `ω_m t = 0` the horn faces the listener, the deviation is zero, and an
instant later (`sin > 0`) it is negative — a falling crossing. §4.3.2 puts
the amplitude maximum at that same instant, since the angle-dependence is
"primarily to decrease amplitude as the horn points away from the listener".
Peak on the falling crossing. The 90°-out and 180°-out failures are now both
named in the row's disconfirmation column, where before only the 90° one was.

**A8.2 — T5's 6 kHz clause is withdrawn from gating.** S3's sentence is
qualified: "*below 12 Barks or so*, the angle-dependence is primarily to
decrease amplitude … with high frequencies decreasing somewhat faster with
angle than low frequencies". Twelve Barks is about 1.7 kHz. A7.8 caught the
qualifier and marked the 6 kHz point as extrapolating past it, but left it
inside the gating clause, so the trait as written could have failed a
correct build for a reason no source supports. The gated comparison now sits
at 1.0 / 1.3 / 1.6 kHz — above the 800 Hz split, below 12 Barks, inside the
source — and the 6 kHz depth is *recorded but not gated*, for Station A.

**A8.3 — T2's rate windows and its ratio clause could not both be met.** The
seed's windows (horn 6.4–6.9, drum 5.5–6.0 Hz) admit a build at 6.4 / 6.0,
whose ratio is 1.07, outside the same row's stated 1.10–1.25. A trait that
can be satisfied and violated by one measurement is not a trait. The rates
are now pinned to the sourced defaults (Fisher's 400/48 and 342/40 rpm) with
a ±2.5 % tolerance, and the ratio window is 1.10–1.30 — jointly satisfiable
at every corner (worst case 6.50 ÷ 5.84 = 1.11; 0.82 ÷ 0.650 = 1.26). Both
readings that survive re-fetch put the horn ahead: Fisher 1.17 and 1.20,
S6's own numbers 1.18 and 1.25. S6's sentence "On both settings, the treble
horn rotates slightly faster than the bass woofer" is added to the
confidence cell, because it is a second independent source for the clause
Azz's reading attacks — the conflict is real but it is one reading against
two.

**A8.4 — T1's two slope bands were the wrong way round.** The row read
"slope fitted over 1.6–6.4 kHz / 100–400 Hz" under a section that has just
defined the order as horn-then-drum, which puts each fit in that band's
*pass*band, where the answer is 0 dB/oct and the measurement cannot fail.
Each band is now named with its own octave pair, two octaves into its
stopband. T1 also gained the two things it lacked: what "crossing" means
(equal magnitude, within 0.5 dB) and a threshold on the cross-modulation
clause (20 dB), which was previously an unfalsifiable "returns that band's
rate alone".

**A8.5 — every unsourced number is now labelled.** T6 already carried the
convention ("an unsourced design threshold"); the other rows did not, so ±15°,
20 dB, 10 %, 5 %, ±10°, 3 dB, 1 dB, −70 dB and −80 dB read as if the sources
supplied them. Each is now marked *(ours)* with the sourced part of its
clause — the direction, or the centre — stated beside it. This changes no
number; it changes what an audit can hold the sources to.

**A8.6 — the measurements that could not fail, and now can.** T3's
"plus the residual" named no threshold, so a fit of any quality passed: it is
now a residual RMS ≤ 10 % of the fitted deviation, and T3 gains a second
falsifiable clause straight out of eq. (20) — halving macro 9 halves the
deviation, since the depth is `r_s·ω_m/c` and `r_s` is that macro. T6's
"largest 1 ms change of instantaneous frequency … not exceeding the
steady-state figure" is replaced by a waveform test that can actually be run
and read, `abs(x[n] − x[n−1])` over the ramp against the same statistic at
steady tremolo. T7's "a lag not scaling as 1/rate" is sharpened into the
failure it is guarding against: a lag equal in *seconds* at both speeds is a
fixed inter-channel delay, which is exactly the widener the trait denies.
T2's envelope-spectrum peak now says that harmonics of the rate are expected
(directivity is not sinusoidal) so a correct build is not failed for them.
T8's THD clause says which lines are counted and excludes the rotors' own
sidebands, which a naive THD would have scored as distortion and failed.

**A8.7 — T10 is new, and §8.11 asks Arthur to accept or strike it.** The
panel is one switch with three positions and the seed's traits gated two of
them. A Brake that steps to zero instead of ramping, or that mutes rather
than freezing the rotors at a fixed angle, passes T1–T9 untouched. S13, read
in this pass, states both halves: the switch "had three positions: slow (or
Chorale), fast (or Tremolo), and Stop", and "there was also a bit of lag when
the brake was applied (Stop) or let go". Patch 4 already ships the state; now
something measures it.

**A8.8 — left alone.** T9 needed nothing but the sample-rate generalisation
(`fs ÷ block`, so the trait is rate-honest as Tier 1 requires); it was
already the strongest row here — a threshold, a named artefact, a probe, and
a measured floor. T6's 5–8 s window, T5(b)'s 200 Hz boundary and T8's
topology all re-fetched clean.

**One evidence note.** A fetch of S2 in this pass returned "a 12 dB per
octave, 16-ohm passive crossover" as if contiguous — the exact splice A7.3
struck after reading the page's raw HTML. A summariser is not the source
(A3), so A7.3 stands unchanged and T1 rests on the two separate phrases the
audit verified; recorded here because the same summariser will produce the
same splice for the next reader.

### A9. License and citation audit, second pass, 2026-09-06

A second independent license-and-citation pass, run after A7 and A8, with no
reliance on either. Every URL in §2 and everywhere else in the seed was
re-fetched from scratch in this run: S1's pp. 1/3/4/5/22 and ManualsLib's
`terms.html`; S2 and dannychesnut.com's homepage; S3's `dafx02.pdf`, its
`/~jos/doppler/` index and the *PASP* page; S4's PDF and `dafx.de/paper-archive/`;
S5's abstract page; S6 as `?action=raw` wikitext **and** as a rendered page for
its licence footer; S7 and `opl.html`; S8; S9; S10's PDF; S11 and the `href`
behind its GPL badge; S12's `COPYING` and GitHub's licence field; S13. HTML was
pulled raw and stripped of markup, never summarised (A3); the three PDFs were
re-extracted with `pypdf` from the venv and grepped for each quoted string.

**Every licence call in §2 was confirmed as written.** ManualsLib's terms do
read "personal non-commercial use" and "commercial use of any User content is
strictly prohibited"; dannychesnut.com carries no copyright or terms line on
the article *or* the homepage; S3's index page reads "Copyright © 2016-03-26
by Julius O. Smith III, Stefania Serafin, Jonathan Abel, David P. Berners";
neither S4's PDF nor dafx.de's paper archive states any licence; S5's footer
reads "site copyright © 2009-2023 Stanford University"; S6 and the new S14 are
CC BY-SA 4.0; S7's page carries the Dairiki copyright and links `opl.html`,
which is the OpenContent License v1.0, share-alike; both Benton pages read
"Copyright © 2026 Benton Electronics"; S10's running footer reads "Copyright ©
2014 Ross Penniman"; S11's GPL badge sits inside
`<a href="https://github.com/pantherb/setBfree">Source Code</a>`, and that
repository's `COPYING` is the GNU GPL v2 with GitHub's field agreeing; S13's
footer reads "© 2026 Strymon, a division of Damage Control Engineering". No
row was downgraded. Every "Reached" cell was true. Six corrections landed, in
§1, §2, §3, A1, A2 and A5; §4–§8 were not touched.

1. **A source already cited contradicts T2, and A2 had struck the wrong
   claim.** S2's "Bass Rotor" paragraph reads: *"The drum assembly is driven
   with a two-speed motor, and ends up at approximately the same rotational
   speed as the treble unit."* A2 had said S2 "contains no such statement"
   when striking S4's attribution — S4 was paraphrasing this sentence, and
   the attribution was sound. The consequence is bigger than the citation:
   A7.7 asked Station A for a third rotor-speed reading, and it was inside a
   source the seed already relies on. It agrees with S7's Azz reading
   (1.03 / 1.00) and against Fisher's and S6's (1.17–1.25). T2's confidence
   drops to **low**, its cell names the conflict, §1 and A5 carry the
   sentence, and the ratio clause goes to Arthur at the survey — 2–1 against
   as it stands. The four *rates* are untouched; only the ratio clause is.
2. **§1 gave the 122 a three-position Stop switch that no reached source
   gives it.** S13's sentence is about the remote switch "found on organs
   like the Hammond B3", not the 122; and S1 p.5, the 122's own manual,
   lists a console-connector TREMOLO control whose CHORALE position brakes
   the rotors "to Chorale speed", with **no Stop position on any page
   reached**. §1 now says which source says what, §2's S13 and S1 rows carry
   it, and A5 quotes p.5's control list. T10's own confidence cell had
   already flagged S13 as a manufacturer history page; §1 had not.
   **T10 as a trait is unaffected** — but Arthur's §8.11 accept-or-strike
   call should be made knowing the 122's own manual does not show the third
   position.
3. **S3 §5's "throb" is S3 reporting Henricksen, not S3's own finding.** The
   paper's sentence begins "In [3], it is mentioned that…", and its [3] is
   Henricksen — whose page has "The result is a low-frequency 'throb'". A7.4
   had split this quotation across S3 and S2 already; this pass restores the
   lead-in so the chain reads correctly. No trait moves.
4. **"Twelve Barks is about 1.7 kHz" was an unsourced conversion** carrying
   T5(a)'s upper bound and §1's qualifier. Sourced now: the 12th critical
   band's cut-off is 1720 Hz (S14, added).
5. **A5 presented S1 p.3 as contiguous quotation.** p.3's OCR is
   column-interleaved exactly as p.4's is — A5 had flagged the scramble for
   p.4 and p.5 only. Every word is the page's; the ordering was ours, and A5
   now says so and shows the fragments. No fact moves: the 800 Hz split, the
   15" woofer and the pair of two-speed motor assemblies are all on the page.
6. **Two "what was reached" claims were imprecise.** A1 called S1 the 122's
   "service manual" after A7.1 had corrected the title to *Installation
   Instructions Manual*, and implied it was the only Leslie manual reachable
   — the same ManualsLib page lists Operating and Maintenance Instructions
   Manuals for the 145 and 147 (not fetched). And A2 recorded
   Kronland-Martinet & Voinier 2008 as "behind a publisher IdP"; this pass
   got a bot "Client Challenge" from both the SpringerOpen article page and
   the `link.springer.com` mirror. Not reached either way, cited nowhere.

**Checked and clean, worth naming so nobody re-checks them.** S10's 2 kHz
band-pass claim really is footnoted to Henricksen and Henricksen's text
really does not contain "2 kHz" or "band-pass" anywhere (§8.4 stands). S8's
"5 to 8 seconds" really does sit under the heading *Adjusting the Lower Belt*,
i.e. the drum, and its italicised *and* is the page's own `<em>`, not emphasis
the seed added. S9 really never says what the relay switches, and never says
"push-pull" (A7.5 stands). S1 p.22's scan really is unusable: its OCR yields
"3.2MH" and "5.2 MH" adrift among amplifier labels and next to "INTERCEPTOR ON
REVERB MODELS", which is the mis-pairing A2 describes — §8.1 stands. Tier 3's
arithmetic checks: 0.20 m ÷ 343 m/s = 0.583 ms = 28 frames at 48 kHz, +1 =
29 frames = 0.60 ms, 6 % of a 10 ms round trip. The one number in §1 or §3
still taken from general knowledge rather than a row is the speed of sound,
c = 343 m/s.

### A10. Trait critic pass, second run, 2026-09-06

A second independent pass over **Tier 2 alone**, run after A7, A8 and A9 and
relying on none of them: every source a rewritten row leans on was re-fetched
in *this* run and read directly, and every palette number a row quotes was
re-measured in this run rather than inherited. The bar is the vision's §3 — is
the row falsifiable as stated, does it name a source, a confidence, a
disconfirmation condition and a concrete measurement, and could that
measurement actually fail. **Ten rows before, ten rows after:** none added,
none deleted, **nine rewritten in place** (T1–T10 less T6, which took only two
markings). The three defects worth leading with are that **T9's measurement
could not have passed a correct build**, that **T2's 20 s chorale record could
not resolve the tolerance it gated**, and that **T10's level clause failed any
build that freezes the horn off-axis**.

#### A10.1 The palette, re-probed in this run

`audiocomponents/.venv/bin/python` (CPython + audioif), one
`audioecho.FeedbackDelay` at `feedback=0, mix=2` — §4's Doppler line — under
`wow_hz` = the rotor rate and `wow_depth_ms = 1000·r_s/c` at the provisional
`r_s = 0.20 m`, fed a −12 dBFS sine. Four probes, every number below measured
here:

- **Doppler depth and shape.** The least-squares sinusoid fit of the
  instantaneous-frequency trace recovered `r_s·ω_m·f/c` to **0.0 %**
  (24.425 Hz fitted against 24.425 Hz predicted, 1 kHz carrier, 6.67 Hz), with
  a residual RMS of **2.2 %** of the fitted deviation and a deviation second
  harmonic **105 dB** down. T3's three thresholds (10 %, 20 dB, and
  proportionality) therefore have real margin on the palette and are not
  floor tests.
- **The naive read.** max−min/2 of the same trace over-read the fit by
  **9.3 %** at this setting. (A4 recorded 47 % at another; the direction is
  what generalises, and it is why T3 and T5 name a fit.)
- **The oscillator's own accuracy.** The realised wow rate, recovered by a
  parabolically interpolated envelope-spectrum peak, was **6.6797 Hz for a
  requested 6.6667 — +0.195 %** (the magic-circle oscillator's frequency
  warping). T2's ±2.5 % window clears it by an order of magnitude; a ±0.1 %
  window would have failed the node, not the class.
- **Spectral purity, and the trap in the seed's measurement.** At the block-rate
  offsets the seed names, the worst line was **−97.0 dB re carrier** (±k·187.5 Hz,
  k = 1…4, 48 kHz/256) and **−98.6 dB** for 128-frame blocks — so T9's −70 dB
  claim is measurable with 27 dB of headroom. But the seed's *measurement*, "the
  largest line that is not a rotation-rate multiple", returned **−53.2 dB under a
  Hann window and −73.2 dB under a Blackman–Harris one, at different
  frequencies** — the modulation index here is ≈3.7, so the carrier sits inside
  ten strong FM sidebands 6.7 Hz apart and that statistic reads the analysis
  window, not the class. As written it would have failed a correct build at the
  −70 dB threshold. T9 now names the offsets and the window.
- **The Drive-0 floor.** Through the same line under rotation, harmonics 2–10 of
  a 200 Hz tone (Blackman–Harris, ±5×rate excluded around each) summed to
  **−90.8 dB** re fundamental — h3 the largest at −92.7 dB. T8's −80 dB clause
  has 10 dB of margin over what the palette does with no drive in it at all.

#### A10.2 Sources re-reached first-hand in this run

Every one fetched in this run and read as text (HTML pulled raw and stripped of
markup; PDFs downloaded and extracted with `pypdf` in the repo venv, never a
fetch summary — A3's rule). No row's licence call was re-litigated; A9 owns
those.

| Source | Reached at | What it settled for a rewrite |
|---|---|---|
| S1 pp. 3, 5 | `manualslib.com/manual/4079586/Leslie-122.html?page=3` / `?page=5` | the 800 Hz split and the pair of two-speed motor assemblies (T1, T8); p.5's CHORALE position "actuated to brake Bass and Treble rotors to Chorale speed" — the down-ramp is driven (T6); the block diagram's switch is TREMOLO/CHORALE, no Stop (T10's confidence) |
| S2 | `dannychesnut.com/Music/Leslie/LeslieMystery.html` | "a 12 dB per octave, 16-ohm crossover" and "The stock Leslie crossover is a 12 dB per octave, 800 Hz unit" (T1); "ends up at approximately the same rotational speed as the treble unit" (T2); "only for the upper two octaves or so of the bass section (200 to 800 Hz)" and "Frequencies lower than 200 Hz are probably uneffected" (T5b); the amplifier "driving a 12 dB per octave, 16-ohm crossover" (T8); the mic pair on opposite corners (T7); **and the lobing sentence** (§8.14) |
| S3 | `ccrma.stanford.edu/~jos/doppler/dafx02.pdf` | eq. 15–20 read in the PDF's own text, including "the source velocity vector is always orthogonal to the source position vector" and eq. 20's far-field sinusoid of amplitude `r_s·ω_m/c` (T3, T4); §4.3.2's "below 12 Barks or so … high frequencies decreasing somewhat faster with angle" (T5a); §3.6's two stereo outputs as L/R mics (T7) |
| S4 | `dafx.de/paper-archive/2011/Papers/49_e.pdf` | "the bass unit accelerates slower due to the inertia of the unit" (T6) |
| S5 | `ccrma.stanford.edu/papers/discrete-time-emulation-of-leslie-speaker` | abstract only, as before: "different shapes for acceleration and deceleration" (T6) |
| S6 | `en.wikipedia.org/wiki/Leslie_speaker?action=raw` | 50/400 against 40/340 rpm and "the treble horn rotates slightly faster than the bass woofer" (T2); "Some early models were limited to 'off' and 'tremolo', and some later models had all three settings" — a second reached source for a third switch position (T10) |
| S7 | `dairiki.org/HammondWiki/LeslieRotationSpeed` | Fisher's 400/48 and 342/40 rpm **and**, on the same page, Azz's 409/396 and "48-49 rpm, for both upper and lower rotors" (T2) |
| S8 | `bentonelectronics.com/servicing-the-leslie-motors/` | "5 to 8 seconds … from slow to fast _and_ fast to slow", under *Adjusting the Lower Belt* — the drum's, and with no percentage attached (T6) |
| S9 | `bentonelectronics.com/servicing-the-leslie-122-amplifier/` | "these amps are only 40 watts and can easily over driven" (T8) |
| S10 | `willpirkle.com/Downloads/Rotary Speaker Sim App Note.pdf` | prose only: mics at −135° and −45° (T7); "Frequencies below 200 Hz are likely unaffected" (T5b). Its C++ listing was not read |
| S13 | `strymon.net/history-of-rotary-speakers/` | the switch's "three positions: slow (or Chorale), fast (or Tremolo), and Stop", of the remote switch on organs like the B3, and "a bit of lag when the brake was applied (Stop) or let go" (T10) |
| S14 | `en.wikipedia.org/wiki/Bark_scale?action=raw` | band 12's cut-off, 1720 Hz (T5a) |

**Not opened in this pass:** S11 and S12, the GPL emulator chain — no Tier 2
row cites them, and a trait critic has no reason to open a copyleft source.

#### A10.3 T4's sign, re-derived, and the measurement that can read it

From S3's own text as fetched here: eq. (15) puts the source at
`r_s·(cos ω_m t, sin ω_m t)`, eq. (19) reduces the far-field projected velocity
to `−r_s·ω_m·sin(ω_m t)`, and eq. (20) gives
`ω_l ≈ ω_s·[1 − (r_s·ω_m/c)·sin(ω_m t)]`. At `ω_m t = 0` the horn is nearest
the listener and pointing at it, the deviation is zero and falling; §4.3.2 puts
the amplitude maximum at that same instant. So the envelope's rotation-rate
component is a **cosine** and the deviation's is `−sin` — the deviation leads by
exactly **+90°**, which is A8.1's conclusion reached again from the paper rather
than from A8.

The pass then checked that the *measurement* can read that, on four synthetic
builds (2 kHz carrier, 6.67 Hz, `r_s = 0.20 m`, AM depth 0.6), fitting
`M·cos(ω_m t + φ)` to the Hilbert envelope and to the instantaneous-frequency
deviation:

| Build | φ_dev − φ_env |
|---|---|
| correct — loudest facing the listener | **+90.0°** |
| inverted directivity (loudest facing away) | −90.0° |
| a quarter turn out, one way | 0.0° |
| a quarter turn out, the other | 180.0° |

Four failures, four distinct readings, each named in T4's disconfirmation
column. The seed's "circular mean of the envelope-**peak** phase" would not
separate them as cleanly, and S2's lobing (§8.14) puts several peaks in a turn.
The same experiment answered a question the rewrite raised: **AM does not bias
the fit.** At AM depths 0, 0.3, 0.6 and 0.9 the fitted deviation was exact to
−0.00 % and the residual stayed at 0.16–0.47 % of it, so T3 needs no
"measure with the AM off" clause and did not get one.

#### A10.4 T1's arithmetic

The seed's crossing-level clause ("3–7 dB below its own passband level") had no
passband reference and, taken against a reference band close to the corner,
excluded the very alignment it was written for: a Butterworth pair measured
against a 1.6–3.2 kHz horn reference reads **2.9 dB**, outside a 3 dB floor by a
tenth of a decibel. Fixed two ways — the reference is now each band's
**asymptote** (horn 3.2–6.4 kHz, drum 100–200 Hz, where a Butterworth pair sits
0.006 dB and a Linkwitz–Riley pair 0.29 dB off flat) and the window is
**2.5–7 dB**, which both alignments clear with margin: computed against those
references at an 800 Hz corner, Butterworth crosses **3.01 dB** below and LR2
**5.73 dB** below. The slope windows check out unchanged: over 100–400 Hz a
Butterworth high-pass fits **11.95 dB/oct** and an LR2 **11.22**, and over
1.6–6.4 kHz the low-passes are the mirror — both inside 10–14 dB/oct. And the sweep is now **stepped**, with the depths at 0 and Brake
on, because a swept sine through a live Doppler line measures the modulation as
much as the filter.

#### A10.5 T2's resolution, and the ratio clause

Two defects, one arithmetic and one evidential.

**The measurement could not resolve its own threshold.** ±2.5 % of the drum's
chorale rate, 0.667 Hz, is ±0.0167 Hz; the seed's "20 s … (0.05 Hz bins)" gives
a bin three times wider than the tolerance, so a build 5 % slow would have
landed in the same bin as a correct one and passed. The row now asks for
**120 s at chorale** (0.0083 Hz bins, tolerance = 2 bins) and keeps 20 s at
tremolo, where 0.05 Hz bins sit against a ±0.14 Hz tolerance.

**The ratio clause was 2–1 against its own sources**, and A9.1 had left it for
Arthur. Rather than gate on a window no majority of the reached readings
supports, this pass narrowed the clause to what all three do support — Fisher
1.17/1.20, Azz 1.03/1.00, S2 "approximately the same", and **not one of them has
the drum faster** — so T2 now gates "horn ≥ drum at both speeds" and the four
rates at ±2.5 % of the defaults §6 declares. §8.13 records the change and leaves
Arthur the option of restoring 1.10–1.30.

#### A10.6 Structural checks, and the rest of the rewrites

- **Tier 1 is verbatim.** `sed -n '112,137p' Rotary.md` diffed against
  `sed -n '37,62p' TEMPLATE.md`: identical, no drift — checked before this
  pass and again after it, since §3's Tier 2 edits sit below the block.
- **Tier 3 carries both boards** — ESP32-P4 0.12, ESP32-S3 0.30 — a lean patch
  call, and the vision §9a latency paragraph with a stated algorithmic latency
  (29 frames, 0.60 ms at 48 kHz), the knob that trades it (macro 9, Horn
  Radius) and the statement that no option adds lookahead. Nothing to fix.
- **Ten Tier 2 rows, above the three a non-*design* grade needs**, and every one
  of them demonstrable: T8's first clause is the only one that cannot be
  exercised at the class gate as things stand, and it already carries the
  *unmeasured: waiting on the Phase 1 waveshaper* wording (§8.12).
- **T5** gained a definition of "envelope depth" — the peak-to-peak of the
  rotation-rate component fitted to the log envelope — because max-minus-min on
  a lobed, noisy envelope is the same trap A4 found in T3.
- **T6** kept its clauses and gained two markings: the **90 %** is ours (S8 times
  the whole change and defines no percentage) and S1 p.5 joins its sources for
  the braked down-ramp.
- **T7** was failing correct builds two ways. "Mic Angle 0° gives byte-identical
  channels" is only true if the *source's* channels are identical — a stereo
  source's own difference survives any mic angle — so the clause now says so.
  And cross-correlating envelopes returns a lag modulo the period and no sign,
  so the row now fits the rotation-rate component of each channel and reports a
  **signed phase**, which is also what makes "the same 90° at two rates 8×
  apart" a real test of a phase against a fixed delay.
- **T10's level clause failed any correct build that freezes off-axis.** "Within
  1 dB of its Brake-off mean" cannot hold when the Brake-off envelope itself
  spans several dB at the default Horn Depth and the rotor stops wherever it
  stops. The clause is now "inside the range its own Brake-off envelope
  spanned", which still fails a mute and still fails a hidden gain — the two
  things the trait exists to catch — and cannot fail a build for stopping in the
  wrong place. Its source cell also gained S6's "some later models had all three
  settings", a second reached source for the third position, though still not of
  the 122 itself.
- **Every probe tone now has a level** (−12 dBFS, in the preamble) — the seed
  stated one for T9 alone, and an AM-depth or THD figure without a level is not
  reproducible.


### A11. Palette verification pass, 2026-09-06

An independent pass over **§4 and §5 alone**: every line citation re-read in
the C and the bindings with `grep -n`, every behavioural claim re-probed
against `audiocomponents/.venv/bin/python` (CPython + audioif) and, where the
claim was about portability, against `cmods/bin/micropython` and
`cmods/bin/circuitpython`. Nothing below is inherited from A4 or A10; every
number was measured in this run. **Two node asks fell.**

#### A11.1 Line citations checked

| Cited as | Verdict |
|---|---|
| `audioif_feedback_delay.c:201-202` make dry 0 and wet 1 at `mix=2` | correct — `:201` `dry = 2−mix` clamped at 1, `:202` `wet = mix` clamped at 1 |
| `:209-210` rotate a magic-circle oscillator once per frame | correct, inside the per-frame loop opened at `:205` |
| `:212-214` add `wow_depth_frames × sine` to the read offset | correct (`:212-213` add, `:214` clamps) |
| `:226-228` interpolate | correct — `near_sample` then the linear blend to `far_frame` |
| Tier 3: the node clamps the offset to `[1, length−2]` (`:214`) | correct, and `:77-84` clamps `delay_ms` the same way, so `delay ≥ depth + 1` frame is right |
| R2: the offset is computed once per frame, outside the channel loop (`:212-214`) | correct — the channel loop opens at `:224` |
| R2: `:163-164` fixes sine 0, cosine 1 | correct as a statement about `state_init`; **the inference drawn from it is wrong** (A11.4) |
| R4: `c_away` from `damping_hz` (`:31-38`), `c_open = 1.0` passed unchanged by `:232-234` | correct — at `coef = 1` the one-pole's state takes the input exactly |
| `audioif_splitter.h:21` gives 4 taps | correct — `AUDIOIF_SPLITTER_MAX_TAPS 4u` |
| `audiofilters.Filter` RBJ biquad at `audioif_biquad.c:70`, `:127` | correct — `configure_w0` and `configure` |
| contract: pulling `output` "must not allocate, block, perform I/O", `audio-component-api.md:231-232` | correct |
| every option coerced with `float(value)`, "`audioecho.py:86`" | **wrong line and no path.** It is `audioif/src/cpython/audioecho.py:87`; the MicroPython binding does the same at `audioif/src/audioecho/FeedbackDelay.c:43` (`mp_obj_get_float`), which is the load-bearing one |
| R1: the table sizes, `modulation.py:185-186` | correct — `_CARRIER_FRAMES = 2048` (`:168`) gives one cycle at these rates: 7059 frames = 28 236 bytes stereo at 6.8 Hz, 60 000 frames = 240 000 bytes at 0.8 Hz |

#### A11.2 Behavioural claims re-probed (CPython + audioif)

- **Doppler depth.** Least-squares sinusoid fit of the instantaneous-frequency
  trace against `f_c · (depth_ms/1000) · 2π f_m`: **+0.001 %** at all four of
  (r_s 0.20 m, 6.6667 Hz, 1 kHz), (0.20, 0.80, 1 kHz), (0.10, 6.6667, 1 kHz)
  and (0.20, 6.6667, 2 kHz). Halving `r_s` halved the fitted deviation exactly
  (24.4247 → 12.2124 Hz), so T3's proportionality clause has no slack problem.
  A naive max−min read over-stated the fit by 9.4–48.9 % depending on rate,
  which is A4's finding reproduced.
- **Interpolation AM.** Envelope peak-to-peak with the modulation on:
  0.023 dB at 1 kHz, **0.083 dB at 2 kHz**, 0.695 dB at 6 kHz; with the
  modulation off, 0.0008 dB. The seed's "≤ 0.09 dB at 2 kHz" stands. *(The
  6 kHz figure is new and belongs to T5's ungated 6 kHz report, not to §4.)*
- **Block-rate purity.** Blackman–Harris, 3.5 s, worst line inside ±3 bins of
  a named offset: **−84.9 dB** re carrier at 48 kHz/256, −77.7 dB at
  48 kHz/128, −85.6 dB at 44.1 kHz/256 — all far under T9's −70 dB. (A10.1's
  −97.0 dB reads the exact bin; a ±3-bin window catches the FM sideband skirt.
  Either reading clears the threshold.)
- **Ramp safety.** `wow_hz` stepped once per block from 0.80 to 6.6667 Hz over
  2 s: largest `abs(x[n] − x[n−1])` during the ramp **2180** against **2183**
  at steady tremolo, envelope excursion 0.083 dB, no inst-frequency
  discontinuity above the steady-state one. Phase-continuous, as claimed.
- **Latency.** An impulse through `delay_ms=3.0` is the only non-zero output
  frame and it is frame **144** = 3.000 ms at 48 kHz.
- **L/R.** With an identical-channel source, largest |L − R| = **0.0** exactly.
- **Mono.** `channel_count=1` builds, renders one lane, and carries the full
  modulation (envelope 0.082 dB p-p, matching the stereo lane).

#### A11.3 The oscillator does not drift, and R1's stated reason was wrong

A10.1 recorded the realised wow rate as "6.6797 Hz for a requested 6.6667 —
+0.195 %", read from a parabolically interpolated envelope-spectrum peak, and
§5 R1 rejected `audiomath.Multiply` partly on that drift. A 120 s record and a
least-squares frequency scan give **6.666670 Hz for 6.66667 (0.0 ppm)** and
**0.799993 Hz for 0.800 (−9 ppm)**. That is what the arithmetic predicts: with
`wow_step = 2·sin(π f/fs)` (`:113-114`) the magic circle's eigenvalues put
`cos ω = 1 − k²/2 = cos(2π f/fs)`, so the realised frequency is the requested
one exactly, in real arithmetic and to float32 within a part per million.
A short-window fit reproduces A10.1's error; a long one does not.

Consequence, measured rather than argued: a `RawSample` table of `L = 7200`
frames (exactly `fs/L` = 6.666667 Hz) driving `audiomath.Multiply`, with the
delay at `wow_hz = fs/L`, held `φ_dev − φ_env` at **−179.93°** in the first
20 s and **−179.93°** in the last 20 s of a 120 s record — locked, not
drifting, and the constant is set by where the table starts, so any quadrature
including T4's +90° is a table-authoring choice. R1 stands anyway, on the two
things a fixed-period table cannot do: follow a rate through T6's ramp, and
survive a chorale↔tremolo swap without restarting at frame 0.

#### A11.4 Two nodes *can* start at different phases — R2 falls

`state_init` fixes `(sine, cosine) = (0, 1)` at construction (`:163-164`), but
`process_s16` advances the pair once per frame **rendered** (`:209-210`), so
pulling a node on a silent source before wiring it into the graph leaves it at
an arbitrary phase, and the delay line stays zero because the input was
silence.

Read directly: `set(wow_hz=0)` zeroes `wow_step` and never touches the state
(`:111-115`), so the oscillator freezes where it is and the read offset becomes
`delay + depth·sin(φ_frozen)` — which an impulse's landing frame reports to one
frame. At `delay_ms=5`, `wow_depth_ms=2`, 6.6667 Hz:

| pre-roll frames | impulse lands at | `delay + depth·sin(2π·rate·pre/fs)` |
|---|---|---|
| 0 | 240 | 240.0 |
| 1024 | 315 | 314.8 |
| 2048 | 334 | 333.8 |
| 3072 | 283 | 282.7 |
| 4096 | 200 | 199.7 |

**Identical on CPython, MicroPython and CircuitPython.** And the offset holds:
two nodes, one pre-rolled 2048 frames, rendered block-for-block for 30 s, gave
`φ_B − φ_A` = **+102.40°** in an early window and **+102.40°** in a late one
(2048 frames at 6.6667 Hz is 0.2844 of a turn = 102.4°, so the pre-roll landed
exactly where it was aimed). Granularity is one node block, 256 frames
(`audioif_feedback_delay.h:39`) = 12.8° at 6.67 Hz and 1.54° at 0.80 Hz.

The stereo-`Multiply`-table route was measured too: one table with a
quarter-period offset in its right channel gave `φ_L − φ_R` = **+90.01°**,
identical in the first and last 15 s of a 40 s record.

#### A11.5 Directivity's depth ordering composes — R4 falls

Two `Multiply` tables at different depths on two sub-bands, both at `fs/L`,
both started with the graph:

| sub-band probe | table depth | measured AM depth | phase of the rotation-rate component |
|---|---|---|---|
| 1.0 kHz | 0.25 | **2.49 dB** p-p | −119.99° early / +0.00° late |
| 1.6 kHz | 0.60 | **7.82 dB** p-p | −119.98° early / −0.01° late |

A 5.33 dB spread against T5(a)'s 0.5 dB, and the two sub-bands' components in
phase to **0.01°** in both windows of a 60 s record — the lock R4 was kept for,
without R4. Under R1 the same split is two `wow_am_depth` values and no table.

The `synthio.LFO`-driven `synthio.Biquad` the seed weighed as R4's palette
alternative was re-probed for completeness: it *is* accepted, and it *does*
advance on CPython (400 distinct `lfo.value` readings over 400 pulls, block
peaks moving with it), on CircuitPython identically. So §8.8's CPython defect
is confined to `audiomixer`'s block inputs — the Mixer voice level under an
LFO left `lfo.value` at **one** value over 400 pulls on CPython where
CircuitPython and MicroPython each gave **250**. That narrows §8.8's scope; it
does not change R1's verdict, since a block-rate sweep is still a second,
unlocked oscillator no Python can ramp.

#### A11.6 What was found and left for Arthur, not edited here

- **A10.1's oscillator figure (+0.195 %) is a measurement artefact** (A11.3).
  T2's "the node's oscillator lands within 0.2 % of a requested rate" in its
  confidence cell understates the node by three orders of magnitude; the window
  is still cleared, so no trait moves, but the sentence is wrong.
- **T3's residual threshold may not survive chorale.** The 10 % residual-RMS
  clause was measured at 2.4 % at tremolo on a 1 kHz carrier — and at **15.4 %**
  at 0.80 Hz on the same carrier, on the bare palette with no class in the way.
  A correct build could fail T3 at chorale for want of deviation to fit
  (2.93 Hz on 1 kHz). Either the clause takes a higher probe tone at chorale or
  the threshold is rate-dependent. §3's, not §5's, so it is recorded, not fixed.
- **§8.7 now has an answer**: two of the four options survive, so the
  `FeedbackDelay`-options form carries `wow_am_depth` and `wow_ramp_ms` only,
  and a separate `audioecho.Rotor` is harder to justify for two floats.


<!-- Phase 0 seed, rotary unit, 2026-09-06. Rewritten from a cut-off run's
draft: every source above was re-fetched in this run, every probe re-run, and
every source the draft named that could not be re-reached was struck
(Lambert's Music Solutions, JPF Amplification, Adam Monroe Music, the
theatreorgans mirror). Audited 2026-09-06 by an independent license and
citation pass: all thirteen sources re-fetched, eight corrections applied,
listed in A7. The HammondWiki OPL licence page, struck by the first run as
unreachable, WAS reached in the audit and is now cited. Then by an
independent TRAIT CRITIC pass the same day (A8): Tier 1 diffed verbatim
against TEMPLATE.md, Tier 3's two boards confirmed, all nine Tier 2 rows
rewritten in place and T10 added, with S2, S3, S6, S7, S13 and the PASP
restatement re-reached first-hand for the rewrites. Two items went to §8 for
Arthur: T10's acceptance (§8.11) and T8's gating dependency (§8.12). Then by a
SECOND independent licence-and-citation pass the same day (A9): all thirteen
rows re-fetched again from scratch, every licence call confirmed unchanged,
S14 added for the Bark conversion, six corrections applied — the largest being
S2's own "approximately the same rotational speed" sentence, which is a third
rotor-speed reading against T2's ratio clause and which A2 had wrongly struck.
T2's ratio clause now needs Arthur's call at the survey alongside §8.11.
Then by a SECOND independent TRAIT CRITIC pass, also 2026-09-06 (A10), which
re-fetched every source a Tier 2 row leans on (S1 pp.3/5, S2, S3, S4, S5, S6,
S7, S8, S9, S10, S13, S14 — not the GPL chain, which no row cites) and re-ran
the palette probes in its own run rather than inheriting A4's numbers. Ten rows
before, ten after; nine rewritten in place. It caught three measurements that
could not have passed a correct build — T9's "largest non-rotation-rate line"
(window leakage, −53 dB under Hann against a −70 dB threshold), T2's 20 s
chorale record (bins three times wider than the tolerance it gated) and T10's
"within 1 dB of the Brake-off mean" (impossible for a rotor that freezes
off-axis) — and settled T2's ratio clause by narrowing it to the ordering all
three reached readings support, recorded in §8.13 for Arthur to reverse if he
wants Fisher's window back. §8.14 records the horn lobing S2 describes and no
trait gates. Finally by an independent PALETTE VERIFICATION pass, also
2026-09-06 (A11), over §4 and §5 alone: every line citation re-read in
audioif's C and bindings with grep -n, every behavioural claim re-probed on
CPython and, where portability was the claim, on cmods/bin/micropython and
cmods/bin/circuitpython. One citation was wrong (audioecho.py:86 -> src/cpython
/audioecho.py:87, plus the MicroPython binding that actually matters). R1's
rejection of audiomath.Multiply rested on a drift that a 120 s record shows
does not exist — the node's oscillator is exact — so R1's reason was replaced
with the one that holds, that a fixed-period table cannot follow a changing
rate. R2 and R4 were REFUTED BY PALETTE: a node pulled on silence before it is
wired starts at any phase you like (measured identical on all three
interpreters), and a two-sub-band split reaches T5(a) with a 5.33 dB spread and
a 0.01 degree lock. Both refutations cost delay lines rather than traits, so
§8.9's S3 budget now decides them; §3's Tier 3 chain assumes all four asks land
and needs re-costing. A11.6 lists what the pass found outside §4 and §5 and
left for Arthur, including A10.1's +0.195 % oscillator figure and T3's residual
threshold at chorale. -->

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

**Class notes.** *Mono:* stereo-by-definition, so a mono source gets **one
listener** — full horn Doppler, horn AM, drum AM and ramps at the left
microphone's angle, no mic-pair lag. *Rate:* every gated Tier 2 trait holds
at 22.05 kHz — the highest gated probe tone is the 2 kHz of T2, T3, T4 and
T7 — while T5's ungated 6 kHz report is dropped at any rate below 16 kHz;
the block-rate figures T9 names are `fs ÷ block` and move with the rate; the
Crossover macro clamps below Nyquist. *Latency:* nonzero (Tier 3), and both
bands must carry the same nominal delay or T1's sum misaligns. *DC:*
measured this run — a `synthio.Biquad` LOW_PASS and HIGH_PASS at 800 Hz
Q 0.707 and LOW_PASS at 150 Hz all reach **exact zero** after a burst, so
audioif#23 does not bite this class; recorded so Gate 0 has three more
configurations on file.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| # | Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|---|
| S1 | Leslie 122 *Installation Instructions Manual*, 26 pp., at ManualsLib | the 800 Hz network and the band split (p.3); 40 W, 16 Ω driver, 15" woofer, the 41×29×20½" cabinet (p.4); the two-speed drives, the 3-step drive pulley and the console-connector TREMOLO control, whose CHORALE position brakes both rotors "to Chorale speed" (p.5) | none on the manual; ManualsLib's terms are personal-non-commercial, no redistribution — **unverified → copyleft**; read as a document | manualslib.com/manual/4079586/Leslie-122.html `?page=1,3,4,5,22` ; manualslib.com/terms.html | yes; p.22's schematic scan re-fetched and confirmed unusable (§8.1, A2) |
| S2 | Henricksen, "Unearthing the Mysteries of the Leslie Cabinet", *Recording Engineer/Producer*, Apr 1981, at dannychesnut.com | the 12 dB/oct 16 Ω crossover; drum AM only 200–800 Hz; the wooden drum, its scoop and the downward-firing bass driver; the stationary Jensen driver under the twin-bell bakelite horn; the drum's slower acceleration; mic distances; the 6550 amp's "warm rich distortion". **Also, and against T2:** the drum "ends up at approximately the same rotational speed as the treble unit" | **none on the page and none in the site footer** (homepage checked) — **unverified → copyleft**; read as a document | dannychesnut.com/Music/Leslie/LeslieMystery.html | yes |
| S3 | Smith, Serafin, Abel & Berners, "Doppler Simulation and the Leslie", DAFx-02, with its *PASP* restatement | eq. 15–20 (§4.1); the Model 600 horn, 44W identical; the 15°-step Golay measurement (§4.2); HF falling faster with angle (§4.3.2 — **only below ~12 Barks ≈ 1.7 kHz**); stereo as two listeners (§3.6); drum AM (§5) | authors' copyright on the `/~jos/doppler/` index, no reuse grant — **unverified → copyleft**; read **as a paper**, math re-derived, nothing copied | ccrma.stanford.edu/~jos/doppler/dafx02.pdf and /~jos/doppler/ ; dsprelated.com/freebooks/pasp/Leslie.html (same result, *PASP* eq. 6.13) | yes |
| S4 | Pekonen, Pihlajamäki & Välimäki, "Computationally Efficient Hammond Organ Synthesis", DAFx-11 | directive horns; the wooden drum's directional pattern and AM; two oscillators because the bass unit accelerates slower — its demo constants (2 / 6 Hz) are **choices, not measurements** | none in the paper, none on dafx.de's archive index — **unverified → copyleft**; read as a paper | dafx.de/paper-archive/2011/Papers/49_e.pdf | yes |
| S5 | Herrera, Hanson & Abel, "Discrete Time Emulation of the Leslie Speaker", AES 127 (2009) | horn and baffle modelled individually; "different shapes for acceleration and deceleration" | "site copyright © 2009-2023 Stanford University", no licence — **unverified → copyleft**; the paper is in the AES e-library | ccrma.stanford.edu/papers/discrete-time-emulation-of-leslie-speaker | **abstract only**, re-checked |
| S6 | Wikipedia, "Leslie speaker" | 50/400 rpm horn vs 40/340 woofer; the 800 Hz crossover; a blocked horn; the 147 "otherwise identical" | CC BY-SA 4.0 (footer) | en.wikipedia.org/wiki/Leslie_speaker | yes |
| S7 | HammondWiki, "Leslie Rotation Speed" | J. Fisher on a 147, middle pulley: upper 400/48 rpm, lower 342/40; chorale ≈ 0.8 Hz, tremolo 5.7–6.8 Hz (D. Dillon). **The same page carries a second, disagreeing reading** — S. Azz: 409 / 396 rpm, and 48–49 rpm "for both upper and lower rotors" (T2) | content © 2000–2002 Dairiki *et al.*, under the **OpenContent License v1.0** — `opl.html` **read this run**: share-alike copyleft. Facts and short quotations only | dairiki.org/HammondWiki/LeslieRotationSpeed ; dairiki.org/HammondWiki/opl.html | yes (both) |
| S8 | Benton Electronics, "Servicing the Leslie Motors" | the O-ring engagement; 5–8 s slow→fast **and** fast→slow, stated of **the lower (drum) belt** | "Copyright © 2026 Benton Electronics" plus the same educational-purposes disclaimer S9 carries — **unverified → copyleft**; read as a document | bentonelectronics.com/servicing-the-leslie-motors/ | yes |
| S9 | Benton Electronics, "Servicing the Leslie 122 Amplifier" | 6550A output pair, the 12AU7a "balanced amplifier", the OC3 regulator, "only 40 watts"; DC on both input pins sensed by a switching tube that works the speed relay — **it does not say what the relay switches** | copyright notice plus an educational-purposes disclaimer — **unverified → copyleft**; read as a document, its reader comments not cited | bentonelectronics.com/servicing-the-leslie-122-amplifier/ | yes |
| S10 | Penniman, "App Note 9: A Rotary Speaker Modeling Plug-In" (2014), at willpirkle.com | two virtual mics at −135°/−45°; Linkwitz-Riley at 800 Hz; drum AM sinusoidal in dB, below 200 Hz unaffected; separate accel/decel; the 2 kHz claim (§8.4) | "Copyright © 2014 Ross Penniman" in the running footer, no licence — **unverified → copyleft**; its C++ listing **not** read, prose only | willpirkle.com/Downloads/Rotary Speaker Sim App Note.pdf | yes |
| S11 | x42 Whirl Speaker (setBfree's `b_whirl`) | what the state of the art models: Model 600 IRs, dummy bell, drum AM, six reflections, per-rotor accel/decel, 180° mic'ing | **GPL** — the page's only licence signal is the GPL badge on its "Source Code" link, which points at S12; chain read this run. Copyleft: never read for code, a candidate proxy oracle whose *output* Station C may measure | x42-plugins.com/x42/x42-whirl | yes |
| S12 | setBfree | the emulator S11 comes from | **GPL-2.0** — the repo's `COPYING` is the GNU GPL v2, read this run (GitHub's licence field agrees). Never read for code | github.com/pantherb/setBfree (`COPYING`) | yes (both) |
| S13 | Strymon, "History of Rotary Speakers" | the switch's three positions — of the remote switch "found on organs like the Hammond B3", not of the 122 specifically; "several seconds" for a change | "© 2026 Strymon, a division of Damage Control Engineering", no licence — **unverified → copyleft**; read as a document | strymon.net/history-of-rotary-speakers/ | yes |
| S14 | Wikipedia, "Bark scale" | the critical-band table: band 12 has centre 1600 Hz and cut-off **1720 Hz**, which is the conversion §1 and T5 use for S3's "12 Barks" | CC BY-SA 4.0 (footer) | en.wikipedia.org/wiki/Bark_scale | yes (added by the second audit pass, A9.4) |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Conf. | Disconfirmed by | Measurement (kit) |
|---|---|---|---|---|---|
| T1 | **Second-order 800 Hz split.** With both Depth macros at 0, Balance centred and Brake on — no modulation in the path — the two bands' magnitudes are equal within 0.5 dB at a crossing frequency in **700–900 Hz**, and each band is **2.5–7 dB** *(ours; both classic second-order alignments, Butterworth's −3 dB and Linkwitz–Riley's −6 dB, fall inside it with margin for the reference — the alignment itself is §4's choice and is unsourced)* below its own **asymptotic passband level** (horn: mean over 3.2–6.4 kHz; drum: mean over 100–200 Hz); the **horn** band's slope fitted over **100–400 Hz** and the **drum** band's over **1.6–6.4 kHz** — two octaves into each band's own *stop*band — each read **10–14 dB/oct** (both alignments compute to 11.2–12.0 dB/oct there, A10.4). Separately, at the shipped depths, each band carries only its own rotor's rate: the other rotor's line and its harmonics sit **≥ 20 dB** *(ours)* below its own. | S1 p.3, S2, S6 (800 Hz); S2 (12 dB/oct, twice) | high on the corner and the order | an equal-magnitude crossing outside 700–900 Hz; a crossing level outside 2.5–7 dB below that band's asymptote; either fitted slope outside 10–14 dB/oct (a 6 or a 24 dB/oct build); either band showing the other rotor's rate within 20 dB of its own | **stepped** sine (1/12 octave, 50 Hz–10 kHz, 0.25 s per tone, steady-state RMS), each band solo, at 48 and 44.1 kHz, depths 0 and Brake on — a *swept* sine is smeared by the Doppler line: the equal-magnitude frequency, each band's level there against its own asymptote, least-squares slope over the two octave pairs named. Then, depths at their defaults and Brake off, T2's per-band envelope spectrum reporting **both** rotor lines |
| T2 | **Two rotors, two speeds each, horn never slower.** At the shipped defaults each of the four rates is within **±2.5 %** *(ours)* of horn **6.67 / 0.80 Hz** and drum **5.70 / 0.667 Hz** (Fisher's 400/48 and 342/40 rpm), and at both speeds the horn's rate is **≥** the drum's. **How much faster is not sourceable, and this row claims nothing about it:** the three reached readings give 1.17/1.20 (Fisher), 1.03/1.00 (Azz) and "approximately the same rotational speed as the treble unit" (S2), so "horn ≥ drum" is the only ordering clause all three support (A10.5). | S7 (Fisher **and** Azz), S6, S2 | high on the four rates — they are the class's own declared defaults, taken from Fisher, and the node's oscillator lands within 0.2 % of a requested rate (A10.1); high on the ordering — **no reached reading has the drum faster**; the *size* of the gap stays unsettled, 1.17–1.25 (Fisher, S6) against ≈1.00–1.03 (Azz, S2) | any of the four rates more than 2.5 % from its default; a drum rate above the horn's at either speed. Equal rates **pass**, and would agree with Azz and S2 | a steady 2 kHz tone (horn solo) and a 300 Hz tone (drum solo) at each patch; the parabolically interpolated peak of the envelope spectrum is that band's rate. **The record must resolve the tolerance:** 20 s at tremolo (0.05 Hz bins against ±0.14 Hz) but **120 s at chorale** (0.0083 Hz bins against ±0.017 Hz on the drum's 0.667 Hz) — a 20 s chorale record cannot resolve ±2.5 % and would pass anything. Harmonics of the rate are expected — directivity is not sinusoidal — but any **other** line sits ≥ 20 dB down |
| T3 | **Horn Doppler is a sinusoid of depth `r_s·ω_m/c`.** The least-squares sinusoid fit at the rotation rate leaves a residual RMS **≤ 10 %** *(ours)* of the fitted peak deviation; the deviation's 2nd harmonic is **≥ 20 dB** *(ours)* below its fundamental; the tremolo ÷ chorale deviation ratio equals the measured rate ratio within **5 %**; and halving macro 9 (Horn Radius) halves the fitted deviation within **5 %**. The **absolute** depth is unsourced (§8.2), so no cents window is claimed. | S3 eq. 15–20 | high on shape, on the rate ratio and on proportionality to the radius — all three are in the source's own equations | no pitch modulation; a triangular or square deviation trace (residual over 10 %, or a 2nd harmonic within 20 dB); a deviation ratio more than 5 % off the rate ratio; a deviation that does not track macro 9 proportionally | instantaneous frequency from the analytic signal of a 2 kHz tone, horn solo, then a least-squares sinusoid fit at that band's extracted rate — the fit, never a peak read, and the fit is unbiased by the horn's own AM (A10.1, A10.3, which carry the palette's measured margins against all three thresholds). Report fitted peak deviation, residual RMS and 2nd-harmonic ratio at both speeds and at macro 9 = default and half default |
| T4 | **AM and FM are locked by geometry and do not walk.** Fit `M·cos(ω_m t + φ)` at the extracted rotation rate to the horn band's envelope and, separately, to its instantaneous-frequency deviation: the deviation **leads** the envelope by **+90° ± 15°** *(±15° is ours; the +90° is the source's geometry)* at both speeds, and still within ±15° after a chorale→tremolo→chorale cycle plus 60 s. That is "the amplitude maximum sits on the **falling** zero-crossing of the pitch deviation": eq. (20)'s deviation is `−(r_s·ω_m/c)·sin(ω_m t)` while §4.3.2 puts the amplitude maximum where the horn faces the listener, `ω_m t = 0` (A8.1, re-derived in A10.3). | S3 eq. 15–20 with §4.3.2; S2 | high — the sign follows from the source's own equations | **−90°**: an inverted directivity, loudest as the horn points away. **0° or 180°**: the amplitude peak at a pitch extreme, a quarter turn out. Any drift beyond ±15° across the ramps or over a minute | a 2 kHz tone, horn solo, ≥ 20 rotations: Hilbert envelope and instantaneous frequency, each least-squares-fitted at the band's extracted rate (T2), the phase difference reported **with its sign** before and after the ramp cycle. Fitting the two *fundamentals* is what makes this measurable — the four cases above come back as +90 / −90 / 0 / 180° exactly (A10.3), where an envelope-**peak** read is scattered by the horn's own lobing (§8.14) |
| T5 | **AM depth grows with frequency, and the drum barely touches the bottom.** *(a)* Horn-band depth is non-decreasing across **1.0, 1.3 and 1.6 kHz** and depth(1.6 kHz) − depth(1.0 kHz) **≥ 0.5 dB** *(ours; the source gives the direction, not a size)* — all three points above the 800 Hz split and below 12 Barks — 1720 Hz, the 12th critical band's cut-off (S14) — which is the range S3's sentence covers. *(b)* Drum-band depth at 300 Hz **≥ 3 dB** while at 150 Hz **≤ 1 dB** *(ours)*. | (a) S3 §4.3.2, with S14 for the Bark→Hz conversion; (b) S2 ("only for the upper two octaves or so of the bass section (200 to 800 Hz)"; "Frequencies lower than 200 Hz are probably uneffected"), S10 | (a) medium; (b) medium | (a) equal depth at 1.0 and 1.6 kHz, or depth falling with frequency — a gain tremolo wearing a crossover; (b) a modulated 150 Hz, or an unmodulated 300 Hz | steady tones at 150, 300, 1000, 1300 and 1600 Hz, each band solo, at tremolo, where **depth is the peak-to-peak of the rotation-rate component fitted to the log envelope** (T4's fit, read in dB) — never max-minus-min, which reads the noise floor and the lobing. **Recorded but not gated:** the depth at 6 kHz — above 12 Barks, where no reached source describes the angle dependence (A7.8, A8.2) |
| T6 | **The speed change is a ramp, and the drum lags.** Each rate moves continuously and monotonically to target; the drum reaches **90 %** *(the percentage is ours — S8 times "slow to fast and fast to slow" and defines none)* of the step in **5–8 s** both ways (S8, of the lower belt) and the horn in **≤ 0.5 ×** the drum's *measured* time on that same switch (**ours** — S2 gives only "a much longer time period" for the drum, and no reached source times the horn); T4 holds throughout; and nothing clicks — the largest `abs(x[n] − x[n−1])` during the ramp does not exceed the same statistic at steady tremolo on the same tone. | S8; S2; S4; S13; S1 p.5 (CHORALE brakes both rotors "to Chorale speed", so the down-ramp is driven, not a coast); S5 (§8.3) | medium | an instantaneous step in either rate; a drum 90 % time outside 5–8 s; a horn slower than half the drum; a non-monotone rate trace; a first difference above the steady-state one, which is a click at the switch | LFO extraction on a 1 s sliding window across a switch in each direction, both bands solo → rate-vs-time trace, 90 % times, monotonicity; plus the largest `abs(x[n] − x[n−1])` over the ramp against 20 s of steady tremolo on the same tone |
| T7 | **Stereo is two listeners, not a widener.** With a source whose two channels are identical, Mic Angle 0° gives **byte-identical** output channels. At 90°, the L and R envelopes' rotation-rate components differ in phase by the macro within **±10°** *(ours)* at chorale **and** at tremolo, with the **same channel leading** at both speeds — the angle is recovered from a phase, so the same 90° must come back at two rates 8× apart. | S3 §3.6; S10 (two mics at −135° and −45°, i.e. 90° apart); S2 (a mic pair on opposite corners of the horn compartment) | medium | any inter-channel difference at 0° with an identical-channel source; no phase difference at 90°; a phase difference that **scales with the rate** — a lag equal in *seconds* at both speeds, which is a fixed inter-channel delay, the widener this trait denies; a recovered angle more than 10° from the macro; the leading channel swapping between speeds | horn band solo on a 2 kHz tone: fit the rotation-rate component of each channel's Hilbert envelope over ≥ 20 rotations at each speed (T4's fit) and report φ_L − φ_R **with its sign**. Cross-correlating the raw envelopes is not enough — it returns a lag modulo the period and no sign |
| T8 | **The drive is before the split.** At Drive 0.7 a 200 Hz tone's harmonics above 800 Hz carry the **horn's** rate while its fundamental carries the **drum's**; at Drive 0, harmonics 2–10 of the fundamental sum to **≤ −80 dB** *(ours)* re fundamental, counting only lines further than ±5 × the rotation rate from each harmonic so the rotors' own sidebands are not scored as distortion. | S2 (the signal "is sent into the Leslie amplifier driving a 12 dB per octave, 16-ohm crossover", and that amp's "warm rich distortion"); S9 ("these amps are only 40 watts and can easily over driven"); S1 p.3 | high on the topology — two reached sources put the one amplifier ahead of the one network; the curve is the Drive family's (§8.5) | harmonics carrying the drum's rate, or the fundamental carrying the horn's — a drive after the split, or one per band; any harmonic distortion above −80 dB at Drive 0 | per-harmonic envelope-rate extraction on a driven 200 Hz tone, both bands live; the Drive-0 figure on the same tone under a Blackman–Harris window. The palette's own Drive-0 floor is 10 dB below the threshold (A10.1), so this is not a floor test in disguise. **Gated only once the Drive family's waveshaper node lands (§8.5):** until then macro 13 is a wire, the first clause is recorded *unmeasured: waiting on the Phase 1 waveshaper*, and the Drive-0 clause is measured on its own |
| T9 | **Nothing steps.** With a steady 1 kHz carrier, every line at a block-rate offset — ±k × (fs ÷ block), k = 1…4: 187.5 Hz at 48 kHz and 256 frames, 375 Hz at 128, 172.3 Hz at 44.1 kHz and 256 — is **≤ −70 dB** re carrier, at both speeds. | mechanism (S2, S3), against the block-rate palette the old class used | high | any line at a **named block-rate offset** above −70 dB re carrier, at either speed or either rate | 4 s of the horn band, the first 0.5 s discarded, an integer number of rotations, **Blackman–Harris window**, read at the named offsets. **Not** "the largest line that is not a rotation-rate multiple": the carrier sits inside ten strong FM sidebands 6.7 Hz apart, so that reading is set by the analysis window and not by the class — the same probe returns −53 dB under a Hann window and −73 dB under Blackman–Harris, both leakage (A10.1). At the named offsets the palette measured **−97.0 dB** re carrier this run, the floor |
| T10 | **Stop is the third position, and it stops without stopping the sound.** With Brake on both rates ramp to zero on T6's times — never a step, since "there was also a bit of lag when the brake was applied (Stop) or let go" (S13) — and after 15 s the output is time-invariant: envelope depth **≤ 0.2 dB** peak-to-peak and instantaneous-frequency deviation **≤ 0.5 Hz** *(ours)* on a 2 kHz and a 300 Hz tone, while each band's frozen level lies **inside the range its own Brake-off envelope spanned** on the same tone (min to max) — a stopped Leslie is a fixed horn and drum, neither a mute nor a gain change. | S13 (the switch's three positions, and the brake's lag); S6 ("Some early models were limited to 'off' and 'tremolo', and some later models had all three settings"); S8 (the same belts, so the same ramp) | medium — S13 is a manufacturer history page and S6's sentence is about Leslie models in general; **the 122's own manual lists only CHORALE and TREMOLO** on the pages reached (S1 p.5, A9.2), which is why §8.11 puts this row to Arthur. That stopped rotors keep passing signal is mechanism, not a quotation | modulation still present 15 s after the brake; a step to zero rather than a ramp; the output muting, or a band's frozen level outside the range its own modulation spanned; a click at the switch (T6's first-difference test) | the T2 envelope and instantaneous-frequency probes with Brake toggled at t = 5 s over a 30 s run, both bands solo, at each speed, each band's Brake-off envelope min and max recorded on the same tone first |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Audited 2026-09-06** by an independent license-and-citation pass: all
thirteen rows re-fetched, every quotation in §1, §3 and A5 checked against
the document's own text, eight corrections applied (A7). **Audited a second
time the same day** by a further independent pass, which re-fetched every one
of those rows again from scratch (S1 pp. 1/3/4/5/22 and ManualsLib's terms,
S2 and dannychesnut.com's homepage, S3's PDF + index + *PASP* page, S4's PDF
and dafx.de's paper archive, S5, S6 as wikitext and as rendered page, S7 and
`opl.html`, S8, S9, S10's PDF, S11 and its GPL badge's href, S12's `COPYING`
and GitHub's licence field, S13) and applied six further corrections (A9),
including one contradiction inside a source already cited. Row S14 was added
by that pass. Nothing in §1 or §3 now rests on a fact without a row above.

*(from §3)*

Rates in hertz (rpm/60); "horn band" / "drum band" mean the output with the
other band muted. No characters: one standout, one trait set. Every probe runs
at patch 0 (chorale) and patch 1 (tremolo) unless a row says otherwise, and
every probe tone is at **−12 dBFS**. A threshold marked *(ours)* is a design
tolerance this dossier chose, not a figure any source states; what is sourced
in that clause is its direction or its centre, and the row says which. Ten
traits; the first trait critic's pass is A8, and the second — which re-reached
every source it leans on and re-ran the palette probes rather than inheriting
their numbers — is **A10**, which also holds the arithmetic behind the windows
below.

*(from §3)*

Budget as a fraction of one stereo 256-frame block's deadline: **ESP32-P4
0.12, ESP32-S3 0.30.** Lean patch expected: **yes** — on the S3 the drum
drops its Doppler line (it is an AM device, S2) and its directivity sweep.
The chain is a `Splitter` copy, two biquads, two `FeedbackDelay` lines with
§5's options (~8 extra multiplies per stereo frame) and a `Mixer` sum.

*(from §3)*

**Latency is not zero and cannot be.** A Doppler read that both advances and
retards needs the line's nominal delay to exceed the modulation depth, and
the node clamps the offset to `[1, length−2]`
(`audioif_feedback_delay.c:214`), so `delay ≥ depth + 1` frame. The depth is
not free either: it is `r_s/c`, the extra distance the sound travels when
the horn points away — so it is **independent of rotation rate**, and it is
the horn's own propagation swing, not lookahead. The class's algorithmic
latency is `r_s/c + 1` frame: at a provisional `r_s = 0.20 m`, c = 343 m/s,
0.583 ms + 1 frame = **29 frames, 0.60 ms at 48 kHz**, reported live in
`latency_samples` and in the docstring in ms. Both bands share that nominal
delay, so it is that number, not twice it. **The knob that trades it is
macro 9, Horn Radius** — smaller radius, less Doppler and proportionally
less latency, down to 2 frames at 0.01 m. **No option adds lookahead:** none
exists and none defaults on; the two that would (a convolved horn response
at the convolver's 256-frame partition; a cabinet-reflection reverb) are out
of scope in §8.6 and would be named in `latency_samples` if they landed. At
0.6 ms the class spends 6 % of the program's 10 ms round-trip target (D11);
the rest is the platform's.

*(from §4)*

```
source → [drive: the Drive family's waveshaper node, Phase 1; a wire until then]
       → Splitter(taps=2)                    # audioif_splitter.h:21 gives 4
            tap 0 → Filter(HP @ f_x) → FeedbackDelay(horn) → Mixer voice 0
            tap 1 → Filter(LP @ f_x) → FeedbackDelay(drum) → Mixer voice 1
       → Mixer → output
```

*(from §4)*

One RBJ biquad per band from `audiofilters.Filter` (`audioif_biquad.c:70`,
`:127`), second order to match the 122's one-coil one-capacitor legs (T1);
the horn's line is `FeedbackDelay(max_delay_ms ≈ 4, delay_ms = depth + 1
frame, feedback=0, mix=2, wow_hz = rate, wow_depth_ms = 1000·r_s/c)`, the
drum's the same nominal delay at small or zero depth. Python turns rpm into
hertz and calls `set(wow_hz=…)` on a Speed or Brake move — the *target*
only. **The ramp must live in the node** (§5 R3): the contract gives an
effect no per-block hook (pulling `output` "must not allocate, block,
perform I/O", `audio-component-api.md:231-232`), the class is not in the
pull path at all, and every option is coerced to a plain float on both
bindings — `audioif/src/cpython/audioecho.py:87` and
`audioif/src/audioecho/FeedbackDelay.c:43` — so no `synthio` block can drive
one. (The limit is this node's option *type*, not block inputs in general: a
`synthio.LFO` on a `synthio.Biquad` frequency does advance on CPython, A11.)
Of the four things this seed asked a node for, the verification pass found
**one** that cannot be composed from what exists: per-sample AM whose rate
*follows a changing rotor rate*. Per-sample AM at a fixed rate, the mic pair's
per-lane phase and directivity's frequency-dependent depth are all reachable on
today's palette — §5 records the routes and the measurements. **Mono**
(`channel_count=1`): the node renders one lane (probed) and the class builds
*one* listener at the left mic's angle, so a mono source gets the full
modulation and no mic-pair lag; Tier 1 measures that, not silence and not a
wire. Python computes coefficients, rates, depth from radius, per-channel
phase, ramp times and level trims at construction or on a macro move, never
per block; C runs two biquads, two interpolated reads, two oscillators and
(with §5) two gains and two one-pole sweeps per sample.

*(from §5)*

**R1 — `wow_am_depth` (0..1): AM from the delay's own oscillator. STANDS.**
*Unblocks* **T4**'s post-cycle clause and **T6**. Wet gain
`1 − depth·(1+s)/2` reuses the sine already at `:209`, so T4's quadrature is
structural, not tuned. *Palette instead, and what each route actually reaches:*

*(from §5)*

- A Mixer voice level under a `synthio.LFO` is block-rate by construction (T9)
  and **on CPython never advances at all** — re-probed on three interpreters
  this run: 400 pulls left `lfo.value` at one single value, where CircuitPython
  and MicroPython each gave 250 distinct ones (A11). An audioif bug in
  `src/cpython/audiomixer.py` (§8.8), not a route.

*(from §5)*

- `audiomath.Multiply` with a table reaches per-sample AM, and reaches it
  **better than this seed claimed**. *The drift the seed rejected it for does
  not exist.* The node's magic-circle oscillator runs at the **requested** rate
  — measured over a 120 s record, 0.0 ppm at 6.66667 Hz and −9 ppm at 0.8 Hz
  — so a table of `L` whole frames driven at `wow_hz = fs/L` is exactly locked
  to it: `φ_dev − φ_env` came back identical to **0.01°** between the first and
  last 20 s of a 120 s run (A11). The clause "its whole-frame period drifts
  against the delay's float-stepped oscillator" is **struck**; it rested on
  A10.1's +0.195 % oscillator reading, which a longer record does not
  reproduce (A11.3 — a correction A10 should carry).

*(from §5)*

- **What a table cannot do is change rate.** It is one fixed period, so chorale
  and tremolo need two of them and a swap restarts the modulator at frame 0
  while the delay's oscillator runs on — the quadrature after a
  chorale→tremolo→chorale cycle is then arbitrary, which is precisely what T4
  gates. And through T6's 5–8 s ramp the rotor's rate sweeps continuously while
  a table cannot follow at all, so T6's "T4 holds throughout" has no build on
  this route. Rebuilding the table inside the pull path is barred by the
  contract and is not small either: 28 kB at 6.8 Hz, 240 kB at 0.8 Hz
  (`lib/audioeffects/modulation.py:185-186`, verified).

*(from §5)*

*Refutation record:* "use Multiply, accept the drift" — the drift premise was
wrong and that objection is withdrawn; the ask survives on the **rate change**,
which is a different and a stronger reason. Fixing the CPython Mixer is a real
bug (§8.8), not a route to per-sample AM. **T9 leaves R1's unblock list:**
`Multiply` is per-sample and clears T9 unaided, so T9 rules out only the Mixer
alternative, never the ask's necessity.

*(from §5)*

**R2 — `wow_phase_deg`: a per-lane phase offset. REFUTED BY PALETTE.**
Half the mechanism claim holds: the read offset *is* computed **once per frame,
outside the channel loop** (`:212-214`), so one node's two lanes get identical
modulation — re-measured, largest |L − R| exactly **0.0**. The conclusion drawn
from `:163-164` does not. Those lines fix the oscillator at *construction*;
`:209-210` then advance it one step per frame **rendered**, so a node pulled
before it is wired into the graph sits at whatever phase you left it at, and
two nodes stepping the same `wow_step` hold that offset indefinitely.

*(from §5)*

REFUTED BY PALETTE: build one mono `FeedbackDelay` per mic lane and pre-roll
the second at construction on a silent source. Measured this run — a
2048-frame pre-roll at 6.6667 Hz held `φ_B − φ_A` at **+102.40°** in both an
early and a late window of a 30 s record, unchanged to 0.01°; and a
frozen-oscillator read (`set(wow_hz=0)`, which stops the step without touching
the phase) put an impulse's landing frame within one frame of
`delay + depth·sin(2π·rate·pre/fs)` at five pre-roll lengths, **identical on
CPython, MicroPython and CircuitPython** (A11). Pre-roll granularity is one
node block, 256 frames (`audioif_feedback_delay.h:39`) — 12.8° at 6.67 Hz,
1.54° at 0.80 Hz, both inside T7's ±10°. A second, independent route reaches
T7 as well: a **stereo** `Multiply` table carries a different envelope in each
channel, measured at `φ_L − φ_R` = **+90.01°**, identical early and late over a
40 s record.

*(from §5)*

What R2 would still buy is **cost, not a trait**: the pre-roll route needs one
mono node per mic lane where R2 needs one stereo node, so refusing it roughly
doubles the horn's interpolated reads. Under vision §6's rule — ask for a node
only when a fixed trait is shown unreachable — that is a Phase 1 budget call
(§8.9), not a node ask.

*(from §5)*

**R3 — `wow_ramp_ms`: `set(wow_hz=…)` becomes a target the node slews to.
STANDS.** *Unblocks* **T6**; no per-sample cost. *Palette instead:* an
instantaneous jump in rate. §4's two reasons the class cannot slew it from
Python were both re-verified: the contract bars work in the pull path
(`audio-component-api.md:231-232`) and the class is not in that path, and the
option is a plain float on both bindings
(`audioif/src/cpython/audioecho.py:87`,
`audioif/src/audioecho/FeedbackDelay.c:43`), never a block input. Nothing
outside the pull path can move a float 187 times a second, and no palette node
schedules one for this option. The probe shows the slew is safe: stepping
`wow_hz` every block from 0.80 to 6.6667 Hz over 2 s was phase-continuous, and
the largest `abs(x[n] − x[n−1])` over the ramp (2180) sat **below** the same
statistic at steady tremolo (2183) — T6's own no-click test, passed by the
step route, so what the slew adds is the *rate trace*, not click-freedom.
*Refutation:* a `synthio` one-shot driving the rate was rejected because the
option is a float, and making it a block input is a wider change than a slew.
**No palette route found.**

*(from §5)*

**R4 — `wow_damping_depth` (0..1): the in-loop one-pole's coefficient swept
per sample by the same oscillator. REFUTED BY PALETTE.** The arithmetic is
sound — `coef = c_open + (c_away − c_open)·(1+s)/2`, `c_away` from `damping_hz`
(`:31-38`) and `c_open = 1.0`, which the one-pole at `:232-234` passes
unchanged, all verified in the C. The trait it names, **T5(a)**, does not need
it.

*(from §5)*

REFUTED BY PALETTE: T5(a) asks only that horn-band AM depth be non-decreasing
across 1.0 / 1.3 / 1.6 kHz with at least 0.5 dB between the ends. Split the
horn band in two at a crossover between 1.0 and 1.3 kHz — this class already
builds a crossover for T1 — and give each sub-band its own AM depth. Measured
this run with `Multiply` tables: **2.49 dB** peak-to-peak at 1.0 kHz against
**7.82 dB** at 1.6 kHz, a 5.3 dB spread against a 0.5 dB threshold, and the two
sub-bands' rotation-rate components in phase to **0.01°** — so T4's lock stays
structural on this route, which is the one thing R4 was kept for. If R1 lands,
the same split is two `wow_am_depth` values on two lines and needs no table.
The block-rate `Filter` route the seed weighed is worse than either and is not
why R4 falls: re-probed, a `synthio.LFO` *does* drive a `synthio.Biquad`
frequency and *does* advance on CPython (400 distinct values, A11) — the
`audiomixer` defect is not general — but it is still a second, unlocked
oscillator that Python cannot ramp, the same wall R3 names.

*(from §5)*

R1 and R3 together cost ~4 multiplies per stereo frame and three floats of
state. **§3's Tier 3 chain assumes all four asks land and must be re-costed
against whichever survive Phase 1:** refusing R2 and R4 buys their traits with
extra `FeedbackDelay` lines — up to six mono lines where the seed budgeted two
stereo ones — and delay lines are the S3's scarce resource, so §8.9's budget
question now decides both.

*(from §7)*

- `:155` with `:135-136` — the Doppler is a granular `audiodelays.PitchShift`
  at a fixed 0.25 semitones whatever the rate. A horn's deviation scales with
  rate (T3), and a rotating horn is a delay line, not a grain cloud.

*(from §7)*

- `:156` with `:101-105` and `:86` — the tremolo is a Mixer voice level under
  a block-rate LFO (T9), and on CPython that LFO never advances (§5 R1): the
  class ships with no tremolo at all on that target.

*(from §7)*

- `:158-159` — one panning LFO pans the **whole** signal, drum included; a
  cabinet does not pan its bass (T5, T7). And `:157`, `:160` end the chain in
  a Mixer, which on CircuitPython silences anything chained after it
  (`upstream-diff.md:887`).

*(from §7)*

- `:141-160` — no crossover of any kind, so one modulation across the whole
  band (T1); and `MACRO_LABELS = ()` with one default patch (`:149-151`), so
  nothing a host can turn.

*(from §7)*

- `:141-160` — no `LATENCY_SAMPLES` override, so `_core.py:140`'s 0 is
  reported while `:136` carries a 1024-byte PitchShift window — 256 stereo
  frames, 5.3 ms at 48 kHz. The reported latency is false (Tier 1).
