# Evidence Pack — `<Class>` (<standout>)

Copy this file to `docs/effects/<Class>-evidence.md` at Station C and fill
it in. It is the record the class gate is read from (the anchor repo's
`docs/effects-roadmap.md`, "The class gate"), one section per gate item, in
the gate's order. A gate item with no section
filled in is not met; a section filled in from memory rather than from a run
is worse than an empty one.

**Three rules this file is written under.**

1. **Numbers come from runs.** Every figure carries the command that
   produced it and the interpreter and rate it ran on. A measurement nobody
   ran is `unmeasured`, with why no number exists — never a blank, never a
   plausible value.
2. **A measurement with no planted fault cannot be cited.** The kit's
   twenty faults live in `tests/test_effect_kit.py`; a *class's* own faults
   live here. Both must be committed, and the class gate cites both
   ([effects-kit-spec.md](../effects-kit-spec.md) §6).
3. **Say what is not done.** §11 is a section, never a clause inside a
   paragraph that ends "nothing else is pending".

---

## 0. Identity

| | |
|---|---|
| Class / `NAME` | `<Class>` |
| Dossier | [`<Class>.md`](<Class>.md), traits fixed <date> at <commit> |
| Module | `lib/audioeffects/rebuilt/<name_lower>.py` |
| Base | `_component.Component` |
| Family / phase | <family>, roadmap Phase <n> |
| Standout | <the circuit> |
| Grade | circuit \| literature \| proxy \| design |
| Portability tier | **stock** \| **audioif** (`REQUIRES = (...)`) |
| Landed in commit | `<sha>` — code, this file and the CHANGELOG line together |
| audioif pin | `AUDIOIF_PIN` = <tag>, both venvs at <sha> |
| Interpreters | `audiocomponents/.venv/bin/python` <version>; `cmods/bin/micropython` <version>; `cmods/bin/circuitpython-effects` <version> |
| Boards | ESP32-P4 <port/firmware>; ESP32-S3 <port/firmware> |

**Dossier trait set frozen before the rebuild began:** yes / no. If no, the
rebuild is not through its gate — say so here and stop.

---

## 1. Traits

Every trait the dossier fixed, in the dossier's own numbering. Nothing is
added here that the dossier did not fix; a trait dropped after the fact
carries its written reason in the last column, not a deletion.

| # | Trait, as the dossier stated it | Verdict | Measurement · rate · interpreter | Planted fault → result | Refutation: argument, and the answer |
|---|---|---|---|---|---|
| T1 | | demonstrated \| disconfirmed \| unmeasured | RESPONSE, 48 kHz, cpython | corner moved 15 % → RED (clean run green) | <refuter's best case against it, and what settled it> |
| T2 | | | | | |
| T3 | | | | | |

- **demonstrated** needs all three of: a measurement, that measurement shown
  red on a planted fault *of the same kind*, and a surviving refutation.
- **disconfirmed** carries the cause and what the class does instead. A
  disconfirmed trait is a result, not a failure — but it must be visible in
  the class's docstring and its README row, not only here.
- **unmeasured** carries why no number exists and what it would take. It may
  not be used for "we ran out of time" without saying so in §11.

**Characters.** Where the class carries several (`Saturation`'s curves,
`Rotary`'s speeds), each gets its own rows above. A character that fails its
traits may not hide behind one that passes.

**Refutation pass.** Who ran it, when, and against what: <name/session,
date>. The record above is per trait; the pass's own summary — what it went
after and what it could not break — goes here in two or three lines.

---

## 2. Tier 1 invariants

The standard block from the dossier's §3, every cell filled from a run. The
kit measurement that owns each row is named; [effects-kit-spec.md](../effects-kit-spec.md) §5 has the
algorithm and the fault.

**Per interpreter, at each rate.** `cp` = `.venv/bin/python`, `mp` =
`cmods/bin/micropython`, `cpy` = `cmods/bin/circuitpython-effects`. A cell
is `pass`, `FAIL` with the number, or `n/a` with the reason (a node the
patched CircuitPython build does not have).

| Invariant | Kit | 48 k cp | 48 k mp | 48 k cpy | 44.1 k cp | 44.1 k mp | 44.1 k cpy | 22.05 k cp | 22.05 k mp | 22.05 k cpy |
|---|---|---|---|---|---|---|---|---|---|---|
| Silence in → silence out; the tail reaches exact zero, no held DC | TAIL | | | | | | | | | |
| `mix` 0 / depth 0 / drive 0 is a wire, byte-identical to the source delayed by `latency_samples` | WIRE | | | | | | | | | |
| Level-honest: unity through the dry path, no hidden gain | LEVEL | | | | | | | | | |
| Reported `latency_samples` / `tail_samples` match what is measured | CLICK, TAIL | | | | | | | | | |
| `reset()` leaves every node the class built silent and stateless, and the borrowed source untouched | STATE | | | | | | | | | |
| `deinit()` releases every node the class built and leaves the source rendering | STATE | | | | | | | | | |
| `capabilities` names exactly the optional behaviours honoured (`"tempo_sync"` iff the transport is read) | STATE | | | | | | | | | |
| Pulling `output` allocates nothing | STATE | | | | | | | | | |
| Rate-honest: Hz spans and options clamp below Nyquist, never refuse | RESPONSE | | | | | | | | | |
| Every invariant also holds at `channel_count` 1 | (all) | | | | | | | | | |

**Mono.** What a mono source gets, as the dossier's §4 stated it (a wire, or
the mono sum of the stereo behaviour), and the measurement that shows it:

