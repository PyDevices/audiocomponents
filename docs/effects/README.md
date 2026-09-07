# Effects dossiers

One file per `audioeffects` class, named `<Class>.md` after its `NAME`, plus
`<Class>-evidence.md` once the class has been rebuilt. This directory belongs
to the **effects program** (anchor repo `docs/effects-vision.md` and
`docs/effects-roadmap.md`); `docs/dossiers/` next door belongs to the
accuracy program and holds instruments.

A dossier here is written **before** the rebuild and fixes the trait set the
rebuild must demonstrate. The shape is [TEMPLATE.md](TEMPLATE.md); the rules
are the vision's §3 (traits), §4 (references, inverted from instruments), §5
(the license gate) and §7 (the stations). The evidence file's shape is
[EVIDENCE-TEMPLATE.md](EVIDENCE-TEMPLATE.md), one section per class-gate
item, in the gate's order. Phase 0 seeds every file; the
implementation session completes it at Station A and adds the evidence file
at Station C.

Nothing in a dossier refers to the previous implementation except in §7,
where a defect the rebuild must not repeat is named. There is no baseline.

## Rebuilt classes

One row per class the effects program has rebuilt, in a musician's terms.
The cost column is the Tier 3 figure from the class's evidence pack, and is
empty until the board run takes it.

| Class | Standout | What it does for you | Tier | Cost (P4 / S3) |
|---|---|---|---|---|
| [`NoiseGate`](NoiseGate.md) | Drawmer DS201 | Shuts the noise floor down by as much as you ask rather than always slamming it to nothing, holds the gate open long enough to make a gated-reverb snare, and listens through its own key band so a tom's gate can ignore the hi-hat above it. `duck=True` inverts it for voice-overs. Two honest limits, both in the class docstring: percussive material triggers it about 0.6 dB earlier than a smooth tone of the same peak, because the key band never leaves the circuit; and a *duck* deeper than about -40 dB does less than the knob says. | audioif (`audiodynamics`, plus `audioroute` and `audiomath` when ducking) | *(board run)* |
