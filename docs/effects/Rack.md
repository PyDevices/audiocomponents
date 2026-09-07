# Effects Dossier — `Rack` (no historical standout — the mechanism)

**Class:** `lib/audioeffects/rack.py` — read once, for §7, and not otherwise
consulted.
**Family / phase:** Racks, roadmap Phase 6
**Standout:** none — this seed **confirms** vision §4.2's "—, mechanism". A
serial chain is not a product; it is the composition rule every plug-in host
already specifies. The referents are three host contracts (VST 3, CLAP, LV2) and
the filter algebra that says when order matters (JOS).
**Grade:** design
**Portability tier:** **stock** for the mechanism — `rack.py` imports only
`_core` (`:26`) and `audioeffects` (`:31`) and builds no node. A *constructed*
rack's tier is the union of its children's, and the §6 wrapper adds `audioroute`
to that union. The README row states both, not one.
**Status:** seed (Phase 0), written 2026-09-06; audited the same day by an
independent licence and citation pass that re-fetched every row and every URL
itself. Its corrections are marked *(audit 2026-09-06)* below.
Trait-critic pass 2026-09-07: every Tier 2 row rewritten to state its setting,
its tolerance and its control; the order trait split into an LTI half that must
pass and a nonlinear half that must fail; S5 re-reached in that run and the
`audioif_convolve.h`, `eq.py` and `drive.py` line numbers re-checked with
`grep -n`.
Palette-verification pass 2026-09-07 (unit racks): every §4/§5 claim about an
audioif node re-read in `audioif/src/` with `grep -n` and, where it was a claim
about behaviour, probed on both interpreters. Two corrections, marked
*(palette 2026-09-07)*, and one open question closed. **Appendix A6.**

## 1. The circuit, in one paragraph

There is no circuit. The mechanism is a **serial cascade**: N effect components,
each built around the previous one's `output`, presented as one component with
the effect shape (`audio-components.md:160-161`). What the rack owns is
bookkeeping, and every piece of it is specified outside this workspace.
**Latency** adds — a stage's reported group delay is what a host compensates, and
each stage "will modify the input presentation latency of the next plug-ins in
the mixer routing graph" (S1b); the contract states the obligation directly, "A
rack reports the latency and tail of its complete graph"
(`audio-component-api.md:100-101`). **Tail** adds but saturates: "kInfiniteTail
when infinite tail" (S1), so one unbounded child makes the chain unbounded.
**Order** is where the mechanism has content — LTI children commute,
`H₁(z)H₂(z)=H₂(z)H₁(z)` (S5), subject to that page's caveat that ordering still
moves numerical performance, while a chain holding one nonlinear or time-varying
child does not commute at all, which is why a chain is a design object and not a
set. The panel controls a rack generalizes are the two an insert rack has on any
desk and no child can supply: a wet/dry **Mix** and an **Output** trim.

## 2. Sources and license calls

Every source reached in this run; quotations in Appendix A1.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 Steinberg, VST 3 `IAudioProcessor` reference | latency = the group delay a host compensates … (App. S1) | "Copyright © Steinberg Media Technologies … (App. S1) | https://steinbergmedia.github.io/vst3_doc/vstinterfaces/classSteinberg_1_1Vst_1_1IAudioProcessor.html | yes, 2026-09-06; re-fetched by the audit |
| S1b Steinberg, VST 3 `IAudioPresentationLatency` reference | §1's "input presentation latency" sentence … (App. S1b) | "Copyright © Steinberg Media Technologies … (App. S1b) | https://steinbergmedia.github.io/vst3_doc/vstinterfaces/classSteinberg_1_1Vst_1_1IAudioPresentationLatency.html | yes, 2026-09-06 (audit) |
| S2 Steinberg, VST 3 dev portal, Processing FAQ | `kLatencyChanged`; `kInfiniteTail` keeps a plug-in … (App. S2) | "© 2026 Steinberg Media Technologies GmbH. … (App. S2) | https://steinbergmedia.github.io/vst3_dev_portal/pages/FAQ/Processing.html | yes, 2026-09-06; re-fetched by the audit |
| S3 CLAP `ext/tail.h` | tail in samples; ≥ INT32_MAX means infinite | no licence header in the file itself … (App. S3) | https://raw.githubusercontent.com/free-audio/clap/main/include/clap/ext/tail.h | yes, 2026-09-06; re-fetched by the audit |
| S4 CLAP `LICENSE` | the license for S3 and for `ext/latency.h` quoted in A1 | "MIT License … Copyright (c) 2021 Alexandre … (App. S4) | https://raw.githubusercontent.com/free-audio/clap/main/LICENSE | yes, 2026-09-06; re-fetched by the audit |
| S5 J. O. Smith III, *Introduction to Digital Filters with Audio … (App. S5) | LTI cascades commute … (App. S5) | "Copyright © 2026-08-21 by Julius O. Smith … (App. S5) | https://ccrma.stanford.edu/~jos/fp/Series_Combination_Commutative.html | yes, 2026-09-06; re-fetched by the audit |
| S6 LV2 `lv2core` | `lv2:latency` is "The latency introduced, in frames" … (App. S6) | "available under the Creative Commons … (App. S6) | https://lv2plug.in/ns/lv2core | yes, 2026-09-06; re-fetched by the audit |
| S7 this repo | the contract's rack clause and shipped-status paragraph | MIT | `audio-component-api.md:95-115`, `audio-components.md:160-196` | in tree |
| S8 audioif `docs/upstream-diff.md` | `SplitterTap.reset_buffer` does nothing (`:706`) … (App. S8) | MIT | in tree | in tree |

