# Evidence Pack — `HighPass` (no historical standout — design grade)

Read with the dossier, [`HighPass.md`](HighPass.md), whose §3 trait table was
frozen at Station A before any of this was written. Every figure here carries
the command that produced it and the interpreter and rate it ran on; a
measurement nobody ran says `unmeasured`, with why.

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `HighPass` |
| Dossier | [`HighPass.md`](HighPass.md), traits fixed 2026-09-07 at `d2f0c0e` |
| Module | `lib/audioeffects/rebuilt/highpass.py` |
| Base | `_component.Component` |
| Family / phase | EQ / Filter, roadmap Phase 2 |
| Standout | none, per vision §4.2 — the two-pole analog low-cut, RBJ's HPF |
| Grade | design |
| Portability tier | **audioif** (`REQUIRES = ("audiobiquad",)`) |
| Landed in commit | `1cc8166` (code, tests, README, CHANGELOG); this file and its two drivers in `ced7eb7` |
| audioif pin | `AUDIOIF_PIN` = `2f6cbc3791efd38dfbf0fb263052400a69b976ed`; `pydevices-audioif` 0.2.0 in the venv |
| Interpreters | `audiocomponents/.venv/bin/python` 3.12.3 (numpy 2.5.2); `cmods/bin/micropython`; `cmods/bin/circuitpython-effects` |
| Boards | **not run** — §4 and §11 |

**Dossier trait set frozen before the rebuild began:** yes. Station A landed
in `d2f0c0e`; the class landed in `1cc8166`.

Two drivers produce everything below, both committed:

- `tools/phase2_probes/highpass_evidence.py` — Station C under CPython with
  the kit (`tools/effect_measurements.py`) and numpy.
- `tools/phase2_probes/highpass_tier1_portable.py` — the Tier 1 rows that are
  *class behaviour* rather than audio, numpy-free, run on all three
  interpreters. It exists because `reset()`, `deinit()` and `capabilities`
  are not settled by two interpreters rendering identical bytes, so claiming
  them off the digest table would be claiming something the digests do not
  say.

---

## 1. Traits

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation: argument, and the answer |
|---|---|---|---|---|---|
| T1 | Exact zero at DC, at Mix 1, every f₀ from 10 Hz up, both slopes | **demonstrated** | TAIL's `dc_step` leg, 48 kHz, cpython: residual **0 LSB**, DC after removal **0.000 LSB**, at f₀ ∈ {10, 30, 100, 2000} Hz and both slopes. Portable row `TAIL exact zero` repeats it at 48 / 44.1 / 22.05 kHz on all three interpreters | the ported `synthio.Biquad` this class moved off, same probe, same 3 s → **RED, residual 71 LSB** | *"Exact zero could be a mute: a class that wrote silence would pass."* The same render carries **10 525 samples of tail** before the zero, and 1 kHz through the same 10 Hz corner reads **+0.0000 dB**. Not a mute |
| T2 | \|H(f₀)\| = Q exactly, both slopes, within 0.05 dB | **demonstrated** | tone at f₀, 48 kHz, cpython: worst **0.001 dB** over Q ∈ {0.5, .707, 1, 2, 4, 8}, at both slopes | the resonance on *both* Butterworth sections → **RED, +15.052 dB where the trait says +6.021** | *"Only checked at f₀ = 1 kHz."* Re-read at 30, 300 and 15 000 Hz and Q ∈ {0.5, 4, 16}: all inside 0.05 dB — **once the settle is scaled to the ring**. A Q-16 corner at 30 Hz rings for half a second, and the first reading (a 1 s render read from its midpoint) was 0.149 dB out. That is the measurement, not the class |
| T3 | +12 dB/oct at the 12 slope, +24 at the 24; −24.10 ± 0.30 dB at f₀/4 (−48.20 ± 0.60 steep); 0.00 ± 0.1 dB at Nyquist | **demonstrated** | tones, 48 kHz, cpython: f₀ ∈ {20, 160, 640, 1280, 3200} Hz, both slopes, every row inside its band; 23 kHz reads **0.000 dB** at every f₀ and both slopes | the second pole left as a wire at 24 dB/oct → **RED, −24.475 dB where the trait says −48.20 ± 0.60** | *"A one-octave fit; two points fit any line."* Re-fitted over three octaves, five points: **12.038 and 12.042 dB/oct** at 12 dB/oct. At 24 dB/oct the wide fit is **unmeasurable in 16 bits** — f₀/32 is 120 dB down and renders as zero, 3 of 5 points under 20 LSB. A bound on the measurement, not on the class |
| T4 | One curve on the bilinear-warped axis, f₀-independent to 0.00000 dB | **demonstrated** to the render's floor, not to 0.00000 dB | tones on the warped grid, 48 kHz, cpython: worst deviation from the 31.5 Hz curve **0.0125 dB** over f₀ ∈ {125, 500, 1 k, 2 k, 4 k}, against the trait's 0.05 dB bar | the built corner 15 % off the asked-for one → **RED, 2.4480 dB against a 0.05 dB bar** | The dossier's 0.00000 dB is arithmetic on the coefficients (A12); a *render* carries int16 quantization, so 0.0125 dB is the render's own floor. Recorded rather than rounded away |
| T5 | Q is the ringing: e^{−π} of peak after Q periods | **demonstrated**, with the dossier's measurement cell corrected | tone burst at f₀ released, 48 kHz, cpython: **1.01, 1.00, 1.00, 1.00 Q** for Q ∈ {2, 4, 8, 16} | the built Q a quarter of the asked-for one → **RED, 0.25 Q** | **The dossier's cell says "impulse", and for this class that is wrong.** A high-pass passes the click itself: the impulse response's first sample is the strike arriving unfiltered, 20–30 dB above the ring behind it, so an envelope peak over the whole response is the strike and e^{−π} of it is reached in a tenth of a period at every Q — measured: Q 2 and Q 16 both read 0.01 Q. A released tone burst excites the same resonance and leaves only its decay |
| T6 | Rate-honest against S1's closed form at the running rate, ≤ 0.1 dB | **demonstrated** | tones at 48 000 / 44 100 / 22 050 Hz differenced against the closed form evaluated at each rate: worst **0.0153 dB** over every rate/f₀/probe combination | coefficients built for 48 kHz while 44.1 kHz runs → **RED, −27.107 dB against a closed form of −24.100** | *"Three rates agreeing could mean the class ignores the rate."* The fault moves the reading 3.0 dB, so the measurement can tell the difference; and each rate is differenced against its own closed form, never against 48 kHz's |

