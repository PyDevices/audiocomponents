# The measurement kit's probe material

`docs/effects-kit-spec.md` section 3. Generated once on CPython by
`make_probes.py`, never recomputed on a board — the ESP32 ports are
single-precision, so a probe computed there would not be the probe the
desktop measured against.

```
tools/effect_probes/probes.json          the manifest
tools/effect_probes/<rate>/<n>ch/<name>.wav   the data
```

**66 probe names, 388 files, 95.8 MB.** Every probe exists at all three
rates (48000 / 44100 / 22050) and at `channel_count` 1 and 2, and every
probe is **identical in both channels** — STEREO's own clause requires it,
or L−R is not silent at width zero and a correct endpoint reads as broken.

## The manifest is the anti-staleness device

`probes.json` records, per probe and per format: the path, the frame count,
the length in seconds, the measured peak and RMS in dBFS, the byte count,
and the **FNV-1a digest of the PCM bytes** (header excluded — the same
`checksum()` `tools/render_effect.py` uses, which is
`audioif/tests/parity/effects_component_probe.py:15` unchanged). It also
records what each probe *is*: the step table of `tones_step` and
`staircase`, the segment plan of `dc_step`, the burst starts of
`burst_train`, the PRNG and seed of `noise_det`, the achieved level of
every probe whose requested level does not land on an exact int16 value.

`render_effect.py` checks that digest before every render and refuses a
probe that has drifted. `make_probes.py --verify` re-checks the whole set.
Both were shown to fail, not only to pass:

```
$ .venv/bin/python -c "d=bytearray(open('tools/effect_probes/48000/2ch/ramp_fs.wav','rb').read()); d[5000]=(d[5000]+1)&0xff; open(...,'wb').write(bytes(d))"
$ .venv/bin/python tools/effect_probes/make_probes.py --verify
DRIFTED ramp_fs 48000/2: file fc7d8e22, manifest aef0fa61
verified 388 files, 1 bad
$ .venv/bin/python tools/render_effect.py LowPass ramp_fs out
probe tools/effect_probes/48000/2ch/ramp_fs.wav does not match probes.json
(file fc7d8e22, manifest aef0fa61) - it is stale; regenerate with
tools/effect_probes/make_probes.py
```

and with the byte restored, `verified 388 files, 0 bad`.

## Usage

```
make_probes.py                 generate everything, write probes.json
make_probes.py --dry-run       print the plan and the disk cost, write nothing
make_probes.py --verify        re-hash every file against probes.json
make_probes.py --only NAME     regenerate one probe, merging the manifest
```

## Choices a reader should not have to infer

- **`ramp_fs` is a repeating ramp, period 1024 frames**, not one long
  monotonic one. WIRE's planted fault (the dry path scaled by 32767/32768)
  is invisible for every |v| ≤ 16384 under round-half-to-even, so the
  material has to carry samples above half scale in *every* block, not only
  at the ends.
- **`tone_fs4` is levelled so the SAMPLE peak lands on −6.00 dBFS**, which
  makes its true peak −2.99 dB — the pair `Limiter.md:557`–`558` measured
  (−6.00 / −2.95). That is the case where a faulted TRUEPEAK certifies a
  −6 dBFS ceiling as met while 3 dB escapes in the reconstructed waveform.
  It exists at 48 kHz and 44.1 kHz only, as section 3 says.
- **`train10_1k_-6_rms` does not exist.** A matched-RMS 10 %-duty train at
  −6 dBFS needs 36723 LSB and cannot exist in int16. It is omitted, with
  the reason in the manifest, rather than clipped: a silently clipped crest
  probe no longer has the crest factor its name claims.
- **The square and train pairs are generated at 1 kHz only.** The rows they
  serve (`Compressor` V3, `Expander` and `DeEsser` XF, `NoiseGate` G6) vary
  crest factor at a level, not frequency. Adding another frequency is an
  edit to `CREST_FREQUENCY` and a regeneration, not a flag.
- **20 kHz does not exist at 22050 Hz.** `sweep_log` and `tones_step` stop
  at 0.45 × rate, and each file records the ceiling it actually reached.
- **`chord` and `hit_levels_*` are rendered from `audioinstruments`**
  (`juno106` and `tr808` note 38), not recorded. Section 3 says "one
  recorded percussive hit"; the recorded captures in `.reference-captures/`
  are reference material this program analyses and never redistributes, so
  a probe cut from one could not be committed beside the code that reads
  it. The deviation is in the manifest too, not only here.
- **Sines hold a whole number of cycles**, so the fundamental lands on an
  exact FFT bin with no window and the probe can be looped. 1.5 s is 33075
  frames at 22050 Hz, so a 32768-point transform fits at the lowest rate; a
  65536-point one does not, which is why SPECTRUM exports its transform
  length.

## Open, and for a person to decide

95.8 MB of WAV in a repo whose `.git` is 6.1 MB is a real change, and
section 3's "committed as data" was written before anyone had counted it.
The manifest works either way: it is 265 KB of text carrying every digest,
so `--verify` detects drift whether the WAVs are tracked or regenerated
from this directory's own source. Nothing here assumes an answer, and no
`.gitignore` entry has been added.