*(More of §2 is in **App. R** — moved under the length rule, nothing deleted.)*

## 3. Traits — fixed before measurement

### Tier 1 — invariants (the standard block, verbatim from vision §3)

The standard block, verbatim from vision §3, is in **App. I** — moved there under the length rule; any class-specific note on it moved with it.

### Tier 2 — circuit traits

Design grade: the textbook properties of a serial cascade, stated to be failed.

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| R1 | `latency_samples` equals the sum of the children's reported `latency_samples` exactly, and a click through the rack emerges that many samples after the same click through the bare source, within ± 1 sample. A chain holding one `ConvolutionReverb` reports ≥ 256 (`audioif_convolve.h:51`, `grep -n` this run), never 0. | S1, S1b, S6, S7; `audioif_convolve.h:20-22` … (App. R1) | high | the report differing from the children's sum by any amount; the measured offset differing from the report by more than 1 sample; or a convolver-bearing chain reporting 0 | click vs dry … (App. R1) |
| R2 | `tail_samples` is the sum of the children's finite tails, and `None` as soon as any child reports `None`. For an all-finite chain the interval from the end of a burst to the last non-zero output sample is **≥ 0.9 × and ≤ 1.0 ×** the reported figure. | S1, S3, S7 | high | a finite report with a non-zero sample past it; a report more than 10 % longer than the measured tail; `None` from all-finite children; or a sum that is not the children's | burst-then-silence … (App. R2) |
| R3 | An empty chain is a wire: `output is source`, `latency_samples` and `tail_samples` are 0, and the rack's FNV digest equals the source's on every probe in the kit's fixed set, at 48, 44.1 and 22.05 kHz. | S7 | high | any node inserted, any digest difference, or a non-zero report | FNV digest of both renders |
| R4 | **Order is neutral for LTI children.** `LowPass` at 1 kHz (`eq.py:114`) and `HighPass` at 200 Hz (`eq.py:126`) in either order give transfer magnitudes agreeing within **0.5 dB** at every analysed frequency from 20 Hz to Nyquist, at −12 dBFS. The bound is this program's, not S5's: S5 gives exact commutativity for the ideal filters and warns only that ordering moves *numerical* performance, so anything above the render's own noise floor is the finding. | S5 | high | any analysed frequency where the two orders differ by more than 0.5 dB — a child that is not LTI, or a rack doing something between its children | swept sine → transfer magnitude … (App. R4) |
| R5 | **Order is decisive once a child is not LTI**, so R4 is not passing on silence: `Distortion` (`drive.py:85`) at a drive yielding ≥ 1 % THD on a 1 kHz sine at −12 dBFS, in series with `LowPass` at 1 kHz, gives a 2 kHz second-harmonic level differing by **more than 6 dB** between the two orders — clip-then-filter attenuates a harmonic the filter never saw, filter-then-clip does not. | S5 (commutativity is an LTI property only) … (App. R5) | high for the … (App. R5) | the two orders agreeing within 6 dB at 2 kHz — a rack that flattens, reorders or bypasses its chain | harmonic spectrum at 1 kHz … (App. R5) |
| R6 | **`reset()` and `deinit()` walk the whole graph, not the tail node.** After rendering the probe and calling `reset()`, a second render of the same probe is byte-identical (FNV digest) to the first — measured on a rack whose last child is built on a `Splitter`, the case a tail-node reset cannot reach, since `SplitterTap.reset_buffer` does nothing (S8 `:706`). After `deinit()` every node any child built is deinitialised except the nodes that carry no `deinit` on the running interpreter, which are named in the evidence rather than claimed — and that set is **not the same on the two interpreters** (A6.1, measured this run): on the workspace MicroPython none of `audioroute.Splitter`, `audioecho.FeedbackDelay`, `audiodynamics.Dynamics`, `audioconvolve.Convolver` or `audiomath.Multiply` has one; on the CPython build only `audioroute.Splitter` lacks it. R6 is therefore measured per interpreter and a green CPython result is never carried across *(palette 2026-09-07)*. | S7, S8 | high | a second render differing from the first by one byte; or any node other than those two still live after `deinit()` | two renders + digest … (App. R6) |
| R7 | **A rack passes its own transport and rate to every child.** With a transport stub at 120 BPM and a tempo-synced delay child on 1/4, the child's delay time reads 500 ms ± one block; at 90 BPM, 666.7 ms ± one block. `capabilities` contains `"tempo_sync"` if and only if at least one child declares it. | S7 (`:103-115`), D10 | medium — §8.1 | a synced child reading the module-global default transport (`_core.py:159`) rather than the rack's; a delay time that does not move with the stub; or a tuple that is not the union of the children's | transport stub advancing tempo … (App. R7) |

### Tier 3 — cost and latency

*(More of §3 is in **App. R** — moved under the length rule, nothing deleted.)*

## 4. Modeling approach on the palette