**Tally: six demonstrated, none disconfirmed, none unmeasured.**

**Characters:** none. A high-pass has one behaviour (dossier §3).

**Refutation pass.** Run by this session, 2026-09-07, as
`highpass_evidence.py`'s `refutation()`. It went after the four traits whose
evidence rests on a single number or a single frequency, and it **broke two
readings**: T2's corner gain at a low f₀ and high Q (a settle too short for
the ring), and T3's wide-span slope fit at 24 dB/oct (below the 16-bit
floor). Neither was a class defect; both are recorded above with their
numbers and both were re-taken. It did not break T1, T4, T5 or T6.

---

## 2. Tier 1 invariants

Two readings, and they say different things.

**(a) The portable rows**, from
`tools/phase2_probes/highpass_tier1_portable.py`, on all three interpreters
at 48 000 / 44 100 / 22 050 Hz and at `channel_count` 1. Nine rows per
(rate, channels) block, 36 rows per interpreter. **All 36 pass on each of the
three, and the three outputs are identical line for line** — `diff` of the
pass/FAIL lines produced no output in either comparison.

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | pass (0 LSB) | pass | pass | pass (0 LSB) | pass | pass | pass (0 LSB) | pass | pass |
| `mix` 0 is a wire, byte-identical to the source | WIRE | pass (0 of 16384) | pass | pass | pass (0 of 16384) | pass | pass | pass (0 of 16384) | pass | pass |
| Level-honest: unity through the dry path, no hidden gain | LEVEL | pass (+0.0000 dB) | pass | pass | pass (−0.0001 dB) | pass | pass | pass (−0.0000 dB) | pass | pass |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | pass (0; frame 50 → 50) | pass | pass | pass | pass | pass | pass | pass | pass |
| `reset()` leaves every node silent and the borrowed source untouched | STATE | pass (primed 4972 → 0 LSB; source resumes at 28152) | pass | pass | pass (5386 → 0) | pass | pass | pass (3022 → 0) | pass | pass |
| `deinit()` releases every node the class built | STATE | pass (3 enumerated, 0 live) | pass | pass | pass | pass | pass | pass | pass | pass |
| `capabilities` names exactly what is honoured | STATE | pass, `()` | pass | pass | pass | pass | pass | pass | pass | pass |
| Pulling `output` allocates nothing | STATE | pass (kit STATE) | *unmeasured* | *unmeasured* | pass | *unmeasured* | *unmeasured* | pass | *unmeasured* | *unmeasured* |
| Rate-honest: Hz spans clamp below Nyquist, never refuse | RESPONSE | pass (20 kHz → 20 000.0 Hz) | pass | pass | pass (→ 20 000.0 Hz) | pass | pass | pass (→ **10 804.5 Hz**, reading −3.030 dB at its own corner) | pass | pass |
| Every invariant also holds at `channel_count` 1 | (all) | pass, all nine rows | pass | pass | — | — | — | — | — | — |