**Planted faults for this block**, each with the command and the clean
control beside it:

| Invariant | Fault planted | Clean run | Faulted run |
|---|---|---|---|
| WIRE | dry path × 32767/32768, on `ramp_fs` | green | RED at offset <n> |
| TAIL | +1 LSB DC in the settled state | green | RED, residual <n> LSB |
| CLICK | report `latency_samples` 256 short | green | RED at both rates |
| STATE | a delay line left full after `reset()`; an intermediate node left live after `deinit()` | green | RED |

`reset()` and `deinit()` walk the node list `_component` requires the class
to enumerate with `self._own()`, so the "which node happened to be last"
dependency `_core` had cannot come back. Nodes enumerated by this class, in
build order: `<list them>`.

---

## 3. Cross-interpreter digests

FNV-1a over the PCM bytes (`effects_component_probe.py:15`), per probe, per
rate, **per source block size**. `sum(data)` is never the comparison.

Command:

```
python tools/render_effect.py --class <Class> --probe chord --rate 48000 --digest
```

| Probe | Rate | Block | cpython | micropython | circuitpython-effects | ESP32-P4 | ESP32-S3 |
|---|---|---|---|---|---|---|---|
| `chord` | 48000 | 2048 | | | | *(board run)* | *(board run)* |
| `noise_det` | 48000 | 2048 | | | | *(board run)* | *(board run)* |
| `sweep_log` | 48000 | 2048 | | | | *(board run)* | *(board run)* |
| `chord` | 44100 | 2048 | | | | *(board run)* | *(board run)* |

**Desktop agreement:** CPython and desktop MicroPython render identical
bytes — yes / no. If no, the cause, recorded here, and it may not be "the
class".

**Board agreement:** the P4 and S3 digests are taken in the cost run (§4)
and are identical to the desktop's, or the difference carries a cause that
is not the class. Float width / FMA contraction is the accepted cause
(the anchor repo's `docs/accuracy-roadmap.md:612-616`, Brad's
per-architecture rule).

**Build against build**, where the class's traits ask for it (a paired
build, a defeated path, an ordering): the export is the ordering or the
difference, never the digests alone.

**Block-size ladder**, where the class's traits ask for it: byte-identical
output from 256-, 8192-, 16384-, 20000- and 32768-frame sources.

---

## 4. Tier 3 — cost on the boards

