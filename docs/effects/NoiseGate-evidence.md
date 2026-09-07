# Evidence Pack — `NoiseGate` (Drawmer DS201)

Written at Station C of the Phase 2 rebuild, from runs made this session.
The dossier it is read against is [`NoiseGate.md`](NoiseGate.md), whose
Tier 2 trait table was frozen before a line of the class was written.

**Three rules this file is written under.** Numbers come from runs, and every
figure names the command, the interpreter and the rate. A measurement with no
planted fault beside it is not cited. What is not done is §11, its own
section, and it is not empty.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `NoiseGate` |
| Dossier | [`NoiseGate.md`](NoiseGate.md), traits frozen 2026-09-07 at `9fcad65` |
| Module | `lib/audioeffects/rebuilt/noisegate.py` |
| Base | `_component.Component` |
| Family / phase | Dynamics, roadmap Phase 2 |
| Standout | Drawmer DS201 dual noise gate |
| Grade | literature |
| Portability tier | **audioif** — `REQUIRES = ("audiodynamics", "audioroute", "audiomath")` |
| Landed in commit | `102ff44` (class, tests, CHANGELOG, catalogue row); this file in the Station C commit named at the end of §9 |
| audioif pin | `AUDIOIF_PIN` = `2f6cbc3791efd38dfbf0fb263052400a69b976ed` |
| Interpreters | `audiocomponents/.venv/bin/python` — Python 3.12.3; `cmods/bin/micropython` — MicroPython v1.28.0 (2026-09-07); `cmods/bin/circuitpython-effects` — CircuitPython 10.2.1 (2026-09-07) |
| Boards | ESP32-P4 — **not run**; ESP32-S3 — **not run** (§4, §11) |

**Dossier trait set frozen before the rebuild began: yes.** Commit `9fcad65`
froze it; the class first existed in `102ff44`. Four rows were restated in
that freeze commit, each with its arithmetic in the dossier's App. C, and
none of them was written after seeing a render of the rebuilt class — the
restatements come from the sources and from `audioif_dynamics.c` at the pin.

---

## 1. Traits