The rack builds no DSP node and asks for none; it needs correct bookkeeping, and
three palette facts shape it. `SplitterTap.reset_buffer` does nothing (S8 `:706`;
probed this run — a tap pulled, reset, then pulled again resumes where it was
rather than at the source's first sample, A6.2), so resetting a child through the
child's *output* cannot reset any child built on a Splitter. **Lifecycle is not
uniform, and it differs between the two interpreters** *(palette 2026-09-07,
correcting this paragraph's earlier "`Splitter` and `Dynamics` have no lifecycle
at all", which read S8 `:709-712` as a statement about the whole palette when it
is a statement about two modules)*: on the workspace MicroPython **no**
audioif-own node exposes `deinit` — `audioroute.Splitter`,
`audioecho.FeedbackDelay` (`src/audioecho/FeedbackDelay.c:214-219`),
`audiodynamics.Dynamics` (`src/audiodynamics/Dynamics.c:206-209`),
`audioconvolve.Convolver` (`src/audioconvolve/Convolver.c:311-324`) and
`audiomath.Multiply` (`src/audiomath/Multiply.c:212-216`) all lack it — while on
the CPython build every one of them **except `audioroute.Splitter`** inherits
`deinit` from `audiocore._AudioSample` (`src/cpython/audiocore.py:25`;
`audioroute.py:30` and `:64`). So `deinit()` releases every node that has one on
the interpreter it is running on, and the evidence names the rest per interpreter.
`FeedbackDelay.reset_buffer` drops everything (S8 `:806`) where `audiodynamics`
does not, so reset behaviour is not uniform and is never assumed. The rewrite
therefore rests on roadmap §3's requirement that the class "enumerate the nodes it
builds so `reset()` and `deinit()` walk that list"; `Rack` walks the concatenation
of its children's lists, reversed for `deinit()`. Python wires at construction and
on a macro move; C runs nothing extra per sample. A mono source gets a mono rack —
the rack reports its source's channel count, each child states its own mono
behaviour, and the kit measures the chain at `channel_count` 1.

## 5. Node asks

**None.** No trait above is shown unreachable: R1–R7 are bookkeeping and
composition, met by Python at construction and by existing nodes at run time.

## 6. Proposed surface

Three macros — the two an insert rack has on any desk, plus a bypass. A generic
chain has no other knob meaning the same thing for every chain, and a row of
"Macro 1…8" is a surface a host cannot label.

| # | Label | Mode | Range | Generalizes |
|---|---|---|---|---|
| 0 | Mix | UNIPOLAR | 0.0 … 1.0 | the insert's wet/dry |
| 1 | Output | UNIPOLAR | −24 … +12 dB | the return trim |
| 2 | Bypass | TOGGLE | off / on | the footswitch |

The wrapper that makes 0 and 2 real (`Splitter` → dry tap and chain tap →
`Mixer`) is built **only** when the constructor is given `mix < 1.0` or
`bypass=True`; the default builds nothing and keeps the mechanism stock-tier and
free. Characters: none. Patches (names describe settings): `0 "Insert"`,
`1 "Parallel Half"`, `2 "Send Only"`, `3 "Bypassed"`. Options: `chain`
(unchanged in meaning), `mix`, `bypass`, `output_db`, `max_depth`.
`capabilities` is the union of the children's, subject to §8.1.

## 7. Defects in the current class the rebuild must not repeat

From one read of `rack.py` plus two probes (Appendix A2).

- **Reported latency is always zero.** `latency_samples` sums the children …  *(argument in full: App. R)*
- **The tail sum is dead code.** No class declares `TAIL_SAMPLES` …  *(argument in full: App. R)*
- **`reset()` resets the tail node and swallows what it cannot do.** `:103-110` …  *(argument in full: App. R)*
- **`deinit()` leaves nodes live.** `:116-117` calls each child's `deinit()`, …  *(argument in full: App. R)*
- **Children are built at a module global, without a transport.** `_child()` …  *(argument in full: App. R)*
- **A failed chain leaks**: `:63-76` builds in a loop, and an exception on entry
  *k* leaves *k−1* children live and undeinitialised.
- **No surface** (`MACRO_LABELS = ()`, `:56`) — listed here as what the rebuild …  *(argument in full: App. R)*

*(More of §7 is in **App. R** — moved under the length rule, nothing deleted.)*

## 8. Open questions

1. **May a rack compute `capabilities` at construction?** The contract calls it
   "a static tuple of ASCII strings" (`audio-component-api.md:103`) and every
   class declares it at class scope; a rack's honest value is the union of its
   children's, known only once built. If "static" means class-level, R7 is
   unreachable and `Rack` declares `()` forever — a contract wall, which roadmap
   §2a parks and files. *Settles:* the implementation session at Phase 1.
2. **The same question for the portability tier and the README row**, which this
   seed proposes state the mechanism's tier plus the union rule. *Settles:*
   Phase 1, with the `sys.modules`-blocking tier test roadmap §3 describes.
3. **Is a Splitter tap at Mixer level 1.0 byte-identical to its source?**
   **Answered yes, 2026-09-07, on CPython** (A6.3): `Splitter(src, taps=2).tap(0)`
   matches the bare source sample-for-sample, and the same tap through
   `audiomixer.Mixer` voice 0 at `level = 1.0` matches it over every sample
   compared — no offset, no rounding. Sample-aligned, so the wrapper adds no
   latency, which is what Tier 3 claims. What remains for Station B is the same
   digest on the workspace MicroPython and at `channel_count` 1. *Settles:*
   Station B, by digest, before the wrapper is adopted.
4. **`max_depth` for nested racks** — what value, and does exceeding it raise at
   construction or flatten? *Settles:* the implementation session.
5. **Where a rack's own macro lands when a child already owns the same
   parameter.** *Settles:* the implementation session, from the two preset racks.
6. **§6's three macros depart from the class gate's `Rack` exception — deliberately.**
   The class gate excepts the generic `Rack` and calls `MACRO_LABELS = ()` with patch 0
   alone "its correct metadata"; §6 proposes `Mix`, `Output`, `Bypass` and four patches,
   so one of the two documents has to move before Phase 6 reaches this class. The seed's
   case — the exception is a permission, roadmap §3 makes macro sets free, and §6's
   wrapper is built only when `mix < 1.0` or `bypass=True` so the default `Rack` still
   costs nothing — is in **App. R**. Not a contract wall; never put to Brad.
   *Settles:* the implementation session at Phase 6.

*(More of §8 is in **App. R** — moved under the length rule, nothing deleted.)*

## Appendix

### A1. Source quotations, as read on 2026-09-06

**S1, VST 3 `IAudioProcessor`.** `getLatencySamples`: "Gets the current Latency in
samples. The returned value defines the group delay or the latency of the
plug-in. For example, if the plug-in internally needs to look in advance (like
compressors) 512 samples then this plug-in should report 512 as latency. If
during the use of the plug-in this latency change, the plug-in has to inform the
host by using IComponentHandler::restartComponent (kLatencyChanged), this could
lead to audio playback interruption because the host has to recompute its
internal mixer delay compensation. Note that for player live recording this
latency should be zero or small." `getTailSamples`: "Gets tail size in samples.
For example, if the plug-in is a Reverb plug-in and it knows that the maximum
length of the Reverb is 2sec, then it has to return in getTailSamples () … :
2*sampleRate. This information could be used by host for offline processing,
process optimization and downmix (avoiding signal cut (clicks))." Return values:
"kNoTail when no tail", "x * sampleRate when x Sec tail", "kInfiniteTail when
infinite tail". The last sentence of `getLatencySamples` is the stompbox clause
of vision §9a arriving from outside this workspace.

**S1b, VST 3 `IAudioPresentationLatency`.** "Each plug-in adding a latency (returning a
none zero value for IAudioProcessor::getLatencySamples) will modify the input
presentation latency of the next plug-ins in the mixer routing graph and will
modify the output presentation latency of the previous plug-ins."

