# The transform length SPECTRUM reads on — 2026-09-17

`tools/effect_measurements.py::exact_bin_size()` used to round. It took the
largest whole number of periods that fits and rounded the product to an
integer sample count, so at 1010 Hz / 48 kHz over 12000 settled frames it
returned 11976 — a quarter of a sample short of whole periods. A rectangular
transform charges for that quarter sample: the same pure tone reads an alias
floor of **-47.0 dB** on 11976 samples and **-95.1 dB** on the exact 9600.
Every Phase 4 gate that cites an alias floor reads it through `spectrum()`
with the default length, so that was a gate failing a working class, or
buying oversampling nobody needed.

It now returns whole periods. When `rate` and `hz` are commensurable a length
is exactly periodic if and only if it is a multiple of
`L = denominator(hz / rate)` samples, and the function returns the largest
multiple of `L` that fits. Only when no multiple fits, or the ratio has no
rational behind it, does it fall back to rounding — and then it picks the
period count that misses by least rather than the largest count that fits.
`tests/test_effect_kit.py::ExactBinSizeTest` holds the fault and its control.

## What this moved, and what it did not

No committed test number changes. Every call site in `tests/` runs at 1000 Hz
or 5500 Hz at 48 kHz over frames that were already whole periods — that run
was instrumented, not estimated, and `exact_bin_size` returned the same
length at all 26 distinct call-and-length combinations, 575 calls.

One test did have to move, and not for its numbers.
`test_effect_kit_graph.py`'s `test_that_is_where_the_seventy_dB_came_from`
reads the low bins of a render whose last 88 frames are silence, and it was
reaching that silence only because the old rounding overshot past it — 11976
samples where whole periods stop at 9600. It now takes its window from the
*end* of the settled region, which is where its defect is, and reads -31.6 dB
against the live control's -111.5 dB where it used to read -33.5 and -112.9.
The guard it exists to explain (`require_live`) is untouched.

The pessimism is confined to a length that lands off the exact grid, which is
what happens at 44.1 k and 22.05 k, and at any quarter-second render. `OLD`
and `NEW` are the two lengths over that many settled frames; `short` is how
many samples the old length was short of whole periods; the two floors are
the alias floor a **pure -6 dBFS tone** reads on each, which is leakage and
nothing else.

| site | rate | hz | frames | OLD | NEW | short | floor OLD | floor NEW |
|---|---|---|---|---|---|---|---|---|
| `tests/` — all 26 call/length pairs | 48000 | 1000 / 5500 | 2048–24000 | = NEW | — | 0.000 | — | — |
| `tools/compressor_evidence.py:366` | 48000 | 50 / 100 / 1000 | any | = NEW | — | 0.000 | — | — |
| " (the one tone with a fractional period) | 48000 | 15000 | 36000 | 36000 | 36000 | 0.000 | -92.2 | -92.2 |
| `probes/overdrive_g4_refute.py` t7_alias | 48000 | 1010 | 24000 | 24000 | 24000 | 0.000 | -91.9 | -91.9 |
| " | 44100 | 1010 | 22050 | 22050 | 22050 | 0.000 | -92.1 | -92.1 |
| " | 22050 | 1010 | 11025 | 11025 | 11025 | 0.000 | -92.1 | -92.1 |
| " (sframes, quarter second) | 48000 | 1010 | 6000 | 5988 | 4800 | 0.119 | **-53.1** | -92.1 |
| " | 44100 | 1010 | 5512 | 5502 | 4410 | 0.416 | **-41.5** | -92.3 |
| " | 22050 | 1010 | 2756 | 2751 | 2205 | 0.208 | **-41.5** | -92.3 |
| " T1/T2/T3/T5 at 1 kHz | 44100 / 22050 | 1000 | 22050 / 11025 | = NEW | — | 0.000 | -92.9 | -92.9 |
| " (sframes) | 44100 | 1000 | 5512 | 5468 | 5292 | 0.400 | **-41.9** | -92.9 |
| " (sframes) | 22050 | 1000 | 2756 | 2734 | 2646 | 0.200 | **-41.9** | -92.6 |
| `probes/saturation_p4fix.py` spec() | 48000 | 1000 | 24000 | 24000 | 24000 | 0.000 | -240 | -240 |
| " | 44100 | 1000 | 24000 | 23990 | 23814 | 0.400 | **-41.9** | -92.9 |
| " | 22050 | 1000 | 24000 | 23990 | 23814 | 0.400 | **-35.9** | -92.6 |
| " walk() | 44100 | 1000 | 12000 | 11995 | 11907 | 0.200 | **-47.9** | -92.9 |
| `probes/distortion/distortion_refute2.py` harm() | 44100 / 22050 | 1000 | 8820 / 4410 | = NEW | — | 0.000 | -92.9 | -92.9 |
| " (rate//10 renders) | 22050 | 1000 | 1102 | 1080 | 882 | 0.450 | **-34.9** | -93.2 |
| `probes/exciter_*.py` | 44100 | 5500 | 22050 / 11025 | = NEW | — | 0.000 | -92.5 | -92.5 |
| " | 22050 | 3010 | 5512 | 5509 | 5355 | 0.163 | **-34.1** | -92.1 |
| `tools/ladderfilter_evidence.py:411` rect read | 48000 | ~999.82 | 24000 | 23956 | 22228 | 0.312 | **-44.8** | -90.1 |

## How to read the bold numbers

A pure tone has no alias products at all, so a bold floor is the highest
number that run could ever have printed. A committed alias floor from one of
those rows is the larger of the class's own floor and that one: **below the
bold figure the number was the transform, not the class.** A floor at -30 dB
from the 22.05 k saturation row is still the class's; a floor at -55 dB from
the same row is leakage, and the class is quieter than the record says by an
unknown margin.

THD and the per-harmonic reads are much safer. The old length put the
fundamental a fraction of a bin off centre, and its own skirt reads about
-91 dB at h2 — so a harmonic above roughly -85 dB is its own, and only a
class whose h2 or THD was recorded below that was reading leakage. The
summed alias floor is the exposed readout because it sums every bin in the
band, and a skirt has a bin everywhere.

The `*_refute2.py` and `*_p4fix.py` probes are one-shot scripts that were run
once and quoted; nothing here re-ran them, and no class was re-measured.
Re-running one is the only way to say what its numbers would be now.

## The fallback, and what it costs

1000.3 Hz is commensurable — 10003/10 — but its exact length is 480000
samples, ten seconds, so nothing that fits is exact and it falls back. So
does a frequency with no rational behind it, like the filter's own 999.82 Hz
above. The fallback buys a small fractional error with bin width: at 1000.3 Hz
over 12000 frames it returns 6670 samples (139 periods, 0.0002 short) where
the old rule returned 11996 (250 periods, 0.4 short), reading -91.9 dB
against -42.6 dB. A caller who needs the resolution more than the floor
should pass `window=` and let `magnitude_spectrum` choose, which is what
`worst_inband` and the ladder filter's T4(b) already do.