*The allocation row* is `tracemalloc`-based and therefore CPython only. On
MicroPython and CircuitPython it is **unmeasured** — §11.

**(b) The kit rows**, from `highpass_evidence.py` under CPython, where
WIRE / TAIL / LEVEL / CLICK / STATE / RESPONSE run as the kit implements
them:

```
== Tier 1, 48000 Hz, 2 channel(s) ==
  WIRE      green   
  TAIL      green   
  LEVEL     green   
  CLICK     green   
  STATE     green   
  RESPONSE  green   
  CLAMP     green   20 kHz asked for at 48000 Hz -> built at 20000.0 Hz (ceiling 20000.0), which reads -3.011 dB at its own corner
```

and at `channel_count` 1:

```
== Tier 1, 48000 Hz, 1 channel(s) ==
  WIRE      green   
  TAIL      green   
  LEVEL     green   
  CLICK     green   
  STATE     green   
  RESPONSE  green   
  CLAMP     green   20 kHz asked for at 48000 Hz -> built at 20000.0 Hz (ceiling 20000.0), which reads -3.011 dB at its own corner
```

**Mono.** The dossier's §4 says a mono source gets the identical filter and
that nothing here is stereo by definition. Measured: all nine portable rows
pass at `channel_count` 1 on all three interpreters, and the kit's six
measurements pass at 1 channel under CPython.

**Planted faults for this block**, each with its clean control beside it:

```
== Tier 1 planted faults, 48 kHz ==
  WIRE   clean green / faulted RED  (16320 of 16384 samples differ, first at frame 0 channel 0 (max 153 LSB))
  TAIL   clean green / faulted RED  (residual 71 LSB in the last 12000 frames (bar 0 LSB))
  CLICK  clean green / faulted RED  (measured [0.0, 0.0] samples against a reported 256 (256.0 samples out, bar 1.0) at 48000 Hz); audio digest unchanged 986ff319 -> 986ff319
  STATE  faulted RED  (after reset() and a silent source the output still reaches 631 LSB (bar 0))
```

Nodes enumerated by this class, in build order: `_pole_one`
(`audiobiquad.Biquad`, `HIGH_PASS`), `_pole_two` (same), `_trim`
(`audiobiquad.Biquad`, `HIGH_SHELF`). `reset()` and `deinit()` walk that
list in reverse, tail first.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes, `tools/render_effect.py`, patch 2 (Stage
Low-Cut — 81.2 Hz, Q 0.71, 12 dB/oct), block 256.

```
$ PYTHONPATH=lib .venv/bin/python tools/render_effect.py HighPass <probe> <dir> \
      --rate <rate> --patch 2
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython <same>
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      -X heapsize=256M <same>
```

| Probe | Rate | Block | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 256 | `8712fd99` | `8712fd99` | `8712fd99` | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 256 | `05309c39` | `05309c39` | `05309c39` | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 256 | `61d4fef1` | `61d4fef1` | `61d4fef1` | *(board run)* | *(board run)* |
| `dc_step` | 48000 | 256 | `ead9136d` | `ead9136d` | `ead9136d` | *(board run)* | *(board run)* |
| `chord` | 44100 | 256 | `c974a6a9` | `c974a6a9` | `c974a6a9` | *(board run)* | *(board run)* |
| `chord` | 22050 | 256 | `7de220b1` | `7de220b1` | `7de220b1` | *(board run)* | *(board run)* |

**Desktop agreement: yes.** All three interpreters render byte-identical PCM
on every probe and every rate above; `sum(data)` agrees too and the renderer
prints it beside each digest, but the comparison is the digest.

**Board agreement:** not taken — §4 and §11.

**Block-size ladder**, `chord` at 48 kHz, patch 2:

| Block | 256 | 8192 | 16384 | 20000 | 32768 |
|---|---|---|---|---|---|
| cpython | `8712fd99` | `8712fd99` | `8712fd99` | `8712fd99` | `8712fd99` |
| micropython | `8712fd99` | `8712fd99` | `8712fd99` | `8712fd99` | `8712fd99` |

