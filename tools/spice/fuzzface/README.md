# Fuzz Face in ngspice — Phase 4 of the effects program

A netlist transcribed from the Fuzz dossier's S1 values, with S9's measured
AC128 Ebers-Moll parameters in our own `.model` line. Not a download.

## Run

```
./run.sh
/home/brad/gh/pydevices/audiocomponents/.venv/bin/python analyze.py
```

## Simplifications, named

- Positive-ground PNP pair; Vee = −9 V; emitters at node 0.
- No guitar pickup, no input buffer. Driven from an ideal 200 mV / 1 kHz sine.
- Volume pot as 500 kΩ to ground, wiper at the cap (volume max).
- Fuzz pot as a single resistor `{fuzz}` (1 / 500 / 1000 Ω), no log taper.
- Direct 1 Ω between Q1 collector and Q2 base (the DC couple).
- Gummel-Poon extras from S9 (VAF, IKF, …) included; capacitances omitted
  (CJE/CJC were listed in A3 and are unused here — a named gap).
- 1 µs step, 30 ms run, THD on the last 10 ms.

## Sources

S1 ElectroSmash Fuzz Face (values). S9 DAFx-17 Table 1 (AC128). Both
read as documents; nothing reproduced.