*(Left for the board run. Fill from `tools/measure_effect_cost.py`; do not
copy a figure from the Phase 1 node table and call it this class's.)*

Dossier budget: ESP32-P4 <x> of one stereo block's real-time deadline;
ESP32-S3 <y>. Lean patch expected: yes / no.

| Board | Patch | Settings the figure was taken at | Blocks/s | ms/block | RT factor | RAM | Within budget |
|---|---|---|---|---|---|---|---|
| P4 | 0 | | | | | | |
| S3 | 0 | | | | | | |
| S3 | `" - lean"` | | | | | | |

**The expensive path was reached**, not idled past: the settings above put
the class in the state its cost is about (a compressor actually reducing
gain, a drive stage above unity, a reverb above mix 0), and the measured
gain reduction / drive / mix is in the settings column. The runner refuses a
render whose digest is the digest of silence; the refusal is the planted
fault, and a muted class must be refused rather than ranked.

Digest printed beside the CPU figure (this is the board leg of §3):
P4 `<fnv>`, S3 `<fnv>`.

---

## 5. Latency

Reported `latency_samples` = `<n>`. Measured click delay against the dry
path, per channel, per patch:

| Rate | Reported | Measured | Δ | ms |
|---|---|---|---|---|
| 48000 | | | | |
| 44100 | | | | |

Dossier latency budget: <n> samples / <n> ms. Met: yes / no.

**Every latency-adding option, each defaulting off or to its shortest**, and
the measured latency with it on, one at a time:

| Option | Default | Latency at default | Latency when on | Named in the docstring, in ms |
|---|---|---|---|---|
| | | | | |

Planted fault: `latency_samples` reported 256 short with the DSP unchanged →
CLICK red at both rates, audio digest unchanged. Result: <>.

---

## 6. Macro surface and patches

| Index | Label | Mode | Engineering span | Panel control it generalizes |
|---|---|---|---|---|
| 0 | | UNIPOLAR \| BIPOLAR \| TOGGLE | | |

At most sixteen; `_component` refuses a seventeenth at construction. A
standout with more panel controls folds them into patches or characters —
say which, here.

| Patch | Name | What it is for |
|---|---|---|
| 0 | | the constructor's defaults on the 0-127 grid |
| 1 | | |

At least one named patch beyond patch 0. *(The generic `Rack` is the one
exception: its surface is its `chain` literal, and `MACRO_LABELS = ()` with
patch 0 alone is its correct metadata. `ShimmerHall` and `AirSpace` are not
excepted.)*

`patch_index` is 0 on a fresh instance, `None` after any macro move, and the
patch's index after `program_change`: shown by
`tests/test_cpython_effects_<family>.py::<test>`.

**`capabilities` = `<tuple>`.** It declares `"tempo_sync"` if and only if
the class reads `self._transport()`; if it is `()`, the dossier's one-line
reason is quoted here.

---

## 7. Portability tier

**Tier:** stock \| audioif. `REQUIRES = (<modules>)`.

Every audioif-own node this class builds on, and the trait each one is
there for:

| Node | Module | Trait it serves | Why the ported palette cannot reach it |
|---|---|---|---|

Test:

```
python -m unittest tests.test_portability_tier
```

Result: `<last lines>`. The class appears in that battery automatically —
it walks `audioeffects.ALL` and `rebuilt.known()` — so a tier claim here
that the class's `TIER` does not match is a test failure, not a wrong
sentence in a document.

**What that test does not prove**, and every pack must repeat it: blocking a
module in `sys.modules` is not a board without the module. No stock
CircuitPython interpreter exists in this workspace, so a stock-tier class
has *not* been shown rendering on a stock CircuitPython build of the ported
C. That is a gap in the method, not in this class.

---

## 8. The gate checklist

Each line is the roadmap's, and is `yes` only when the section above it is
filled from a run.

- [ ] The dossier fixed the trait set before the rebuild began, and §1 lists
      every trait as demonstrated, disconfirmed (with cause) or unmeasured
      (with why no number exists).
- [ ] Every Tier 1 invariant is green on CPython and MicroPython at 48 kHz,
      44.1 kHz and 22.05 kHz, and on the patched CircuitPython build where
      its nodes exist; every Tier 2 measurement names the rate it ran at.
- [ ] Every demonstrated Tier 2 trait has a measurement, and that
      measurement was shown red on a planted fault of the same kind.
- [ ] Every demonstrated trait survived an independent refutation attempt,
      recorded with the refuter's argument and the answer.
- [ ] CPython and desktop MicroPython render identical bytes on the probe
      material; the P4 and S3 digests match the desktop's or their
      difference has a recorded cause that is not the class.
- [ ] Tier 3 cost is measured on the P4 and the S3 and sits within the
      dossier's budget, or a `" - lean"` patch exists that does.
- [ ] Reported `latency_samples` equals the measured click delay at 48 kHz
      and 44.1 kHz; the dossier's latency budget is met; every
      latency-adding option defaults off or to its shortest and is named in
      the docstring in milliseconds.
- [ ] The class declares a macro surface (at most sixteen) and at least one
      named patch beyond patch 0.
- [ ] `validate_api`, `validate_metadata`, the CPython tests (the
      contract-level suite plus this class's own invariant and
      planted-fault tests, its old-surface trait tests retired in the same
      commit), the portability-tier test, the three-interpreter smoke and
      flake8 all pass.
- [ ] The README catalogue row and the docstring describe the standout, the
      portability tier and the cost, in a musician's terms.
- [ ] The class's code, this file and the CHANGELOG line landed in one
      audiocomponents commit, named in §0.

---

## 9. Commands, verbatim

Every gate claim above quotes its command and that command's last lines. Not
a summary of them.

```
$ audiocomponents/.venv/bin/python -m flake8
<last lines>

$ audiocomponents/.venv/bin/python -m unittest discover -s tests -p "test_*.py"
<last lines>

$ audiocomponents/.venv/bin/python tools/validate_api.py
<last lines>

$ audiocomponents/.venv/bin/python tools/validate_metadata.py
<last lines>

$ audiocomponents/.venv/bin/python -m unittest tests.test_portability_tier
<last lines>

$ audiocomponents/.venv/bin/python tests/parity/effects_library_smoke.py
<last lines>

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/micropython \
    tests/parity/effects_library_smoke.py
<last lines>

$ MICROPYPATH=lib:../cmods/micropython/lib ../cmods/bin/circuitpython-effects \
    tests/parity/effects_library_smoke.py
<last lines>

$ audiocomponents/.venv/bin/python tools/measure_effect_cost.py --subject <Class> --port <COMn>
<last lines>
```

---

## 10. Defects in the old class that this rebuild does not repeat

From the dossier's §7, and only from there. One line each, with what the
rebuild does instead. Nothing else about the previous implementation is
carried forward.

---

## 11. What is not done

Its own section, on purpose. Every gap gets its own line — a gap tucked into
a paragraph that ends "nothing else is pending" is the failure this section
exists to prevent.

- <the measurement not run, and what it would take>
- <the trait left `unmeasured`, and why>
- <the board leg not taken, and which board>
- <the issue filed for anything deferred: audiocomponents#nn>

If this section is empty, say so explicitly — "nothing outstanding" written
out — rather than leaving a blank that reads as either.