Byte-identical at every source block size. The class holds no ring buffer
that a block size could outrun.

---

## 4. Tier 3 — cost on the boards

**Not run.** Neither an ESP32-P4 nor an ESP32-S3 was attached this session,
and `tools/measure_effect_cost.py` was not invoked. Every cell below is
`unmeasured`, and the class gate's Tier 3 line is **not met**.

Dossier budget: ESP32-P4 ≤ 1.5 % of one stereo block's real-time deadline at
12 dB/oct and ≤ 2.5 % at 24; ESP32-S3 ≤ 5 % and ≤ 9 %. Lean patch expected:
no.

| Board | Patch | Settings the figure was taken at | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | — | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| S3 | 0 | — | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |

**The expensive path**, when the board run happens, is patch 1 or patch 5
with the Slope macro at 127 and the Trim off its centre: three live sections
rather than one. Patch 0 is one pole and two wires, and ranking the class on
patch 0 alone would rank the wires.

---

## 5. Latency

Reported `latency_samples` = **0**, at every setting and every rate.

```
== Latency: reported against measured ==
  48000 Hz  reported 0  measured (integer) [0.0, 0.0]  (sub-sample) [0.001, 0.001] -> green
  44100 Hz  reported 0  measured (integer) [0.0, 0.0]  (sub-sample) [0.001, 0.001] -> green
```

| Rate | Reported | Measured (integer onset) | Δ | ms |
|---|---|---|---|---|
| 48000 | 0 | 0.0, 0.0 (both channels) | 0 | 0.000 |
| 44100 | 0 | 0.0, 0.0 | 0 | 0.000 |

The sub-sample reading is +0.001 samples at both rates — a minimum-phase
filter's group delay, which is a property of the class and *not* the
processing latency `latency_samples` declares (the kit's CLICK docstring
settles which reading a row wants). The portable driver reads the same thing
the crude way at three rates: a click at input frame 50 leaves at output
frame 50.

Dossier latency budget: zero samples. **Met.**

**Every latency-adding option, each defaulting off or to its shortest:**
there are none. Every section is a recursive biquad reading no sample it has
not been given; no option on this class adds a lookahead, a partition or a
window. The docstring says exactly that, and there is therefore no
millisecond figure for it to name.

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| *(none exists)* | — | 0 | — | n/a — no option adds latency |

Planted fault: `latency_samples` reported 256 short with the DSP unchanged →
**CLICK red at 48 kHz, audio digest unchanged `986ff319` → `986ff319`**. The
fault fires on the latency claim alone, which is what makes it a latency
check rather than an audio check.

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | Frequency | UNIPOLAR | 10 … 20 000 Hz, log; `_hz()` clamps at 0.49·F_s | the low-cut knob |
| 1 | Resonance | UNIPOLAR | Q 0.5 … 16, log | the resonance/emphasis knob |
| 2 | Slope | TOGGLE | 0 = 12 dB/oct, 1 = 24 | a desk's low-cut slope switch |
| 3 | Mix | UNIPOLAR | 0 … 1; 0 is a byte-exact wire | a dry/wet blend |
| 4 | Trim | BIPOLAR | −12 … +12 dB; under 0.2 dB the section is a wire | the make-up a resonant corner needs |

Five of the sixteen the contract allows.

| Patch | Name | What it is for |
|---|---|---|
| 0 | Flat | subsonic protection and nothing else — the constructor's defaults on the grid |
| 1 | Rumble Cut | stage and traffic rumble off a full mix (29.4 Hz, 24 dB/oct) |
| 2 | Stage Low-Cut | the console low-cut a live vocal gets (81.2 Hz) |
| 3 | Thin It Out | take the body out of a pad or a guitar (303 Hz) |
| 4 | Radio | a telephone voice (701 Hz, Q 1.49, 24 dB/oct, −2.93 dB) |
| 5 | Whistle | the corner as an effect (2 057 Hz, Q 10.06, −8.98 dB) |

`patch_index` is 0 on a fresh instance, `None` after any macro move and the
patch's index after `program_change`: held for every class in `ALL` by
`tests/test_cpython_effects_library.py`, and for this class's own grid by
`tests/test_cpython_effects_highpass.py::TheSurface`, which pins patch 0 to
the constructor's own defaults within one grid step and every patch to a
distinct corner.