**S3/S4, CLAP.** `"clap.tail"`, "Returns tail length in samples. Any value
greater or equal to INT32_MAX implies infinite tail." `LICENSE`: "MIT License …
Copyright (c) 2021 Alexandre BIQUE". `ext/latency.h`
(https://raw.githubusercontent.com/free-audio/clap/main/include/clap/ext/latency.h,
fetched by the audit) gives `"clap.latency"` and "Returns the plugin latency in
samples. [main-thread & (being-activated | active)]", and carries no license
header of its own — MIT by the same chain to S4.

**S5, JOS.** "any ordering of filters in series results in the same overall
transfer function"; "Since multiplication of complex numbers is commutative, we
have H₁(z)H₂(z)=H₂(z)H₁(z)"; and the caveat R4 quotes a bound against: "the
numerical performance of the overall filter is usually affected by the ordering
of filter stages in a series combination".

**S6, LV2.** "Control port value is the plugin latency in frames"; "If a plugin
introduces latency it MUST provide EXACTLY ONE port with this property set." The
specification "is available under the Creative Commons Attribution-ShareAlike
License", http://creativecommons.org/licenses/by-sa/3.0/. Both quoted sentences document
the **deprecated** `lv2:reportsLatency`; `lv2:latency` itself is documented only
as "The latency introduced, in frames" (audit A3.4).

### A2. The two probes run for §7

Both under `audiocomponents/.venv/bin/python` with `lib/` on the path, source a
bare `synthio.Synthesizer(sample_rate=48000, channel_count=2)`.

```
Rack(chain=(LowPass, ConvolutionReverb))   latency 0   tail None   caps ()
  LowPass            latency 0  tail None
  ConvolutionReverb  latency 0  tail None
Rack(chain=())                             latency 0   tail 0      output is source: True
ShimmerHall                                latency 0   tail None
```

After `ShimmerHall.deinit()`, checking each node the graph built:

```
Octaver.splitter        STILL LIVE   (splitter.tap(0) returns a SplitterTap)
Octaver.mixer           deinitialized
Octaver.up (PitchShift) STILL LIVE
TapeDelay.node          deinitialized
Reverb.node             deinitialized
```

`audioconvolve.FRAMES` reads 256 from the same interpreter, which is the number
R1 holds a `ConvolutionReverb`-bearing rack to.

### A3. The licence and citation audit, 2026-09-06

An independent pass re-fetched every §2 row and every URL in the file, and
re-checked every in-tree line number with `grep -n`. Five corrections, applied
above; everything not listed here was confirmed as the seed stated it.

