# DS-1 clipper in ngspice

Netlist written from Distortion.md S2 / S5 Fig. 8: R14 2.2K into a 1N4148
pair to ground with C10 0.01 uF across them (7.2 kHz).

## Run

```sh
./run.sh
/home/brad/gh/pydevices/audiocomponents/.venv/bin/python analyze.py
```

## Simplifications, named

- No Q2 booster, no op-amp Distortion stage, no tone stack. The booster's
  even harmonics are Waveshaper.bias in the class (static; the envelope-
  following bias ask was not granted).
- Matched 1N4148, 0 V bias. Transient at 0.35 / 1.0 / 3.5 V peak.

## Analysis (pasted from a real run)

```
$ ./run.sh && python analyze.py
DS-1 clipper transients (last 10 ms, 1 kHz):
  amp 0.35 V: peak 0.3383 V  THD 0.79 %  h3 -42.4  h5 -54.2
  amp 1.0 V: peak 0.5324 V  THD 17.23 %  h3 -15.5  h5 -29.2
  amp 3.5 V: peak 0.6227 V  THD 31.28 %  h3 -11.4  h5 -17.5
```

`/usr/bin/ngspice` 42, 2026-09-17. 1.0 V and 3.5 V peaks match Appendix A
(0.532 / 0.622 V).