**`capabilities` = `()`.** The dossier's one-line reason, quoted: *"Nothing
in a high-pass is measured in beats; the class never reads
`self._transport()`."* The portable driver checks the tuple on all three
interpreters at every rate.

---

## 7. Portability tier

**Tier: audioif.** `REQUIRES = ("audiobiquad",)`.

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|
| `Biquad` × 2, `HIGH_PASS` | `audiobiquad` | T1, and Tier 1's exact-zero row | `synthio.Biquad` keeps its output memory in Q12 sample units and rounds to nearest with no dither and no leak, so the recursion has fixed points. Measured on this class's own corners: **71 LSB held for ever at 10 Hz, 18 at 20 Hz, 8 at 30 Hz** (dossier A15). `audiobiquad` is float and writes any state word below 1e-20 as exact zero |
| `Biquad` × 1, `HIGH_SHELF` | `audiobiquad` | the Trim macro | the same node for the same reason: a shelf on the ported biquad has the same fixed points, and it sits in the same chain as the poles |

```
$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
Ran 7 tests in 0.004s

OK
```

The class appears in that battery automatically — it walks
`audioeffects.ALL` and `rebuilt.known()` — so a tier claim here that the
class's `TIER` does not match is a test failure, not a wrong sentence.

**What that test does not prove**, and every pack must repeat it: blocking a
module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace, so a stock-tier class has
*not* been shown rendering on a stock CircuitPython build of the ported C.
That is a gap in the method, not in this class — and for `HighPass` it is
moot in one direction: this class is audioif tier and **cannot** run on a
stock board, which its docstring and its README row both say.

---

## 8. The gate checklist

- [x] The dossier fixed the trait set before the rebuild began (`d2f0c0e`
      precedes `1cc8166`), and §1 lists every trait as demonstrated,
      disconfirmed or unmeasured: **six demonstrated, none disconfirmed,
      none unmeasured**.
- [x] Every Tier 1 invariant is green on CPython and MicroPython at 48 kHz,
      44.1 kHz and 22.05 kHz, and on the patched CircuitPython build — 36
      rows per interpreter, identical line for line — **except** the
      no-allocation row, which is CPython only (§2, §11).
- [x] Every demonstrated Tier 2 trait has a measurement, and that
      measurement was shown red on a planted fault of the same kind (§1,
      column 5).
- [x] Every demonstrated trait survived an independent refutation attempt,
      recorded with the argument and the answer (§1, column 6). Two readings
      were broken and re-taken; no trait fell.
- [x] CPython and desktop MicroPython render identical bytes on the probe
      material — and so does `circuitpython-effects`, on six probe/rate
      combinations and a five-step block-size ladder (§3).
- [ ] **Tier 3 cost is measured on the P4 and the S3.** Not done — §4, §11.
- [x] Reported `latency_samples` equals the measured click delay at 48 kHz
      and 44.1 kHz; the dossier's zero-latency budget is met; no option adds
      latency, so none has to default off (§5).
- [x] The class declares a macro surface (five, at most sixteen) and five
      named patches beyond patch 0 (§6).
- [x] `validate_api`, `validate_metadata`, the CPython tests (the
      contract-level suite plus this class's own 32-test battery, its
      old-surface trait row retired in the same commit), the
      portability-tier test, the three-interpreter smoke and flake8 all pass
      (§9).
- [x] The README catalogue row and the docstring describe the standout, the
      portability tier and the cost, in a musician's terms.
- [x] The class's code, its tests, its README row and its CHANGELOG line
      landed in one commit (`1cc8166`); this file and its two drivers landed in
      `ced7eb7`.

---

## 9. Commands, verbatim

```
$ PYTHONPATH=lib .venv/bin/python -m flake8
(no output, exit 0)

$ PYTHONPATH=lib .venv/bin/python -m unittest discover -s tests -p "test_*.py"
Ran 259 tests in 23.966s
OK (skipped=1)

$ PYTHONPATH=lib .venv/bin/python tools/validate_api.py
validated 53 instruments and 46 effects

$ PYTHONPATH=lib .venv/bin/python tools/validate_metadata.py
audio component metadata is valid

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_portability_tier
Ran 7 tests in 0.004s

OK

$ PYTHONPATH=lib .venv/bin/python -m unittest tests.test_cpython_effects_highpass
Ran 32 tests in 0.999s

OK

$ PYTHONPATH=lib .venv/bin/python tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      tests/parity/effects_library_smoke.py
46 classes, 88 patches, 0 failures

$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/highpass_tier1_portable.py
0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      -X heapsize=256M tools/phase2_probes/highpass_tier1_portable.py
0 failures

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
      -X heapsize=256M tools/phase2_probes/highpass_tier1_portable.py
0 failures

$ PYTHONPATH=lib .venv/bin/python tools/measure_effect_cost.py --subject HighPass --port <COMn>
NOT RUN - no board attached this session (§4, §11)
```