1. **S1's licence call.** The seed read "Steinberg SDK license, all rights
   reserved". The page states only "Copyright © Steinberg Media Technologies
   GmbH. All Rights Reserved. This documentation is under this license" — "this
   license" is a link, and the audit did not open it. Recorded as unverified and
   treated as copyleft; the practical treatment (documentation, nothing ported)
   is unchanged.
2. **§1's "input presentation latency" quotation was attributed to S1 and is not
   on S1's page.** It is on `IAudioPresentationLatency`, now S1b, fetched by the
   audit: "Each plug-in adding a latency (returning a none zero value for
   IAudioProcessor::getLatencySamples) will modify the input presentation latency
   of the next plug-ins in the mixer routing graph and will modify the output
   presentation latency of the previous plug-ins." Everything else the seed
   attributes to S1 — `getLatencySamples`, `getTailSamples`, `kNoTail`,
   `kInfiniteTail`, and the "player live recording" sentence — is on S1 verbatim.
3. **S5 is not *PASP*.** The page's own footer reads "Introduction to Digital
   Filters with Audio Applications, by Julius O. Smith III (September 2007
   Edition)". Both quotations and the numerical-performance caveat are verbatim.
4. **S6 ran two LV2 properties together.** "Control port value is the plugin
   latency in frames" and the "EXACTLY ONE port" MUST both document
   `lv2:reportsLatency`, which the specification marks **deprecated**;
   `lv2:latency` is documented as "The latency introduced, in frames". R1 is
   unaffected — LV2 still reports latency in frames on exactly one port — but the
   citation now says which property says what. CC BY-SA 3.0 confirmed.
5. **The "no chain-composition paper" negative, narrowed.** A fresh search
   surfaced DAFx-17 "Audio Processing Chain Recommendation", DAFx-24 "Audio
   Effect Chain Estimation and Dry Signal Recovery", and an arXiv paper on
   order-aware classification of effect chains. None is about composition
   semantics (latency and tail summation, commutativity); none was fetched;
   none is cited.
6. **One line number.** The contract's rack clause is
   `audio-component-api.md:100-101`, not `:99-100` (`grep -n`). Every other
   in-tree citation checked clean: `audio-components.md:160-161`,
   `audio-component-api.md:103`, `audioif_convolve.h:20-22` and `:51` (256),
   `upstream-diff.md:706`, `:709-712`, `:806`, and the Splitter's 32 KB ring
   (8192 frames × 2 × `int16_t`, `audioif_splitter.h:20`).

Confirmed as reached, this run: S1, S1b, S2, S3, S4, S5, S6. CLAP's
`ext/latency.h`, quoted in A1 without a row of its own, was fetched too and is
MIT by the same chain to S4.

### A6. The palette-verification pass, 2026-09-07

Every §4 and §5 claim about an audioif node re-read in `audioif/src/` with
`grep -n`, and every claim about behaviour probed. Sources re-checked clean:
`audioif_convolve.h:51` (`AUDIOIF_CONVOLVE_FRAMES 256u`) and `:20-22` (the one
unavoidable partition of latency); `audioif_splitter.h:20` (`RING_FRAMES 8192u`)
with `:29` (`int16_t ring[RING_FRAMES * 2]` = 32768 bytes = the 32 KB Tier 3
prices) and `:21` (`MAX_TAPS 4u`); `upstream-diff.md:706`, `:709`, `:806`.
`audioroute.Splitter(source, taps=2)` is the real signature
(`src/audioroute/Splitter.c:34`, default 2, refused above 4 at `:43`).

**A6.1 — `deinit` is not a property of the node, it is a property of the
interpreter.** Probed by `hasattr(cls, "deinit")`:

```
                        MicroPython   CPython
audioroute.Splitter          no          no
audioroute.SplitterTap        -          yes
audioecho.FeedbackDelay      no          yes
audiodynamics.Dynamics       no          yes
audioconvolve.Convolver      no          yes
audiomath.Multiply           no          yes
audiofreeverb.Freeverb       yes         yes     (CircuitPython port)
audiodelays.Echo             yes         yes     (CircuitPython port)
```

The MicroPython column is the bindings' own locals tables — no `MP_QSTR_deinit`
in `Splitter.c`, `FeedbackDelay.c:214-219`, `Dynamics.c:206-209`,
`Convolver.c:311-324` or `Multiply.c:212-216`. The CPython column is one line of
inheritance: `_AudioSample.deinit` at `src/cpython/audiocore.py:25`, which every
audioif-own shim subclasses except `Splitter` (`src/cpython/audioroute.py:64`,
against `SplitterTap` at `:30`). R6 and every rack's Tier 1 `deinit()` item are
therefore measured on **both** interpreters or the result means nothing — the
exact shape `workspace-craft.md` calls a checker that has only ever passed.

**A6.2 — `SplitterTap.reset_buffer` really does nothing.** Four pulls from
`tap(0)`, then `audiocore.reset_buffer(tap, False, 0)`, then four more: the
second run starts at `[6534, 6534, 6087, …]` where the first started at
`[0, 0, 575, …]`. The cursor did not move.

**A6.3 — a tap, and a tap through a Mixer at unity, are the source.** A 440 Hz
stereo `RawSample` compared sample-for-sample over 10240 samples: `tap(0)`
matches the bare source exactly, and `Mixer(voice_count=2)` voice 0 at
`level = 1.0` fed from that tap matches it exactly too — first samples
`[0, 0, 575, 575, 1149, 1149, 1719, 1719]` on both paths. §8.3 closed on CPython.

