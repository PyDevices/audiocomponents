# Rat clipper and gain stage in ngspice

Netlists written from Distortion.md S1 (ProCo Rat). The clipper deck is the
oracles for F3's ceiling and harmonics; the gain deck is F2's GBW assumption.

## Run

```sh
./run.sh
/home/brad/gh/pydevices/audiocomponents/.venv/bin/python analyze.py
```

## Simplifications, named

- Clipper: ideal source through R6 1K into a matched 1N4148 pair to ground.
  No C7, no 4.5 V bias rail, no Filter, no volume pot.
- Gain AC: two-leg feedback (47 Ohm / 2.2 uF and 560 Ohm / 4.7 uF), 100K
  Distortion at max, C4 100 pF, behavioural op-amp with AOL 100 dB and
  **GBW 0.32 MHz** (dossier Q4: the value that reproduces S1's 30 dB at
  10 kHz). No slew limit. Single supply 0..9 V, input biased at 4.5 V.
- 1N4148 parameters: Nexperia IS/N as Distortion.md S8; comment text not
  copied.

## Analysis (pasted from a real run)

```
$ ./run.sh && python analyze.py
Rat clipper transients (last 10 ms, 1 kHz):
  amp 0.35 V: peak 0.3452 V  THD 0.44 %  h3 -47.5  h5 -57.6
  amp 1.0 V: peak 0.5675 V  THD 16.83 %  h3 -15.6  h5 -30.6
  amp 3.5 V: peak 0.6618 V  THD 32.47 %  h3 -11.2  h5 -17.0
Rat gain AC at pot max: peak 62.03 dB at 458 Hz; 10 kHz 30.02 dB
```

`/usr/bin/ngspice` 42, 2026-09-17. Clipper matches dossier Appendix A to
0.01 V / 0.5 % THD. Gain AC reproduces the licence-audit GBW figures
(peak below 1 kHz, 30 dB at 10 kHz), not the seed's 52 dB / 411 Hz row.