Verdicts use the dossier's own numbering. **Six demonstrated, one
disconfirmed, none unmeasured** — with one clause of G4 carried as
unmeasured inside a demonstrated row, and said so in §11.

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation: argument, and the answer |
|---|---|---|---|---|---|
| G1 | The envelope is one-shot: a 1 ms full-scale burst under a 200 ms attack reaches within 0.5 dB of full open after the burst has gone | **demonstrated** | GAINTRACE, 48 kHz, cpython: peak gain reduction reached **0.00 dB** on a probe whose burst is 1 ms and whose remainder is 40 dB under the threshold | `NoHoldGate` (`hold_ms` forced to 0, so the node falls back to its memoryless computer): peak **−81.97 dB** — the gate never opens at all → RED | *"The tone after the burst opened it, not the burst."* It is 40 dB below the threshold, and the fault run proves it: the same tone under the same settings leaves the faulted gate shut at the floor for the whole render. |
| G2 | Hold is a real stage, 2 ms–2 s: the time the gain stays within 0.5 dB of full open after the key falls is within 10 % of the setting | **demonstrated** | GAINTRACE, 48 kHz, cpython, release at its 2 ms minimum, hop 0.5 ms: **19.5 / 100.5 / 513.5 / 986.0 ms** for settings of 20 / 100 / 500 / 1000 ms (−2.5 / +0.5 / +2.7 / −1.4 %) | `NoHoldGate`: no open period is measurable at any setting → RED | *"The release is doing this, not the hold."* Release is pinned at 2 ms across all four points and only Hold moves; a 2 ms release cannot account for 986 ms. The first draft's version of this row measured with a 1000 ms release and read +170 % at the 20 ms point — the release's own first 0.5 dB — which is why the release is pinned here and why the dossier's App. C struck the "attack + hold + decay" formulation. |
| G3 | The key path is a band with two settable ends: with the band at 500 Hz–2 kHz, a 250 Hz and a 4 kHz tone need at least 4 dB more level to open the gate than a 1 kHz tone does. Key Listen puts the band on the output | **demonstrated** | Bisected opening level, 48 kHz, cpython: 1 kHz opens at **−37.42 dBFS**, 250 Hz at **−32.33** (**+5.09 dB**), 4 kHz at **−32.11** (**+5.30 dB**). Key Listen: a 220 Hz tone with the key high-passed at 4 kHz peaks at **684** against the ordinary output's **16384** | `OpenKeyBand` (both corners pinned at their end stops): shifts collapse to **+0.04** and **+0.05 dB** → RED | *"5 dB is one pole; a real DS201 might be steeper."* Neither source states the filters' order, which the dossier records, and the trait asks for a band and not a slope. The number is what one pole gives; `key_poles=2` is offered and unmeasured (§11). |
| G4 | The closed state is Range, not zero: settled closed gain equals the setting within 0.5 dB at 0, −20, −40, −60 and −80 dB; and the law is a depth, not a slope | **demonstrated** (the −80 dB point is unmeasured — §11) | GAINTRACE settled gain, 48 kHz, cpython, input −6 dBFS at threshold 0 dB: **0.000 / −20.162 / −40.349 / −60.128 dB** for settings of 0 / −20 / −40 / −60. Depth-not-slope: two inputs 10 dB apart at Range −20 give **−20.175** and **−20.233 dB**, 0.058 dB apart | `NoHoldGate` two dB under the threshold, where the memoryless `over * 8.0f` has not yet clamped: **−16 dB** against the setting's −40 → RED (clean run at the same settings: −40.0 ± 0.5) | *"You picked an input level that flatters it."* The level is named and it is the highest one 16 bits allow: a −6 dBFS input at −80 dB of Range is 1.6 LSB, which is why that point is unmeasured rather than reported. |
| G5 | Attack and decay are exponential stages whose time constant is the setting; the fastest attack opens inside 0.2 ms at 48 kHz | **demonstrated** | GAINTRACE trace read on the **gain** axis, 48 kHz, cpython. Attack 10–90 %: **2.241 / 21.582 / 227.877 / 2181.243 ms** at settings 1 / 10 / 100 / 1000 ms against 2.197 × the setting (+2.0 / −1.8 / +3.7 / −0.7 %). Decay t63: **9.364 / 94.862 / 986.456 / 3926.666 ms** at 10 / 100 / 1000 / 4000 (−6.4 / −5.1 / −1.4 / −1.8 %). Fastest attack (0.01 ms): byte-identical to the source **3 samples** after the onset, **0.0625 ms** | `HalvedTimes` (coefficients from half the setting): 10–90 % measures **111 ms** against the 219.7 ms a 100 ms setting asks for, 49 % out against a 15 % bar → RED | *"You chose the axis that fits."* The trait names a transition of the *gain*, and a gain is linear; GAINTRACE's own `attack_t10_90_ms` reads its dB trace, which for a gate's ∞:1 law is a different quantity — it reads 1.00 × the setting where the linear reading reads 2.20 ×. Both numbers are in §9's notes so a reader can check the choice. |
| G6 | Peak detection: equal-**peak** sine and square open within 0.5 dB of each other; equal-**RMS** open about 3.0 dB apart | **disconfirmed** — the equal-peak clause. Equal-RMS holds | Bisected Threshold, 48 kHz, cpython. Equal peak: **+0.630 dB** apart, against a 0.5 dB bar. Equal RMS: **−2.520 dB** apart. Bare `Dynamics` node with no key filters, same material: **0.000 dB** apart at equal peak; with the class's key filters in circuit: **+0.403 dB** | `RmsDetector` (`detector="rms"`): the pair swaps — equal-peak **+2.520**, equal-RMS **−0.630 dB** → RED on the clause that separates the detectors | **Cause, measured not argued:** the class's key high-pass is always in circuit (the DS201's L.F. control bottoms at 25 Hz, it does not switch off), and a one-pole high-pass overshoots a square's edges, lifting its detected peak. The detector itself is a peak detector: the bare node opens both at exactly the same threshold, and the equal-RMS separation is 2.52 dB where an RMS detector gives 0.63. Carried in the class docstring and the catalogue row. |
| G7 | Duck inverts the sense: unity below threshold (±0.05 dB) and the Range setting above it (±0.5 dB) at 0, −6, −20 and −40 dB, on the same envelope | **demonstrated** | GAINTRACE settled gain, 48 kHz, cpython, `duck=True`: **0.000 / −6.299 / −20.155 / −40.279 dB**. Below threshold, LEVEL wet:dry **−0.0009 dB** both channels. Same hold: ducked for **105.5** and **518.5 ms** at settings of 100 and 500 ms | `AddingDuck` (the inverter's modulator at +32767): the "duck" **boosts**, +3.61 dB at Range −6 and +5.58 dB at −20 → RED | *"Two nearly equal int16 streams subtracted cannot be accurate."* True at the deep end and measured: Range −60 reads −59.47 and −80 reads −77.18, which is the subtraction's own quantisation floor, which is why the dossier states the trait to −40 dB and records the deep end in App. C. |

- **demonstrated** = a measurement, that measurement red on a planted fault
  of the same kind, and a surviving refutation. All six carry all three.
- **disconfirmed** carries the cause and what the class does instead. G6's is
  in the class docstring and in the catalogue row of
  [`README.md`](README.md), not only here.

**Characters:** none. Gate and duck are one mechanism under a switch and G7
states the switch.

**Refutation pass.** Run by this session, 2026-09-07, against every
demonstrated row, and the arguments and answers are the last column above.
Two of them changed a measurement rather than surviving it, and both are
recorded: G2's first attempt read the release's own first half-decibel as
hold and was re-run with the release pinned at its minimum; G5's first
attempt read GAINTRACE's dB-axis transition and was re-run on the gain axis
the trait names. What the pass could not break was G1 — the fault run pins
the gate shut on the same material — and G4's depth-not-slope clause, whose
two levels differ by 0.058 dB where a slope would put them 80 dB apart.

---

## 2. Tier 1 invariants

`cp` = `.venv/bin/python`, `mp` = `cmods/bin/micropython`, `cpy` =
`cmods/bin/circuitpython-effects`. Every cell below is a render made by
`tools/render_effect.py` on that interpreter and measured by
`tools/effect_measurements.py` on CPython.

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Range 0 dB with the gate shut is a wire, byte-identical to the source | WIRE | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Range 0 dB across the gate's **first** opening | WIRE | 6.90 ms | 6.90 ms | 6.90 ms | 6.89 ms | 6.89 ms | 6.89 ms | 6.89 ms | 6.89 ms | 6.89 ms |
| Level-honest: unity through the open path, no hidden gain | LEVEL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| `reset()` leaves every node the class built silent and stateless | STATE + this class's own probe | pass* | pass* | pass* | pass* | pass* | pass* | pass* | pass* | pass* |
| `deinit()` releases every node the class built and leaves the source rendering | STATE | pass | *(cp only)* | *(cp only)* | pass | | | pass | | |
| `capabilities` names exactly the optional behaviours honoured | STATE | pass | *(cp only)* | *(cp only)* | pass | | | pass | | |
| Pulling `output` allocates nothing | STATE | pass | *(cp only)* | *(cp only)* | pass | | | pass | | |
| Rate-honest: Hz spans clamp below Nyquist, never refuse | this class's own test, plus every render above | pass | pass | pass | pass | pass | pass | pass | pass | pass |
| Every invariant also holds at `channel_count` 1 | WIRE, TAIL, LEVEL, CLICK | pass | pass | pass | pass | pass | pass | pass | pass | pass |

Every cell in the WIRE, TAIL, LEVEL and CLICK rows is a separate render on
that interpreter at that rate, at `channel_count` 2 **and** 1, measured on
CPython; 36 renders per row-set, and the `channel_count` 1 row is those same
four measurements at one channel rather than a fifth measurement.

**STATE drives the class rather than reading a render**, so its three rows
are CPython only — the kit's own rule (`effect_measurements.py`: "the render
is dual-runtime; the analysis is not") — and the *(cp only)* cells say so
rather than claiming a run that did not happen. Nothing in this pack shows
`deinit()`, the allocation leg or `capabilities` exercised on MicroPython or
CircuitPython; what those two interpreters do show is that the class builds
and renders identically at every rate and channel count (§3).

**The rate-honesty row is not the kit's RESPONSE.** RESPONSE measures a
frequency response and this class's audio path is a VCA, flat by
construction; what "rate-honest" means here is that a Hz-valued span clamps
rather than refuses. That is measured directly — `self._hz(35000.0)` against
0.98 × Nyquist at all three rates, with the class still rendering
(`test_hz_spans_clamp_below_nyquist_rather_than_refusing`, CPython) — and on
the other two interpreters by the renders themselves: every one of the
18 per-interpreter renders at 44.1 kHz and 22.05 kHz was built with the Key
High macro in play and none of them raised.

**The two WIRE rows are one measurement with the gate in two states, and
both are wanted.** Range 0 dB means "0 dB of attenuation when the gate is
shut", which the node makes an exact unity floor: with the threshold at the
top, a full-scale ramp comes back byte-identical — 0 of 16 384 samples
differ, at every rate, on every interpreter, at both channel counts. Let the
gate actually open and the **first** transition ramps up from the machine's
cold zero rather than from that floor, because `state_init` and
`clear_extras` write 0.0 to the gain (`audioif_dynamics.c:265`) and only the
CLOSED branch ever writes `floor_gain` (`:719-722`). Measured: 331 frames at
48 kHz, 304 at 44.1 k, 152 at 22.05 k — **6.90, 6.89 and 6.89 ms**, the same
time at every rate, which is the 6.8 attack time constants the machine's
0.999 snap needs at patch 0's 1.0 ms attack. From 10 ms on the render is
byte-identical to its source. The class cannot reach that state through any
API the node offers; committed as
`test_the_first_opening_ramps_from_the_nodes_cold_zero`.

`pass*` on the reset row: the walk is green and the class's own reset probe
is green, with the qualification two paragraphs below — the node's key
filters are not clearable.


**Mono.** The dossier's §4/App. I says a mono source gets identical
processing, because one gain from a channel-linked detector lands on every
channel. Measured: at `channel_count` 1 the settled closed gain at Range
−40 dB is within 0.5 dB of the setting, the same reading as stereo
(`tests.test_noisegate.Tier1Invariants.test_mono_gets_the_same_gate_as_stereo`),
and every row above holds at `channel_count` 1 as well as 2.

**Rate-honesty.** The Key High macro's span tops at 35 kHz, above Nyquist at
every rate here. `self._hz()` clamps it to 0.98 × Nyquist and never refuses:
23 520 Hz at 48 k, 21 609 at 44.1 k, 10 804.5 at 22.05 k, verified at all
three with the class still rendering
(`test_hz_spans_clamp_below_nyquist_rather_than_refusing`). The Hold macro's
2 ms floor is 96 frames at 48 kHz and 44 at 22.05 kHz, so the node's gate
machine — which is off when the frame count rounds to zero
(`audioif_dynamics.c:452`) — cannot be switched off by a low rate
(`test_the_hold_floor_keeps_the_gate_machine_on_at_every_rate`).
**`macro(6)` reports the nominal span value, not the clamped one**: at
22.05 kHz a Key High of 20 kHz reads back 20 000 while the filter sits at
10 804.5 Hz. That is `_hz`'s documented contract (clamp at the node, never
refuse) and not a defect, but a host reading the knob back should know it.

**Planted faults for this block**, each with its clean control beside it,
all in `tests/test_noisegate.py`:

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | `kit_faults.OneLsbScale` on the output, on `ramp_fs` at Range 0 dB | green, 0 of 16 384 samples differ | RED |
| TAIL | `kit_faults.StuckDc`, +1 LSB held in the settled state | green, residual 0 LSB | RED |
| CLICK | a `lookahead_ms=1.0` build reporting `latency_samples = 0`, DSP untouched (`UnderReportedLatency`) | green at 48 and reported 48 | RED |
| STATE / reset | the `Dynamics` node kept out of the reset walk (`UnclearedGate`) | first block after `reset()` is exactly 0 LSB | RED, 8192 LSB — **but only against this class's own reset probe, not the kit's STATE** |

**The kit's STATE cannot see this class's reset, and that is recorded rather
than worked around.** STATE's third read is `reset()` plus a *silent* source,
and a gate holds no audio: a machine left wide open renders silence out of
silence exactly as a cleared one does, so `UnclearedGate` passes STATE. The
class therefore carries its own reset probe — quiet material rather than
silence, and the readout is the first block after the reset — and the fault
turns *that* red. Both are asserted in
`test_planted_fault_a_gate_left_open_across_reset`, including the assertion
that STATE stays green, so the blind spot is committed and not just
described.

**A Tier 1 miss, measured: `reset()` cannot clear the key filters.**
`audioif_dynamics_reset` deliberately keeps the side-chain filter memory
(`audioif/src/shared/audioif_dynamics.c:281-288`) and nothing in the node's
keyword table reaches that state, so the class's reset walk cannot clear it.
Consequence, measured: after a full-scale pass, `reset()`, and then a
−60 dBFS tone under a −39.7 dB threshold, the first block comes out at
**33 LSB** — the gate opened on the difference between silence and a stale
high-pass state. It decays with the filter's own 6.4 ms time constant.
Committed as `test_reset_does_not_clear_the_key_filters_and_the_node_says_so`,
which goes red on purpose if audioif ever clears them. **This wants an
audioif issue; none was filed by this session** (§11).

Nodes this class enumerates with `self._own()`, in build order — the default
build: `Dynamics`. The `duck=True` build: `Splitter` (reset and deinit both
`False`; it implements neither), `SplitterTap` ×2, `Dynamics`, the constant
`RawSample` modulator, `Multiply`, `Mixer` (reset through a callable, see
below). Seven, asserted in `test_every_node_the_class_built_is_walked`.

**The duck's mixer clears through a callable.** Upstream CircuitPython's
`Mixer.reset_buffer` **stops its voices**, which audioif's own does not
(`audioif/src/audiomixer/MixerVoice.c:91` says so in as many words).
Measured, minimal repro, a mixer with one voice playing a looping sample:

```
cpython         before reset peak 8000 after  reset peak 8000
micropython     before reset peak 8000 after  reset peak 8000
circuitpython   before reset peak 8000 after  reset peak 0
```

So `NoiseGate.reset()` on a duck build would silence it permanently on one
interpreter of three. The class hands the voices back after clearing, and a
duck build renders on all three after a reset
(`test_a_duck_build_still_renders_after_reset`). What the class cannot fix
is a caller reaching past it: `tools/render_effect.py` calls
`audiocore.reset_buffer(effect.output)` directly, which is why §3's duck row
still differs on `circuitpython-effects`.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes (`effects_component_probe.py:15`), per probe, per
rate, per channel count, at source block 256. `sum(data)` is never the
comparison.

Command shape (one of thirty-eight):

```
$ PYTHONPATH=lib .venv/bin/python tools/render_effect.py NoiseGate chord out/cpython --rate 48000
NoiseGate chord 48000 Hz 2ch block 256 -> 144000 frames  fnv 9919aaad  sum 4090943  audio
```

| Probe / settings | Rate | ch | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|
| `ramp_fs, Range 0, gate shut` | 48000 | 2 | `aef0fa61` | `aef0fa61` | `aef0fa61` | *(board run)* | *(board run)* |
| `ramp_fs, Range 0, gate shut` | 48000 | 1 | `7bbcbf39` | `7bbcbf39` | `7bbcbf39` | *(board run)* | *(board run)* |
| `ramp_fs, Range 0, gate shut` | 44100 | 2 | `aa6aeabd` | `aa6aeabd` | `aa6aeabd` | *(board run)* | *(board run)* |
| `ramp_fs, Range 0, gate shut` | 44100 | 1 | `9fa9cd6d` | `9fa9cd6d` | `9fa9cd6d` | *(board run)* | *(board run)* |
| `ramp_fs, Range 0, gate shut` | 22050 | 2 | `4a36acb1` | `4a36acb1` | `4a36acb1` | *(board run)* | *(board run)* |
| `ramp_fs, Range 0, gate shut` | 22050 | 1 | `215e1a09` | `215e1a09` | `215e1a09` | *(board run)* | *(board run)* |
| `ramp_fs, Range 0, gate opens` | 48000 | 2 | `db67ff25` | `db67ff25` | `db67ff25` | *(board run)* | *(board run)* |
| `ramp_fs, Range 0, gate opens` | 48000 | 1 | `2a7cd484` | `2a7cd484` | `2a7cd484` | *(board run)* | *(board run)* |
| `ramp_fs, Range 0, gate opens` | 44100 | 2 | `ecfbd7d9` | `ecfbd7d9` | `ecfbd7d9` | *(board run)* | *(board run)* |
| `ramp_fs, Range 0, gate opens` | 44100 | 1 | `4b315270` | `4b315270` | `4b315270` | *(board run)* | *(board run)* |
| `ramp_fs, Range 0, gate opens` | 22050 | 2 | `b5555665` | `b5555665` | `b5555665` | *(board run)* | *(board run)* |
| `ramp_fs, Range 0, gate opens` | 22050 | 1 | `39939981` | `39939981` | `39939981` | *(board run)* | *(board run)* |
| `burst_silence, patch 0` | 48000 | 2 | `340b9de5` | `340b9de5` | `340b9de5` | *(board run)* | *(board run)* |
| `burst_silence, patch 0` | 48000 | 1 | `1f34a648` | `1f34a648` | `1f34a648` | *(board run)* | *(board run)* |
| `burst_silence, patch 0` | 44100 | 2 | `1134748d` | `1134748d` | `1134748d` | *(board run)* | *(board run)* |
| `burst_silence, patch 0` | 44100 | 1 | `5d21d2f5` | `5d21d2f5` | `5d21d2f5` | *(board run)* | *(board run)* |
| `burst_silence, patch 0` | 22050 | 2 | `ed4cfcf5` | `ed4cfcf5` | `ed4cfcf5` | *(board run)* | *(board run)* |
| `burst_silence, patch 0` | 22050 | 1 | `bfa20e36` | `bfa20e36` | `bfa20e36` | *(board run)* | *(board run)* |
| `sine_1k_-14, gate held open` | 48000 | 2 | `c64c76b9` | `c64c76b9` | `c64c76b9` | *(board run)* | *(board run)* |
| `sine_1k_-14, gate held open` | 48000 | 1 | `23813c59` | `23813c59` | `23813c59` | *(board run)* | *(board run)* |
| `sine_1k_-14, gate held open` | 44100 | 2 | `2c5e6c8d` | `2c5e6c8d` | `2c5e6c8d` | *(board run)* | *(board run)* |
| `sine_1k_-14, gate held open` | 44100 | 1 | `1a360689` | `1a360689` | `1a360689` | *(board run)* | *(board run)* |
| `sine_1k_-14, gate held open` | 22050 | 2 | `f8445ca5` | `f8445ca5` | `f8445ca5` | *(board run)* | *(board run)* |
| `sine_1k_-14, gate held open` | 22050 | 1 | `31a0f00b` | `31a0f00b` | `31a0f00b` | *(board run)* | *(board run)* |
| `click_stereo, gate held open` | 48000 | 2 | `385c5d15` | `385c5d15` | `385c5d15` | *(board run)* | *(board run)* |
| `click_stereo, gate held open` | 48000 | 1 | `67da3e99` | `67da3e99` | `67da3e99` | *(board run)* | *(board run)* |
| `click_stereo, gate held open` | 44100 | 2 | `0d9a7099` | `0d9a7099` | `0d9a7099` | *(board run)* | *(board run)* |
| `click_stereo, gate held open` | 44100 | 1 | `f00130b2` | `f00130b2` | `f00130b2` | *(board run)* | *(board run)* |
| `click_stereo, gate held open` | 22050 | 2 | `0107fd8d` | `0107fd8d` | `0107fd8d` | *(board run)* | *(board run)* |
| `click_stereo, gate held open` | 22050 | 1 | `60004249` | `60004249` | `60004249` | *(board run)* | *(board run)* |
| `sweep_log, Key Listen on` | 48000 | 2 | `94027745` | `94027745` | `94027745` | *(board run)* | *(board run)* |
| `sweep_log, Key Listen on` | 48000 | 1 | `143389f1` | `143389f1` | `143389f1` | *(board run)* | *(board run)* |
| `sweep_log, Key Listen on` | 44100 | 2 | `1c2869f1` | `1c2869f1` | `1c2869f1` | *(board run)* | *(board run)* |
| `sweep_log, Key Listen on` | 44100 | 1 | `e97bcd57` | `e97bcd57` | `e97bcd57` | *(board run)* | *(board run)* |
| `sweep_log, Key Listen on` | 22050 | 2 | `8fa38aad` | `8fa38aad` | `8fa38aad` | *(board run)* | *(board run)* |
| `sweep_log, Key Listen on` | 22050 | 1 | `51512357` | `51512357` | `51512357` | *(board run)* | *(board run)* |
| `chord, patch 0` | 48000 | 2 | `9919aaad` | `9919aaad` | `9919aaad` | *(board run)* | *(board run)* |
| `chord, patch 0` | 44100 | 2 | `ac0873b1` | `ac0873b1` | `ac0873b1` | *(board run)* | *(board run)* |
| `noise_det, patch 0` | 48000 | 2 | `abbbad5d` | `abbbad5d` | `abbbad5d` | *(board run)* | *(board run)* |
| `click_stereo, lookahead 1.0 ms` | 48000 | 2 | `48ea1781` | `48ea1781` | `48ea1781` | *(board run)* | *(board run)* |
| `click_stereo, lookahead 1.0 ms` | 44100 | 2 | `d9fcc1c9` | `d9fcc1c9` | `d9fcc1c9` | *(board run)* | *(board run)* |
| `burst_silence, `duck=True`` | 48000 | 2 | `1fa4a6bd` | `1fa4a6bd` | `bae41dc5` **differs** | *(board run)* | *(board run)* |
| `burst_silence, `duck=True`, Range -20` | 48000 | 2 | `57bd7045` | `57bd7045` | `bae41dc5` **differs** | *(board run)* | *(board run)* |

**Desktop agreement: yes, on every render but one.** **Forty-one of forty-three**
renders are byte-identical across CPython, desktop MicroPython and
`circuitpython-effects`.

**The exception is the `duck=True` build, and the cause is not the class.**
`tools/render_effect.py` calls `audiocore.reset_buffer(effect.output)` before
it renders; on `circuitpython-effects` that stops the summing mixer's voices
for good (the minimal repro is in §2), so the duck render is exact silence
there and carries audio on the other two. Reproduced without the class at
all, and without the renderer, in nine lines. The class's own `reset()` is
not affected — it hands the voices back — and the plain gate build has no
mixer and no difference.

**Board agreement:** not taken. The P4 and S3 digests come with the cost run
(§4), which has not been run (§11).

---

## 4. Tier 3 — cost on the boards

**Not run.** No ESP32-P4 or ESP32-S3 figure exists for this class, and none
is estimated here. Dossier budget: P4 **6 %** of one stereo block's real-time
deadline, S3 **12 %**; lean patch expected **no**.

| Board | Patch | Settings | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | — | *(not run)* | | | | |
| S3 | 0 | — | *(not run)* | | | | |

What a board run must do when it happens: put the class in the state its cost
is about — the gate actually opening and closing, not idling shut — and
print the render digest beside the CPU figure so §3's board leg is taken at
the same time. `tools/measure_effect_cost.py` refuses a render whose digest
is the digest of silence, and a gate at patch 0 over quiet material renders
exactly that, so the cost material must be programme material that crosses
the threshold.

---

## 5. Latency

Reported `latency_samples` = **0** on the default build, and the class
overrides the property to report its own instance rather than a class field,
because `lookahead_ms` is a per-instance choice.

| Rate | Reported | Measured (integer onset, both channels) | Δ | ms |
|---|---|---|---|---|
| 48000 | 0 | 0.0, 0.0 | 0 | 0.000 |
| 44100 | 0 | 0.0, 0.0 | 0 | 0.000 |
| 22050 | 0 | 0.0, 0.0 | 0 | 0.000 |
| 48000, `lookahead_ms=1.0` | 48 | 48.0, 48.0 | 0 | 1.000 |
| 44100, `lookahead_ms=1.0` | 44 | 44.0, 44.0 | 0 | 0.998 |

Every row is CLICK against the `click_stereo` probe, and every one of them
reads the same on all three interpreters.

Dossier latency budget: **0 samples**. Met: **yes**, on the default build.

**Every latency-adding option**, each defaulting off or to its shortest:

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| `lookahead_ms` | `0.0` | 0 samples | 48 samples at 1.0 ms / 48 kHz, measured; 96 at 2.0 ms | yes — "**1.0 ms of look-ahead is 1.0 ms of latency**, 48 samples at 48 kHz, and the cap is 50 ms" |

There is no other. `duck=True` adds three nodes and **no latency**: measured
through the class on `click_stereo`, a duck build at Range −6 dB reports 0
and measures **0.0, 0.0** samples, and its `tail_samples` is 0.

Planted fault: `UnderReportedLatency` — a `lookahead_ms=1.0` build reporting
`latency_samples = 0`, the DSP untouched. CLICK measures 48 against a
reported 0 → RED, with the audio digest unchanged from the clean run.

---

## 6. Macro surface and patches

Eight macros, every one a DS201 panel control. `_component` refuses a
seventeenth at construction; three proposed macros became construction
options or were struck, and the dossier's §6 and App. R2 carry the argument
for each.

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Threshold | UNIPOLAR | −80 … 0 dB | Threshold (−54 dB … ∞) |
| 1 | Attack | UNIPOLAR | 0.01 … 1000 ms, log | Attack (10 µs … 1 s) |
| 2 | Hold | UNIPOLAR | 2 … 2000 ms, log | Hold (2 ms … 2 s) |
| 3 | Release | UNIPOLAR | 2 … 4000 ms, log | Decay (2 ms … 4 s) |
| 4 | Range | UNIPOLAR | 0 … −80 dB | Range |
| 5 | Key Low | UNIPOLAR | 25 … 4000 Hz, log | L.F. |
| 6 | Key High | UNIPOLAR | 250 … 35000 Hz, log, clamped to 0.98 × Nyquist | H.F. |
| 7 | Key Listen | TOGGLE | off / on | Key Listen |

| Patch | Name | What it is for |
|---|---|---|
| 0 | Default | the constructor's own defaults on the 0–127 grid: −39.7 dB, 1.0 ms, 49.5 ms hold, 200.7 ms release, −80 dB Range, key wide open |
| 1 | Tom Tighten | −30 dB, fast attack, 61 ms hold, −40 dB Range, key 80 Hz–4 kHz — the hat above the tom stops opening it |
| 2 | Gated Reverb | 391 ms hold and a 19 ms decay: the tail is chopped square |
| 3 | Vocal Breath Trim | −12 dB Range and a wide key — it ducks the breath rather than removing it |
| 4 | Amp Hiss | key 2–8 kHz, −80 dB Range: the gate hears the hiss and not the guitar |
| 5 | Drum Bleed | key 100 Hz–1 kHz, 30 ms hold, −50 dB Range |

Key Listen is 0 in every patch: it replaces the output, and no patch should
hand a host a different signal.

`patch_index` is 0 on a fresh instance, `None` after any macro move, and the
patch's index after `program_change` — the base class's behaviour, exercised
by `tests/test_component_foundation.py` and by
`tests.test_noisegate.TheRegistryServesIt`.

**`capabilities` = `()`.** The dossier's one-line reason: "A gated-reverb
hold in bars is tempting and neither source's box has one; the class does not
read the transport." Nothing in the class reads `self._transport()`.

---

## 7. Portability tier

**Tier: audioif.** `REQUIRES = ("audiodynamics", "audioroute", "audiomath")`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `Dynamics(DYN_GATE)` | `audiodynamics` | G1, G2, G4, G5, G6, and G3's key band | `audiodynamics` is audioif's own module and has no CircuitPython ancestor (`audioif/docs/upstream-diff.md:661`). Nothing in the ported palette has a per-sample gain computer with a trigger state, and a component has no per-block hook to take the decision in Python (`docs/audio-component-api.md:231-233`) |
| `Splitter(taps=2)` | `audioroute` | G7 | The ported palette has no fan-out: one source can be played by one node |
| `Multiply` | `audiomath` | G7 | `(a · −32768) >> 15 = −a` is an exact sign flip; `audiomixer.Mixer` clamps a voice level to 0…1 before its Q15 multiply (`Mixer.c:332`) and therefore cannot subtract |

Test:

```
$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
.......
----------------------------------------------------------------------
Ran 7 tests in 0.054s

OK
```

The class enters that battery on its own, because it walks `audioeffects.ALL`
and `rebuilt.known()`.

**What that test does not prove**, and every pack repeats it: blocking a
module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace, so no stock-tier class
has been shown rendering on a stock CircuitPython build of the ported C.
That is a gap in the method rather than in this class — and it costs this
class nothing directly, since `NoiseGate` is audioif-tier and its half of the
battery is the `ImportError`, which the block does test honestly.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began, and §1 lists
      every trait as demonstrated or disconfirmed with cause.
- [x] Every Tier 1 invariant is green on CPython, desktop MicroPython and
      `circuitpython-effects`, at 48 kHz, 44.1 kHz and 22.05 kHz, at
      `channel_count` 2 and 1; every Tier 2 measurement names its rate.
      **One qualification, in §2:** `reset()` cannot clear the node's
      side-chain filters, and the measured consequence is recorded there.
- [x] Every demonstrated Tier 2 trait has a measurement, and that
      measurement was shown red on a planted fault of the same kind.
- [x] Every demonstrated trait survived an independent refutation attempt,
      recorded with the argument and the answer (§1's last column).
- [x] CPython and desktop MicroPython render identical bytes on the probe
      material; `circuitpython-effects` matches too, except the `duck=True`
      render, whose cause is recorded in §3 and is not the class.
- [ ] **Tier 3 cost is not measured.** No board run (§4, §11).
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz
      and 44.1 kHz; the dossier's 0-sample budget is met; the one
      latency-adding option defaults off and is named in the docstring in
      milliseconds.
- [x] The class declares eight macros and five named patches beyond patch 0.
- [x] `validate_api`, `validate_metadata`, the CPython tests, the
      portability-tier test, the three-interpreter smoke and flake8 all pass
      (§9). The suite is **262 tests** where the Phase 2 foundation left it
      at 227: the 35 this class brought.
- [x] The catalogue row in [`README.md`](README.md) and the class docstring
      describe the standout and the tier in a musician's terms; the **cost**
      column is empty because the board run has not happened.
- [x] The class, its tests and its CHANGELOG line landed in `102ff44`; this
      file lands in the Station C commit.

---

## 9. Commands, verbatim

All run from the worktree `ac-wt-noisegate` with
`PYTHONPATH=lib` and `audiocomponents/.venv/bin/python`.

```
$ python -m flake8
exit 0

$ python tools/validate_api.py
validated 53 instruments and 46 effects

$ python tools/validate_metadata.py
audio component metadata is valid

$ python -m unittest tests.test_portability_tier
.......
----------------------------------------------------------------------
Ran 7 tests in 0.073s

OK

$ python -m unittest tests.test_noisegate
...................................
----------------------------------------------------------------------
Ran 35 tests in 116.790s

OK

$ python -m unittest discover -s tests -p "test_*.py"
----------------------------------------------------------------------
Ran 262 tests in 28.680s

OK (skipped=1)

$ PYTHONPATH=lib .venv/bin/python tests/parity/effects_library_smoke.py

46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython tests/parity/effects_library_smoke.py

46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects tests/parity/effects_library_smoke.py

46 classes, 88 patches, 0 failures
```

```
$ .venv/bin/python tools/measure_effect_cost.py --subject NoiseGate --port <COMn>
(not run - no board leg this session, section 4 and section 11)
```


**The two axis notes behind §1's numbers**, so a reader can check the
choices rather than take them:

```
G5 attack, GAINTRACE's own attack_t10_90_ms (dB axis):
  attack     1.0 -> t10_90     1.329 ms  want     2.20  (-39.5 %)
  attack    10.0 -> t10_90    10.058 ms  want    21.97  (-54.2 %)
  attack   100.0 -> t10_90   103.001 ms  want   219.70  (-53.1 %)
  attack  1000.0 -> t10_90  1098.221 ms  want  2197.00  (-50.0 %)
G5 attack, the same trace on the gain axis (what §1 reports):
  attack     1.0 ->     2.241 ms  want      2.20  (+2.0 %)
  attack    10.0 ->    21.582 ms  want     21.97  (-1.8 %)
  attack   100.0 ->   227.877 ms  want    219.70  (+3.7 %)
  attack  1000.0 ->  2181.243 ms  want   2197.00  (-0.7 %)

G6, the cause of the equal-peak spread, on the bare node:
  node without key filters: sine -14.000  square -14.000  -> +0.000 dB
  node with key filters:    sine -13.832  square -13.429  -> +0.403 dB
```

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

- **No surface and no docstring** (`dynamics.py:161-177`). The rebuild has
  eight macros, six patches and a docstring written for a musician.
- **No Range**, so the old class inherited the node's fixed −80 dB clamp.
  Range is macro 4 and reaches the −15 dB the DS201's manual recommends;
  measured to 0.5 dB at four settings (§1, G4).
- **No hold**, so it could not make the gated-reverb sound. Hold is macro 2,
  measured to 10 % at four settings, and patch 2 is that sound.
- **The gate law was a slope and nothing said so** — ~8 dB of attenuation per
  dB below the knee. The rebuild's law is a depth: two inputs 10 dB apart get
  gains 0.058 dB apart.
- **The threshold defaulted to −50 dB with no key filter.** The default is
  −39.7 dB with a key band the caller can close around what should trigger
  it, and five of the six patches set that band deliberately.

---

## 11. What is not done

- **No board run.** Neither the ESP32-P4 nor the ESP32-S3 has rendered this
  class. §4's table is empty and §3's board columns are empty, so the Tier 3
  gate line and the board leg of the digest line are both open. Nothing here
  estimates either.
- **G4's −80 dB Range point is unmeasured.** A −6 dBFS input attenuated by
  80 dB is 1.6 LSB, so 16-bit output cannot carry it; the measured reading is
  −83.96 dB against a 0.5 dB bar. The node's own figure at that setting is
  −80.00 dB (`audioif/docs/upstream-diff.md`, the `depth_db` paragraph), but
  that is the node's measurement and not this class's, and it is not counted
  as one.
- **G7's deep end is measured and out of tolerance, deliberately outside the
  trait.** Range −60 reads −59.47 dB and −80 reads −77.18 dB in duck mode,
  which is the int16 subtraction's own floor. The dossier states G7 to
  −40 dB for that reason; a caller who sets a duck deeper than that gets less
  attenuation than the knob says, and the class docstring says so.
- **`key_poles=2` is offered and never measured.** The option is passed
  through to the node, which upstream measures at 10.31 dB/octave against one
  pole's 5.29, but no measurement in this pack exercises it.
- **`key=` (the external key) is offered and never measured.** One line
  hands a second stream to the detector; no probe in this pack drives it, and
  the starvation behaviour it inherits (a key that runs dry silences the
  node) is quoted from the C rather than measured.
- **No audioif issue was filed** for the two node findings this session
  measured: `audioif_dynamics_reset` leaving the side-chain filters loaded
  with no way for a class to clear them (§2), and upstream CircuitPython's
  `Mixer.reset_buffer` stopping its voices where audioif's does not (§2, §3).
  Both are reproduced minimally here; neither has an issue number.
- **The `sweep_log` probe at patch 0 renders exact silence** on all three
  interpreters — correct, since the probe is at −40 dBFS and patch 0's
  threshold is −39.7 dB — and is therefore not cited as a digest row. The
  digest row uses the same probe with the gate held open.
- **`Rack` composition is unmeasured.** Nothing here builds a `NoiseGate`
  inside a rack or checks that a rack's summed latency and tail read 0.