`-X heapsize=256M` on the two native builds is not optional for the portable
driver: it holds a two-second stereo probe resident, and the default heaps
are smaller than that. MicroPython without it raises `MemoryError: memory
allocation failed, allocating 384000 bytes`.

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there.

| Old defect | What the rebuild does |
|---|---|
| **No surface at all** — `MACRO_LABELS = ()` (`eq.py:132`) | five macros and six patches (§6) |
| **`q` frozen at construction** — a bare float at `eq.py:104` where `frequency` got a block | Resonance is a live macro; `_refresh()` writes `Q` on every section on every move |
| **`mix` accepted and then hidden** (taken `eq.py:101`, forwarded `:105`, unreachable after) | Mix is macro 3, and its zero is a byte-exact wire (§2, WIRE) |
| **`set_frequency` is off-contract and it raises** above Nyquist (`eq.py:110-111` → `_core.check_hz`) | there is no `set_frequency`; hertz arrive through the macro grid and `_hz()` **clamps** — measured at 22.05 kHz: 20 kHz asked for is built at 10 804.5 Hz and reads −3.030 dB at its own corner |
| **The default is 1 kHz** — a vocal-thinning filter, not a low-cut | default 10 Hz, patch 0 "Flat" |
| **No tail declared** (`TAIL_SAMPLES = None`) | `TAIL_SAMPLES = 305 152`, from a measurement (dossier A15), and checked against a rendered tail by `TheDeclaredTailIsTheMeasuredOne` |
| **Held DC at low corners**, which contradicted T1 | exact zero at every setting (§1, T1) |
| **`reset()` reaches one node**, and resets the borrowed source through it | `_component.reset()` walks the three nodes this class enumerated, tail first; the borrowed source is never named. Measured on all three interpreters: primed → 0 LSB, and the source resumes |

---

## 11. What is not done

- **The board leg.** No ESP32-P4 or ESP32-S3 was attached this session, so
  `tools/measure_effect_cost.py` was not run, §4 is entirely `unmeasured`,
  and the P4/S3 digest columns in §3 are empty for the same reason. The
  class gate's Tier 3 line is not met, and the dossier's 1.5 % / 5 % budget
  is a budget, not a measurement.
- **The no-allocation invariant on MicroPython and CircuitPython.** The kit's
  STATE measurement reads allocation through `tracemalloc`, which is CPython
  only, so that one row of §2 is `unmeasured` on the two native builds. What
  *is* shown there is that the same class renders byte-identical audio and
  passes the other eight rows on both.
- **T4's 0.00000 dB.** The dossier's figure is arithmetic on the
  coefficients; a render cannot resolve it. The measured 0.0125 dB is the
  render's own int16 floor, and what was checked is the trait's 0.05 dB bar.
- **T3's slope at 24 dB/oct over more than one octave.** Below f₀/8 a
  fourth-order skirt is more than 72 dB down and 16-bit renders it as zero:
  3 of 5 points in the wide fit were under 20 LSB. The one-octave fit the
  trait states is what is demonstrated; a wider one needs a float render
  path the kit does not have.
- **The dossier's T5 measurement cell says "impulse", and it is wrong for
  this class** (§1, T5). The dossier is not edited here — the correction and
  the numbers behind it live in this pack and in `ring_periods()`'s
  docstring. An issue should be filed to fold it back into `HighPass.md` §3
  and to check the sibling filter seeds for the same cell.


---

## Appendix A — the Station C run, verbatim

```
$ PYTHONPATH=lib .venv/bin/python tools/phase2_probes/highpass_evidence.py
```

Tier 2, every trait and its planted fault:

```
== T1  exact zero at DC ==
  f0=10       slope=12  green  residual 0 LSB, dc after removal 0.000 LSB, tail 10525 samples
  f0=10       slope=24  green  residual 0 LSB, dc after removal 0.000 LSB, tail 19847 samples
  f0=30       slope=12  green  residual 0 LSB, dc after removal 0.000 LSB, tail 3532 samples
  f0=100      slope=24  green  residual 0 LSB, dc after removal 0.000 LSB, tail 1963 samples
  f0=2000     slope=12  green  residual 0 LSB, dc after removal 0.000 LSB, tail 53 samples

== T2  |H(f0)| = Q, both slopes ==
  Q        20logQ      12 dB/oct  24 dB/oct
  0.5      -6.021         -6.021     -6.021  green
  0.707107 -3.010         -3.010     -3.010  green
  1        0.000           0.000      0.000  green
  2        6.021           6.021      6.021  green
  4        12.041         12.041     12.042  green
  8        18.062         18.062     18.061  green
  planted fault - the resonance on both Butterworth sections:
    Q 2 at 24 dB/oct reads +15.052 dB against 20log10(2) = +6.021 -> RED

== T3  the skirt, both slopes, and unity at Nyquist ==
  f0       slope   |H(f0/4)|       dB/oct       23 kHz
  20       12        -24.114       12.026        0.000  green
  20       24        -48.192       24.084        0.000  green
  160      12        -24.099       12.026        0.000  green
  160      24        -48.165       24.061        0.000  green
  640      12        -24.109       12.026        0.000  green
  640      24        -48.182       24.160       -0.000  green
  1280     12        -24.138       12.027       -0.000  green
  1280     24        -48.228       24.174       -0.000  green
  3200     12        -24.339       12.039        0.000  green
  3200     24        -48.634       24.089        0.000  green
  planted fault - the second pole left as a wire at 24 dB/oct:
    reads -24.475 dB where the trait says -48.20 +/- 0.60 -> RED

== T4  one curve on the warped axis ==
  f0=31.5     green  worst |dev| from the 31.5 Hz curve 0.0000 dB
  f0=125      green  worst |dev| from the 31.5 Hz curve 0.0117 dB
  f0=500      green  worst |dev| from the 31.5 Hz curve 0.0125 dB
  f0=1000     green  worst |dev| from the 31.5 Hz curve 0.0124 dB
  f0=2000     green  worst |dev| from the 31.5 Hz curve 0.0124 dB
  f0=4000     green  worst |dev| from the 31.5 Hz curve 0.0124 dB
  planted fault - the built corner 15 % off the asked-for one:
    worst |dev| 2.4480 dB against a 0.05 dB bar -> RED

== T5  Q is the ringing (decay time is Q periods) ==
     tone burst at f0, released; periods to e^-pi of the
     amplitude at release. See ring_periods() for why not a click.
  Q=2      e^-pi reached after   2.02 periods = 1.01 Q  green
  Q=4      e^-pi reached after   4.01 periods = 1.00 Q  green
  Q=8      e^-pi reached after   8.00 periods = 1.00 Q  green
  Q=16     e^-pi reached after  16.00 periods = 1.00 Q  green
  planted fault - the built Q a quarter of the asked-for one:
    e^-pi after 2.01 periods = 0.25 Q -> RED

== T6  rate-honest against the closed form at the running rate ==
  worst |rendered - closed form| over every rate/f0/probe: 0.0153 dB (bar 0.10) -> green
  planted fault - coefficients built for 48 kHz while 44.1 kHz runs:
    -27.107 dB against a closed form of -24.100 -> RED
```

The refutation pass, in the same run:

```
== Refutation pass ==
  T2  "|H(f0)| = Q was only checked at f0 = 1 kHz; the corner
      gain could be right there and wrong elsewhere."
      Re-read with the settle scaled to the ring: a Q-16 corner
      at 30 Hz rings for half a second, and a one-second render
      read from its midpoint reads the ring, not the corner
      (it did: +23.933 dB against +24.082, 0.149 dB out).
      f0=30       Q=0.5      -6.021 dB against   -6.021  (1.00 s)  green
      f0=30       Q=4       +12.043 dB against  +12.041  (1.32 s)  green
      f0=30       Q=16      +24.081 dB against  +24.082  (4.52 s)  green
      f0=300      Q=0.5      -6.020 dB against   -6.021  (1.00 s)  green
      f0=300      Q=4       +12.041 dB against  +12.041  (1.00 s)  green
      f0=300      Q=16      +24.082 dB against  +24.082  (1.00 s)  green
      f0=15000    Q=0.5      -6.021 dB against   -6.021  (1.00 s)  green
      f0=15000    Q=4       +12.041 dB against  +12.041  (1.00 s)  green
      f0=15000    Q=16      +24.082 dB against  +24.082  (1.00 s)  green
  T3  "the slope is fitted over one octave, f0/8 to f0/4; two
      points can fit any line."  Fitted over three octaves,
      f0/32 to f0/4, five points -- and the fit is bounded by
      the 16-bit floor, not by the filter: at 24 dB/oct, f0/32
      is 120 dB down, which at any input level inside full
      scale renders as zero. Points under 20 LSB are dropped
      and the count is printed.
      f0=640      slope=12  fitted 12.038 dB/oct over 5 points (0 dropped under 20 LSB)  green
      f0=640      slope=24  unmeasurable: 3 of 5 points under 20 LSB
      f0=3200     slope=12  fitted 12.042 dB/oct over 5 points (0 dropped under 20 LSB)  green
      f0=3200     slope=24  unmeasurable: 3 of 5 points under 20 LSB
  T1  "exact zero could be a mute rather than a filter: a class
      that wrote silence would pass this."
      the same render has 10525 samples of tail before the zero, and 1 kHz through the same corner reads +0.0000 dB
  T6  "three rates agreeing could mean the class ignores the
      rate rather than honouring it."  The fault run above
      moves the reading 3.0 dB, so the measurement can tell the
      difference; and the closed form it is differenced against
      is evaluated at each rate separately.
```