**Probed and not corrected.** `latency 0 / tail None` on
`Rack(LowPass, ConvolutionReverb)` and the post-`deinit()` liveness walk of A2
were not re-run; A2's numbers stand as the previous run recorded them, and A6
does not claim them.

### A5. The trait-critic pass, 2026-09-07

Seven rows, all demonstrable on today's palette. R4 and R5 are a deliberate
pair: R4 must pass and R5 must *fail* to agree, so a suite that returns
"identical" because both renders were silent is caught by its own control
(`workspace-craft.md`, the rig-comparator instance). `Rack` is grade *design*
and would be gated on Tier 1 and Tier 3 alone (vision §4.1); these rows are
offered above that bar, not required by it.

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

Notes, not edits: `mix` at zero is a wire only once the §6 wrapper is built; with
the default `mix=1.0` no wrapper exists and the item is met at the chain level,
which the evidence pack records rather than ticks. A rack is not stereo by
definition — it reports its source's channel count
(`audio-component-api.md:95-96`) and a mono source gets what each child states.

### App. S — §2 source rows, in full

Moved here under the length rule (vision §7; §§1–8 are an 8–12 KB read).
§2 keeps every source id, its lead, its **URL** and its **reached /
not-reached** call — those are the gate conditions — and the full reading
of what each source gave and how its licence reads is here.

| Source | What it gave | License as read | URL | Reached |
|---|---|---|---|---|
| S1 Steinberg, VST 3 `IAudioProcessor` reference | latency = the group delay a host compensates; tail, `kNoTail`, `kInfiniteTail` | "Copyright © Steinberg Media Technologies GmbH. All Rights Reserved." as read; the SDK licence the page links to was not opened, so **licence unverified — treated as copyleft**, and not permissive either way; read as documentation (audit A3.1) | https://steinbergmedia.github.io/vst3_doc/vstinterfaces/classSteinberg_1_1Vst_1_1IAudioProcessor.html | yes, 2026-09-06; re-fetched by the audit |
| S1b Steinberg, VST 3 `IAudioPresentationLatency` reference | §1's "input presentation latency" sentence — which is here and **not** on S1's page, where the seed had cited it (audit A3.2) | "Copyright © Steinberg Media Technologies GmbH. All Rights Reserved." — not permissive; read as documentation | https://steinbergmedia.github.io/vst3_doc/vstinterfaces/classSteinberg_1_1Vst_1_1IAudioPresentationLatency.html | yes, 2026-09-06 (audit) |
| S2 Steinberg, VST 3 dev portal, Processing FAQ | `kLatencyChanged`; `kInfiniteTail` keeps a plug-in processing | "© 2026 Steinberg Media Technologies GmbH. All rights reserved." as read — not permissive | https://steinbergmedia.github.io/vst3_dev_portal/pages/FAQ/Processing.html | yes, 2026-09-06; re-fetched by the audit |
| S3 CLAP `ext/tail.h` | tail in samples; ≥ INT32_MAX means infinite | no licence header in the file itself (checked); **MIT** by the chain to S4, the repository's `LICENSE` | https://raw.githubusercontent.com/free-audio/clap/main/include/clap/ext/tail.h | yes, 2026-09-06; re-fetched by the audit |
| S4 CLAP `LICENSE` | the license for S3 and for `ext/latency.h` quoted in A1 | "MIT License … Copyright (c) 2021 Alexandre BIQUE" | https://raw.githubusercontent.com/free-audio/clap/main/LICENSE | yes, 2026-09-06; re-fetched by the audit |
| S5 J. O. Smith III, *Introduction to Digital Filters with Audio Applications* (Sept. 2007 ed.), "Series Combination is Commutative" — the seed cited *PASP*; the page names this book (audit A3.3) | LTI cascades commute; ordering still moves numerical performance | "Copyright © 2026-08-21 by Julius O. Smith III … CCRMA, Stanford University" as read; no licence stated — **unverified, treated as copyleft**; quoted, not copied | https://ccrma.stanford.edu/~jos/fp/Series_Combination_Commutative.html | yes, 2026-09-06; re-fetched by the audit |
| S6 LV2 `lv2core` | `lv2:latency` is "The latency introduced, in frames"; the "EXACTLY ONE port" MUST documents the **deprecated** `lv2:reportsLatency`, which the seed ran together with it (audit A3.4) | "available under the Creative Commons Attribution-ShareAlike License", CC BY-SA 3.0, as read | https://lv2plug.in/ns/lv2core | yes, 2026-09-06; re-fetched by the audit |
| S8 audioif `docs/upstream-diff.md` | `SplitterTap.reset_buffer` does nothing (`:706`); `Splitter`/`Dynamics` have no `deinit` (`:709-712` — that sentence is about audioroute and audiodynamics only, and A6.1 shows the tree's exception set is wider on MicroPython and narrower on CPython); `FeedbackDelay.reset_buffer` drops everything (`:806`) | MIT | in tree | in tree |

### App. T — Tier 2 rows, in full

Moved here under the length rule. The trait statement, its disconfirmation
and its measurement stay in §3 in full — they are what the gate checks; the
source reading and the confidence reasoning sit here behind each row's
cell-level `App. <id>` reference.

| # | Trait (falsifiable as stated) | Source | Confidence | What would disconfirm it | Measurement (kit) |
|---|---|---|---|---|---|
| R1 | `latency_samples` equals the sum of the children's reported `latency_samples` exactly, and a click through the rack emerges that many samples after the same click through the bare source, within ± 1 sample. A chain holding one `ConvolutionReverb` reports ≥ 256 (`audioif_convolve.h:51`, `grep -n` this run), never 0. | S1, S1b, S6, S7; `audioif_convolve.h:20-22`, `:51` | high | the report differing from the children's sum by any amount; the measured offset differing from the report by more than 1 sample; or a convolver-bearing chain reporting 0 | click vs dry, cross-correlation peak, 48 and 44.1 kHz |
| R2 | `tail_samples` is the sum of the children's finite tails, and `None` as soon as any child reports `None`. For an all-finite chain the interval from the end of a burst to the last non-zero output sample is **≥ 0.9 × and ≤ 1.0 ×** the reported figure. | S1, S3, S7 | high | a finite report with a non-zero sample past it; a report more than 10 % longer than the measured tail; `None` from all-finite children; or a sum that is not the children's | burst-then-silence, last-non-zero index |
| R3 | An empty chain is a wire: `output is source`, `latency_samples` and `tail_samples` are 0, and the rack's FNV digest equals the source's on every probe in the kit's fixed set, at 48, 44.1 and 22.05 kHz. | S7 | high | any node inserted, any digest difference, or a non-zero report | FNV digest of both renders |
| R4 | **Order is neutral for LTI children.** `LowPass` at 1 kHz (`eq.py:114`) and `HighPass` at 200 Hz (`eq.py:126`) in either order give transfer magnitudes agreeing within **0.5 dB** at every analysed frequency from 20 Hz to Nyquist, at −12 dBFS. The bound is this program's, not S5's: S5 gives exact commutativity for the ideal filters and warns only that ordering moves *numerical* performance, so anything above the render's own noise floor is the finding. | S5 | high | any analysed frequency where the two orders differ by more than 0.5 dB — a child that is not LTI, or a rack doing something between its children | swept sine → transfer magnitude, both orders, 48 and 44.1 kHz |
| R5 | **Order is decisive once a child is not LTI**, so R4 is not passing on silence: `Distortion` (`drive.py:85`) at a drive yielding ≥ 1 % THD on a 1 kHz sine at −12 dBFS, in series with `LowPass` at 1 kHz, gives a 2 kHz second-harmonic level differing by **more than 6 dB** between the two orders — clip-then-filter attenuates a harmonic the filter never saw, filter-then-clip does not. | S5 (commutativity is an LTI property only); the measurement itself | high for the direction; medium for the figure — a second-order low-pass at the fundamental puts 2 kHz an octave into the stopband, so 6 dB is deliberately loose | the two orders agreeing within 6 dB at 2 kHz — a rack that flattens, reorders or bypasses its chain | harmonic spectrum at 1 kHz, both orders |
| R6 | **`reset()` and `deinit()` walk the whole graph, not the tail node.** After rendering the probe and calling `reset()`, a second render of the same probe is byte-identical (FNV digest) to the first — measured on a rack whose last child is built on a `Splitter`, the case a tail-node reset cannot reach, since `SplitterTap.reset_buffer` does nothing (S8 `:706`). After `deinit()` every node any child built is deinitialised except the nodes that carry no `deinit` on the running interpreter, which are named in the evidence rather than claimed — and that set is **not the same on the two interpreters** (A6.1, measured this run): on the workspace MicroPython none of `audioroute.Splitter`, `audioecho.FeedbackDelay`, `audiodynamics.Dynamics`, `audioconvolve.Convolver` or `audiomath.Multiply` has one; on the CPython build only `audioroute.Splitter` lacks it. R6 is therefore measured per interpreter and a green CPython result is never carried across *(palette 2026-09-07)*. | S7, S8 | high | a second render differing from the first by one byte; or any node other than those two still live after `deinit()` | two renders + digest; a node-by-node liveness walk after `deinit()`; Tier 1's two planted faults, per child type a shipped rack uses |
| R7 | **A rack passes its own transport and rate to every child.** With a transport stub at 120 BPM and a tempo-synced delay child on 1/4, the child's delay time reads 500 ms ± one block; at 90 BPM, 666.7 ms ± one block. `capabilities` contains `"tempo_sync"` if and only if at least one child declares it. | S7 (`:103-115`), D10 | medium — §8.1 | a synced child reading the module-global default transport (`_core.py:159`) rather than the rack's; a delay time that does not move with the stub; or a tuple that is not the union of the children's | transport stub advancing tempo; child's delay time read back from an impulse |

### App. R — §§1–8 prose moved under the length rule

Derivations, source excerpts, measurement notes and per-row prose, verbatim,
each tagged with the section it came from. The audits check them here.

*(from §2)*

**Looked for, not found.** A DAFx/AES/CCRMA paper on effect-*chain* composition
semantics — latency and tail summation, and when order matters: none found. The
audit searched again and surfaced three chain papers, all **recognition or
recommendation** rather than composition semantics, none fetched and none cited
(A3.5), so the claim stands as narrowed there. The material lives in host
contracts, which is why three are cited. Apple's `kAudioUnitProperty_TailTime` was not fetched and
is not cited; AAX was not attempted.

*(from §3)*

Seven rows, all demonstrable on today's palette. R4 and R5 are a deliberate
pair — R4 must pass and R5 must *fail* to agree — so a suite returning
"identical" on two silent renders is caught by its own control. `Rack` is
grade *design* and would be gated on Tier 1 and Tier 3 alone (vision §4.1);
these are offered above that bar. **Appendix A5.**

*(from §3)*

Budget as a fraction of one stereo block's deadline: ESP32-P4 **0 + Σ(children)**,
ESP32-S3 **0 + Σ(children)** — the rack processes nothing, and the gate measures
that the rack's cost equals the sum of its children's within the cost runner's
run-to-run noise on both boards. The §6 wrapper adds one `audioroute.Splitter`
(a 32 KB ring, S8) and one `audiomixer.Mixer` voice pair, priced once and reused.
Lean patch expected: **no** — a lean rack is a lean chain.

*(from §3)*

Latency: **zero samples (0.0 ms at 48 kHz)** of the rack's own; it never looks
ahead, and **no option of its own adds any** (the wrapper's tap and voice are
same-block). `latency_samples` reports the children's sum, the only number a host
can use (S1). Inherited latency is named in the children's dossiers — the
convolver's 256-frame partition (5.3 ms at 48 kHz), `Dynamics` lookahead (opt-in,
off by default), a pitch window on a wet branch. Phase 6's evidence states each
shipped rack's latency and a five-effect chain's (roadmap M6).