## Appendix B — the portable Tier 1 rows on MicroPython, verbatim

The CircuitPython and CPython outputs are identical to this, line for line
(`diff` of the pass/FAIL lines produced no output in either comparison).

```
$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
      -X heapsize=256M tools/phase2_probes/highpass_tier1_portable.py
HighPass Tier 1, portable rows -- interpreter: micropython

== 48000 Hz, 2 channel(s) ==
  WIRE mix 0                 pass  0 of 16384 samples differ
  TAIL exact zero            pass  0 LSB in the last 12000 frames
  LEVEL unity                pass  wet:dry +0.0000 dB
  CLICK latency 0            pass  reported 0, first output frame 50 (input at 50)
  STATE reset                pass  primed 4972 LSB, after reset 0 LSB (the source replays its silent lead)
  STATE source untouched     pass  28152 LSB once the source reaches its burst again
  STATE deinit               pass  3 nodes enumerated, 0 live afterwards
  STATE capabilities         pass  (); the class never reads self._transport()
  RATE clamp                 pass  20 kHz asked for -> built at 20000.0 Hz (ceiling 20000.0)

== 44100 Hz, 2 channel(s) ==
  WIRE mix 0                 pass  0 of 16384 samples differ
  TAIL exact zero            pass  0 LSB in the last 11025 frames
  LEVEL unity                pass  wet:dry -0.0001 dB
  CLICK latency 0            pass  reported 0, first output frame 50 (input at 50)
  STATE reset                pass  primed 5386 LSB, after reset 0 LSB (the source replays its silent lead)
  STATE source untouched     pass  28139 LSB once the source reaches its burst again
  STATE deinit               pass  3 nodes enumerated, 0 live afterwards
  STATE capabilities         pass  (); the class never reads self._transport()
  RATE clamp                 pass  20 kHz asked for -> built at 20000.0 Hz (ceiling 20000.0)

== 22050 Hz, 2 channel(s) ==
  WIRE mix 0                 pass  0 of 16384 samples differ
  TAIL exact zero            pass  0 LSB in the last 5512 frames
  LEVEL unity                pass  wet:dry -0.0000 dB
  CLICK latency 0            pass  reported 0, first output frame 50 (input at 50)
  STATE reset                pass  primed 3022 LSB, after reset 0 LSB (the source replays its silent lead)
  STATE source untouched     pass  28019 LSB once the source reaches its burst again
  STATE deinit               pass  3 nodes enumerated, 0 live afterwards
  STATE capabilities         pass  (); the class never reads self._transport()
  RATE clamp                 pass  20 kHz asked for -> built at 10804.5 Hz (ceiling 10804.5)

== 48000 Hz, 1 channel(s) ==
  WIRE mix 0                 pass  0 of 8192 samples differ
  TAIL exact zero            pass  0 LSB in the last 12000 frames
  LEVEL unity                pass  wet:dry +0.0000 dB
  CLICK latency 0            pass  reported 0, first output frame 50 (input at 50)
  STATE reset                pass  primed 4972 LSB, after reset 0 LSB (the source replays its silent lead)
  STATE source untouched     pass  28152 LSB once the source reaches its burst again
  STATE deinit               pass  3 nodes enumerated, 0 live afterwards
  STATE capabilities         pass  (); the class never reads self._transport()
  RATE clamp                 pass  20 kHz asked for -> built at 20000.0 Hz (ceiling 20000.0)

0 failures
```