*(from §7)*

- **Reported latency is always zero.** `latency_samples` sums the children
  (`:80-82`) but no class declares `LATENCY_SAMPLES`, so each returns the
  base-class 0 (`_core.py:140`). Probed: `Rack(LowPass, ConvolutionReverb)`
  reports 0, while `ConvolutionReverb`'s docstring says the output trails by
  `audioconvolve.FRAMES` (`reverb.py:87`; 256, `audioif_convolve.h:51`).

*(from §7)*

- **The tail sum is dead code.** No class declares `TAIL_SAMPLES`
  (`_core.py:141`), so the first child returns `None`, `:91` returns `None` for
  every non-empty rack, and the summing line at `:92` has never run. Probed.

*(from §7)*

- **`reset()` resets the tail node and swallows what it cannot do.** `:103-110`
  calls `audiocore.reset_buffer` on each child's *output* only, inside
  `except (AttributeError, RuntimeError): pass` (`:109-110`) — a child whose
  history sits behind its output keeps it, and a node that refuses is skipped
  silently: absence reading as agreement, the shape `workspace-craft.md` names.

*(from §7)*

- **`deinit()` leaves nodes live.** `:116-117` calls each child's `deinit()`,
  which releases only that child's output node (`_core.py:379-383`). Probed on
  `ShimmerHall`: the Octaver's `PitchShift` and `Splitter` survive while the
  Mixer, FeedbackDelay and Freeverb are gone — Tier 1's planted fault, shipping.

*(from §7)*

- **Children are built at a module global, without a transport.** `_child()`
  passes `_core.sample_rate()` (`:29-32`), not the rack's own rate, and no
  transport, so a transport-reading child would silently get the static default
  (`_core.py:159`).

*(from §7)*

- **No surface** (`MACRO_LABELS = ()`, `:56`) — listed here as what the rebuild
  changes, *not* as a contract violation: the class gate excepts the generic
  `Rack` and calls the empty tuple correct metadata. §8.6 argues the departure.
  Also **private reach** (`:105` reads the child's `_source`) and **nesting
  documented with no depth or cycle guard** (`:21`), which are defects outright.

*(from §8)*

6. **§6's three macros depart from the class gate's `Rack` exception — deliberately,
   and this seed argues for the departure.** The roadmap's class gate excepts the
   generic `Rack` from the "at least one named patch beyond patch 0" rule in terms:
   *"its surface is its `chain` literal, and `MACRO_LABELS = ()` with patch 0 alone
   is its correct metadata (`ShimmerHall` and `AirSpace` are not excepted)"*. §6
   proposes `Mix`, `Output`, `Bypass` and four patches, so one of the two documents
   has to move before Phase 6 reaches this class. **The seed's case:** the exception
   is written as a *permission* — a rack whose surface is only its chain is not in
   breach — and roadmap §3 puts "the macro set, its labels, modes and ranges; the
   patches and their names" squarely in the **free** column, which a dossier
   proposes without asking. The three macros are not generic filler: each is the
   control an insert rack has on any desk, each has one meaning for every possible
   chain, and §6 keeps the exception's real intent by building the wrapper
   (`Splitter` → dry tap and chain tap → `Mixer`) **only** when the constructor is
   given `mix < 1.0` or `bypass=True`, so the default `Rack` still costs nothing,
   still needs no audioif-own node, and still has its chain literal as its whole
   surface. On that reading nothing in §6 breaks the exception; it takes the
   permission and adds three labels the exception does not forbid. *Settles:* the
   implementation session at Phase 6 — either by adopting §6 and striking the
   parenthetical from the class gate, or by dropping §6's surface and shipping
   `MACRO_LABELS = ()`. It is **not** a contract wall (roadmap §3 freezes the
   metadata *shape*, and 3 labels with 3 modes and 4 contiguous patches is a legal
   shape), so it is never put to Brad.
